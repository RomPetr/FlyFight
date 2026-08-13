import tempfile
import unittest
from pathlib import Path

from game.systems.sound import discover_music_tracks


class TestMusicTrackDiscovery(unittest.TestCase):
    def test_discovers_wav_ogg_mp3_sorted_numerically(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "music10.mp3").write_bytes(b"x")
            (root / "music2.wav").write_bytes(b"x")
            (root / "music1.wav").write_bytes(b"x")
            (root / "music3.ogg").write_bytes(b"x")

            tracks = discover_music_tracks(root)
            numbers = [number for number, _path in tracks]
            self.assertEqual(numbers, [1, 2, 3, 10])

    def test_ignores_invalid_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "music1.wav").write_bytes(b"x")
            (root / "background.wav").write_bytes(b"x")
            (root / "music.wav").write_bytes(b"x")
            (root / "music5.flac").write_bytes(b"x")

            tracks = discover_music_tracks(root)
            self.assertEqual(len(tracks), 1)
            self.assertEqual(tracks[0][0], 1)

    def test_duplicate_number_prefers_wav(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "music3.ogg").write_bytes(b"x")
            (root / "music3.wav").write_bytes(b"x")

            tracks = discover_music_tracks(root)
            self.assertEqual(len(tracks), 1)
            self.assertEqual(tracks[0][1].suffix.lower(), ".wav")


if __name__ == "__main__":
    unittest.main()
