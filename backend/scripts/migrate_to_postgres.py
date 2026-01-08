#!/usr/bin/env python3
"""
SQLite到PostgreSQL数据迁移脚本
将开发环境的SQLite数据迁移到生产环境的PostgreSQL
"""
import sys
import os
from pathlib import Path

# 设置UTF-8编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加backend到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.database import Base, User, PictureBook, BookPage
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """数据库迁移工具"""

    def __init__(self, sqlite_url: str, postgres_url: str):
        self.sqlite_url = sqlite_url
        self.postgres_url = postgres_url

        # 创建SQLite引擎
        self.sqlite_engine = create_engine(sqlite_url)

        # 创建PostgreSQL引擎
        self.postgres_engine = create_engine(
            postgres_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )

    def migrate_users(self):
        """迁移用户数据"""
        logger.info("📚 迁移用户数据...")

        # 从SQLite读取
        SessionLocal = sessionmaker(bind=self.sqlite_engine)
        sqlite_session = SessionLocal()

        try:
            users = sqlite_session.query(User).all()
            logger.info(f"  找到 {len(users)} 个用户")

            # 写入PostgreSQL
            PostgresSession = sessionmaker(bind=self.postgres_engine)
            postgres_session = PostgresSession()

            try:
                for user in users:
                    logger.info(f"  - 迁移用户: {user.username}")
                    new_user = User(
                        id=user.id,
                        username=user.username,
                        email=user.email,
                        hashed_password=user.hashed_password,
                        created_at=user.created_at
                    )
                    postgres_session.merge(new_user)

                postgres_session.commit()
                logger.info("✅ 用户数据迁移成功")

            except Exception as e:
                postgres_session.rollback()
                logger.error(f"❌ 用户数据迁移失败: {e}")
                raise
            finally:
                postgres_session.close()

        finally:
            sqlite_session.close()

    def migrate_books(self):
        """迁移绘本数据"""
        logger.info("📖 迁移绘本数据...")

        SessionLocal = sessionmaker(bind=self.sqlite_engine)
        sqlite_session = SessionLocal()

        try:
            books = sqlite_session.query(PictureBook).all()
            logger.info(f"  找到 {len(books)} 本绘本")

            PostgresSession = sessionmaker(bind=self.postgres_engine)
            postgres_session = PostgresSession()

            try:
                for book in books:
                    logger.info(f"  - 迁移绘本: {book.title} (ID: {book.id})")
                    new_book = PictureBook(
                        id=book.id,
                        title=book.title,
                        description=book.description,
                        theme=book.theme,
                        target_age=book.target_age,
                        style=book.style,
                        status=book.status,
                        cover_image=book.cover_image,
                        owner_id=book.owner_id,
                        created_at=book.created_at,
                        updated_at=book.updated_at
                    )
                    postgres_session.merge(new_book)

                postgres_session.commit()
                logger.info("✅ 绘本数据迁移成功")

            except Exception as e:
                postgres_session.rollback()
                logger.error(f"❌ 绘本数据迁移失败: {e}")
                raise
            finally:
                postgres_session.close()

        finally:
            sqlite_session.close()

    def migrate_pages(self):
        """迁移页面数据"""
        logger.info("📄 迁移页面数据...")

        SessionLocal = sessionmaker(bind=self.sqlite_engine)
        sqlite_session = SessionLocal()

        try:
            pages = sqlite_session.query(BookPage).all()
            logger.info(f"  找到 {len(pages)} 个页面")

            PostgresSession = sessionmaker(bind=self.postgres_engine)
            postgres_session = PostgresSession()

            try:
                for page in pages:
                    logger.info(f"  - 迁移页面: 绘本ID {page.book_id}, 页码 {page.page_number}")
                    new_page = BookPage(
                        id=page.id,
                        book_id=page.book_id,
                        page_number=page.page_number,
                        text_content=page.text_content,
                        image_prompt=page.image_prompt,
                        image_url=page.image_url,
                        layout=page.layout,
                        created_at=page.created_at
                    )
                    postgres_session.merge(new_page)

                postgres_session.commit()
                logger.info("✅ 页面数据迁移成功")

            except Exception as e:
                postgres_session.rollback()
                logger.error(f"❌ 页面数据迁移失败: {e}")
                raise
            finally:
                postgres_session.close()

        finally:
            sqlite_session.close()

    def reset_sequences(self):
        """重置PostgreSQL序列"""
        logger.info("🔄 重置数据库序列...")

        with self.postgres_engine.connect() as conn:
            try:
                # 重置users表序列
                conn.execute(text("SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id), 1) FROM users));"))

                # 重置picture_books表序列
                conn.execute(text("SELECT setval('picture_books_id_seq', (SELECT COALESCE(MAX(id), 1) FROM picture_books));"))

                # 重置book_pages表序列
                conn.execute(text("SELECT setval('book_pages_id_seq', (SELECT COALESCE(MAX(id), 1) FROM book_pages));"))

                conn.commit()
                logger.info("✅ 数据库序列重置成功")
            except Exception as e:
                conn.rollback()
                logger.warning(f"⚠️  序列重置失败（可能不影响使用）: {e}")

    def migrate_all(self):
        """执行完整迁移"""
        print("="*60)
        print("🚀 SQLite → PostgreSQL 数据迁移")
        print("="*60)
        print(f"\n源数据库: {self.sqlite_url}")
        print(f"目标数据库: {self.postgres_url}\n")

        try:
            # 1. 创建表结构
            logger.info("📋 创建PostgreSQL表结构...")
            Base.metadata.create_all(self.postgres_engine)
            logger.info("✅ 表结构创建成功\n")

            # 2. 迁移数据
            self.migrate_users()
            self.migrate_books()
            self.migrate_pages()

            # 3. 重置序列
            self.reset_sequences()

            print("\n" + "="*60)
            print("✅ 迁移完成！")
            print("="*60)
            print("\n下一步:")
            print("1. 验证数据完整性")
            print("2. 更新 .env 配置使用PostgreSQL")
            print("3. 重启应用服务")

        except Exception as e:
            logger.error(f"\n❌ 迁移失败: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="数据库迁移工具")
    parser.add_argument(
        "--sqlite",
        default="sqlite:///./picturebook.db",
        help="SQLite数据库URL（默认: sqlite:///./picturebook.db）"
    )
    parser.add_argument(
        "--postgres",
        required=True,
        help="PostgreSQL数据库URL（必须）"
    )

    args = parser.parse_args()

    # 执行迁移
    migrator = DatabaseMigrator(args.sqlite, args.postgres)
    migrator.migrate_all()


if __name__ == '__main__':
    main()
