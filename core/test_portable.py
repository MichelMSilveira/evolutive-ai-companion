import json
import tempfile
import unittest
from pathlib import Path
from nova_core import new_state, save_state
from portable import export_character, import_character

class PortableTests(unittest.TestCase):
    def test_export_excludes_private_data_and_imports_character(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            state = new_state(); state["name"] = "Nova Michel"; state["xp"] = 240
            state["memory"] = ["private"]; save_state(root / "state.json", state)
            export_character(root / "state.json", root / "character.nova.json")
            package = json.loads((root / "character.nova.json").read_text(encoding="utf-8"))
            self.assertNotIn("private", json.dumps(package))
            imported = import_character(root / "character.nova.json", root / "new.json")
            self.assertEqual(imported["xp"], 240)

if __name__ == "__main__": unittest.main()
