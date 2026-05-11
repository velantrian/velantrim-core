# memory/memory_engine_interface.py
# Velantrim Core - Memory Engine Interface (v1.0)
# Абстракция для подключения разных движков памяти

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class MemoryEngine(ABC):
    """Единый интерфейс для всех движков памяти в Velantrim Core"""

    @abstractmethod
    def store(self, key: str, value: Any, importance: float = 0.5, tags: Optional[List[str]] = None) -> bool:
        """Сохранить факт"""
        pass

    @abstractmethod
    def recall(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Вспомнить релевантные факты"""
        pass

    @abstractmethod
    def adapt_behavior(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Адаптация поведения (эпигенетика)"""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Полный статус движка памяти"""
        pass


class LegacyMemoryEngine(MemoryEngine):
    """Адаптер для текущей памяти (SSB + LTM)"""
    def __init__(self, core):
        self.core = core

    def store(self, key: str, value: Any, importance: float = 0.5, tags: Optional[List[str]] = None) -> bool:
        return self.core.ltm.store(key, value, tags)

    def recall(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        return self.core.ltm.recall(query, limit)

    def adapt_behavior(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "legacy", "message": "Legacy memory does not support adaptation"}

    def get_status(self) -> Dict[str, Any]:
        return {"engine": "legacy", "type": "SSB + LTM (SQLite)"}


# Адаптер для HybridBiologicalMemory (из exocortex-crystal)
try:
    from hybrid_biological_memory import HybridBiologicalMemory
except ImportError:
    HybridBiologicalMemory = None

class HybridBiologicalMemoryEngine(MemoryEngine):
    """Адаптер для новой гибридной биологической памяти"""
    def __init__(self):
        if HybridBiologicalMemory is None:
            raise ImportError("hybrid_biological_memory not found. Install from velantrim-exocortex-crystal")
        self.engine = HybridBiologicalMemory(name="Velantrim-Core-Hybrid")

    def store(self, key: str, value: Any, importance: float = 0.5, tags: Optional[List[str]] = None) -> bool:
        self.engine.add_memory(f"{key}: {value}", importance=importance)
        return True

    def recall(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        # Упрощённый recall (можно улучшить)
        return [{"key": query, "value": "(hybrid recall)"}]

    def adapt_behavior(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return self.engine.adapt_behavior(params)

    def get_status(self) -> Dict[str, Any]:
        return self.engine.get_full_status()
