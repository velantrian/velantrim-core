import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from velantrim_core_2_1_crystal import VelantrimCore
from memory.memory_engine_interface import LegacyMemoryEngine


class MemoryConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.core = VelantrimCore(db_path=":memory:")

    def tearDown(self):
        self.core.ltm.close()

    def seed(self):
        self.core.remember("meeting", "Monday")
        self.assertEqual(self.core.ask("meeting")["result"], "Monday")

    def test_remember_invalidates_cached_value(self):
        self.seed()
        self.core.remember("meeting", "Tuesday")
        self.assertEqual(self.core.ask("meeting")["result"], "Tuesday")

    def test_forget_does_not_return_deleted_value(self):
        self.seed()
        self.assertTrue(self.core.forget("meeting"))
        self.assertIsNone(self.core.recall("meeting"))
        self.assertNotEqual(self.core.ask("meeting")["result"], "Monday")

    def test_forget_already_absent_ltm_key_clears_ssb(self):
        self.core.ssb.set("meeting", "cached-only")
        self.assertFalse(self.core.forget("meeting"))
        self.assertIsNone(self.core.ssb.get("meeting"))
        self.assertNotIn("meeting", self.core.ssb.hot_keys(0))

    def test_failed_save_preserves_cached_record(self):
        self.seed()
        with patch.object(self.core.ltm, "save", side_effect=sqlite3.OperationalError("write failed")):
            with self.assertRaises(sqlite3.OperationalError):
                self.core.remember("meeting", "Tuesday")
        self.assertEqual(self.core.ask("meeting")["result"], "Monday")

    def test_failed_forget_preserves_cached_record(self):
        self.seed()
        with patch.object(self.core.ltm, "forget", side_effect=sqlite3.OperationalError("delete failed")):
            with self.assertRaises(sqlite3.OperationalError):
                self.core.forget("meeting")
        self.assertEqual(self.core.ask("meeting")["result"], "Monday")

    def test_invalidation_preserves_other_context_and_task_state(self):
        self.seed()
        self.core.ssb.set("other", "unrelated")
        self.core.ssb.active_task = "current task"
        self.core.ssb.active_goal = "current goal"
        self.core.ssb.set_state("attention")
        self.core.remember("meeting", "Tuesday")
        self.assertEqual(self.core.ssb.get("other"), "unrelated")
        self.assertEqual(self.core.ssb.active_task, "current task")
        self.assertEqual(self.core.ssb.active_goal, "current goal")
        self.assertEqual(self.core.ssb.state, "attention")

    def test_adapter_store_uses_cache_aware_boundary(self):
        self.seed()
        adapter = LegacyMemoryEngine(self.core)
        self.assertTrue(adapter.store("meeting", "Tuesday", tags=["calendar"]))
        self.assertEqual(self.core.ask("meeting")["result"], "Tuesday")

    def test_adapter_recall_has_list_shape_and_metadata(self):
        adapter = LegacyMemoryEngine(self.core)
        adapter.store("meeting", "Tuesday", tags=["calendar"])
        rows = adapter.recall("meeting")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["key"], "meeting")
        self.assertEqual(rows[0]["value"], "Tuesday")
        self.assertEqual(rows[0]["tags"], ["calendar"])
        self.assertEqual(adapter.recall("absent"), [])

    def test_adapter_nonpositive_limit_returns_no_items(self):
        self.seed()
        adapter = LegacyMemoryEngine(self.core)
        self.assertEqual(adapter.recall("meeting", 0), [])
        self.assertEqual(adapter.recall("meeting", -1), [])

    def test_committed_update_survives_reopen(self):
        with tempfile.TemporaryDirectory() as scratch:
            path = str(Path(scratch) / "memory.db")
            with VelantrimCore(db_path=path) as first:
                first.remember("meeting", "Monday")
                first.ask("meeting")
                first.remember("meeting", "Tuesday")
            with VelantrimCore(db_path=path) as second:
                self.assertEqual(second.ask("meeting")["result"], "Tuesday")


if __name__ == "__main__":
    unittest.main()
