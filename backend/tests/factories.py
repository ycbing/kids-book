# backend/tests/factories.py
"""
测试数据工厂
使用工厂模式快速创建测试数据
"""

import random
import string
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy.orm import Session

from app.models.database import PictureBook, BookPage, User
from app.models.enums import BookStatus

fake = Faker(['zh_CN'])  # 使用中文假数据生成器


class UserFactory:
    """用户数据工厂"""

    @staticmethod
    def create(
        db: Session,
        username: str = None,
        email: str = None,
        hashed_password: str = "hashed_password",
        commit: bool = True
    ) -> User:
        """创建用户实例"""
        user = User(
            username=username or fake.user_name(),
            email=email or fake.email(),
            hashed_password=hashed_password
        )

        db.add(user)

        if commit:
            db.commit()
            db.refresh(user)

        return user

    @staticmethod
    def create_batch(db: Session, count: int = 10, commit: bool = True) -> list[User]:
        """批量创建用户"""
        users = []
        for _ in range(count):
            user = UserFactory.create(db, commit=False)
            users.append(user)

        if commit:
            db.commit()

        return users


class BookFactory:
    """绘本数据工厂"""

    @staticmethod
    def create(
        db: Session,
        owner_id: int = 1,
        theme: str = None,
        description: str = None,
        target_age: str = None,
        style: str = None,
        status: BookStatus = BookStatus.DRAFT,
        commit: bool = True
    ) -> PictureBook:
        """创建绘本实例"""
        book = PictureBook(
            theme=theme or fake.sentence(nb_words=5)[:-1],  # 去掉句号
            description=description or fake.text(max_nb_chars=200),
            target_age=target_age or random.choice(["3-5", "6-8", "9-12", "13-15"]),
            style=style or random.choice([
                "水彩风格", "卡通风格", "素描风格", "油画风格", "动漫风格"
            ]),
            status=status,
            owner_id=owner_id
        )

        db.add(book)

        if commit:
            db.commit()
            db.refresh(book)

        return book

    @staticmethod
    def create_batch(
        db: Session,
        count: int = 10,
        owner_id: int = 1,
        commit: bool = True
    ) -> list[PictureBook]:
        """批量创建绘本"""
        books = []
        for _ in range(count):
            book = BookFactory.create(db, owner_id=owner_id, commit=False)
            books.append(book)

        if commit:
            db.commit()

        return books

    @staticmethod
    def create_with_pages(
        db: Session,
        owner_id: int = 1,
        page_count: int = 8,
        commit: bool = True
    ) -> PictureBook:
        """创建带页面的绘本"""
        book = BookFactory.create(db, owner_id=owner_id, commit=False)

        for i in range(page_count):
            PageFactory.create(
                db,
                book_id=book.id,
                page_number=i + 1,
                commit=False
            )

        if commit:
            db.commit()
            db.refresh(book)

        return book


class PageFactory:
    """页面数据工厂"""

    @staticmethod
    def create(
        db: Session,
        book_id: int,
        page_number: int = None,
        text_content: str = None,
        image_prompt: str = None,
        image_url: str = None,
        commit: bool = True
    ) -> BookPage:
        """创建页面实例"""
        # 如果没有指定页号，查询该绘本的最大页号+1
        if page_number is None:
            max_page = db.query(BookPage).filter(
                BookPage.book_id == book_id
            ).order_by(BookPage.page_number.desc()).first()

            page_number = (max_page.page_number if max_page else 0) + 1

        page = BookPage(
            book_id=book_id,
            page_number=page_number,
            text_content=text_content or fake.paragraph(nb_sentences=3),
            image_prompt=image_prompt or fake.sentence(nb_words=10),
            image_url=image_url
        )

        db.add(page)

        if commit:
            db.commit()
            db.refresh(page)

        return page

    @staticmethod
    def create_batch(
        db: Session,
        book_id: int,
        count: int,
        commit: bool = True
    ) -> list[BookPage]:
        """批量创建页面"""
        pages = []
        for i in range(count):
            page = PageFactory.create(
                db,
                book_id=book_id,
                page_number=i + 1,
                commit=False
            )
            pages.append(page)

        if commit:
            db.commit()

        return pages


# ================================
# 辅助函数
# ================================

def generate_random_string(length: int = 10) -> str:
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_future_date(days: int = 30) -> datetime:
    """生成未来日期"""
    return datetime.now() + timedelta(days=days)


def generate_past_date(days: int = 30) -> datetime:
    """生成过去日期"""
    return datetime.now() - timedelta(days=days)


# ================================
# 测试数据生成器
# ================================

class TestDataGenerator:
    """测试数据生成器"""

    @staticmethod
    def book_create_request(**kwargs) -> dict:
        """生成绘本创建请求数据"""
        defaults = {
            "theme": fake.sentence(nb_words=5)[:-1],
            "keywords": fake.words(nb=3),
            "target_age": random.choice(["3-5", "6-8", "9-12", "13-15"]),
            "style": random.choice(["水彩风格", "卡通风格", "素描风格"]),
            "page_count": random.randint(4, 16),
            "custom_prompt": fake.text(max_nb_chars=100)
        }

        defaults.update(kwargs)
        return defaults

    @staticmethod
    def book_update_request(**kwargs) -> dict:
        """生成绘本更新请求数据"""
        defaults = {
            "title": fake.sentence(nb_words=4)[:-1],
            "description": fake.text(max_nb_chars=200),
            "theme": fake.sentence(nb_words=5)[:-1]
        }

        defaults.update(kwargs)
        return defaults

    @staticmethod
    def user_credentials(**kwargs) -> dict:
        """生成用户登录数据"""
        defaults = {
            "username": fake.user_name(),
            "password": "TestPassword123!"
        }

        defaults.update(kwargs)
        return defaults

    @staticmethod
    def user_registration(**kwargs) -> dict:
        """生成用户注册数据"""
        defaults = {
            "username": fake.user_name(),
            "email": fake.email(),
            "password": "TestPassword123!"
        }

        defaults.update(kwargs)
        return defaults


# ================================
# 示例使用
# ================================

if __name__ == "__main__":
    from app.models.database import SessionLocal

    db = SessionLocal()

    try:
        # 创建用户
        user = UserFactory.create(db)
        print(f"创建用户: {user.username}")

        # 创建绘本
        book = BookFactory.create_with_pages(
            db,
            owner_id=user.id,
            page_count=5
        )
        print(f"创建绘本: {book.theme}, 页数: {len(book.pages)}")

        # 批量创建
        books = BookFactory.create_batch(db, count=10, owner_id=user.id)
        print(f"批量创建 {len(books)} 本绘本")

    finally:
        db.close()
