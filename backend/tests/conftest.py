# backend/tests/conftest.py
"""
pytest配置文件 - 共享fixtures和测试配置
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.models.database import Base, get_db
from app.core.config import settings


# ================================
# 数据库Fixtures
# ================================

@pytest.fixture(scope="function")
def db_engine():
    """
    创建测试数据库引擎（内存数据库）
    每个测试函数使用独立的数据库
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    yield engine

    # 清理：删除所有表
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """
    创建测试数据库会话
    """
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    创建测试客户端
    使用测试数据库会话覆盖正常的数据库依赖
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(db_session: Session) -> AsyncGenerator[AsyncClient, None]:
    """
    创建异步测试客户端
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ================================
# 认证Fixtures
# ================================

@pytest.fixture
def test_user_token() -> str:
    """
    生成测试用户token
    在实际项目中，这里应该调用认证API获取真实token
    """
    # 临时返回假token，实现认证后更新
    return "test_token_12345678"


@pytest.fixture
def auth_headers(test_user_token: str) -> dict:
    """
    带认证的请求头
    """
    return {"Authorization": f"Bearer {test_user_token}"}


# ================================
# 数据Fixtures
# ================================

@pytest.fixture
def sample_book_data() -> dict:
    """
    示例绘本创建数据
    """
    return {
        "theme": "勇敢的小兔子",
        "keywords": ["勇敢", "友谊", "冒险"],
        "target_age": "3-6岁",
        "style": "水彩风格",
        "page_count": 8,
        "custom_prompt": "一个关于勇气和友谊的温馨故事"
    }


@pytest.fixture
def sample_book_update_data() -> dict:
    """
    示例绘本更新数据
    """
    return {
        "title": "更新后的标题",
        "description": "更新后的描述",
        "theme": "更新的主题"
    }


# ================================
# Mock Fixtures
# ================================

@pytest.fixture
def mock_ai_response(monkeypatch):
    """
    Mock AI API响应
    """
    class MockAIResponse:
        async def generate(self, prompt: str):
            return {
                "text": "这是生成的测试故事文本",
                "pages": [
                    {
                        "page_number": 1,
                        "text": "从前有一只小兔子",
                        "image_prompt": "一只可爱的小兔子在森林里"
                    },
                    {
                        "page_number": 2,
                        "text": "它遇到了好朋友",
                        "image_prompt": "小兔子和小熊一起玩耍"
                    }
                ]
            }

    return MockAIResponse()


@pytest.fixture
def mock_image_generation(monkeypatch):
    """
    Mock图片生成响应
    """
    def mock_generate(prompt: str, style: str):
        return f"http://example.com/images/{hash(prompt)}.jpg"

    return mock_generate


# ================================
# 事件循环Fixture
# ================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    创建事件循环用于异步测试
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ================================
# 测试工具函数
# ================================

@pytest.fixture
def assert_valid_response():
    """
    验证API响应格式的辅助函数
    """
    def _assert(response_data: dict, expected_keys: list = None):
        assert "success" in response_data

        if response_data.get("success"):
            assert "data" in response_data
            if expected_keys:
                for key in expected_keys:
                    assert key in response_data["data"], f"缺少预期的key: {key}"
        else:
            assert "error" in response_data

    return _assert


# ================================
# 性能测试Fixture
# ================================

@pytest.fixture
def benchmark():
    """
    性能基准测试
    """
    import time

    class Benchmark:
        def __init__(self):
            self.results = []

        def measure(self, func, *args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            duration = end - start

            self.results.append({
                "function": func.__name__,
                "duration": duration
            })

            return result

        def report(self):
            if not self.results:
                return "No benchmark results"

            total = sum(r["duration"] for r in self.results)
            avg = total / len(self.results)

            return f"""
            Benchmark Results:
            - Total: {total:.4f}s
            - Average: {avg:.4f}s
            - Calls: {len(self.results)}
            """

    return Benchmark()


# ================================
# Pytest钩子
# ================================

def pytest_configure(config):
    """
    Pytest配置钩子
    """
    config.addinivalue_line(
        "markers", "slow: 标记慢速测试"
    )
    config.addinivalue_line(
        "markers", "integration: 标记集成测试"
    )
    config.addinivalue_line(
        "markers", "unit: 标记单元测试"
    )


def pytest_collection_modifyitems(config, items):
    """
    修改测试收集结果
    """
    # 自动为没有标记的测试添加unit标记
    for item in items:
        if not any(item.get_closest_marker(name) for name in ["slow", "integration", "e2e"]):
            item.add_marker(pytest.mark.unit)
