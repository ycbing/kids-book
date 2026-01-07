# backend/app/models/database.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

from app.config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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
    
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="books")
    pages = relationship("BookPage", back_populates="book", order_by="BookPage.page_number")

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

# 创建表
Base.metadata.create_all(bind=engine)

# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
