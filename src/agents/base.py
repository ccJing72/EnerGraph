"""Agent 基类 — 统一所有 Agent 的接口契约"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    """所有 Agent 的抽象基类.

    新增 Agent 时继承此类并实现 run() 方法，
    确保接口一致，便于 Supervisor 统一调度。
    """

    @abstractmethod
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Agent 主流程.

        Args:
            inputs: 输入数据字典.

        Returns:
            包含 report 和中间结果的输出字典.
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent 唯一标识名称."""
        ...
