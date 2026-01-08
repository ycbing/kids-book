# backend/app/services/book_tasks.py
"""
绘本生成Celery任务
处理长时间运行的绘本内容生成任务
"""
from celery import Task
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from app.core.celery_app import celery_app
from app.models.database import SessionLocal, PictureBook, BookPage, BookStatus
from app.models.schemas import BookCreateRequest, ArtStyle
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """带数据库会话的Celery任务基类"""

    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        """任务完成后关闭数据库连接"""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(bind=True, base=DatabaseTask, name='app.tasks.generate_book_content')
def generate_book_content_task(
    self,
    book_id: int,
    request_data: Dict[str, Any],
    user_id: int
):
    """
    异步生成绘本内容任务

    参数:
        book_id: 绘本ID
        request_data: 创建绘本的请求数据
        user_id: 用户ID

    返回:
        任务结果字典
    """
    logger.info(f"📚 开始生成绘本内容 - Book ID: {book_id}")

    try:
        # 更新任务状态
        self.update_state(
            state='PROGRESS',
            meta={
                'stage': '初始化',
                'progress': 0,
                'message': '正在准备生成绘本...'
            }
        )

        # 获取绘本
        book = self.db.query(PictureBook).filter(PictureBook.id == book_id).first()
        if not book:
            logger.error(f"❌ 绘本不存在 - Book ID: {book_id}")
            return {
                'status': 'FAILED',
                'error': f'绘本 {book_id} 不存在',
                'book_id': book_id
            }

        # 更新状态为生成中
        book.status = BookStatus.GENERATING
        self.db.commit()

        # 构建请求对象
        request = BookCreateRequest(**request_data)

        # ========== 步骤1: 生成故事 ==========
        self.update_state(
            state='PROGRESS',
            meta={
                'stage': 'generating_story',
                'progress': 10,
                'message': '正在生成故事文本...'
            }
        )

        from app.models.schemas import StoryGenerateRequest

        story_request = StoryGenerateRequest(
            theme=request.theme,
            keywords=request.keywords,
            target_age=request.target_age,
            page_count=request.page_count,
            custom_prompt=request.custom_prompt
        )

        try:
            story = await ai_service.generate_story(story_request)

            # 更新绘本信息
            book.title = request.title or story.title
            book.description = story.description
            self.db.commit()

            logger.info(f"✅ 故事生成完成 - Book ID: {book_id}")

        except Exception as e:
            logger.error(f"❌ 故事生成失败 - Book ID: {book_id}, Error: {e}")
            book.status = BookStatus.FAILED
            self.db.commit()
            raise

        # ========== 步骤2: 生成配图 ==========
        self.update_state(
            state='PROGRESS',
            meta={
                'stage': 'generating_images',
                'progress': 30,
                'message': f'正在生成 {len(story.pages)} 张配图...'
            }
        )

        async def image_progress(current, total):
            """图片生成进度回调"""
            progress = 30 + int((current / total) * 60)  # 30-90%
            self.update_state(
                state='PROGRESS',
                meta={
                    'stage': 'generating_images',
                    'progress': progress,
                    'message': f'正在生成第 {current}/{total} 张配图...',
                    'current_page': current,
                    'total_pages': total
                }
            )

        try:
            image_urls = await ai_service.generate_book_images(
                story.pages,
                request.style,
                image_progress
            )

            logger.info(f"✅ 配图生成完成 - Book ID: {book_id}")

        except Exception as e:
            logger.error(f"❌ 配图生成失败 - Book ID: {book_id}, Error: {e}")
            book.status = BookStatus.FAILED
            self.db.commit()
            raise

        # ========== 步骤3: 保存页面内容 ==========
        self.update_state(
            state='PROGRESS',
            meta={
                'stage': 'saving_pages',
                'progress': 90,
                'message': '正在保存绘本内容...'
            }
        )

        try:
            for i, page in enumerate(story.pages):
                book_page = BookPage(
                    book_id=book.id,
                    page_number=page.page_number,
                    text_content=page.text,
                    image_prompt=page.image_prompt,
                    image_url=image_urls[i] if i < len(image_urls) else None,
                    layout={"type": "standard"}
                )
                self.db.add(book_page)

                # 每保存5页提交一次
                if (i + 1) % 5 == 0:
                    self.db.commit()

            # 设置封面（使用第一页图片）
            if image_urls and image_urls[0]:
                book.cover_image = image_urls[0]

            # 更新状态为完成
            book.status = BookStatus.COMPLETED
            book.completed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(book)

            logger.info(f"✅ 绘本生成完成 - Book ID: {book_id}")

        except Exception as e:
            logger.error(f"❌ 保存内容失败 - Book ID: {book_id}, Error: {e}")
            book.status = BookStatus.FAILED
            self.db.commit()
            raise

        # ========== 完成 ==========
        return {
            'status': 'SUCCESS',
            'book_id': book_id,
            'title': book.title,
            'page_count': len(story.pages),
            'completed_at': book.completed_at.isoformat() if book.completed_at else None
        }

    except Exception as e:
        logger.error(f"❌ 绘本生成任务失败 - Book ID: {book_id}, Error: {e}", exc_info=True)

        # 更新绘本状态为失败
        try:
            book = self.db.query(PictureBook).filter(PictureBook.id == book_id).first()
            if book:
                book.status = BookStatus.FAILED
                self.db.commit()
        except:
            pass

        # 返回失败结果
        return {
            'status': 'FAILED',
            'error': str(e),
            'book_id': book_id
        }


@celery_app.task(bind=True, name='app.tasks.regenerate_page_image')
def regenerate_page_image_task(
    self,
    book_id: int,
    page_number: int,
    style: str
):
    """
    异步重新生成单页配图任务

    参数:
        book_id: 绘本ID
        page_number: 页码
        style: 艺术风格

    返回:
        任务结果字典
    """
    logger.info(f"🎨 开始重新生成配图 - Book ID: {book_id}, Page: {page_number}")

    try:
        # 获取绘本和页面
        book = self.db.query(PictureBook).filter(PictureBook.id == book_id).first()
        if not book:
            return {
                'status': 'FAILED',
                'error': f'绘本 {book_id} 不存在'
            }

        page = self.db.query(BookPage).filter(
            BookPage.book_id == book_id,
            BookPage.page_number == page_number
        ).first()

        if not page:
            return {
                'status': 'FAILED',
                'error': f'页面 {page_number} 不存在'
            }

        # 更新进度
        self.update_state(
            state='PROGRESS',
            meta={
                'stage': 'generating_image',
                'progress': 50,
                'message': f'正在重新生成第 {page_number} 页配图...'
            }
        )

        # 生成图片
        from app.models.schemas import ImageGenerateRequest

        art_style = ArtStyle(style) if style else ArtStyle(book.style)

        request = ImageGenerateRequest(
            prompt=page.image_prompt,
            style=art_style
        )

        import asyncio
        result = asyncio.run(ai_service.generate_image(request))

        # 更新页面图片
        page.image_url = result.image_url
        self.db.commit()

        logger.info(f"✅ 配图重新生成完成 - Book ID: {book_id}, Page: {page_number}")

        return {
            'status': 'SUCCESS',
            'book_id': book_id,
            'page_number': page_number,
            'image_url': result.image_url
        }

    except Exception as e:
        logger.error(f"❌ 配图重新生成失败 - Book ID: {book_id}, Page: {page_number}, Error: {e}")

        return {
            'status': 'FAILED',
            'error': str(e),
            'book_id': book_id,
            'page_number': page_number
        }


@celery_app.task(name='app.tasks.cleanup_old_books')
def cleanup_old_books_task(days: int = 30):
    """
    清理旧绘本任务（定期任务）

    参数:
        days: 保留天数，默认30天

    返回:
        清理统计信息
    """
    logger.info(f"🧹 开始清理 {days} 天前的旧绘本")

    try:
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # 查询旧绘本
        old_books = self.db.query(PictureBook).filter(
            PictureBook.created_at < cutoff_date,
            PictureBook.status == BookStatus.DRAFT
        ).all()

        count = 0
        for book in old_books:
            # 删除关联的页面
            self.db.query(BookPage).filter(BookPage.book_id == book.id).delete()
            # 删除绘本
            self.db.delete(book)
            count += 1

        self.db.commit()

        logger.info(f"✅ 清理完成 - 删除了 {count} 个旧绘本")

        return {
            'status': 'SUCCESS',
            'deleted_count': count,
            'cutoff_date': cutoff_date.isoformat()
        }

    except Exception as e:
        logger.error(f"❌ 清理任务失败: {e}")
        return {
            'status': 'FAILED',
            'error': str(e)
        }
