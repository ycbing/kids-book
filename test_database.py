#!/usr/bin/env python3
"""
数据库配置测试脚本
验证数据库连接和配置是否正确
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
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from app.config import settings
from app.models.database import engine, SessionLocal, Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_database_connection():
    """测试数据库连接"""
    print("="*60)
    print("🗄️  数据库连接测试")
    print("="*60)

    db_url = settings.DATABASE_URL
    print(f"\n数据库URL: {db_url}")

    if db_url.startswith("sqlite"):
        print("✅ 数据库类型: SQLite（开发环境）")
    else:
        print("✅ 数据库类型: PostgreSQL（生产环境）")

    # 测试连接
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ 数据库连接成功")

        # 显示连接池信息
        if hasattr(engine.pool, 'size'):
            print(f"\n📊 连接池信息:")
            print(f"  连接池大小: {engine.pool.size()}")
            print(f"  当前连接数: {engine.pool.checkedout()}")
            if hasattr(engine.pool, 'max_overflow'):
                print(f"  最大溢出: {engine.pool.max_overflow}")
        else:
            print(f"\n📊 SQLite不需要连接池")

        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


def test_database_tables():
    """测试数据库表"""
    print("\n" + "="*60)
    print("📋 数据库表测试")
    print("="*60)

    db_url = settings.DATABASE_URL

    try:

        with engine.connect() as conn:
            # 获取所有表名
            result = conn.execute(text("""
                SELECT name FROM sqlite_master
                WHERE type='table'
                ORDER BY name
            """ if "sqlite" in db_url else """
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """))

            tables = [row[0] for row in result]

            if tables:
                print(f"\n✅ 找到 {len(tables)} 个表:")
                for table in tables:
                    print(f"  - {table}")

                # 检查每个表的记录数
                print(f"\n📊 表记录数:")
                for table in tables:
                    try:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.scalar()
                        print(f"  - {table}: {count} 条记录")
                    except Exception as e:
                        print(f"  - {table}: 查询失败 ({e})")
            else:
                print("⚠️  数据库中没有表，需要运行迁移")
                return False

        return True
    except Exception as e:
        print(f"❌ 检查表失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_indexes():
    """测试数据库索引"""
    print("\n" + "="*60)
    print("🔍 数据库索引测试")
    print("="*60)

    db_url = settings.DATABASE_URL

    try:
        with engine.connect() as conn:
            # 查询索引
            if "sqlite" in db_url:
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master
                    WHERE type='index'
                    AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """))
            else:
                result = conn.execute(text("""
                    SELECT indexname FROM pg_indexes
                    WHERE schemaname = 'public'
                    ORDER BY indexname
                """))

            indexes = [row[0] for row in result]

            print(f"\n找到 {len(indexes)} 个索引:")
            for idx in indexes[:10]:  # 最多显示10个
                print(f"  - {idx}")

            if len(indexes) > 10:
                print(f"  ... 还有 {len(indexes) - 10} 个索引")

            # 检查关键索引
            key_indexes = ['idx_picture_books_owner_created',
                          'idx_picture_books_status',
                          'idx_picture_books_created_at']

            print(f"\n🔑 关键索引检查:")
            for key_idx in key_indexes:
                if any(key_idx in idx for idx in indexes):
                    print(f"  ✅ {key_idx} - 存在")
                else:
                    print(f"  ⚠️  {key_idx} - 缺失（可能影响性能）")

        return True
    except Exception as e:
        print(f"❌ 检查索引失败: {e}")
        return False


def test_database_performance():
    """测试数据库性能"""
    print("\n" + "="*60)
    print("⚡ 数据库性能测试")
    print("="*60)

    import time

    try:
        with engine.connect() as conn:
            # 测试查询性能
            queries = [
                ("SELECT 1", "简单查询"),
                ("SELECT COUNT(*) FROM users", "统计用户"),
            ]

            # 如果有picture_books表
            try:
                queries.append(("SELECT COUNT(*) FROM picture_books", "统计绘本"))
            except:
                pass

            print("\n查询性能测试:")
            for query, desc in queries:
                start = time.time()
                result = conn.execute(text(query))
                count = result.scalar()
                duration = (time.time() - start) * 1000

                status = "✅" if duration < 100 else "⚠️"
                print(f"  {status} {desc}: {count} 条记录 ({duration:.2f}ms)")

            # 测试批量插入（仅SQLite）
            if "sqlite" in settings.DATABASE_URL:
                print("\n💡 建议: 生产环境切换到PostgreSQL可获得更好性能")
            else:
                print("\n✅ 当前使用PostgreSQL，适合生产环境")

        return True
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False


def main():
    """主函数"""
    print("🔧 AI绘本平台 - 数据库配置测试")
    print(f"项目路径: {Path(__file__).parent}\n")

    # 检查配置
    print("📋 当前配置:")
    print(f"  - 数据库: {settings.DATABASE_URL}")
    print(f"  - 连接池大小: {settings.DB_POOL_SIZE}")
    print(f"  - 最大溢出: {settings.DB_MAX_OVERFLOW}")
    print(f"  - 连接回收: {settings.DB_POOL_RECYCLE}秒")

    # 运行测试
    results = []

    results.append(("数据库连接", test_database_connection()))
    results.append(("数据库表", test_database_tables()))
    results.append(("数据库索引", test_database_indexes()))
    results.append(("性能测试", test_database_performance()))

    # 总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status} {name}")

    print(f"\n通过率: {passed}/{total} ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n✅ 所有测试通过！数据库配置正常。")
    else:
        print("\n⚠️  部分测试失败，请检查配置。")

    print("="*60)

    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(main())
