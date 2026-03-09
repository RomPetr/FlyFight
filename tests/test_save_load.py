import unittest

from game import config
from game.main import load_session, new_session, serialize_session
from game.save.checkpoint import load_checkpoint, save_checkpoint


class TestSaveLoad(unittest.TestCase):
    def test_save_and_load_checkpoint_payload(self) -> None:
        session = new_session()
        session.scoring.score = 3456
        session.scoring.lives = 2
        session.scoring.run_time_seconds = 88.4
        save_checkpoint(serialize_session(session))

        payload = load_checkpoint()
        self.assertIsNotNone(payload)
        assert payload is not None
        restored = load_session(payload)
        self.assertEqual(restored.scoring.score, 3456)
        self.assertEqual(restored.scoring.lives, 2)
        self.assertAlmostEqual(restored.scoring.run_time_seconds, 88.4, places=1)

    def tearDown(self) -> None:
        if config.CHECKPOINT_FILE.exists():
            config.CHECKPOINT_FILE.unlink()
        if config.SAVE_DIR.exists():
            try:
                config.SAVE_DIR.rmdir()
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()

