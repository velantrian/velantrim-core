import sqlite3
import threading
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


    def test_failed_commit_rolls_back_pending_save(self):
        with tempfile.TemporaryDirectory() as scratch:
            path = str(Path(scratch) / "locked.db")
            with VelantrimCore(db_path=path) as core:
                core.remember("meeting", "Monday")
                core.ask("meeting")
                blocker = sqlite3.connect(path, timeout=0.1)
                try:
                    blocker.execute("BEGIN")
                    blocker.execute("SELECT * FROM ltm").fetchall()
                    core.ltm._conn.execute("PRAGMA busy_timeout = 100")
                    with self.assertRaises(sqlite3.OperationalError):
                        core.remember("meeting", "Tuesday")
                    self.assertFalse(core.ltm._conn.in_transaction)
                    self.assertEqual(core.ssb.get("meeting"), "Monday")
                    blocker.rollback()
                    core.remember("other", "ok")
                    self.assertEqual(core.recall("meeting")["summary"], "Monday")
                finally:
                    blocker.close()

    def test_failed_commit_rolls_back_pending_delete(self):
        with tempfile.TemporaryDirectory() as scratch:
            path = str(Path(scratch) / "locked.db")
            with VelantrimCore(db_path=path) as core:
                core.remember("meeting", "Monday")
                core.ask("meeting")
                blocker = sqlite3.connect(path, timeout=0.1)
                try:
                    blocker.execute("BEGIN")
                    blocker.execute("SELECT * FROM ltm").fetchall()
                    core.ltm._conn.execute("PRAGMA busy_timeout = 100")
                    with self.assertRaises(sqlite3.OperationalError):
                        core.forget("meeting")
                    self.assertFalse(core.ltm._conn.in_transaction)
                    self.assertEqual(core.ssb.get("meeting"), "Monday")
                    blocker.rollback()
                    core.remember("other", "ok")
                    self.assertEqual(core.recall("meeting")["summary"], "Monday")
                finally:
                    blocker.close()

    def test_parallel_read_cannot_repopulate_stale_cache_after_write(self):
        self.seed()
        self.core.ssb.discard("meeting")
        entered = threading.Event()
        release = threading.Event()
        original_load = self.core.ltm.load
        results = []
        failures = []

        def delayed_load(key):
            result = original_load(key)
            entered.set()
            if not release.wait(3):
                raise TimeoutError("read was not released")
            return result

        def reader():
            try:
                results.append(self.core.ask("meeting"))
            except Exception as exc:
                failures.append(exc)

        def writer():
            try:
                self.core.remember("meeting", "Tuesday")
            except Exception as exc:
                failures.append(exc)

        with patch.object(self.core.ltm, "load", side_effect=delayed_load):
            read_thread = threading.Thread(target=reader)
            write_thread = threading.Thread(target=writer)
            read_thread.start()
            try:
                self.assertTrue(entered.wait(3))
                write_thread.start()
            finally:
                release.set()
                read_thread.join(3)
                if write_thread.ident is not None:
                    write_thread.join(3)
            self.assertFalse(read_thread.is_alive())
            self.assertFalse(write_thread.is_alive())
        self.assertEqual(failures, [])
        self.assertEqual(len(results), 1)
        self.assertEqual(self.core.ask("meeting")["result"], "Tuesday")
        self.assertEqual(self.core.ssb.get("meeting"), "Tuesday")

if __name__ == "__main__":
    unittest.main()
