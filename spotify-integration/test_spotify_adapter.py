import unittest
from spotify_adapter import SpotifyAdapter

class SpotifyAdapterTests(unittest.TestCase):
    def test_mock_mode_needs_no_account(self):
        adapter = SpotifyAdapter()
        self.assertEqual(adapter.status()["mode"], "mock")
        self.assertEqual(adapter.learning_queue("intermediate")[0]["level"], "intermediate")

if __name__ == "__main__": unittest.main()
