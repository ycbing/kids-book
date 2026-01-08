# backend/app/services/export_service.py
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
import io
import os
import aiohttp
import asyncio
from typing import List, Optional
from pathlib import Path

from app.config import settings
from app.models.schemas import BookResponse, PageContent

class ExportService:

    def __init__(self):
        self.output_dir = Path(settings.OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 注册中文字体 - 尝试多个可能的字体位置
        self.chinese_font = self._register_chinese_font()

    def _register_chinese_font(self) -> str:
        """注册中文字体，返回字体名称"""
        # 可能的字体路径
        font_paths = [
            Path(__file__).parent.parent / "assets" / "fonts" / "SimHei.ttf",
            Path(__file__).parent.parent / "assets" / "fonts" / "msyh.ttc",  # 微软雅黑
            Path(__file__).parent.parent / "assets" / "fonts" / "simsun.ttc",  # 宋体
            # Windows系统字体
            Path("C:/Windows/Fonts/msyh.ttc"),
            Path("C:/Windows/Fonts/simsun.ttc"),
            Path("C:/Windows/Fonts/simhei.ttf"),
            # Linux系统字体
            Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            # macOS系统字体
            Path("/System/Library/Fonts/PingFang.ttc"),
            Path("/System/Library/Fonts/STHeiti Light.ttc"),
        ]

        for font_path in font_paths:
            if font_path.exists():
                try:
                    font_name = f"ChineseFont_{font_path.stem}"
                    pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
                    print(f"✅ 成功加载中文字体: {font_path}")
                    return font_name
                except Exception as e:
                    print(f"⚠️ 无法加载字体 {font_path}: {e}")
                    continue

        print("⚠️ 警告: 未找到中文字体，PDF中文可能显示异常")
        return 'Helvetica'
    
    async def download_image(self, url: str) -> Optional[bytes]:
        """下载图片"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.read()
        except Exception as e:
            print(f"下载图片失败: {e}")
        return None
    
    async def export_to_pdf(
        self, 
        book: BookResponse,
        quality: str = "high"
    ) -> str:
        """导出为PDF"""
        
        # 设置页面大小（横向A4）
        page_width, page_height = landscape(A4)
        
        # 创建PDF文件
        output_path = self.output_dir / f"book_{book.id}_{book.title}.pdf"
        c = canvas.Canvas(str(output_path), pagesize=landscape(A4))
        
        # 质量设置
        dpi_settings = {"low": 72, "medium": 150, "high": 300}
        dpi = dpi_settings.get(quality, 150)
        
        # 生成封面
        await self._create_cover_page(c, book, page_width, page_height)
        c.showPage()
        
        # 生成内容页
        for page in book.pages:
            await self._create_content_page(c, page, page_width, page_height)
            c.showPage()
        
        # 生成封底
        self._create_back_cover(c, book, page_width, page_height)
        
        c.save()
        
        return str(output_path)
    
    async def _create_cover_page(
        self, 
        c: canvas.Canvas, 
        book: BookResponse,
        width: float,
        height: float
    ):
        """创建封面页"""
        
        # 背景色
        c.setFillColorRGB(0.95, 0.95, 0.98)
        c.rect(0, 0, width, height, fill=True)
        
        # 封面图片
        if book.cover_image:
            image_data = await self.download_image(book.cover_image)
            if image_data:
                img = Image.open(io.BytesIO(image_data))
                img_reader = ImageReader(img)
                
                # 计算图片位置和大小
                img_width = width * 0.6
                img_height = height * 0.5
                img_x = (width - img_width) / 2
                img_y = height * 0.35
                
                c.drawImage(img_reader, img_x, img_y, img_width, img_height, preserveAspectRatio=True)
        
        # 标题
        c.setFont(self.chinese_font, 36)
        c.setFillColorRGB(0.2, 0.2, 0.3)
        title_width = c.stringWidth(book.title, self.chinese_font, 36)
        c.drawString((width - title_width) / 2, height * 0.25, book.title)
        
        # 描述
        c.setFont(self.chinese_font, 14)
        c.setFillColorRGB(0.4, 0.4, 0.5)
        desc_width = c.stringWidth(book.description, self.chinese_font, 14)
        c.drawString((width - desc_width) / 2, height * 0.18, book.description)
    
    async def _create_content_page(
        self,
        c: canvas.Canvas,
        page: PageContent,
        width: float,
        height: float
    ):
        """创建内容页"""
        
        # 白色背景
        c.setFillColorRGB(1, 1, 1)
        c.rect(0, 0, width, height, fill=True)
        
        # 页面布局：左图右文
        margin = 1 * cm
        
        # 图片区域（左半部分）
        if page.image_url:
            image_data = await self.download_image(page.image_url)
            if image_data:
                img = Image.open(io.BytesIO(image_data))
                img_reader = ImageReader(img)
                
                img_width = (width / 2) - (2 * margin)
                img_height = height - (2 * margin)
                
                c.drawImage(
                    img_reader, 
                    margin, 
                    margin, 
                    img_width, 
                    img_height,
                    preserveAspectRatio=True
                )
        
        # 文字区域（右半部分）
        text_x = width / 2 + margin
        text_width = (width / 2) - (2 * margin)
        text_y = height - (3 * margin)
        
        # 页码
        c.setFont(self.chinese_font, 10)
        c.setFillColorRGB(0.6, 0.6, 0.6)
        c.drawString(width - margin - 20, margin, str(page.page_number))
        
        # 正文
        c.setFont(self.chinese_font, 16)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        
        # 文字换行处理
        lines = self._wrap_text(page.text_content, text_width, self.chinese_font, 16, c)
        line_height = 24
        
        for i, line in enumerate(lines):
            y_pos = text_y - (i * line_height)
            if y_pos > margin:
                c.drawString(text_x, y_pos, line)
    
    def _create_back_cover(
        self,
        c: canvas.Canvas,
        book: BookResponse,
        width: float,
        height: float
    ):
        """创建封底"""
        
        # 背景色
        c.setFillColorRGB(0.95, 0.95, 0.98)
        c.rect(0, 0, width, height, fill=True)
        
        # 结束语
        c.setFont(self.chinese_font, 24)
        c.setFillColorRGB(0.3, 0.3, 0.4)
        end_text = "~ 故事结束 ~"
        text_width = c.stringWidth(end_text, self.chinese_font, 24)
        c.drawString((width - text_width) / 2, height / 2, end_text)
        
        # 版权信息
        c.setFont(self.chinese_font, 10)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        copyright_text = f"由AI绘本创作平台生成 | {book.created_at.strftime('%Y年%m月%d日')}"
        text_width = c.stringWidth(copyright_text, self.chinese_font, 10)
        c.drawString((width - text_width) / 2, height * 0.1, copyright_text)
    
    def _wrap_text(
        self, 
        text: str, 
        max_width: float, 
        font_name: str, 
        font_size: int,
        canvas: canvas.Canvas
    ) -> List[str]:
        """文字换行"""
        
        lines = []
        current_line = ""
        
        for char in text:
            test_line = current_line + char
            if canvas.stringWidth(test_line, font_name, font_size) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = char
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    async def export_to_images(
        self,
        book: BookResponse,
        format: str = "png"
    ) -> List[str]:
        """导出为图片序列"""
        
        output_paths = []
        book_dir = self.output_dir / f"book_{book.id}"
        book_dir.mkdir(parents=True, exist_ok=True)
        
        for page in book.pages:
            if page.image_url:
                image_data = await self.download_image(page.image_url)
                if image_data:
                    # 创建带文字的图片
                    img = Image.open(io.BytesIO(image_data))
                    
                    # 保存图片
                    output_path = book_dir / f"page_{page.page_number:02d}.{format}"
                    img.save(str(output_path), format.upper())
                    output_paths.append(str(output_path))
        
        return output_paths

# 创建服务实例
export_service = ExportService()
