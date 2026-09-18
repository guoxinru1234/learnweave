import asyncio
from typing import Dict, List, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class Event:
    """事件对象"""
    type: str
    data: Dict[str, Any]
    source: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    id: str = field(default_factory=lambda: str(datetime.now().timestamp()))

class EventBus:
    """事件总线 - 多智能体间通信核心，支持 wildcard 订阅"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._subscribers = {}
            cls._instance._event_history = []
            cls._instance._max_history = 100
        return cls._instance

    def subscribe(self, event_type: str, callback: Callable):
        """订阅事件"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        return callback

    def unsubscribe(self, event_type: str, callback: Callable):
        """取消订阅"""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass

    def on(self, event_type: str, callback: Callable):
        """注册监听器（subscribe 别名，支持 '*' wildcard）"""
        return self.subscribe(event_type, callback)

    def off(self, event_type: str, callback: Callable):
        """移除监听器"""
        return self.unsubscribe(event_type, callback)

    async def publish(self, event_type: str, data: Dict[str, Any], source: str = "system"):
        """发布事件，通知精确匹配 + '*' wildcard 订阅者"""
        event = Event(type=event_type, data=data, source=source)
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        try:
            print(f"[Event] {event_type} from {source}: {str(data)[:100]}")
        except UnicodeEncodeError:
            print(f"[Event] {event_type} from {source}")

        # 收集精确匹配 + wildcard 订阅者
        callbacks = list(self._subscribers.get(event_type, []))
        callbacks += list(self._subscribers.get("*", []))

        tasks = []
        for callback in callbacks:
            result = callback(event)
            if asyncio.iscoroutine(result):
                tasks.append(result)
        if tasks:
            await asyncio.gather(*tasks)

    def get_history(self, limit: int = 20) -> List[Event]:
        """获取事件历史"""
        return self._event_history[-limit:]


# 单例实例
event_bus = EventBus()
