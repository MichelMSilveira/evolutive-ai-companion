import tempfile
import unittest
from pathlib import Path
from orchestrator import NovaOrchestrator


class OrchestratorTests(unittest.TestCase):
    def test_prepare_unifies_state_and_context(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            app = NovaOrchestrator(root / "state.json", root / "memory.db", "You are Nova.")
            app.remember("Michel trabalha com automação", "profile")
            context = app.prepare("Quero estudar automação", "study")
            self.assertEqual(context["state"]["xp"], 15)
            self.assertEqual(context["messages"][0]["role"], "system")
            self.assertEqual(len(app.memories.search("automação")), 1)
            app.close()


if __name__ == "__main__":
    unittest.main()
