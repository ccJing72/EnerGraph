"""test_ui_router_skill — UIRouterSkill 路由匹配单元测试

测试范围：
  - RouteRegistry.find_route() 模糊匹配功能
  - 精确匹配、模糊匹配、受限页面、无匹配等场景
"""
import pytest

from src.skills.ui_router_skill import RouteRegistry


class TestRouteRegistry:
    """RouteRegistry 路由匹配测试"""

    def test_exact_match(self):
        """测试精确匹配 - 完整页面名称"""
        registry = RouteRegistry()
        result = registry.find_route("能源监控")

        assert "error" not in result
        assert result["path"] == "/integrated-monitor/energy-monitor"
        assert result["name"] == "能源监控"
        assert result["is_restricted"] is False
        assert result["restriction_reason"] is None

    def test_fuzzy_match(self):
        """测试模糊匹配 - 部分关键词"""
        registry = RouteRegistry()
        result = registry.find_route("能源")

        assert "error" not in result
        assert result["path"] == "/integrated-monitor/energy-monitor"
        assert result["name"] == "能源监控"

    def test_restricted_page(self):
        """测试受限页面 - 需要项目上下文"""
        registry = RouteRegistry()
        result = registry.find_route("冷水机房")

        assert "error" not in result
        assert result["path"] == "/integrated-monitor/conditioning-terminal"
        assert result["name"] == "冷水机房"
        assert result["is_restricted"] is True
        assert "需要选择项目后查看" in result["restriction_reason"]

    def test_no_match(self):
        """测试无匹配结果 - 不存在的页面"""
        registry = RouteRegistry()
        result = registry.find_route("不存在的页面XYZ123")

        assert "error" in result
        assert "未找到匹配的页面" in result["error"]

