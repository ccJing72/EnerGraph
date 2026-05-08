"""统一配置加载模块

加载优先级: 环境变量 > YAML 配置 > 默认值
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# 加载 .env 文件
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _PROJECT_ROOT / ".env"
if _ENV_FILE.exists():
    load_dotenv(_ENV_FILE)


class ModelConfig(BaseModel):
    """模型配置"""
    provider: str = Field(default="openai", description="LLM 提供商")
    name: str = Field(default="gpt-4", description="模型名称")
    temperature: float = Field(default=0.7, ge=0, le=2, description="温度参数")
    max_tokens: int = Field(default=2000, gt=0, description="最大输出 token 数")


class AgentConfig(BaseModel):
    """Agent 行为配置"""
    max_iterations: int = Field(default=10, ge=1, le=50, description="最大迭代次数")
    timeout: int = Field(default=60, gt=0, description="超时时间 (秒)")


class ToolDef(BaseModel):
    """工具定义"""
    name: str
    description: str


class OutputConfig(BaseModel):
    """输出配置"""
    language: str = Field(default="zh", description="输出语言")
    format: str = Field(default="markdown", description="输出格式")


class AppConfig(BaseModel):
    """应用顶层配置"""
    model: ModelConfig = Field(default_factory=ModelConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    tools: List[ToolDef] = Field(default_factory=list)
    output: OutputConfig = Field(default_factory=OutputConfig)


def _load_yaml_config(yaml_path: Optional[Path] = None) -> Dict[str, Any]:
    """加载 YAML 配置文件"""
    if yaml_path is None:
        yaml_path = _PROJECT_ROOT / "config" / "agent_config.yaml"

    if not yaml_path.exists():
        return {}

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except (yaml.YAMLError, OSError) as e:
        print(f"[WARNING] 无法加载配置文件 {yaml_path}: {e}")
        return {}


def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """用环境变量覆盖 YAML 配置"""
    env_map = {
        "OPENAI_API_KEY": ("api_key", None),
        "OPENAI_MODEL": ("model", "name"),
        "OPENAI_BASE_URL": ("model", "base_url"),
        "ANTHROPIC_API_KEY": ("api_key", None),
        "ANTHROPIC_MODEL": ("model", "name"),
        "AGENT_TEMPERATURE": ("model", "temperature"),
        "AGENT_MAX_ITERATIONS": ("agent", "max_iterations"),
        "LOG_LEVEL": ("log_level", None),
    }

    for env_var, (section, key) in env_map.items():
        value = os.getenv(env_var)
        if value is None:
            continue
        if key is None:
            config[section] = value
        else:
            config.setdefault(section, {})[key] = value
            # 环境变量类型转换
            if value.isdigit():
                config[section][key] = int(value)
            elif value.replace(".", "", 1).isdigit():
                config[section][key] = float(value)
            elif value.lower() in ("true", "false"):
                config[section][key] = value.lower() == "true"

    return config


def create_settings(yaml_path: Optional[Path] = None) -> AppConfig:
    """创建应用配置实例

    加载顺序: YAML 文件 → 环境变量覆盖 → Pydantic 验证
    """
    raw = _load_yaml_config(yaml_path)
    raw = _apply_env_overrides(raw)
    return AppConfig(**raw)


# 全局单例
settings = create_settings()
