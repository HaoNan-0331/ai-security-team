"""
跨进程文件锁 - 用于SQLite写入同步
"""
import os
import sys
import time


class DatabaseLock:
    """
    跨进程数据库锁

    使用方式：
        with DatabaseLock(db_path):
            # 执行数据库写入操作
    """

    def __init__(self, db_path: str, timeout: float = 30.0):
        """
        Args:
            db_path: 数据库文件路径
            timeout: 获取锁的超时时间（秒）
        """
        self.lock_path = db_path + '.lock'
        self.timeout = timeout
        self.fd = None

    def __enter__(self):
        self._acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._release()
        return False

    def _acquire(self):
        """获取锁"""
        start = time.time()
        while True:
            try:
                # 确保锁文件目录存在
                lock_dir = os.path.dirname(self.lock_path)
                if lock_dir and not os.path.exists(lock_dir):
                    os.makedirs(lock_dir, exist_ok=True)

                self.fd = open(self.lock_path, 'w')
                self._lock()
                return
            except (IOError, OSError):
                if self.fd:
                    try:
                        self.fd.close()
                    except:
                        pass
                    self.fd = None
                if time.time() - start > self.timeout:
                    raise TimeoutError(f"获取数据库锁超时: {self.lock_path}")
                time.sleep(0.05)

    def _lock(self):
        """平台特定的锁实现"""
        if sys.platform == 'win32':
            import msvcrt
            msvcrt.locking(self.fd.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(self.fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _release(self):
        """释放锁"""
        if self.fd:
            try:
                if sys.platform == 'win32':
                    import msvcrt
                    # Windows需要先移动文件指针到开头
                    self.fd.seek(0)
                    msvcrt.locking(self.fd.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self.fd.fileno(), fcntl.LOCK_UN)
            except:
                pass
            finally:
                try:
                    self.fd.close()
                except:
                    pass
                self.fd = None
