"""限流装饰器生成器"""
from core.decorators import Generator
from ..base import BaseTemplateGenerator


@Generator(
    category="decorator",
    priority=85,
    description="生成限流装饰器 (app/decorators/rate_limit.py)"
)
class RateLimitDecoratorGenerator(BaseTemplateGenerator):
    """限流装饰器生成器"""

    def generate(self) -> None:
        """生成限流装饰器文件"""
        content = '''"""API 接口限流装饰器"""
import time
from functools import wraps
from typing import Dict, Callable
from fastapi import HTTPException, Request
from collections import defaultdict


class RateLimiter:
    """简单的内存级限流器
    
    注意：
        这是一个仅适用于单实例应用的基础实现。
        在多实例或分布式生产环境中，建议使用基于 Redis 的限流方案。
    """
    
    def __init__(self):
        # 存储结构: {identifier: [timestamp, ...]}
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """判断当前请求是否允许通过限流规则
        
        参数：
            identifier: 唯一标识（如 IP 地址、用户 ID）
            max_requests: 时间窗口内允许的最大请求数
            window_seconds: 时间窗口（秒）
            
        返回：
            bool: 允许返回 True，否则返回 False
        """
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        # 清理时间窗口之外的旧请求
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff_time
        ]
        
        # 判断是否超过限流阈值
        if len(self.requests[identifier]) >= max_requests:
            return False
        
        # 记录当前请求时间
        self.requests[identifier].append(current_time)
        return True
    
    def get_remaining(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int
    ) -> int:
        """获取当前时间窗口内剩余可用请求次数
        
        参数：
            identifier: 唯一标识
            max_requests: 最大允许请求数
            window_seconds: 时间窗口（秒）
            
        返回：
            int: 剩余请求次数
        """
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        # 统计当前时间窗口内的请求数量
        recent_requests = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff_time
        ]
        
        return max(0, max_requests - len(recent_requests))


# 全局限流器实例
rate_limiter = RateLimiter()


def rate_limit(
    max_requests: int = 100,
    window_seconds: int = 60,
    identifier_func: Callable[[Request], str] = None
):
    """FastAPI 接口限流装饰器
    
    参数：
        max_requests: 时间窗口内允许的最大请求数
        window_seconds: 时间窗口（秒）
        identifier_func: 从 Request 中提取唯一标识的函数（默认使用客户端 IP）
        
    示例：
        @router.get("/api/data")
        @rate_limit(max_requests=10, window_seconds=60)
        async def get_data(request: Request):
            return {"data": "value"}
        
        # 自定义标识（例如用户 ID）
        @router.get("/api/user-data")
        @rate_limit(
            max_requests=50,
            window_seconds=3600,
            identifier_func=lambda req: req.state.user.id
        )
        async def get_user_data(request: Request):
            return {"data": "value"}
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从参数中提取 Request 对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                request = kwargs.get('request')
            
            if not request:
                raise ValueError("未在函数参数中找到 Request 对象")
            
            # 获取唯一标识（默认使用客户端 IP）
            if identifier_func:
                identifier = identifier_func(request)
            else:
                identifier = request.client.host if request.client else "unknown"
            
            # 检查是否超过限流
            if not rate_limiter.is_allowed(identifier, max_requests, window_seconds):
                remaining = rate_limiter.get_remaining(
                    identifier, max_requests, window_seconds
                )
                raise HTTPException(
                    status_code=429,
                    detail=f"请求过于频繁，请在 {window_seconds} 秒后重试。",
                    headers={
                        "X-RateLimit-Limit": str(max_requests),
                        "X-RateLimit-Remaining": str(remaining),
                        "X-RateLimit-Reset": str(int(time.time() + window_seconds))
                    }
                )
            
            # 执行原始接口函数
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# 常用限流装饰器封装
def rate_limit_strict(func):
    """严格限流：每分钟最多 10 次请求"""
    return rate_limit(max_requests=10, window_seconds=60)(func)


def rate_limit_moderate(func):
    """中等限流：每分钟最多 100 次请求"""
    return rate_limit(max_requests=100, window_seconds=60)(func)


def rate_limit_relaxed(func):
    """宽松限流：每小时最多 1000 次请求"""
    return rate_limit(max_requests=1000, window_seconds=3600)(func)
'''
        
        self.file_ops.create_file(
            file_path="app/decorators/rate_limit.py",
            content=content,
            overwrite=True
        )
