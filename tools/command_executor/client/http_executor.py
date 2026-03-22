"""
HTTP请求模块
使用requests发送HTTP/HTTPS请求
"""
import requests
import logging
from typing import Tuple, Dict, Optional

logger = logging.getLogger(__name__)


class HTTPExecutor:
    """HTTP请求执行器"""

    @staticmethod
    def execute(
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        timeout: int = 30
    ) -> Tuple[bool, str, str, int]:
        """
        执行HTTP请求

        返回: (成功, 响应体, 错误信息, 状态码)
        """
        try:
            # 准备请求参数
            request_headers = headers or {}
            request_body = body

            # 发送请求
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=request_headers,
                data=request_body,
                timeout=timeout,
                verify=False  # 忽略SSL证书验证
            )

            # 获取响应内容
            response_body = response.text

            # 判断是否成功 (2xx状态码)
            success = 200 <= response.status_code < 300

            logger.info(f"HTTP请求完成: {method} {url}, status={response.status_code}")

            return success, response_body, "", response.status_code

        except requests.exceptions.Timeout:
            logger.error(f"HTTP请求超时: {url}")
            return False, "", "请求超时", 0

        except requests.exceptions.ConnectionError as e:
            logger.error(f"HTTP连接错误: {e}")
            return False, "", f"连接错误: {str(e)}", 0

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP请求错误: {e}")
            return False, "", f"请求错误: {str(e)}", 0

        except Exception as e:
            logger.error(f"HTTP执行错误: {e}")
            return False, "", f"执行错误: {str(e)}", 0
