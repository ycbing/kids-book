# backend/app/models/database.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum, Index
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
        # SQLite配置
        logger.info("📦 使用SQLite数据库（开发环境）")
        return {
            "url": db_url,
            "connect_args": {"check_same_thread": False},
            "echo": settings.DEBUG,
        }
    else:
        # PostgreSQL配置（生产环境）
        logger.info("🐘 使用PostgreSQL数据库（生产环境）")
        return {
            "url": db_url,
            "poolclass": QueuePool,
            "pool_size": 5,  # 连接池大小
            "max_overflow": 10,  # 最大溢出连接数
            "pool_pre_ping": True,  # 连接前检查有效性
            "pool_recycle": 3600,  # 1小时后回收连接
            "echo": settings.DEBUG,
        }

# 创建数据库引擎
engine_config = get_engine_config()
engine = create_engine(**engine_config)

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
    
    books = relationship("PictureBook", back_populates="owner")

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

    # 添加索引以优化查询性能
    __table_args__ = (
        Index('idx_picture_books_owner_created', 'owner_id', 'created_at'),
        Index('idx_picture_books_status', 'status'),
        Index('idx_picture_books_created_at', 'created_at'),
    )

class BookPage(Base):
    __tablename__ = "book_pages"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("picture_books.id"))
    page_number = Column(Integer)
    text_content = Column(Text)
    image_prompt = Column(Text)
    image_url = Column(String(500))
    layout = Column(JSON)  # 页面布局配置
    created_at = Column(DateTime, default=datetime.utcnow)
    
    book = relationship("PictureBook", back_populates="pages")

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
