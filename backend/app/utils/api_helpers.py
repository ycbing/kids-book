# backend/app/utils/api_helpers.py
"""
API辅助工具函数
"""

from typing import TypeVar, List, Optional, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from fastapi import Query
from app.models.pagination import PaginatedResponse, PaginationParams

T = TypeVar('T')


def paginate_query(
    db: Session,
    model: T,
    page: int = 1,
    page_size: int = 20,
    filters: Optional[Dict] = None,
    order_by: Optional[Any] = None,
    options: Optional[List] = None
) -> PaginatedResponse:
    """
    通用分页查询函数

    Args:
        db: 数据库会话
        model: 模型类
        page: 页码
        page_size: 每页数量
        filters: 过滤条件字典
        order_by: 排序字段
        options: 预加载选项

    Returns:
        分页响应对象
    """
    # 构建基础查询
    query = db.query(model)

    # 应用过滤条件
    if filters:
        for key, value in filters.items():
            if value is not None:
                query = query.filter(getattr(model, key) == value)

    # 获取总数
    total = query.count()

    # 应用排序
    if order_by:
        query = query.order_by(order_by)

    # 应用预加载
    if options:
        query = query.options(*options)

    # 应用分页
    skip = (page - 1) * page_size
    items = query.offset(skip).limit(page_size).all()

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


async def async_paginate_query(
    query,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """
    异步分页查询（适用于async/await）

    Args:
        query: SQLAlchemy查询对象
        page: 页码
        page_size: 每页数量

    Returns:
        分页结果字典
    """
    # 获取总数
    total_query = select(func.count()).select_from(query.subquery())
    total = await query.session.execute(total_query)
    total = total.scalar()

    # 应用分页
    skip = (page - 1) * page_size
    items = await query.offset(skip).limit(page_size).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0
    }


def get_pagination_params(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
) -> PaginationParams:
    """
    获取分页参数的依赖注入函数

    Usage:
        @router.get("/books")
        async def list_books(
            params: PaginationParams = Depends(get_pagination_params)
        ):
            ...
    """
    return PaginationParams(page=page, page_size=page_size)


def build_pagination_links(
    base_url: str,
    page: int,
    page_size: int,
    total_pages: int,
    **kwargs
) -> Dict[str, Optional[str]]:
    """
    构建分页链接（用于响应头）

    Args:
        base_url: 基础URL
        page: 当前页码
        page_size: 每页数量
        total_pages: 总页数
        **kwargs: 其他查询参数

    Returns:
        分页链接字典
    """
    links = {
        "self": f"{base_url}?page={page}&page_size={page_size}",
        "first": f"{base_url}?page=1&page_size={page_size}",
        "last": f"{base_url}?page={total_pages}&page_size={page_size}" if total_pages > 0 else None,
    }

    if page > 1:
        links["prev"] = f"{base_url}?page={page-1}&page_size={page_size}"

    if page < total_pages:
        links["next"] = f"{base_url}?page={page+1}&page_size={page_size}"

    return links


def sanitize_response(data: Any, exclude_fields: List[str] = None) -> Any:
    """
    清理响应数据（移除敏感字段）

    Args:
        data: 响应数据
        exclude_fields: 要排除的字段列表

    Returns:
        清理后的数据
    """
    if isinstance(data, dict):
        if exclude_fields:
            return {k: v for k, v in data.items() if k not in exclude_fields}
        return data

    elif isinstance(data, list):
        return [sanitize_response(item, exclude_fields) for item in data]

    elif hasattr(data, '__dict__'):
        # SQLAlchemy模型对象
        if exclude_fields:
            return {
                k: v for k, v in data.__dict__.items()
                if not k.startswith('_') and k not in exclude_fields
            }
        return {k: v for k, v in data.__dict__.items() if not k.startswith('_')}

    return data


def format_response(
    success: bool = True,
    data: Any = None,
    message: str = None,
    error: dict = None
) -> Dict[str, Any]:
    """
    统一格式化API响应

    Args:
        success: 是否成功
        data: 响应数据
        message: 提示消息
        error: 错误详情

    Returns:
        格式化的响应字典
    """
    from datetime import datetime

    response = {
        "success": success,
        "timestamp": datetime.utcnow().isoformat()
    }

    if success:
        response["data"] = data
        if message:
            response["message"] = message
    else:
        response["error"] = error

    return response
