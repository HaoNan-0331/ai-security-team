"""
密码加密解密工具
使用Fernet对称加密
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


# 默认密钥文件路径
DEFAULT_KEY_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', '.secret_key')


def generate_key(password: str = None, salt: bytes = None) -> bytes:
    """
    生成加密密钥

    Args:
        password: 密码字符串，如果不提供则生成随机密钥
        salt: 盐值，如果不提供则生成随机盐

    Returns:
        Fernet兼容的密钥
    """
    if password is None:
        return Fernet.generate_key()

    if salt is None:
        salt = os.urandom(16)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


def _get_key() -> bytes:
    """
    获取或创建加密密钥

    Returns:
        Fernet密钥
    """
    import threading

    key_file = os.environ.get('ASSET_DB_KEY_FILE', DEFAULT_KEY_FILE)

    # 确保目录存在
    key_dir = os.path.dirname(key_file)
    if key_dir and not os.path.exists(key_dir):
        os.makedirs(key_dir, exist_ok=True)

    # 使用文件锁避免竞态条件
    lock_path = key_file + '.lock'
    lock_fd = None

    try:
        # 获取锁
        lock_fd = open(lock_path, 'w')
        import sys
        if sys.platform == 'win32':
            import msvcrt
            msvcrt.locking(lock_fd.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)

        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # 生成新密钥并保存
            key = generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # 设置文件权限为仅所有者可读写
            if os.name != 'nt':  # 非Windows系统
                os.chmod(key_file, 0o600)
            return key
    finally:
        # 释放锁
        if lock_fd:
            try:
                import sys
                if sys.platform == 'win32':
                    import msvcrt
                    lock_fd.seek(0)
                    msvcrt.locking(lock_fd.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
            except:
                pass
            finally:
                lock_fd.close()


def encrypt_password(password: str) -> str:
    """
    加密密码

    Args:
        password: 明文密码

    Returns:
        加密后的密码（Base64编码）
    """
    if not password:
        return ''

    key = _get_key()
    f = Fernet(key)
    encrypted = f.encrypt(password.encode())
    return encrypted.decode()


def decrypt_password(encrypted_password: str) -> str:
    """
    解密密码

    Args:
        encrypted_password: 加密后的密码

    Returns:
        明文密码
    """
    if not encrypted_password:
        return ''

    try:
        key = _get_key()
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_password.encode())
        return decrypted.decode()
    except Exception as e:
        raise ValueError(f"密码解密失败: {str(e)}")


def verify_key(key: bytes) -> bool:
    """
    验证密钥是否有效

    Args:
        key: Fernet密钥

    Returns:
        是否有效
    """
    try:
        Fernet(key)
        return True
    except Exception:
        return False
