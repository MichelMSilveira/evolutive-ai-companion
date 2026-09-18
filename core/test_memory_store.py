import tempfile
import unittest
from pathlib import Path
from memory_store import MemoryStore

class MemoryStoreTests(unittest.TestCase):
    def test_add_search_and_forget(self):
        with tempfile.TemporaryDirectory() as folder:
            store = MemoryStore(Path(folder) / "nova.db")
            memory_id = store.add("Michel quer praticar inglês profissional", "profile")
            self.assertEqual(store.search("inglês")[0]["id"], memory_id)
            store.forget(memory_id)
            self.assertEqual(store.search("inglês"), [])
            store.close()

if __name__ == "__main__":
    unittest.main()
