"""主 API 端点测试生成器"""
from core.decorators import Generator
from pathlib import Path
from ..base import BaseTemplateGenerator


@Generator(
    category="test",
    priority=111,
    requires=["MainGenerator"],
    enabled_when=lambda c: c.has_testing(),
    description="生成主 API 测试文件 (tests/test_main.py)"
)
class TestMainGenerator(BaseTemplateGenerator):
    """生成 test_main.py 文件"""

    def generate(self) -> None:
        """生成 test_main.py"""
        if not self.config_reader.has_testing():
            return

        content = self._build_test_main()
        self.file_ops.create_file(
            file_path="tests/test_main.py",
            content=content,
            overwrite=True
        )

    def _build_test_main(self) -> str:
        """构建 test_main.py 内容"""
        return '''"""主 API 端点测试"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """测试健康检查端点"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_docs(client: AsyncClient):
    """测试 API 文档端点"""
    response = await client.get("/docs")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_openapi(client: AsyncClient):
    """测试 OpenAPI 架构端点"""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
'''
