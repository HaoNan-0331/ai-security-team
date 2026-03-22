#!/usr/bin/env python3
"""
Syslog Server Deployment Script
Deploy to Linux server 192.168.31.248
"""

import os
import sys
import tarfile
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import paramiko
except ImportError:
    print("Installing paramiko...")
    os.system("pip install paramiko")
    import paramiko


class SyslogDeployer:
    """Deploy syslog server to remote host."""

    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password
        self.client = None
        self.sftp = None

    def connect(self):
        """Connect to remote server."""
        print(f"Connecting to {self.host}...")

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self.client.connect(
                hostname=self.host,
                username=self.user,
                password=self.password,
                timeout=30
            )
            print(f"[OK] Connected to {self.host}")
            return True
        except Exception as e:
            print(f"[FAIL] Cannot connect: {e}")
            return False

    def execute(self, command, check_result=False):
        """Execute command on remote server."""
        stdin, stdout, stderr = self.client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()

        if check_result and error and "error" in error.lower():
            print(f"  Error: {error}")
            return False

        return output

    def upload_file(self, local_path, remote_path):
        """Upload file to remote server."""
        if not self.sftp:
            self.sftp = self.client.open_sftp()

        try:
            self.sftp.put(local_path, remote_path)
            return True
        except Exception as e:
            print(f"  Upload error: {e}")
            return False

    def deploy(self):
        """Deploy syslog server."""
        print("\n" + "="*60)
        print("  Syslog Server Deployment")
        print("="*60)

        # Step 1: Check server
        print("\n[1/8] Checking server...")

        # Get system info
        output = self.execute("uname -a")
        print(f"  OS: {output.strip()}")

        # Check Docker
        output = self.execute("docker --version 2>&1")
        if "command not found" in output or "not found" in output.lower():
            print("  Docker not found, installing...")
            self.execute("curl -fsSL https://get.docker.com | sh")
            self.execute("systemctl enable docker && systemctl start docker")
        else:
            print(f"  {output.strip()}")

        # Step 2: Create directories
        print("\n[2/8] Creating directories...")
        self.execute("mkdir -p /opt/syslog-server/{config,data,logs,certs}")
        print("  [OK] Directories created")

        # Step 3: Generate passwords
        print("\n[3/8] Generating secure passwords...")
        import secrets
        db_password = secrets.token_urlsafe(32)
        redis_password = secrets.token_urlsafe(24)
        secret_key = secrets.token_urlsafe(64)

        # Step 4: Create environment file
        print("\n[4/8] Creating configuration...")

        env_content = f"""# Production Environment Configuration
APP_ENV=production
LOG_LEVEL=INFO

# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=syslog_db
DB_USER=syslog_user
DB_PASSWORD={db_password}
DB_POOL_SIZE=20

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD={redis_password}

# Syslog Ports
SYSLOG_UDP_PORT=514
SYSLOG_TCP_PORT=514

# Secret
SECRET_KEY={secret_key}

# Data Directories
CONFIG_DIR=/app/config
DATA_DIR=/app/data
LOG_DIR=/app/logs
"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as f:
            f.write(env_content)
            env_file = f.name

        self.sftp = self.client.open_sftp()
        self.sftp.put(env_file, '/tmp/production.env')
        os.unlink(env_file)

        self.execute("mv /tmp/production.env /opt/syslog-server/config/.env")
        print("  [OK] Configuration created")

        # Step 5: Create docker-compose.yml
        print("\n[5/8] Creating docker-compose.yml...")

        compose_content = f"""version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: syslog-postgres
    environment:
      POSTGRES_DB: syslog_db
      POSTGRES_USER: syslog_user
      POSTGRES_PASSWORD: {db_password}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U syslog_user -d syslog_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: syslog-redis
    command: redis-server --requirepass {redis_password} --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "-a", {redis_password}, "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  syslog-server:
    image: syslog-server:latest
    container_name: syslog-server
    network_mode: host
    env_file:
      - config/.env
    ports:
      - "8000:8000"
      - "9090:9090"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
      - ./logs:/app/logs
      - ./certs:/app/certs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
  redis_data:
"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yml') as f:
            f.write(compose_content)
            compose_file = f.name

        self.sftp.put(compose_file, '/opt/syslog-server/docker-compose.yml')
        os.unlink(compose_file)
        print("  [OK] docker-compose.yml created")

        # Step 6: Build Docker image locally
        print("\n[6/8] Building Docker image...")
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Check if Dockerfile exists
        dockerfile_path = os.path.join(project_root, 'Dockerfile')
        if not os.path.exists(dockerfile_path):
            print("  Creating Dockerfile...")
            dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    libpq-dev \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY syslog_server/ /app/syslog_server/

# Create directories
RUN mkdir -p /app/data /app/config /app/logs /app/certs

# Set environment
ENV PYTHONPATH=/app
ENV APP_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Expose ports
EXPOSE 8000 9090 514/udp 514/tcp 6514/tcp

# Run the application
CMD ["python", "-m", "uvicorn", "syslog_server.api:app", "--host", "0.0.0.0", "--port", "8000"]
"""

            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)

        # Build image on remote server
        print("  Building image on server (this may take a few minutes)...")

        # First, copy project files
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create archive
            tar_path = os.path.join(tmpdir, 'syslog-server.tar.gz')

            with tarfile.open(tar_path, 'w:gz') as tar:
                tar.add(os.path.join(project_root, 'syslog_server'), arcname='syslog_server')
                tar.add(os.path.join(project_root, 'requirements.txt'), arcname='requirements.txt')
                tar.add(dockerfile_path, arcname='Dockerfile')

            # Upload archive
            print("  Uploading files...")
            self.sftp.put(tar_path, '/tmp/syslog-server.tar.gz')

        # Extract and build
        self.execute("cd /opt/syslog-server && tar -xzf /tmp/syslog-server.tar.gz")
        self.execute("rm /tmp/syslog-server.tar.gz")

        # Build image
        self.execute("cd /opt/syslog-server && docker build -t syslog-server:latest . 2>&1 | tail -20")
        print("  [OK] Image built")

        # Step 7: Start services
        print("\n[7/8] Starting services...")
        self.execute("cd /opt/syslog-server && docker-compose up -d")
        print("  [OK] Services started")

        # Wait for services to be ready
        print("  Waiting for services to initialize...")
        import time
        time.sleep(20)

        # Step 8: Check status
        print("\n[8/8] Checking service status...")
        output = self.execute("cd /opt/syslog-server && docker-compose ps")
        print(output)

        # Done
        print("\n" + "="*60)
        print("  Deployment Complete!")
        print("="*60)
        print(f"\n  Server: {self.host}")
        print(f"  API: http://{self.host}:8000")
        print(f"  Health: http://{self.host}:8000/health")
        print(f"  Metrics: http://{self.host}:9090/metrics")
        print(f"\n  Syslog Ports: UDP/TCP 514")
        print(f"\n  Useful Commands:")
        print(f"    SSH: ssh {self.user}@{self.host}")
        print(f"    Logs: ssh {self.user}@{self.host} 'cd /opt/syslog-server && docker-compose logs -f'")
        print(f"    Stop: ssh {self.user}@{self.host} 'cd /opt/syslog-server && docker-compose down'")
        print(f"    Restart: ssh {self.user}@{self.host} 'cd /opt/syslog-server && docker-compose restart'")
        print()

    def close(self):
        """Close connections."""
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()


def main():
    """Main entry point."""
    print("Syslog Server Deployment")
    print("="*60)

    # Configuration
    HOST = "192.168.31.248"
    USER = "root"
    PASSWORD = "Qch@2025"

    deployer = SyslogDeployer(HOST, USER, PASSWORD)

    try:
        if not deployer.connect():
            print("Failed to connect to server")
            return 1

        deployer.deploy()
        return 0

    except KeyboardInterrupt:
        print("\nDeployment cancelled")
        return 1
    except Exception as e:
        print(f"Deployment error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        deployer.close()


if __name__ == "__main__":
    sys.exit(main())
