import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import upgrade_agent

class UpgradeAgentTests(unittest.TestCase):
    def test_validation(self):
        old = 'from smart_ai import main as start_browser\ndef main():\n    start_browser()\nif __name__ == "__main__":\n    main()\n'
        new = 'from smart_ai import main as start_browser\ndef main():\n    print("Hi")\n    start_browser()\nif __name__ == "__main__":\n    main()\n'
        good, msg = upgrade_agent.validate_candidate('main.py', old, new)
        self.assertTrue(good, msg)
        good, msg = upgrade_agent.validate_candidate('main.py', old, 'import subprocess\n' + new)
        self.assertFalse(good)
        good, msg = upgrade_agent.validate_candidate('ai.py', 'x=1\n', 'def broken(:\n')
        self.assertFalse(good)

    def test_job_applies_only_main_and_saves_backups(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            initial = 'from smart_ai import main as start_browser\ndef main():\n    start_browser()\nif __name__ == "__main__":\n    main()\n'
            updated = initial.replace('    start_browser()', '    print("Hello")\n    start_browser()')
            (root / 'main.py').write_text(initial, encoding='utf-8')
            (root / 'ai.py').write_text('x = 1\n', encoding='utf-8')
            with patch.object(upgrade_agent, 'ROOT', root), patch.object(upgrade_agent, 'PREVIEW_DIR', root/'proposals'), patch.object(upgrade_agent, 'BACKUP_DIR', root/'backups'):
                result = upgrade_agent.job('main.py', 'Improve greeting', 'fake', True, ask=lambda *a: updated)
                self.assertEqual(result['status'], 'applied_to_main')
                self.assertEqual((root/'main.py').read_text(), updated)
                self.assertEqual(len(list((root/'backups').glob('*'))), 1)
                result2 = upgrade_agent.job('ai.py', 'Improve docs', 'fake', True, ask=lambda *a: 'x = 2\n')
                self.assertEqual(result2['status'], 'proposal')
                self.assertEqual((root/'ai.py').read_text(), 'x = 1\n')

if __name__ == '__main__':
    unittest.main()
