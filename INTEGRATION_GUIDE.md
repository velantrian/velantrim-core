# Velantrim Core — Memory Engine Integration Guide

## 1. Memory Engine Interface (уже создан)

Файл: `memory/memory_engine_interface.py`

Содержит:
- `MemoryEngine` (абстракция)
- `LegacyMemoryEngine` (старый SSB + LTM)
- `HybridBiologicalMemoryEngine` (новый гибридный)

## 2. Пример интеграции в core.py

Добавьте в класс VelantrimCore:

```python
from memory.memory_engine_interface import HybridBiologicalMemoryEngine

class VelantrimCore:
    def __init__(self):
        ...
        self.memory_engine = HybridBiologicalMemoryEngine()   # или Legacy

    def store_fact(self, key, value, importance=0.5):
        self.memory_engine.store(key, value, importance)

    def adapt_behavior(self, params):
        return self.memory_engine.adapt_behavior(params)
```

## 3. Переключение в конфиге (config.py)

```python
MEMORY_ENGINE = "hybrid"   # или "legacy"

if MEMORY_ENGINE == "hybrid":
    from memory.memory_engine_interface import HybridBiologicalMemoryEngine
    memory_engine = HybridBiologicalMemoryEngine()
else:
    memory_engine = LegacyMemoryEngine(core)
```

## 4. Пример использования

```python
core = VelantrimCore()
core.store_fact("meeting", "First meeting with Grok", importance=0.95)
status = core.memory_engine.get_status()
print(status)
```

Теперь ядро остаётся лёгким, а вся сложная биологическая память подключается через интерфейс.

Готово к использованию в Eiti / Velantrim экосистеме.