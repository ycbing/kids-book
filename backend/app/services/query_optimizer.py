# backend/app/services/query_optimizer.py
"""
数据库查询优化工具

提供：
- 查询优化建议
- 执行计划分析
- 慢查询检测
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import text, func
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.sql import Select
from app.models.database import PictureBook, BookPage, User

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """查询优化器"""

    def __init__(self, db: Session):
        self.db = db

    def explain_query(self, query: Select) -> List[Dict[str, Any]]:
        """
        分析查询执行计划

        Args:
            query: SQLAlchemy查询对象

        Returns:
            执行计划列表
        """
        try:
            # 获取查询的SQL语句
            statement = query.statement
            compiled = statement.compile(
                dialect=self.db.bind.dialect,
                compile_kwargs={"literal_binds": True}
            )

            # 执行EXPLAIN
            result = self.db.execute(
                text(f"EXPLAIN {compiled.string}")
            )

            # 解析结果
            explain_plan = []
            for row in result:
                explain_plan.append(dict(row._mapping))

            return explain_plan

        except Exception as e:
            logger.error(f"执行计划分析失败: {str(e)}")
            return []

    def get_query_stats(self) -> Dict[str, Any]:
        """
        获取数据库统计信息

        Returns:
            统计信息字典
        """
        stats = {
            "tables": {},
            "indexes": {}
        }

        try:
            # 获取表行数
            stats["tables"]["users"] = self.db.query(User).count()
            stats["tables"]["picture_books"] = self.db.query(PictureBook).count()
            stats["tables"]["book_pages"] = self.db.query(BookPage).count()

            # SQLite索引信息
            if self.db.bind.dialect.name == "sqlite":
                result = self.db.execute(text(
                    "SELECT name, tbl_name FROM sqlite_master WHERE type='index'"
                ))
                stats["indexes"] = [dict(row) for row in result]

        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")

        return stats


class OptimizedBookQuery:
    """优化的绘本查询类"""

    def __init__(self, db: Session):
        self.db = db
        self.query = db.query(PictureBook)

    def by_owner(self, user_id: int) -> 'OptimizedBookQuery':
        """
        按所有者筛选（使用索引）
        """
        self.query = self.query.filter(PictureBook.owner_id == user_id)
        return self

    def by_status(self, status: str) -> 'OptimizedBookQuery':
        """
        按状态筛选（使用索引）
        """
        self.query = self.query.filter(PictureBook.status == status)
        return self

    def by_theme(self, theme: str) -> 'OptimizedBookQuery':
        """
        按主题筛选
        """
        self.query = self.query.filter(PictureBook.theme == theme)
        return self

    def recent_first(self) -> 'OptimizedBookQuery':
        """
        按创建时间降序排序（使用索引）
        """
        self.query = self.query.order_by(PictureBook.created_at.desc())
        return self

    def with_pages(self) -> 'OptimizedBookQuery':
        """
        预加载页面数据（使用joinedload避免N+1查询）
        """
        self.query = self.query.options(joinedload(PictureBook.pages))
        return self

    def with_owner(self) -> 'OptimizedBookQuery':
        """
        预加载所有者数据
        """
        self.query = self.query.options(joinedload(PictureBook.owner))
        return self

    def paginate(self, skip: int = 0, limit: int = 20) -> List[PictureBook]:
        """
        分页查询
        """
        return self.query.offset(skip).limit(limit).all()

    def first(self) -> Optional[PictureBook]:
        """
        获取第一条记录
        """
        return self.query.first()

    def count(self) -> int:
        """
        获取总数
        """
        return self.query.count()

    def all(self) -> List[PictureBook]:
        """
        获取所有记录
        """
        return self.query.all()


def get_user_books_optimized(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    with_pages: bool = False
) -> List[PictureBook]:
    """
    优化的用户绘本查询

    Args:
        db: 数据库会话
        user_id: 用户ID
        skip: 跳过记录数
        limit: 限制记录数
        status: 状态筛选（可选）
        with_pages: 是否预加载页面

    Returns:
        绘本列表
    """
    # 使用查询构建器
    query_builder = OptimizedBookQuery(db)

    # 构建查询
    query = query_builder.by_owner(user_id)

    if status:
        query = query.by_status(status)

    # 预加载关联数据（避免N+1查询）
    if with_pages:
        query = query.with_pages()

    # 排序和分页
    return query.recent_first().paginate(skip, limit)


def get_book_with_relationships(
    db: Session,
    book_id: int,
    load_owner: bool = True,
    load_pages: bool = True
) -> Optional[PictureBook]:
    """
    优化的单本绘本查询（包含关联数据）

    Args:
        db: 数据库会话
        book_id: 绘本ID
        load_owner: 是否加载所有者
        load_pages: 是否加载页面

    Returns:
        绘本对象或None
    """
    query = db.query(PictureBook).filter(PictureBook.id == book_id)

    # 使用eager loading优化关联查询
    options = []
    if load_owner:
        options.append(joinedload(PictureBook.owner))
    if load_pages:
        options.append(selectinload(PictureBook.pages))

    if options:
        query = query.options(*options)

    return query.first()


def count_books_by_status(db: Session, user_id: Optional[int] = None) -> Dict[str, int]:
    """
    统计各状态的绘本数量（使用聚合优化）

    Args:
        db: 数据库会话
        user_id: 用户ID（可选，用于统计特定用户）

    Returns:
        状态计数字典
    """
    query = db.query(
        PictureBook.status,
        func.count(PictureBook.id)
    ).group_by(PictureBook.status)

    if user_id:
        query = query.filter(PictureBook.owner_id == user_id)

    results = query.all()
    return {status.value: count for status, count in results}


def get_popular_themes(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """
    获取热门主题（使用聚合和索引）

    Args:
        db: 数据库会话
        limit: 返回数量

    Returns:
        热门主题列表
    """
    results = db.query(
        PictureBook.theme,
        func.count(PictureBook.id).label('count')
    ).group_by(
        PictureBook.theme
    ).order_by(
        func.count(PictureBook.id).desc()
    ).limit(limit).all()

    return [
        {"theme": theme, "count": count}
        for theme, count in results
    ]


def batch_insert_pages(
    db: Session,
    pages_data: List[Dict[str, Any]]
) -> List[BookPage]:
    """
    批量插入页面（优化插入性能）

    Args:
        db: 数据库会话
        pages_data: 页面数据列表

    Returns:
        创建的页面对象列表
    """
    pages = []
    for page_data in pages_data:
        page = BookPage(**page_data)
        db.add(page)
        pages.append(page)

    db.commit()

    # 刷新以获取ID
    for page in pages:
        db.refresh(page)

    return pages


def update_book_status_optimized(
    db: Session,
    book_id: int,
    new_status: str
) -> bool:
    """
    优化的状态更新（只更新必要字段）

    Args:
        db: 数据库会话
        book_id: 绘本ID
        new_status: 新状态

    Returns:
        是否成功
    """
    try:
        # 只更新status和updated_at字段
        db.query(PictureBook).filter(
            PictureBook.id == book_id
        ).update({
            "status": new_status,
            "updated_at": func.now()
        }, synchronize_session=False)

        db.commit()
        return True

    except Exception as e:
        logger.error(f"更新状态失败: {str(e)}")
        db.rollback()
        return False


# 查询性能监控
def log_slow_query(query: Select, threshold: float = 1.0):
    """
    慢查询日志装饰器

    Args:
        query: 查询对象
        threshold: 慢查询阈值（秒）

    Returns:
        装饰器函数
    """
    import time
    from functools import wraps

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            if duration > threshold:
                logger.warning(
                    f"慢查询检测: {func.__name__} "
                    f"耗时: {duration:.3f}秒 > {threshold}秒"
                )

            return result
        return wrapper
    return decorator
