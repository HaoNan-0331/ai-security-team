"""
共享数据模型
定义客户端和服务端之间通信的消息格式
Python 3.6 兼容版本
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import json


@dataclass
class TaskMessage:
    """任务消息模型"""
    task_id: str
    client_id: str
    task_type: str  # "ssh", "http", "local", "telnet"
    data: dict
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "TaskMessage":
        data = json.loads(json_str)
        return cls(**data)


@dataclass
class TaskResult:
    """任务结果模型"""
    task_id: str
    client_id: str
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "TaskResult":
        data = json.loads(json_str)
        return cls(**data)


@dataclass
class ClientRegister:
    """客户端注册消息"""
    client_id: str
    hostname: str
    os_info: str
    username: Optional[str] = None  # 登录用户名
    access_token: Optional[str] = None  # 访问Token
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "ClientRegister":
        data = json.loads(json_str)
        return cls(**data)


@dataclass
class SSHParams:
    """SSH执行参数"""
    host: str
    port: int
    username: str
    password: str
    command: str
    timeout: int = 30


@dataclass
class HTTPParams:
    """HTTP请求参数"""
    url: str
    method: str  # "GET", "POST", "PUT", "DELETE"
    headers: dict = field(default_factory=dict)
    body: Optional[str] = None
    timeout: int = 30


@dataclass
class TelnetParams:
    """Telnet执行参数"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    command: str = ""
    timeout: int = 30
    login_prompt: str = "login:"
    password_prompt: str = "Password:"
    shell_prompt: Optional[str] = None
