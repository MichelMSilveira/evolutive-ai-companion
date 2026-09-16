import tempfile
import unittest
from pathlib import Path

from nova_core import apply_event, load_state, save_state

class NovaCoreTests(unittest.TestCase):
    def test_new_state_is_complete(self):
        state = load_state(Path("missing-state.json"))
        self.assertEqual(state["form"], "base-cat")
        self.assertEqual(state["level"], 1)
        self.assertEqual(set(state["attributes"]), {"intelligence", "creativity", "energy", "sociability", "curiosity"})

    def test_progression_and_persistence(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "nova.json"
            state = load_state(path)
            for _ in range(10):
                apply_event(state, "conversation")
            save_state(path, state)
            restored = load_state(path)
            self.assertEqual(restored["level"], 2)
            self.assertEqual(restored["xp"], 100)
            self.assertEqual(len(restored["history"]), 10)

    def test_evolution_form_unlocks(self):
        state = load_state(Path("missing-state.json"))
        for _ in range(34):
            apply_event(state, "study")
        self.assertEqual(state["form"], "evolved-cat")
        self.assertLessEqual(state["attributes"]["intelligence"], 5)

if __name__ == "__main__":
    unittest.main()
