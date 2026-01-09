# backend/app/models/pagination.py
"""
分页响应模型
"""

from typing import Generic, TypeVar, List, Optional, Any
from pydantic import BaseModel, Field
from math import ceil

T = TypeVar('T')


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(1, ge=1, description="页码（从1开始）")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")

    @property
    def skip(self) -> int:
        """计算跳过的记录数"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """获取限制数量"""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    items: List[T] = Field(..., description="数据列表")
    total: int = Field(..., ge=0, description="总记录数")
    page: int = Field(..., ge=1, description="当前页码")
    page_size: int = Field(..., ge=1, description="每页数量")
    total_pages: int = Field(..., ge=0, description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ) -> 'PaginatedResponse[T]':
        """
        创建分页响应

        Args:
            items: 数据列表
            total: 总记录数
            page: 当前页码
            page_size: 每页数量

        Returns:
            分页响应对象
        """
        total_pages = ceil(total / page_size) if total > 0 else 0

        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )


class ApiErrorResponse(BaseModel):
    """API错误响应"""
    success: bool = False
    error: dict = Field(..., description="错误详情")
    path: Optional[str] = None
    timestamp: str


class ApiSuccessResponse(BaseModel):
    """API成功响应"""
    success: bool = True
    data: Any = Field(..., description="响应数据")
    message: Optional[str] = None
    timestamp: str
