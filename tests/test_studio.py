"""KYCode Studio: trace engine, quiz, publishing, RSS, and Stripe honesty."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "evals" / "fixtures" / "notes-app"


def load_server(db_path):
    os.environ["KYC_DB"] = str(db_path)
    spec = importlib.util.spec_from_file_location("studio_server", ROOT / "app" / "server.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.init_db()
    return module


class StudioChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.srv = load_server(Path(self.tmp.name) / "test.db")
        self.project = self.srv.resolve_project(str(FIXTURE.relative_to(ROOT)))

    def test_scan_finds_files_and_actions(self):
        scan = self.srv.scan_project(self.project)
        self.assertEqual(scan["file_count"], 7)
        self.assertIn("Save", [entry["label"] for entry in scan["entry_labels"]])

    def test_trace_follows_save_to_storage(self):
        trace = self.srv.trace_action(self.project, "What happens when I press Save?")
        labels = [hop["label"] for hop in trace["hops"]]
        self.assertEqual(labels[0], '"Save" action')
        self.assertIn("on_save()", labels)
        self.assertIn("save_note()", labels)
        self.assertIn("put()", labels)
        for hop in trace["hops"]:
            source = (self.project / hop["file"]).read_text().splitlines()
            self.assertIn(hop["snippet"], source[hop["line"] - 1])
        self.assertTrue(trace["checks"])

    def test_trace_does_not_bleed_into_neighbour_handlers(self):
        trace = self.srv.trace_action(self.project, "What happens when I press Save?")
        labels = [hop["label"] for hop in trace["hops"]]
        self.assertNotIn("on_search()", labels)
        self.assertNotIn("on_export()", labels)

    def test_traversal_and_system_paths_are_rejected(self):
        with self.assertRaises(ValueError):
            self.srv.resolve_project("/etc")
        with self.assertRaises(ValueError):
            self.srv.resolve_project("no-such-folder-here")

    def test_quiz_waits_then_grades_from_the_trace(self):
        asked = self.srv.chat_turn(self.project, "Quiz me on Save", [], "quiz", None, None, None)
        self.assertIn("quiz", asked)
        self.assertEqual(asked["resume_point"], "waiting for your quiz answer")
        self.assertNotIn("expected", asked["quiz"])
        session = self.srv.get_trace_session(asked["session_id"])
        graded = self.srv.chat_turn(self.project, f"It ends at {session['quiz']['expected']}",
                                    [], "quiz-answer", None, None, None, session_id=asked["session_id"])
        self.assertTrue(graded["quiz_result"]["correct"])
        wrong = self.srv.grade_quiz(session["quiz"], "the butler did it")
        self.assertFalse(wrong["correct"])

    def test_local_chat_needs_no_key_and_cites_files(self):
        reply = self.srv.chat_turn(self.project, "What happens when I press Save?", [],
                                   "walkthrough", None, None, None)
        self.assertEqual(reply["source"], "local")
        self.assertIn("handlers.py", reply["reply"])
        self.assertTrue(reply["trace"]["hops"])

    def test_seed_publish_and_rss_round_trip(self):
        self.srv.seed_demo()
        episodes = self.srv.list_episodes()
        self.assertEqual(len(episodes), 1)
        episode = episodes[0]
        self.assertTrue(episode["demo"])
        self.assertTrue(episode["proof"]["verified"])
        self.assertGreaterEqual(episode["proof"]["hops"], 3)
        self.assertTrue(all(hop["file"] for hop in episode["code_path"]))

    def test_stripe_is_honest_when_unconfigured(self):
        os.environ.pop("STRIPE_SECRET_KEY", None)
        self.srv.seed_demo()
        result = self.srv.create_checkout("tip", self.srv.get_creator("demo"), None, "http://127.0.0.1:8765")
        self.assertFalse(result["configured"])
        self.assertFalse(self.srv.verify_checkout("cs_test_anything")["verified"])
        with self.srv.db() as conn:
            count = conn.execute("SELECT COUNT(*) AS n FROM purchases").fetchone()["n"]
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()


class ProofIntegrityChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.srv = load_server(Path(self.tmp.name) / "test.db")
        self.project = self.srv.resolve_project(str(FIXTURE.relative_to(ROOT)))
    def test_forged_episode_without_session_is_not_verified(self):
        episode_id = self.srv.create_episode({
            "creator": "faker", "title": "Forged proof", "published": True,
            "code_path": [{"label": "x()", "file": "fake.py", "line": 1, "snippet": "def x"}],
            "quiz": {"correct": True}})
        episode = self.srv.get_episode(episode_id)
        self.assertFalse(episode["proof"]["verified"])
        self.assertIn("does not prove", episode["proof"]["disclosure"])

    def test_unknown_session_is_rejected(self):
        with self.assertRaises(ValueError):
            self.srv.create_episode({"creator": "x", "title": "t", "session_id": "nope-not-real"})

    def test_server_session_attests_episode_and_grades_quiz(self):
        chat = self.srv.chat_turn(self.project, "Quiz me on the Save path", [], "quiz", None, None, None)
        self.assertIn("session_id", chat)
        self.assertNotIn("expected", chat["quiz"])  # answer never reaches the client
        session = self.srv.get_trace_session(chat["session_id"])
        self.assertTrue(session["hops"][0]["sha256"])
        graded = self.srv.chat_turn(self.project, f"It ends at {session['quiz']['expected']}",
                                    [], "quiz-answer", None, None, None, session_id=chat["session_id"])
        self.assertTrue(graded["quiz_result"]["correct"])
        episode_id = self.srv.create_episode({
            "creator": "real", "title": "Real proof", "published": True,
            "session_id": chat["session_id"],
            "code_path": [{"label": "forged()", "file": "no.py", "line": 9, "snippet": "x"}]})
        episode = self.srv.get_episode(episode_id)
        self.assertTrue(episode["proof"]["verified"])
        self.assertTrue(episode["proof"]["quiz_correct"])
        self.assertEqual(episode["code_path"][0]["label"], '"Save" action')  # server hops win

    def test_range_parser(self):
        self.assertEqual(self.srv.parse_range("bytes=0-99", 1000), (0, 99))
        self.assertEqual(self.srv.parse_range("bytes=900-", 1000), (900, 999))
        self.assertEqual(self.srv.parse_range("bytes=-50", 1000), (950, 999))
        self.assertIsNone(self.srv.parse_range("nonsense", 1000))
        self.assertIsNone(self.srv.parse_range(None, 1000))


class TokenChecks(unittest.TestCase):
    def test_tokens_css_is_generated_and_in_sync(self):
        import importlib.util as iu
        spec = iu.spec_from_file_location("gen_tokens", ROOT / "app" / "gen_tokens.py")
        gen = iu.module_from_spec(spec); spec.loader.exec_module(gen)
        import json as _json
        tokens = _json.loads((ROOT / "app" / "tokens.json").read_text())
        self.assertEqual(gen.render(tokens), (ROOT / "app" / "static" / "tokens.css").read_text())
        css = gen.render(tokens)
        for required in ("--background:", "--brand:", "--success:", "--warning:", "--info:", "--invert:", "--text-2xl:"):
            self.assertIn(required, css)
