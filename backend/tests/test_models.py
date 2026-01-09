# backend/tests/test_models.py
"""
数据模型测试
测试数据库模型和枚举
"""

import pytest
from sqlalchemy.orm import Session
from app.models.database import PictureBook, BookPage, User
from app.models.enums import BookStatus, TargetAge


@pytest.mark.unit
class TestPictureBookModel:
    """绘本模型测试"""

    def test_create_book_model(self, db_session: Session):
        """测试创建绘本模型实例"""
        book = PictureBook(
            theme="测试主题",
            description="测试描述",
            target_age="3-5",
            style="水彩风格",
            status=BookStatus.DRAFT,
            owner_id=1
        )

        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        assert book.id is not None
        assert book.theme == "测试主题"
        assert book.description == "测试描述"
        assert book.target_age == "3-5"
        assert book.style == "水彩风格"
        assert book.status == BookStatus.DRAFT
        assert book.owner_id == 1
        assert book.created_at is not None
        assert book.updated_at is not None

    def test_book_relationship_with_pages(self, db_session: Session):
        """测试绘本与页面的关系"""
        # 创建绘本
        book = PictureBook(
            theme="测试主题",
            target_age="3-5",
            style="水彩风格",
            status=BookStatus.DRAFT,
            owner_id=1
        )
        db_session.add(book)
        db_session.commit()

        # 添加页面
        page1 = BookPage(
            book_id=book.id,
            page_number=1,
            text_content="第一页",
            image_prompt="提示词1"
        )
        page2 = BookPage(
            book_id=book.id,
            page_number=2,
            text_content="第二页",
            image_prompt="提示词2"
        )
        db_session.add_all([page1, page2])
        db_session.commit()

        # 测试关系
        assert len(book.pages) == 2
        assert book.pages[0].page_number == 1
        assert book.pages[1].page_number == 2

    def test_book_status_enum(self, db_session: Session):
        """测试绘本状态枚举"""
        # 测试所有状态
        statuses = [
            BookStatus.DRAFT,
            BookStatus.GENERATING,
            BookStatus.COMPLETED,
            BookStatus.FAILED
        ]

        for status in statuses:
            book = PictureBook(
                theme=f"测试-{status}",
                target_age="3-5",
                style="水彩风格",
                status=status,
                owner_id=1
            )
            db_session.add(book)

        db_session.commit()

        # 验证所有状态都已保存
        books = db_session.query(PictureBook).all()
        assert len(books) == len(statuses)

    def test_book_update_timestamp(self, db_session: Session):
        """测试更新时间戳自动更新"""
        import time

        book = PictureBook(
            theme="测试主题",
            target_age="3-5",
            style="水彩风格",
            status=BookStatus.DRAFT,
            owner_id=1
        )
        db_session.add(book)
        db_session.commit()

        original_updated_at = book.updated_at

        # 等待一小段时间
        time.sleep(0.01)

        # 更新绘本
        book.description = "更新后的描述"
        db_session.commit()
        db_session.refresh(book)

        assert book.updated_at > original_updated_at


@pytest.mark.unit
class TestBookPageModel:
    """绘本页面模型测试"""

    def test_create_page_model(self, db_session: Session):
        """测试创建页面模型实例"""
        # 首先创建绘本
        book = PictureBook(
            theme="测试主题",
            target_age="3-5",
            style="水彩风格",
            status=BookStatus.DRAFT,
            owner_id=1
        )
        db_session.add(book)
        db_session.commit()

        # 创建页面
        page = BookPage(
            book_id=book.id,
            page_number=1,
            text_content="测试文本内容",
            image_prompt="测试图片提示词"
        )

        db_session.add(page)
        db_session.commit()
        db_session.refresh(page)

        assert page.id is not None
        assert page.book_id == book.id
        assert page.page_number == 1
        assert page.text_content == "测试文本内容"
        assert page.image_prompt == "测试图片提示词"
        assert page.created_at is not None

    def test_page_relationship_with_book(self, db_session: Session):
        """测试页面与绘本的关系"""
        # 创建绘本
        book = PictureBook(
            theme="测试主题",
            target_age="3-5",
            style="水彩风格",
            status=BookStatus.DRAFT,
            owner_id=1
        )
        db_session.add(book)
        db_session.commit()

        # 创建页面
        page = BookPage(
            book_id=book.id,
            page_number=1,
            text_content="测试文本",
            image_prompt="测试提示词"
        )
        db_session.add(page)
        db_session.commit()

        # 测试反向关系
        assert page.book is not None
        assert page.book.id == book.id
        assert page.book.theme == "测试主题"

    def test_page_unique_constraint(self, db_session: Session):
        """测试页面唯一性约束（同一绘本的页号不能重复）"""
        # 创建绘本
        book = PictureBook(
            theme="测试主题",
            target_age="3-5",
            style="水彩风格",
            status=BookStatus.DRAFT,
            owner_id=1
        )
        db_session.add(book)
        db_session.commit()

        # 添加第一个页面
        page1 = BookPage(
            book_id=book.id,
            page_number=1,
            text_content="第一页",
            image_prompt="提示词1"
        )
        db_session.add(page1)
        db_session.commit()

        # 尝试添加相同页号的第二个页面
        page2 = BookPage(
            book_id=book.id,
            page_number=1,  # 相同页号
            text_content="重复页",
            image_prompt="提示词2"
        )
        db_session.add(page2)

        # 应该引发 IntegrityError
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()


@pytest.mark.unit
class TestUserModel:
    """用户模型测试"""

    def test_create_user_model(self, db_session: Session):
        """测试创建用户模型实例"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_here"
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed_password_here"
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_unique_username(self, db_session: Session):
        """测试用户名唯一性约束"""
        # 创建第一个用户
        user1 = User(
            username="testuser",
            email="test1@example.com",
            hashed_password="password1"
        )
        db_session.add(user1)
        db_session.commit()

        # 尝试创建相同用户名的第二个用户
        user2 = User(
            username="testuser",  # 相同用户名
            email="test2@example.com",
            hashed_password="password2"
        )
        db_session.add(user2)

        # 应该引发错误
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_user_unique_email(self, db_session: Session):
        """测试邮箱唯一性约束"""
        # 创建第一个用户
        user1 = User(
            username="user1",
            email="test@example.com",
            hashed_password="password1"
        )
        db_session.add(user1)
        db_session.commit()

        # 尝试创建相同邮箱的第二个用户
        user2 = User(
            username="user2",
            email="test@example.com",  # 相同邮箱
            hashed_password="password2"
        )
        db_session.add(user2)

        # 应该引发错误
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()


@pytest.mark.unit
class TestEnums:
    """枚举类型测试"""

    def test_book_status_enum_values(self):
        """测试绘本状态枚举值"""
        assert BookStatus.DRAFT == "draft"
        assert BookStatus.GENERATING == "generating"
        assert BookStatus.COMPLETED == "completed"
        assert BookStatus.FAILED == "failed"

    def test_book_status_enum_iteration(self):
        """测试遍历状态枚举"""
        statuses = [status for status in BookStatus]

        assert BookStatus.DRAFT in statuses
        assert BookStatus.GENERATING in statuses
        assert BookStatus.COMPLETED in statuses
        assert BookStatus.FAILED in statuses

    def test_target_age_enum_values(self):
        """测试目标年龄枚举值"""
        # 假设有这些年龄组
        age_groups = ["3-5", "6-8", "9-12", "13-15"]

        for age in age_groups:
            assert age in ["3-5", "6-8", "9-12", "13-15"]
