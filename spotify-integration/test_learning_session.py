import unittest
from learning_session import create_activity

class LearningSessionTests(unittest.TestCase):
    def test_activity_is_created_by_level(self):
        activity = create_activity("advanced")
        self.assertEqual(activity["source"]["level"], "advanced")
        self.assertIn("three words", activity["instruction"])

if __name__ == "__main__": unittest.main()
