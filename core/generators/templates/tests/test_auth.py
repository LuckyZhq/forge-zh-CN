"""认证端点测试生成器"""
from core.decorators import Generator
from pathlib import Path
from ..base import BaseTemplateGenerator


@Generator(
    category="test",
    priority=112,
    requires=["AuthRouterGenerator"],
    enabled_when=lambda c: c.has_testing() and c.has_auth(),
    description="生成认证测试文件 (tests/api/test_auth.py)"
)
class TestAuthGenerator(BaseTemplateGenerator):
    """生成 test_auth.py 文件"""

    def generate(self) -> None:
        """生成 test_auth.py"""
        if not self.config_reader.has_testing() or not self.config_reader.has_auth():
            return

        auth_type = self.config_reader.get_auth_type()

        if auth_type == "basic":
            content = self._build_basic_auth_tests()
        else:  # complete
            content = self._build_complete_auth_tests()

        self.file_ops.create_file(
            file_path="tests/api/test_auth.py",
            content=content,
            overwrite=True
        )

    def _build_basic_auth_tests(self) -> str:
        """构建基础认证测试"""
        return '''"""认证端点测试 - 基础 JWT 认证"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    """测试用户注册"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "newpassword123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user_verified):
    """测试使用重复邮箱注册"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user_verified.email,
            "username": "anotheruser",
            "password": "password123"
        }
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login(client: AsyncClient, test_user_verified):
    """测试用户登录"""
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user_verified.email,
            "password": "testpassword"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """测试使用无效凭证登录"""
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "wrong@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401


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
'''

    def _build_complete_auth_tests(self) -> str:
        """构建完整认证测试"""
        return '''"""认证端点测试 - 完整 JWT 认证"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    """测试用户注册"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "newpassword123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"
    assert "id" in data


@pytest.mark.asyncio
async def test_login(client: AsyncClient, test_user_verified):
    """测试用户登录"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user_verified.email,
            "password": "testpassword"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, test_user_verified):
    """测试令牌刷新"""
    # 首先登录以获取刷新令牌
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user_verified.email,
            "password": "testpassword"
        }
    )
    refresh_token = login_response.json()["refresh_token"]
    
    # 使用刷新令牌获取新的访问令牌
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_request_password_reset(client: AsyncClient, test_user_unverified):
    """测试密码重置请求"""
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": test_user_unverified.email}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_verify_email_request(client: AsyncClient, test_user_unverified):
    """测试邮箱验证请求"""
    response = await client.post(
        "/api/v1/auth/resend-verification",
        json={"email": test_user_unverified.email}
    )
    assert response.status_code == 200


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
'''
