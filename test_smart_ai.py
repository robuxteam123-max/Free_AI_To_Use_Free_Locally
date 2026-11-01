"""Offline sanity checks: run with `py -m unittest test_smart_ai.py`."""
import unittest
from unittest.mock import patch
import smart_ai

class TestSmartAI(unittest.TestCase):
    def test_paths(self):
        expected = smart_ai.WORKSPACE.resolve() / "hello.py"
        self.assertEqual(smart_ai.workspace_path("hello.py"), expected)
        self.assertEqual(smart_ai.workspace_path("src/app.js"), smart_ai.WORKSPACE.resolve() / "src/app.js")
        for path in ("../outside.py", "C:/windows/win.ini", "/etc/passwd", ".env", "file.exe", "folder/../../secret.py", "file.py/evil.py"):
            with self.subTest(path=path), self.assertRaises(smart_ai.AppError):
                smart_ai.workspace_path(path)

    def test_fence_cleanup(self):
        self.assertEqual(smart_ai.strip_code_fences("```python\nprint('hi')\n```"), "print('hi')\n")
        self.assertEqual(smart_ai.strip_code_fences("print('hi')"), "print('hi')\n")

    @patch("smart_ai.ollama_json")
    def test_chat_forwards_user_and_system(self, fake):
        fake.return_value = {"message": {"content": "Hello from local model!"}}
        result = smart_ai.chat("qwen2.5-coder:3b", [{"role": "user", "content": "hi"}])
        self.assertEqual(result, "Hello from local model!")
        args, kwargs = fake.call_args
        self.assertEqual(args[0], "/api/chat")
        self.assertEqual(args[1]["model"], "qwen2.5-coder:3b")
        self.assertEqual(args[1]["messages"][0]["role"], "system")
        self.assertEqual(args[1]["messages"][1]["content"], "hi")
        self.assertFalse(args[1]["stream"])

if __name__ == "__main__":
    unittest.main()
