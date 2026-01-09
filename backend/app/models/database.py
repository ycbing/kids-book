# backend/app/models/database.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum, Index, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import QueuePool
from datetime import datetime
import enum
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# 检测数据库类型
def is_sqlite_database(url: str) -> bool:
    """检查是否为SQLite数据库"""
    return url.startswith("sqlite")

def get_engine_config():
    """获取数据库引擎配置"""
    db_url = settings.DATABASE_URL

    if is_sqlite_database(db_url):
        # SQLite配置（开发环境）
        logger.info("📦 使用SQLite数据库（开发环境）")

        # SQLite性能优化
        connect_args = {"check_same_thread": False}

        # 启用WAL模式和性能优化
        def on_connect(dbapi_conn, connection_record):
            """SQLite连接时执行的性能优化"""
            cursor = dbapi_conn.cursor()
            # 启用WAL模式（提高并发）
            cursor.execute("PRAGMA journal_mode=WAL")
            # 同步模式（性能与安全平衡）
            cursor.execute("PRAGMA synchronous=NORMAL")
            # 缓存大小（-20000表示20MB）
            cursor.execute("PRAGMA cache_size=-20000")
            # 临时存储在内存中
            cursor.execute("PRAGMA temp_store=MEMORY")
            # 页面大小（4096字节）
            cursor.execute("PRAGMA page_size=4096")
            cursor.close()

        return {
            "url": db_url,
            "connect_args": connect_args,
            "echo": settings.DEBUG,
            "pool_pre_ping": True,  # 连接前检查
            # SQLite连接池配置
            "poolclass": QueuePool,
            "pool_size": 5,
            "max_overflow": 10,
        }
    else:
        # PostgreSQL配置（生产环境）
        logger.info("🐘 使用PostgreSQL数据库（生产环境）")

        return {
            "url": db_url,
            "poolclass": QueuePool,
            "pool_size": settings.DB_POOL_SIZE,  # 连接池大小
            "max_overflow": settings.DB_MAX_OVERFLOW,  # 最大溢出连接数
            "pool_pre_ping": True,  # 连接前检查有效性
            "pool_recycle": settings.DB_POOL_RECYCLE,  # 连接回收时间
            "echo": settings.DB_ECHO,  # SQL日志
            # 连接超时
            "connect_args": {
                "connect_timeout": 10,
                "options": "-c statement_timeout=30000"  # 30秒查询超时
            },
        }

# 创建数据库引擎
engine_config = get_engine_config()
engine = create_engine(**engine_config)

# SQLite性能优化事件监听器
if is_sqlite_database(settings.DATABASE_URL):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """SQLite连接时执行的性能优化"""
        cursor = dbapi_conn.cursor()
        # 启用WAL模式（提高并发）
        cursor.execute("PRAGMA journal_mode=WAL")
        # 同步模式（性能与安全平衡）
        cursor.execute("PRAGMA synchronous=NORMAL")
        # 缓存大小（-20000表示20MB）
        cursor.execute("PRAGMA cache_size=-20000")
        # 临时存储在内存中
        cursor.execute("PRAGMA temp_store=MEMORY")
        # 页面大小（4096字节）
        cursor.execute("PRAGMA page_size=4096")
        cursor.close()

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

class BookStatus(enum.Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    books = relationship("PictureBook", back_populates="owner", cascade="all, delete-orphan")

    # 用户表索引优化
    __table_args__ = (
        Index('idx_users_created_at', 'created_at'),
        Index('idx_users_username_email', 'username', 'email'),
    )

class PictureBook(Base):
    __tablename__ = "picture_books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200))
    description = Column(Text)
    theme = Column(String(100))
    target_age = Column(String(20))  # 目标年龄段
    style = Column(String(50))  # 绘画风格
    status = Column(Enum(BookStatus), default=BookStatus.DRAFT)
    cover_image = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    owner = relationship("User", back_populates="books")
    pages = relationship("BookPage", back_populates="book", order_by="BookPage.page_number")

    # 绘本表索引优化
    __table_args__ = (
        # 复合索引用于用户绘本列表查询
        Index('idx_picture_books_owner_created', 'owner_id', 'created_at'),
        # 状态索引用于筛选
        Index('idx_picture_books_status', 'status'),
        # 时间索引用于排序
        Index('idx_picture_books_created_at', 'created_at'),
        # 更新时间索引用于增量同步
        Index('idx_picture_books_updated_at', 'updated_at'),
        # 主题和年龄段索引（用于内容搜索）
        Index('idx_picture_books_theme_age', 'theme', 'target_age'),
        # 风格索引
        Index('idx_picture_books_style', 'style'),
        # owner和status复合索引（常用的过滤条件组合）
        Index('idx_picture_books_owner_status', 'owner_id', 'status'),
    )

class BookPage(Base):
    __tablename__ = "book_pages"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("picture_books.id", ondelete="CASCADE"))
    page_number = Column(Integer)
    text_content = Column(Text)
    image_prompt = Column(Text)
    image_url = Column(String(500))
    layout = Column(JSON)  # 页面布局配置
    created_at = Column(DateTime, default=datetime.utcnow)

    book = relationship("PictureBook", back_populates="pages")

    # 页面表索引优化
    __table_args__ = (
        # book_id索引用于关联查询
        Index('idx_book_pages_book_id', 'book_id'),
        # book_id和page_number复合索引用于获取书的页面（有序）
        Index('idx_book_pages_book_number', 'book_id', 'page_number'),
        # 创建时间索引用于排序
        Index('idx_book_pages_created_at', 'created_at'),
    )

# 创建表（仅SQLite）
if is_sqlite_database(settings.DATABASE_URL):
    Base.metadata.create_all(bind=engine)
    logger.info("✅ SQLite数据库表已创建")
else:
    # PostgreSQL使用Alembic进行迁移
    logger.info("ℹ️  PostgreSQL数据库，请使用Alembic进行迁移: alembic upgrade head")

# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
