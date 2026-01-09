# backend/tests/test_services.py
"""
服务层测试
测试业务逻辑和服务
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.book_service import book_service
from app.models.database import PictureBook, BookPage
from app.models.enums import BookStatus


@pytest.mark.unit
class TestBookService:
    """绘本服务测试"""

    def test_create_book_success(self, db_session, sample_book_data):
        """测试成功创建绘本"""
        # 使用服务创建绘本
        book = book_service.create_book(
            db=db_session,
            request=sample_book_data,
            user_id=1
        )

        assert book is not None
        assert book.id is not None
        assert book.theme == sample_book_data["theme"]
        assert book.target_age == sample_book_data["target_age"]
        assert book.style == sample_book_data["style"]
        assert book.status == BookStatus.DRAFT
        assert book.owner_id == 1

    def test_get_book_by_id(self, db_session):
        """测试通过ID获取绘本"""
        # 创建测试绘本
        book = PictureBook(
            theme="测试主题",
            target_age="3-6岁",
            style="水彩风格",
            status=BookStatus.DRAFT,
            owner_id=1
        )
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # 获取绘本
        result = book_service.get_book(db=db_session, book_id=book.id)

        assert result is not None
        assert result.id == book.id
        assert result.theme == book.theme

    def test_get_book_not_found(self, db_session):
        """测试获取不存在的绘本"""
        with pytest.raises(Exception):  # 应该抛出NotFoundException
            book_service.get_book(db=db_session, book_id=99999)

    def test_get_user_books(self, db_session):
        """测试获取用户的绘本列表"""
        # 为用户1创建多个绘本
        for i in range(3):
            book = PictureBook(
                theme=f"测试绘本 {i}",
                target_age="3-6岁",
                style="水彩风格",
                status=BookStatus.DRAFT,
                owner_id=1
            )
            db_session.add(book)

        # 为用户2创建绘本
        book = PictureBook(
            theme="用户2的绘本",
            target_age="6-8岁",
            style="卡通风格",
            status=BookStatus.DRAFT,
            owner_id=2
        )
        db_session.add(book)
        db_session.commit()

        # 获取用户1的绘本
        books = book_service.get_user_books(
            db=db_session,
            user_id=1,
            skip=0,
            limit=10
        )

        assert len(books) == 3
        assert all(book.owner_id == 1 for book in books)

    def test_update_book(self, db_session):
        """测试更新绘本"""
        # 创建测试绘本
        book = PictureBook(
            theme="原始主题",
            target_age="3-6岁",
            style="水彩风格",
            status=BookStatus.DRAFT,
            owner_id=1
        )
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # 更新绘本
        updated_book = book_service.update_book(
            db=db_session,
            book_id=book.id,
            title="新标题",
            description="新描述"
        )

        assert updated_book.title == "新标题"
        assert updated_book.description == "新描述"

    def test_delete_book(self, db_session):
        """测试删除绘本"""
        # 创建测试绘本
        book = PictureBook(
            theme="测试主题",
            target_age="3-6岁",
            style="水彩风格",
            status=BookStatus.DRAFT,
            owner_id=1
        )
        db_session.add(book)
        db_session.commit()
        book_id = book.id

        # 删除绘本
        book_service.delete_book(db=db_session, book_id=book_id)

        # 验证已删除
        result = db_session.query(PictureBook).filter(
            PictureBook.id == book_id
        ).first()

        assert result is None

    def test_add_page_to_book(self, db_session):
        """测试添加页面到绘本"""
        # 创建测试绘本
        book = PictureBook(
            theme="测试主题",
            target_age="3-6岁",
            style="水彩风格",
            status=BookStatus.DRAFT,
            owner_id=1
        )
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # 添加页面
        page = book_service.add_page(
            db=db_session,
            book_id=book.id,
            page_number=1,
            text_content="测试文本",
            image_prompt="测试提示词"
        )

        assert page is not None
        assert page.page_number == 1
        assert page.text_content == "测试文本"
        assert page.book_id == book.id

    @pytest.mark.slow
    @patch('app.services.book_service.openai_client')
    def test_generate_story_content(self, mock_openai, db_session):
        """测试生成故事内容"""
        # Mock OpenAI响应
        mock_openai.chat.completions.create.return_value = Mock(
            choices=[
                Mock(
                    message=Mock(
                        content='{"title": "测试故事", "description": "这是一个测试", "pages": [{"page_number": 1, "text": "从前", "scene_description": "场景", "image_prompt": "提示词"}]}'
                    )
                )
            ]
        )

        # 创建测试绘本
        book = PictureBook(
            theme="勇敢的小兔子",
            target_age="3-6岁",
            style="水彩风格",
            status=BookStatus.DRAFT,
            owner_id=1
        )
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # 生成故事
        result = book_service.generate_story_content(
            db=db_session,
            book=book,
            theme="勇敢的小兔子",
            keywords=["勇气", "友谊"],
            target_age="3-6岁",
            page_count=8
        )

        assert result is not None
        assert "title" in result
        assert "pages" in result


@pytest.mark.unit
class TestPageService:
    """页面服务测试"""

    def test_create_page(self, db_session):
        """测试创建页面"""
        # 创建测试绘本
        book = PictureBook(
            theme="测试主题",
            target_age="3-6岁",
            style="水彩风格",
            status=BookStatus.DRAFT,
            owner_id=1
        )
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # 创建页面
        page = BookPage(
            book_id=book.id,
            page_number=1,
            text_content="测试文本",
            image_prompt="测试提示词"
        )
        db_session.add(page)
        db_session.commit()
        db_session.refresh(page)

        assert page.id is not None
        assert page.book_id == book.id

    def test_update_page(self, db_session):
        """测试更新页面"""
        # 创建测试绘本和页面
        book = PictureBook(
            theme="测试主题",
            target_age="3-6岁",
            style="水彩风格",
            status=BookStatus.DRAFT,
            owner_id=1
        )
        db_session.add(book)
        db_session.commit()

        page = BookPage(
            book_id=book.id,
            page_number=1,
            text_content="原始文本",
            image_prompt="原始提示词"
        )
        db_session.add(page)
        db_session.commit()
        db_session.refresh(page)

        # 更新页面
        page.text_content = "更新后的文本"
        page.image_prompt = "更新后的提示词"
        db_session.commit()
        db_session.refresh(page)

        assert page.text_content == "更新后的文本"
        assert page.image_prompt == "更新后的提示词"

    def test_delete_page(self, db_session):
        """测试删除页面"""
        # 创建测试绘本和页面
        book = PictureBook(
            theme="测试主题",
            target_age="3-6岁",
            style="水彩风格",
            status=BookStatus.DRAFT,
            owner_id=1
        )
        db_session.add(book)
        db_session.commit()

        page = BookPage(
            book_id=book.id,
            page_number=1,
            text_content="测试文本",
            image_prompt="测试提示词"
        )
        db_session.add(page)
        db_session.commit()
        page_id = page.id

        # 删除页面
        db_session.delete(page)
        db_session.commit()

        # 验证已删除
        result = db_session.query(BookPage).filter(
            BookPage.id == page_id
        ).first()

        assert result is None

    def test_get_book_pages(self, db_session):
        """测试获取绘本的所有页面"""
        # 创建测试绘本
        book = PictureBook(
            theme="测试主题",
            target_age="3-6岁",
            style="水彩风格",
            status=BookStatus.DRAFT,
            owner_id=1
        )
        db_session.add(book)
        db_session.commit()

        # 创建多个页面
        for i in range(3):
            page = BookPage(
                book_id=book.id,
                page_number=i + 1,
                text_content=f"页面 {i + 1}",
                image_prompt=f"提示词 {i + 1}"
            )
            db_session.add(page)
        db_session.commit()

        # 获取所有页面
        pages = db_session.query(BookPage).filter(
            BookPage.book_id == book.id
        ).order_by(BookPage.page_number).all()

        assert len(pages) == 3
        assert pages[0].page_number == 1
        assert pages[1].page_number == 2
        assert pages[2].page_number == 3


@pytest.mark.unit
class TestImageService:
    """图片生成服务测试"""

    @patch('app.services.image_service.openai_client')
    def test_generate_image_success(self, mock_openai):
        """测试成功生成图片"""
        # Mock OpenAI响应
        mock_response = Mock()
        mock_response.data = [Mock(url="http://example.com/image.jpg")]
        mock_openai.images.generate.return_value = mock_response

        from app.services.image_service import image_service

        image_url = image_service.generate_image(
            prompt="一只可爱的小兔子",
            style="水彩风格"
        )

        assert image_url == "http://example.com/image.jpg"
        mock_openai.images.generate.assert_called_once()

    @patch('app.services.image_service.openai_client')
    def test_generate_image_failure(self, mock_openai):
        """测试图片生成失败"""
        # Mock失败响应
        mock_openai.images.generate.side_effect = Exception("API错误")

        from app.services.image_service import image_service

        with pytest.raises(Exception):
            image_service.generate_image(
                prompt="测试提示词",
                style="水彩风格"
            )
