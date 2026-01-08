# backend/app/services/book_service.py
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
from datetime import datetime

from app.models.database import PictureBook, BookPage, BookStatus
from app.models.schemas import (
    BookCreateRequest, BookResponse, PageContent,
    StoryGenerateRequest, ArtStyle
)
from app.services.ai_service import ai_service
from app.core.exceptions import NotFoundException, ExternalServiceException, not_found

class BookService:
    
    async def create_book(
        self, 
        db: Session, 
        request: BookCreateRequest,
        user_id: int
    ) -> PictureBook:
        """创建新绘本"""
        
        # 创建绘本记录
        book = PictureBook(
            title=request.title or "未命名绘本",
            description="",
            theme=request.theme,
            target_age=request.target_age.value,
            style=request.style.value,
            status=BookStatus.DRAFT,
            owner_id=user_id
        )
        db.add(book)
        db.commit()
        db.refresh(book)
        
        return book
    
    async def generate_book_content(
        self,
        db: Session,
        book_id: int,
        request: BookCreateRequest,
        progress_callback=None,
        ws_manager=None
    ) -> PictureBook:
        """生成绘本内容（故事+配图）"""

        book = db.query(PictureBook).filter(PictureBook.id == book_id).first()
        if not book:
            raise not_found("绘本", book_id)

        try:
            # 更新状态为生成中
            book.status = BookStatus.GENERATING
            db.commit()

            # 通知WebSocket：开始生成
            if ws_manager:
                await ws_manager.send_progress(str(book_id), {
                    "type": "status_update",
                    "book_id": book_id,
                    "status": "generating",
                    "stage": "初始化",
                    "completed_pages": 0,
                    "total_pages": request.page_count
                })

            # 1. 生成故事
            if progress_callback:
                await progress_callback("generating_story", 0, 100)

            story_request = StoryGenerateRequest(
                theme=request.theme,
                keywords=request.keywords,
                target_age=request.target_age,
                page_count=request.page_count,
                custom_prompt=request.custom_prompt
            )

            story = await ai_service.generate_story(story_request)

            # 更新绘本信息
            book.title = request.title or story.title
            book.description = story.description
            db.commit()

            if progress_callback:
                await progress_callback("generating_story", 100, 100)

            # 2. 生成配图
            async def image_progress(current, total):
                if progress_callback:
                    progress = int((current / total) * 100)
                    await progress_callback("generating_images", progress, 100)

                # 通知WebSocket：图片生成进度
                if ws_manager:
                    await ws_manager.send_progress(str(book_id), {
                        "type": "image_progress",
                        "book_id": book_id,
                        "stage": "generating_images",
                        "completed_pages": current,
                        "total_pages": total,
                        "progress": int((current / total) * 100)
                    })

            image_urls = await ai_service.generate_book_images(
                story.pages,
                request.style,
                image_progress
            )

            # 3. 保存页面内容
            for i, page in enumerate(story.pages):
                book_page = BookPage(
                    book_id=book.id,
                    page_number=page.page_number,
                    text_content=page.text,
                    image_prompt=page.image_prompt,
                    image_url=image_urls[i] if i < len(image_urls) else None,
                    layout={"type": "standard"}
                )
                db.add(book_page)

                # 每保存一页就通知一次
                db.commit()
                if ws_manager and i < len(image_urls) and image_urls[i]:
                    await ws_manager.send_progress(str(book_id), {
                        "type": "page_completed",
                        "book_id": book_id,
                        "page_number": page.page_number,
                        "image_url": image_urls[i]
                    })

            # 设置封面（使用第一页图片）
            if image_urls and image_urls[0]:
                book.cover_image = image_urls[0]

            book.status = BookStatus.COMPLETED
            db.commit()
            db.refresh(book)

            # 通知WebSocket：生成完成
            if ws_manager:
                await ws_manager.send_progress(str(book_id), {
                    "type": "generation_completed",
                    "book_id": book_id,
                    "status": "completed"
                })

            return book

        except Exception as e:
            book.status = BookStatus.FAILED
            db.commit()

            # 通知WebSocket：生成失败
            if ws_manager:
                await ws_manager.send_progress(str(book_id), {
                    "type": "generation_failed",
                    "book_id": book_id,
                    "status": "failed",
                    "error": str(e)
                })

            raise e
    
    def get_book(self, db: Session, book_id: int) -> Optional[BookResponse]:
        """获取绘本详情"""
        
        book = db.query(PictureBook).filter(PictureBook.id == book_id).first()
        if not book:
            return None
        
        pages = [
            PageContent(
                page_number=p.page_number,
                text_content=p.text_content,
                image_prompt=p.image_prompt,
                image_url=p.image_url
            )
            for p in book.pages
        ]
        
        return BookResponse(
            id=book.id,
            title=book.title,
            description=book.description,
            theme=book.theme,
            target_age=book.target_age,
            style=book.style,
            status=book.status.value,
            cover_image=book.cover_image,
            pages=pages,
            created_at=book.created_at
        )
    
    def get_user_books(
        self, 
        db: Session, 
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[BookResponse]:
        """获取用户的绘本列表"""
        
        books = db.query(PictureBook)\
            .filter(PictureBook.owner_id == user_id)\
            .order_by(PictureBook.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
        
        return [
            BookResponse(
                id=book.id,
                title=book.title,
                description=book.description,
                theme=book.theme,
                target_age=book.target_age,
                style=book.style,
                status=book.status.value,
                cover_image=book.cover_image,
                pages=[],
                created_at=book.created_at
            )
            for book in books
        ]
    
    def update_page(
        self,
        db: Session,
        book_id: int,
        page_number: int,
        text_content: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> BookPage:
        """更新页面内容"""
        
        page = db.query(BookPage).filter(
            BookPage.book_id == book_id,
            BookPage.page_number == page_number
        ).first()

        if not page:
            raise not_found("绘本页面", f"book_id={book_id}, page_number={page_number}")
        
        if text_content is not None:
            page.text_content = text_content
        if image_url is not None:
            page.image_url = image_url
        
        db.commit()
        db.refresh(page)
        
        return page
    
    def delete_book(self, db: Session, book_id: int) -> bool:
        """删除绘本"""
        
        book = db.query(PictureBook).filter(PictureBook.id == book_id).first()
        if not book:
            return False
        
        # 删除关联的页面
        db.query(BookPage).filter(BookPage.book_id == book_id).delete()
        db.delete(book)
        db.commit()
        
        return True

# 创建服务实例
book_service = BookService()
