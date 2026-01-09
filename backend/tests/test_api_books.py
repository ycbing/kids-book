# backend/tests/test_api_books.py
"""
绘本API测试
测试所有绘本相关的API端点
"""

import pytest
from fastapi import status


@pytest.mark.integration
class TestBooksAPI:
    """绘本API集成测试"""

    def test_create_book_success(self, client, sample_book_data, auth_headers):
        """测试成功创建绘本"""
        response = client.post(
            "/api/v1/books",
            json=sample_book_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] is True
        assert "data" in data
        assert "id" in data["data"]
        assert data["data"]["theme"] == sample_book_data["theme"]
        assert data["data"]["status"] == "draft"

    def test_create_book_missing_theme(self, client, auth_headers):
        """测试缺少主题字段时创建绘本"""
        response = client.post(
            "/api/v1/books",
            json={
                "keywords": ["测试"],
                "target_age": "3-6岁",
                "style": "水彩风格",
                "page_count": 8
            },
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_book_invalid_age_range(self, client, sample_book_data, auth_headers):
        """测试无效的年龄范围"""
        sample_book_data["target_age"] = "invalid-age"

        response = client.post(
            "/api/v1/books",
            json=sample_book_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_books_empty(self, client, auth_headers):
        """测试获取空的绘本列表"""
        response = client.get("/api/v1/books", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) == 0

    def test_list_books_with_pagination(self, client, auth_headers):
        """测试分页获取绘本列表"""
        # 首先创建一些绘本
        for i in range(5):
            client.post("/api/v1/books", json={
                "theme": f"测试绘本 {i}",
                "keywords": ["测试"],
                "target_age": "3-6岁",
                "style": "水彩风格",
                "page_count": 8
            }, headers=auth_headers)

        # 测试分页
        response = client.get("/api/v1/books?skip=0&limit=3", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] is True
        assert len(data["data"]) == 3

    def test_get_book_by_id(self, client, sample_book_data, auth_headers):
        """测试通过ID获取绘本"""
        # 先创建绘本
        create_response = client.post(
            "/api/v1/books",
            json=sample_book_data,
            headers=auth_headers
        )
        book_id = create_response.json()["data"]["id"]

        # 获取绘本
        response = client.get(f"/api/v1/books/{book_id}", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] is True
        assert data["data"]["id"] == book_id
        assert data["data"]["theme"] == sample_book_data["theme"]

    def test_get_book_not_found(self, client, auth_headers):
        """测试获取不存在的绘本"""
        response = client.get("/api/v1/books/99999", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()

        assert data["success"] is False
        assert "error" in data

    def test_update_book(self, client, sample_book_data, sample_book_update_data, auth_headers):
        """测试更新绘本"""
        # 先创建绘本
        create_response = client.post(
            "/api/v1/books",
            json=sample_book_data,
            headers=auth_headers
        )
        book_id = create_response.json()["data"]["id"]

        # 更新绘本
        response = client.put(
            f"/api/v1/books/{book_id}",
            json=sample_book_update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] is True
        assert data["data"]["title"] == sample_book_update_data["title"]

    def test_delete_book(self, client, sample_book_data, auth_headers):
        """测试删除绘本"""
        # 先创建绘本
        create_response = client.post(
            "/api/v1/books",
            json=sample_book_data,
            headers=auth_headers
        )
        book_id = create_response.json()["data"]["id"]

        # 删除绘本
        response = client.delete(f"/api/v1/books/{book_id}", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] is True

        # 验证已删除
        get_response = client.get(f"/api/v1/books/{book_id}", headers=auth_headers)
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_unauthorized_access(self, client, sample_book_data):
        """测试未授权访问"""
        response = client.post("/api/v1/books", json=sample_book_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.unit
class TestBooksValidation:
    """绘本API验证测试"""

    def test_validate_page_count_min(self, client, auth_headers):
        """测试页数最小值验证"""
        response = client.post("/api/v1/books", json={
            "theme": "测试",
            "keywords": ["测试"],
            "target_age": "3-6岁",
            "style": "水彩风格",
            "page_count": 1  # 最小值是2
        }, headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_validate_page_count_max(self, client, auth_headers):
        """测试页数最大值验证"""
        response = client.post("/api/v1/books", json={
            "theme": "测试",
            "keywords": ["测试"],
            "target_age": "3-6岁",
            "style": "水彩风格",
            "page_count": 100  # 最大值是50
        }, headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_validate_keywords_empty(self, client, auth_headers):
        """测试关键词为空列表"""
        response = client.post("/api/v1/books", json={
            "theme": "测试",
            "keywords": [],  # 不能为空
            "target_age": "3-6岁",
            "style": "水彩风格",
            "page_count": 8
        }, headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
