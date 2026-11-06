import functools
import os
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from main import BotControlError, BotProcessManager, _request_handler


class BotProcessManagerTests(unittest.TestCase):
    def test_requires_token_before_starting(self) -> None:
        with patch.dict(os.environ, {"TELEBOT_TOKEN": ""}):
            with self.assertRaises(BotControlError):
                BotProcessManager().start()

    def test_starts_and_stops_bot_child_process(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_dir = Path(directory)
            (project_dir / "bot.py").touch()
            process = Mock()
            process.poll.return_value = None

            with (
                patch.dict(os.environ, {"TELEBOT_TOKEN": "test-token"}),
                patch("main.subprocess.Popen", return_value=process) as popen,
            ):
                manager = BotProcessManager(project_dir, "python-test")
                started = manager.start()

                self.assertTrue(started["running"])
                self.assertEqual(started["pid"], process.pid)
                self.assertNotIn("test-token", repr(started))
                self.assertEqual(popen.call_args.args[0][0:2], [
                    "python-test",
                    str(project_dir / "bot.py"),
                ])

                stopped = manager.stop()

            self.assertFalse(stopped["running"])
            process.terminate.assert_called_once()
            process.wait.assert_called_once_with(timeout=5)


class BotControlHTTPTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.frontend_patch = patch(
            "main.FRONTEND_DIR",
            Path(self.temporary_directory.name) / "missing-frontend",
        )
        self.frontend_patch.start()
        self.manager = Mock()
        self.manager.status.return_value = {
            "configured": True,
            "state": "running",
            "running": True,
            "pid": 42,
            "exit_code": None,
        }
        handler = functools.partial(
            _request_handler(
                package_install_enabled=True,
                install_token="local-test-token",
                bot_manager=self.manager,
            ),
            directory=tempfile.gettempdir(),
        )
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.origin = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.frontend_patch.stop()
        self.temporary_directory.cleanup()

    def request(self, path: str, method: str = "GET", token: str = "local-test-token"):
        headers = {"X-PyCompiler-Local-Token": token}
        if method == "POST":
            headers["Origin"] = self.origin
        request = Request(f"{self.origin}{path}", method=method, headers=headers)
        return urlopen(request, timeout=2)

    def test_serves_dashboard_and_authenticated_status(self) -> None:
        with urlopen(f"{self.origin}/bot", timeout=2) as response:
            self.assertEqual(response.status, 200)
            self.assertIn("Telegram bot", response.read().decode("utf-8"))
        with urlopen(f"{self.origin}/", timeout=2) as response:
            self.assertIn("Telegram bot", response.read().decode("utf-8"))

        with self.request("/api/bot/status") as response:
            payload = response.read().decode("utf-8")
            self.assertIn('"pid": 42', payload)

    def test_rejects_invalid_token_for_bot_control(self) -> None:
        with self.assertRaises(HTTPError) as raised:
            self.request("/api/bot/start", method="POST", token="wrong-token")

        self.assertEqual(raised.exception.code, 403)
        raised.exception.close()
        self.manager.start.assert_not_called()

    def test_local_status_rejects_cross_origin_token_requests(self) -> None:
        request = Request(
            f"{self.origin}/api/local/status",
            headers={"Origin": "http://attacker.example"},
        )
        with self.assertRaises(HTTPError) as raised:
            urlopen(request, timeout=2)

        self.assertEqual(raised.exception.code, 403)
        raised.exception.close()

    def test_start_and_stop_routes_control_the_bot(self) -> None:
        self.manager.start.return_value = {"running": True, "pid": 42}
        self.manager.stop.return_value = {"running": False, "pid": None}

        with self.request("/api/bot/start", method="POST") as response:
            self.assertEqual(response.status, 200)
        with self.request("/api/bot/stop", method="POST") as response:
            self.assertEqual(response.status, 200)

        self.manager.start.assert_called_once()
        self.manager.stop.assert_called_once()


if __name__ == "__main__":
    unittest.main()
