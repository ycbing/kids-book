# backend/app/core/exceptions.py
"""
统一异常处理
定义应用中的所有自定义异常类
"""
from typing import Optional, Any


class AppException(Exception):
    """应用基础异常类

    所有自定义异常的基类，提供统一的错误响应格式
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "INTERNAL_ERROR"
        self.details = details
        super().__init__(message)

    def to_dict(self) -> dict:
        """转换为字典格式，用于API响应"""
        result = {
            "success": False,
            "error": {
                "code": self.error_code,
                "message": self.message
            }
        }
        if self.details is not None:
            result["error"]["details"] = self.details
        return result


class NotFoundException(AppException):
    """资源不存在异常 (404)"""

    def __init__(self, message: str = "资源不存在", details: Any = None):
        super().__init__(message, 404, "NOT_FOUND", details)


class BadRequestException(AppException):
    """请求参数错误异常 (400)"""

    def __init__(self, message: str = "请求参数错误", details: Any = None):
        super().__init__(message, 400, "BAD_REQUEST", details)


class UnauthorizedException(AppException):
    """未授权异常 (401)"""

    def __init__(self, message: str = "未授权访问", details: Any = None):
        super().__init__(message, 401, "UNAUTHORIZED", details)


class ForbiddenException(AppException):
    """无权限访问异常 (403)"""

    def __init__(self, message: str = "无权限访问", details: Any = None):
        super().__init__(message, 403, "FORBIDDEN", details)


class ValidationException(AppException):
    """数据验证失败异常 (422)"""

    def __init__(self, message: str = "数据验证失败", details: Any = None):
        super().__init__(message, 422, "VALIDATION_ERROR", details)


class ConflictException(AppException):
    """资源冲突异常 (409)"""

    def __init__(self, message: str = "资源冲突", details: Any = None):
        super().__init__(message, 409, "CONFLICT", details)


class RateLimitException(AppException):
    """请求过于频繁异常 (429)"""

    def __init__(self, message: str = "请求过于频繁", details: Any = None):
        super().__init__(message, 429, "RATE_LIMIT_EXCEEDED", details)


class ExternalServiceException(AppException):
    """外部服务异常 (502)"""

    def __init__(
        self,
        message: str = "外部服务调用失败",
        service_name: str = "unknown",
        details: Any = None
    ):
        full_message = f"{service_name}: {message}" if service_name != "unknown" else message
        super().__init__(full_message, 502, "EXTERNAL_SERVICE_ERROR", details)


class DatabaseException(AppException):
    """数据库操作异常 (500)"""

    def __init__(self, message: str = "数据库操作失败", details: Any = None):
        super().__init__(message, 500, "DATABASE_ERROR", details)


# 便捷函数
def not_found(resource: str, id: Any = None) -> NotFoundException:
    """创建404异常的便捷函数"""
    message = f"{resource}不存在"
    if id is not None:
        message += f" (ID: {id})"
    return NotFoundException(message)


def bad_request(field: str, reason: str) -> BadRequestException:
    """创建400异常的便捷函数"""
    return BadRequestException(f"{field}: {reason}")


def unauthorized(reason: str = "需要登录") -> UnauthorizedException:
    """创建401异常的便捷函数"""
    return UnauthorizedException(reason)


def forbidden(action: str, resource: str = "该资源") -> ForbiddenException:
    """创建403异常的便捷函数"""
    return ForbiddenException(f"无权限{action}{resource}")


def validation_error(field: str, reason: str) -> ValidationException:
    """创建422异常的便捷函数"""
    return ValidationException(f"{field}验证失败: {reason}")
