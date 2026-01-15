"""用户端点测试生成器"""
from core.decorators import Generator
from pathlib import Path
from ..base import BaseTemplateGenerator


@Generator(
    category="test",
    priority=113,
    requires=["UserRouterGenerator"],
    enabled_when=lambda c: c.has_testing() and c.has_auth(),
    description="生成用户测试文件 (tests/api/test_users.py)"
)
class TestUsersGenerator(BaseTemplateGenerator):
    """生成 test_users.py 文件"""

    def generate(self) -> None:
        """生成 test_users.py"""
        if not self.config_reader.has_testing() or not self.config_reader.has_auth():
            return

        content = self._build_user_tests()
        self.file_ops.create_file(
            file_path="tests/api/test_users.py",
            content=content,
            overwrite=True
        )

    def _build_user_tests(self) -> str:
        """构建用户测试"""
        return '''"""用户端点测试"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, auth_headers):
    """测试获取当前用户"""
    response = await client.get(
        "/api/v1/users/me",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert "username" in data
    assert "id" in data


@pytest.mark.asyncio
async def test_update_current_user(client: AsyncClient, auth_headers):
    """测试更新当前用户"""
    response = await client.put(
        "/api/v1/users/me",
        headers=auth_headers,
        json={"username": "updateduser"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "updateduser"


@pytest.mark.asyncio
async def test_get_user_without_auth(client: AsyncClient):
    """测试未认证情况下获取用户"""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401
'''
