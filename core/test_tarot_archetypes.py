import unittest
from tarot_archetypes import advice, dominant_archetype

class TarotArchetypeTests(unittest.TestCase):
    def test_dominant_archetype_comes_from_metrics(self):
        state = {"attributes": {"intelligence": 1, "creativity": 5, "energy": 1, "sociability": 1, "curiosity": 1}}
        self.assertEqual(dominant_archetype(state)["name"], "O Mago")
        self.assertIn("ação concreta", advice(state))

if __name__ == "__main__": unittest.main()
