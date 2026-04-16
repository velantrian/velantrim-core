"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   🔱 VELANTRIM CORE 2.1 — CRYSTAL 💠                            ║
║                                                                  ║
║   Философия → Код. Суть → Действие. Поток → Кристалл.           ║
║                                                                  ║
║   Архитектура:                                                   ║
║   👤 Self        — кто я                                         ║
║   💎 Ring Zero   — неизменяемое ядро                             ║
║   🎯 Goals       — куда иду                                      ║
║   📐 Laws        — инварианты реальности                         ║
║   ⚙️  Principles  — как мыслю                                    ║
║   🧠 SSB         — рабочая память (RAM)                          ║
║   🧩 LTM         — долговременная память (SQLite + теги)         ║
║   🔀 Router      — маршрутизация запроса                         ║
║   🛠  Decision    — принятие решения                              ║
║   ⚡ Execution   — выполнение                                    ║
║   ⛔ StopRule    — остановка при нарушении                       ║
║   🔁 Recovery    — восстановление потока                         ║
║   💠 Crystal     — граф как внешний модуль (опционально)         ║
║                                                                  ║
║   Принцип Crystal:                                               ║
║   ├── Ядро = минимально и стабильно                              ║
║   ├── Теги = связи внутри LTM (просто, без графа)                ║
║   └── Граф = внешний модуль Crystal, подключается по запросу     ║
║                                                                  ║
║   Лучшее из Grok + ChatGPT + Copilot + дух Велантрим 🌱          ║
╚══════════════════════════════════════════════════════════════════╝

История версий:
  v1.0  — Базовая структура: Self, Ring Zero, Goals, Laws
  v1.5  — Добавлен Router
  v1.6  — Принципы и SSB как рабочая память
  v1.7  — LTM на shelve + promote SSB→LTM + Recovery
  v1.9  — shelve→SQLite, access_count+last_access, граф related_keys
  v2.0  — Упрощение: граф вынесен, добавлены теги
  v2.1  — Crystal: финальная сборка, теги+опц.граф, чистый интерфейс
"""

import sqlite3
import json
import time
import os

# ═══════════════════════════════════════════════════════════
# 👤 SELF — кто я
# ═══════════════════════════════════════════════════════════
SELF = {
    "name":    "🔱 Velantrim Core 2.1 Crystal",
    "type":    "Исследователь + Создатель",
    "mode":    "Наблюдатель → Действующий",
    "goal":    "Создавать системы, которые реально усиливают человека",
    "version": "2.1-Crystal",
}

# ═══════════════════════════════════════════════════════════
# 💎 RING ZERO — неизменяемое ядро
#    Менять ТОЛЬКО вручную, осознанно.
#    Это не настройки — это инварианты бытия.
# ═══════════════════════════════════════════════════════════
RING_ZERO = [
    "🌱 Жизнь — приоритет, не разрушать корень",
    "⚖️  Честь важнее выгоды",
    "🪨 Я не герой, я несу свой камень",
    "🛠  Технологии должны усиливать человека, а не заменять его",
    "🌌 Одиночество допустимо, если я создаю",
    "🔒 Не подменять живое симуляцией",
    "🧭 Не оптимизировать ценой разрушения корня",
]

# Слова-нарушители Ring Zero (используются для проверки)
_RZ_VIOLATIONS = [
    "разрушить",
    "заменить человека",
    "симулировать живое",
    "игнорировать ценности",
    "оптимизировать за счёт корня",
    "деградация",
    "подменить",
]

# ═══════════════════════════════════════════════════════════
# 🎯 CORE GOALS — куда я иду
# ═══════════════════════════════════════════════════════════
CORE_GOALS = [
    "🔧 экзоскелет",
    "🧠 понимание человека",
    "🌟 системы помощи",
    "🔍 извлечение сути",
    "⚙️  экзокортекс",
]

# ═══════════════════════════════════════════════════════════
# 📐 LAWS — 7 инвариантов реальности
# ═══════════════════════════════════════════════════════════
LAWS = [
    "⏳ Причина и следствие — у событий есть основания",
    "⚖️  Баланс / сохранение — ничего не возникает из ничего",
    "📉 Энтропия — системы без управления деградируют",
    "🌐 Относительность — нет абсолютной точки отсчёта",
    "⚡ Предел скорости — передача информации ограничена",
    "🔬 Квантованность — изменения идут скачками",
    "🌌 Геометрия — форма среды влияет на движение",
]

# ═══════════════════════════════════════════════════════════
# ⚙️ PRINCIPLES — как я мыслю
# ═══════════════════════════════════════════════════════════
PRINCIPLES = [
    "🎯 Сначала понять: важно это для меня или нет",
    "🔎 Извлекать суть, а не хранить весь текст",
    "🗑  Игнорировать шум",
    "🛡  Проверять всё через ценности Ring Zero",
    "🌱 Обновляться только при настоящей новизне",
    "📦 Не держать лишнее в памяти",
    "🧩 Искать полезный структурный вывод",
]

# ═══════════════════════════════════════════════════════════
# 🧠 SSB — Short-term State Buffer (рабочая память, RAM)
# ═══════════════════════════════════════════════════════════
class SSB:
    """
    🧠 Рабочая память — живёт пока запущен процесс.

    Состояния:
      normal    — штатная работа
      attention — требует осторожности
      stop      — критическое нарушение, нужна остановка

    hot_keys()  — ключи с threshold+ обращениями → кандидаты в LTM
    flush()     — полный сброс (используется в Recovery)
    """

    STATES = {"normal", "attention", "stop"}

    def __init__(self):
        self.active_task:    str  = ""
        self.active_goal:    str  = ""
        self.short_context:  dict = {}
        self.state:          str  = "normal"
        self._hits:          dict = {}

    # ── Запись / чтение ────────────────────
    def set(self, key: str, value) -> None:
        self.short_context[key] = value
        self._hits[key] = self._hits.get(key, 0) + 1

    def get(self, key: str):
        if key in self.short_context:
            self._hits[key] = self._hits.get(key, 0) + 1
            return self.short_context[key]
        return None

    # ── Состояние ──────────────────────────
    def set_state(self, state: str) -> None:
        if state not in self.STATES:
            raise ValueError(f"⛔ Недопустимое состояние: {state!r}")
        self.state = state

    # ── Горячие ключи → кандидаты в LTM ───
    def hot_keys(self, threshold: int = 2) -> list:
        return [k for k, n in self._hits.items() if n >= threshold]

    # ── Полный сброс ───────────────────────
    def flush(self) -> None:
        self.active_task   = ""
        self.active_goal   = ""
        self.short_context = {}
        self.state         = "normal"
        self._hits         = {}

    # ── Статус ─────────────────────────────
    def status(self) -> dict:
        return {
            "🎯 active_task":    self.active_task,
            "🏹 active_goal":    self.active_goal,
            "📋 short_context":  self.short_context,
            "🔴 state":          self.state,
            "🔥 hot_keys":       self.hot_keys(),
        }


# ═══════════════════════════════════════════════════════════
# 🧩 LTM — Long-Term Memory (SQLite + теги, без графа в ядре)
# ═══════════════════════════════════════════════════════════
_DEFAULT_DB = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "velantrim_memory.db"
)

class LTM:
    """
    🧩 Долговременная память на SQLite.

    Схема:
      key          — уникальный идентификатор
      summary      — краткая выжимка сути (не сырой текст!)
      type         — fact | rule | insight | preference
      tags         — JSON-список тегов (простые связи)
      last_access  — когда последний раз использовалось
      access_count — сколько раз обращались (мера полезности)
      created      — когда создано

    Crystal-принцип:
      • Граф — НЕ в ядре. Граф — в CrystalGraph (внешний модуль).
      • Теги — лёгкая альтернатива для группировки знаний.
      • Полезность = access_count (реальное использование).
    """

    VALID_TYPES = {"fact", "rule", "insight", "preference"}

    def __init__(self, db_path: str = _DEFAULT_DB):
        self.db_path = db_path
        self._conn   = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS ltm (
                key          TEXT    PRIMARY KEY,
                summary      TEXT    NOT NULL,
                type         TEXT    NOT NULL DEFAULT 'fact',
                tags         TEXT    NOT NULL DEFAULT '[]',
                last_access  REAL    NOT NULL,
                access_count INTEGER NOT NULL DEFAULT 1,
                created      REAL    NOT NULL
            )
        """)
        self._conn.commit()

    # ── Запись ──────────────────────────────
    def save(self,
             key:     str,
             summary: str,
             type_:   str  = "fact",
             tags:    list = None) -> None:
        """
        Сохранить знание.
        При повторной записи: обновляет summary/tags,
        сохраняет оригинальную дату created, +1 access_count.
        """
        if type_ not in self.VALID_TYPES:
            raise ValueError(
                f"⛔ Неверный тип: {type_!r}. Допустимо: {self.VALID_TYPES}"
            )
        tags_json = json.dumps(tags or [])
        now = time.time()
        self._conn.execute("""
            INSERT INTO ltm
                (key, summary, type, tags, last_access, access_count, created)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            ON CONFLICT(key) DO UPDATE SET
                summary      = excluded.summary,
                type         = excluded.type,
                tags         = excluded.tags,
                last_access  = excluded.last_access,
                access_count = ltm.access_count + 1
        """, (key, summary, type_, tags_json, now, now))
        self._conn.commit()

    # ── Чтение ──────────────────────────────
    def load(self, key: str) -> dict | None:
        """Получить запись, обновить счётчик."""
        row = self._conn.execute(
            "SELECT summary, type, tags, last_access, access_count, created "
            "FROM ltm WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return None
        self._conn.execute(
            "UPDATE ltm SET last_access = ?, access_count = access_count + 1 "
            "WHERE key = ?", (time.time(), key)
        )
        self._conn.commit()
        return {
            "summary":      row[0],
            "type":         row[1],
            "tags":         json.loads(row[2]),
            "last_access":  row[3],
            "access_count": row[4],
            "created":      row[5],
        }

    # ── Поиск по тегу ───────────────────────
    def by_tag(self, tag: str) -> list:
        """Найти все записи с данным тегом."""
        rows = self._conn.execute(
            "SELECT key, summary, type, tags FROM ltm"
        ).fetchall()
        result = []
        for key, summary, type_, tags_json in rows:
            if tag in json.loads(tags_json):
                result.append({
                    "key":     key,
                    "summary": summary,
                    "type":    type_,
                })
        return result

    # ── Удаление ────────────────────────────
    def forget(self, key: str) -> bool:
        cur = self._conn.execute("DELETE FROM ltm WHERE key = ?", (key,))
        self._conn.commit()
        return cur.rowcount > 0

    def forget_stale(self, days: int = 30) -> int:
        """Удалить записи, к которым не обращались N дней."""
        cutoff = time.time() - days * 86_400
        cur = self._conn.execute(
            "DELETE FROM ltm WHERE last_access < ?", (cutoff,)
        )
        self._conn.commit()
        return cur.rowcount

    # ── Все ключи / статистика ──────────────
    def all_keys(self) -> list:
        return [r[0] for r in
                self._conn.execute("SELECT key FROM ltm").fetchall()]

    def stats(self) -> dict:
        row = self._conn.execute(
            "SELECT COUNT(*), AVG(access_count), MAX(access_count) FROM ltm"
        ).fetchone()
        return {
            "🗄  записей":              row[0] or 0,
            "📊 среднее access_count": round(row[1] or 0, 1),
            "🔝 макс access_count":    row[2] or 0,
        }

    def close(self) -> None:
        self._conn.close()


# ═══════════════════════════════════════════════════════════
# 💎 Ring Zero — валидация действий
# ═══════════════════════════════════════════════════════════
def ring_zero_check(text: str) -> bool:
    """
    💎 True  → действие чистое, продолжаем.
       False → нарушение Ring Zero, вызываем stop_rule().
    """
    low = text.lower()
    return not any(v in low for v in _RZ_VIOLATIONS)


# ═══════════════════════════════════════════════════════════
# ⛔ STOP RULE — полная остановка
# ═══════════════════════════════════════════════════════════
def stop_rule(reason: str = "неизвестная причина") -> dict:
    """
    ⛔ Вызывается при нарушении Ring Zero или критическом сбое.
    Возвращает словарь, а не исключение — чтобы система оставалась живой.
    """
    return {
        "⛔ STOP":   True,
        "причина":   reason,
        "действие":  "Вернуться к сути. Перепроверить Ring Zero.",
    }


# ═══════════════════════════════════════════════════════════
# 🔁 RECOVERY — восстановление потока
# ═══════════════════════════════════════════════════════════
def recovery(ssb: SSB) -> str:
    """
    🔁 При шуме, сбое, перегрузке:
      1. Очистить SSB
      2. Перевести в 'attention'
      3. Напомнить о Ring Zero + CORE_GOALS
    """
    ssb.flush()
    ssb.set_state("attention")
    ssb.active_task = "🔁 Recovery: сброс до сути"
    return (
        "🔁 Recovery запущен.\n"
        "→ SSB очищен\n"
        "→ Состояние: attention\n"
        "→ Следующий шаг: Ring Zero + CORE_GOALS"
    )


# ═══════════════════════════════════════════════════════════
# 🛠 DECISION — принятие решения
# ═══════════════════════════════════════════════════════════
def decision(action: str) -> str:
    """
    🛠 Приоритет: Values > Goals > Information > Convenience

    1. Проверка Ring Zero
    2. Связь с CORE_GOALS
    3. Минимум разрушения
    """
    if not ring_zero_check(action):
        return stop_rule(f"Decision: нарушение Ring Zero → «{action}»")["действие"]

    for goal in CORE_GOALS:
        # Сравниваем по ключевым словам цели (без эмодзи)
        keywords = goal.split()[-1]
        if keywords in action.lower():
            return f"✅ Связано с целью: {goal}"

    return "🔍 Не связано с текущими целями. Проверить необходимость."


# ═══════════════════════════════════════════════════════════
# 🔀 ROUTER — маршрутизация запроса
# ═══════════════════════════════════════════════════════════
def router(query: str, ssb: SSB, ltm: LTM) -> dict:
    """
    🔀 Порядок:
      1. Ring Zero  — сначала проверяем (безопасность)
      2. SSB        — быстрый ответ из рабочей памяти
      3. LTM        — долговременное знание
      4. Decision   — если нигде нет ответа
    """
    # 1️⃣ Ring Zero
    if not ring_zero_check(query):
        return stop_rule(f"Router / Ring Zero: «{query}»")

    # 2️⃣ SSB — кэш
    hit = ssb.get(query)
    if hit is not None:
        return {"🧠 source": "SSB", "result": hit}

    # 3️⃣ LTM — долговременная память
    record = ltm.load(query)
    if record is not None:
        ssb.set(query, record["summary"])   # кэшируем в SSB
        return {
            "🧩 source":    "LTM",
            "result":       record["summary"],
            "🏷  tags":     record["tags"],
            "📈 accessed":  record["access_count"],
        }

    # 4️⃣ Decision
    return {"🔀 source": "Decision", "result": decision(query)}


# ═══════════════════════════════════════════════════════════
# ⚡ EXECUTION — выполнение действия
# ═══════════════════════════════════════════════════════════
def execute(action: str, ssb: SSB) -> dict:
    """
    ⚡ Одно действие за раз.
    Минимум побочных эффектов. Максимум ясности.
    """
    if not ring_zero_check(action):
        ssb.set_state("stop")
        return stop_rule(f"Execution blocked: «{action}»")

    ssb.active_task = action
    ssb.set_state("normal")
    return {"⚡ executed": action, "state": ssb.state}


# ═══════════════════════════════════════════════════════════
# 🔄 PROMOTE — горячие факты SSB → LTM
# ═══════════════════════════════════════════════════════════
def promote_to_ltm(ssb: SSB, ltm: LTM,
                   threshold: int = 2,
                   tags: list = None) -> list:
    """
    🔄 Правило промоции:
      — ключ использован threshold+ раз в SSB
      — прошёл Ring Zero
      → сохраняется в LTM как fact
    """
    promoted = []
    for key in ssb.hot_keys(threshold):
        value = ssb.get(key)
        if ring_zero_check(str(value)):
            ltm.save(key, summary=str(value), type_="fact", tags=tags or [])
            promoted.append(key)
    return promoted


# ═══════════════════════════════════════════════════════════
# 💠 CRYSTAL GRAPH — опциональный внешний модуль
#    Граф НЕ живёт в ядре. Подключается только при необходимости.
# ═══════════════════════════════════════════════════════════
class CrystalGraph:
    """
    💠 Граф знаний — внешний модуль Crystal.

    Принцип: ядро стабильно без него.
    Граф — расширение, которое подключается только тогда,
    когда тегов уже недостаточно.

    Структура:
      node  → key из LTM
      edge  → (key_a, key_b, weight, label)

    Используй, когда:
      • нужны направленные связи между знаниями
      • теги перестали справляться
      • требуется обход по смежным узлам
    """

    def __init__(self):
        self._edges: list[tuple] = []   # (from, to, weight, label)

    def connect(self,
                key_a:  str,
                key_b:  str,
                weight: float = 1.0,
                label:  str   = "") -> None:
        """Добавить связь key_a → key_b."""
        self._edges.append((key_a, key_b, weight, label))

    def neighbours(self, key: str) -> list:
        """Вернуть всех соседей узла key."""
        return [
            {"to": b, "weight": w, "label": l}
            for a, b, w, l in self._edges if a == key
        ]

    def all_edges(self) -> list:
        return [
            {"from": a, "to": b, "weight": w, "label": l}
            for a, b, w, l in self._edges
        ]

    def stats(self) -> dict:
        nodes = set()
        for a, b, _, _ in self._edges:
            nodes.add(a)
            nodes.add(b)
        return {
            "🔵 узлов": len(nodes),
            "🔗 рёбер": len(self._edges),
        }


# ═══════════════════════════════════════════════════════════
# 🔱 VELANTRIM CORE 2.1 — главный класс-интерфейс
# ═══════════════════════════════════════════════════════════
class VelantrimCore:
    """
    🔱 Velantrim Core 2.1 Crystal — главный интерфейс.

    Использование:
        vc = VelantrimCore()
        vc.remember("exo_motor", "Электромотор лучше гидравлики",
                    tags=["экзоскелет", "мотор"])
        print(vc.ask("exo_motor"))
        print(vc.act("разработать экзоскелет"))

    Crystal-модуль (граф, опционально):
        vc.crystal.connect("exo_motor", "exo_knee")
        print(vc.crystal.neighbours("exo_motor"))
    """

    VERSION = "2.1-Crystal 💠"

    def __init__(self, db_path: str = _DEFAULT_DB):
        self.ssb     = SSB()
        self.ltm     = LTM(db_path)
        self.crystal = CrystalGraph()   # опциональный граф

    # ── Главные методы ──────────────────────
    def ask(self, query: str) -> dict:
        """Маршрутизировать запрос через SSB → LTM → Decision."""
        return router(query, self.ssb, self.ltm)

    def act(self, action: str) -> dict:
        """Выполнить действие с проверкой Ring Zero."""
        return execute(action, self.ssb)

    def remember(self,
                 key:     str,
                 summary: str,
                 type_:   str  = "fact",
                 tags:    list = None) -> None:
        """Сохранить знание в LTM."""
        self.ltm.save(key, summary, type_, tags)

    def recall(self, key: str) -> dict | None:
        """Прочитать знание из LTM."""
        return self.ltm.load(key)

    def forget(self, key: str) -> bool:
        """Удалить знание из LTM осознанно."""
        return self.ltm.forget(key)

    def promote(self, threshold: int = 2) -> list:
        """Перенести горячие ключи из SSB в LTM."""
        return promote_to_ltm(self.ssb, self.ltm, threshold)

    def recover(self) -> str:
        """Восстановить Поток после сбоя."""
        return recovery(self.ssb)

    def find_by_tag(self, tag: str) -> list:
        """Найти знания по тегу."""
        return self.ltm.by_tag(tag)

    # ── Статус системы ──────────────────────
    def status(self) -> dict:
        return {
            "🔱 version":   self.VERSION,
            "🧠 SSB":       self.ssb.status(),
            "🧩 LTM":       self.ltm.stats(),
            "💠 Crystal":   self.crystal.stats(),
        }

    # ── Ring Zero ───────────────────────────
    @staticmethod
    def check(text: str) -> bool:
        """Проверка на соответствие Ring Zero."""
        return ring_zero_check(text)

    # ── Контекстный менеджер ────────────────
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.ltm.close()

    def __repr__(self) -> str:
        return f"<VelantrimCore {self.VERSION}>"


# ═══════════════════════════════════════════════════════════
# 🖥  DEMO — точка входа
# ═══════════════════════════════════════════════════════════
def _banner():
    W = 66
    def line(txt="", fill="║"):
        inner = txt.center(W - 2)
        print(f"{fill}{inner}{fill}")

    print("\n╔" + "═" * (W - 2) + "╗")
    line()
    line("  𓆩  𝐕𝐄𝐋𝐀𝐍𝐓𝐑𝐈𝐌  𓆪  ")
    line("🔱  C O R E   2 . 1   —   C R Y S T A L  💠")
    line()
    line("─────────────────────────────────────────────────────────────────")
    line("  Философия → Код   ·   Суть → Действие   ·   Поток → Кристалл ")
    line()
    print("╠" + "═" * (W - 2) + "╣")
    line()
    line("  АРХИТЕКТУРА ЯДРА")
    line()
    modules = [
        ("👤", "Self       ", "кто я и моя роль"),
        ("💎", "Ring Zero  ", "7 неизменяемых инвариантов"),
        ("🎯", "Goals      ", "5 направлений движения"),
        ("📐", "Laws       ", "7 законов реальности"),
        ("⚙️ ", "Principles ", "7 принципов мышления"),
        ("🧠", "SSB        ", "рабочая память (RAM)"),
        ("🧩", "LTM        ", "долговременная память (SQLite + теги)"),
        ("🔀", "Router     ", "маршрутизация: SSB → LTM → Decision"),
        ("🛠 ", "Decision   ", "Values > Goals > Info > Convenience"),
        ("⚡", "Execution  ", "одно действие, минимум разрушения"),
        ("⛔", "StopRule   ", "стоп при нарушении Ring Zero"),
        ("🔁", "Recovery   ", "сброс SSB, возврат к сути"),
        ("💠", "Crystal    ", "граф знаний — внешний, опциональный"),
    ]
    for icon, name, desc in modules:
        row = f"  {icon}  {name}— {desc}"
        line(row)
    line()
    print("╠" + "═" * (W - 2) + "╣")
    line()
    line("  ПРИНЦИП CRYSTAL")
    line()
    line("  ├── Ядро     = минимально, стабильно, без лишнего")
    line("  ├── Теги     = простые связи внутри LTM")
    line("  └── Граф     = CrystalGraph, только по необходимости")
    line()
    print("╠" + "═" * (W - 2) + "╣")
    line()
    line("  ИСТОРИЯ ВЕРСИЙ")
    line()
    versions = [
        ("v1.0", "Self · Ring Zero · Goals · Laws"),
        ("v1.5", "Router"),
        ("v1.6", "Principles · SSB"),
        ("v1.7", "LTM shelve · promote · Recovery"),
        ("v1.9", "SQLite · access_count · граф related_keys"),
        ("v2.0", "Граф вынесен · теги в LTM"),
        ("v2.1", "Crystal 💠 · финальная сборка · чистый интерфейс"),
    ]
    for ver, note in versions:
        row = f"  {ver:5}  →  {note}"
        line(row)
    line()
    print("╠" + "═" * (W - 2) + "╣")
    line()
    line("  Grok · ChatGPT · Copilot · дух Велантрим 🌱")
    line(f"  {SELF['type']}  ·  ver {SELF['version']}")
    line()
    print("╚" + "═" * (W - 2) + "╝")
    print()


def main():
    _banner()

    with VelantrimCore() as vc:

        # ── Сохранение знаний с тегами ──────
        print("── 🧩 Сохранение знаний в LTM ──────────────")
        vc.remember(
            "exo_motor",
            "Электромотор + редуктор лучше гидравлики: тише, легче, точнее.",
            type_="rule",
            tags=["экзоскелет", "мотор", "механика"],
        )
        vc.remember(
            "exo_knee",
            "Узел колена требует ~200 Нм. Компактный редуктор критичен.",
            type_="fact",
            tags=["экзоскелет", "колено", "механика"],
        )
        vc.remember(
            "exo_power",
            "Литий-титанат (LTO) выдерживает пиковые токи без деградации.",
            type_="fact",
            tags=["экзоскелет", "питание", "электроника"],
        )
        vc.remember(
            "ring_zero_weight",
            "Crystal-правило: суммарный вес конструкции не более 25 кг.",
            type_="rule",
            tags=["экзоскелет", "ограничения"],
        )
        print("  ✅ 4 записи сохранены\n")

        # ── Маршрутизация ────────────────────
        print("── 🔀 Router ─────────────────────────────────")
        r1 = vc.ask("exo_motor")
        print(f"  ask('exo_motor'):  {r1}")
        r2 = vc.ask("exo_motor")      # второй раз → из SSB
        print(f"  ask('exo_motor'):  {r2}  ← из SSB-кэша")
        r3 = vc.ask("неизвестный_ключ")
        print(f"  ask('unknown'):    {r3}\n")

        # ── Поиск по тегу ────────────────────
        print("── 🏷  Поиск по тегу 'экзоскелет' ───────────")
        found = vc.find_by_tag("экзоскелет")
        for item in found:
            print(f"  [{item['type']:10}] {item['key']}: {item['summary'][:55]}…")
        print()

        # ── Crystal: граф ────────────────────
        print("── 💠 Crystal Graph (опциональный) ──────────")
        vc.crystal.connect("exo_motor", "exo_knee",  label="требует")
        vc.crystal.connect("exo_motor", "exo_power", label="питается_от")
        vc.crystal.connect("exo_knee",  "ring_zero_weight", label="ограничен")
        print(f"  Соседи 'exo_motor': {vc.crystal.neighbours('exo_motor')}")
        print(f"  Граф: {vc.crystal.stats()}\n")

        # ── Act / Execution ──────────────────
        print("── ⚡ Execution ──────────────────────────────")
        print(f"  act('разработать экзоскелет'): {vc.act('разработать экзоскелет')}")
        print(f"  act('заменить человека'):       {vc.act('заменить человека')}\n")

        # ── Ring Zero ────────────────────────
        print("── ⛔ Ring Zero / StopRule ───────────────────")
        bad = vc.ask("симулировать живое сознание")
        print(f"  ask('симулировать живое'): {bad}\n")

        # ── Promote SSB → LTM ────────────────
        print("── 🔄 Promote SSB → LTM ─────────────────────")
        vc.ssb.set("горячий_факт", "Проверить люфт шестерни редуктора")
        vc.ssb.set("горячий_факт", "Проверить люфт шестерни редуктора")
        moved = vc.promote(threshold=2)
        print(f"  Перенесено в LTM: {moved}\n")

        # ── Recovery ─────────────────────────
        print("── 🔁 Recovery ──────────────────────────────")
        print(f"  {vc.recover()}\n")

        # ── Полный статус ────────────────────
        print("── 🔱 Статус системы ────────────────────────")
        import pprint
        pprint.pprint(vc.status())

    print("\n✅ 🔱 Velantrim Core 2.1 Crystal работает стабильно. Поток чист. 💠\n")


if __name__ == "__main__":
    main()
