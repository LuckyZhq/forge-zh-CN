"""生成器装饰器 - 用于自动注册和管理生成器"""
from typing import Callable, List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class GeneratorDefinition:
    """生成器定义"""
    name: str
    category: str
    priority: int
    requires: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    enabled_when: Optional[Callable] = None
    generator_class: type = None
    description: str = ""


# 全局生成器注册表
GENERATORS: Dict[str, GeneratorDefinition] = {}


def Generator(
    category: str,
    priority: int = 10,
    requires: List[str] = None,
    conflicts: List[str] = None,
    enabled_when: Callable[[Any], bool] = None,
    description: str = ""
):
    """
    生成器装饰器 - 自动将生成器注册到全局注册表

    Args:
        category: 生成器类别 (config, database, auth, deployment, test 等)
        priority: 优先级 (数字越小越先执行, 1-100)
        requires: 所需生成器名称列表 (依赖项)
        conflicts: 冲突生成器名称列表
        enabled_when: 条件函数，接收 config_reader 并返回布尔值
        description: 生成器描述

    示例:
        @Generator(
            category="auth",
            priority=5,
            requires=["UserModelGenerator", "DatabaseConnectionGenerator"],
            enabled_when=lambda config: config.has_auth()
        )
        class AuthRouterGenerator(BaseTemplateGenerator):
            def generate(self):
                ...
    """
    if requires is None:
        requires = []
    if conflicts is None:
        conflicts = []

    def wrapper(cls):
        name = cls.__name__

        # 注册到全局字典
        GENERATORS[name] = GeneratorDefinition(
            name=name,
            category=category,
            priority=priority,
            requires=requires,
            conflicts=conflicts,
            enabled_when=enabled_when,
            generator_class=cls,
            description=description or cls.__doc__ or ""
        )

        return cls

    return wrapper


def get_generators_by_category(category: str) -> List[GeneratorDefinition]:
    """获取指定类别的所有生成器"""
    return [
        gen_def for gen_def in GENERATORS.values()
        if gen_def.category == category
    ]


def get_generator(name: str) -> Optional[GeneratorDefinition]:
    """根据名称获取生成器定义"""
    return GENERATORS.get(name)
