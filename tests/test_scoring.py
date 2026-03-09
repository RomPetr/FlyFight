import unittest

from game.systems.scoring import difficulty_multiplier, points_for_enemy


class TestScoring(unittest.TestCase):
    def test_stronger_enemy_is_worth_more(self) -> None:
        run_time = 70.0
        score = 1200
        danger = difficulty_multiplier(run_time, score)
        light_points = points_for_enemy(80, danger)
        elite_points = points_for_enemy(700, danger)
        self.assertGreater(elite_points, light_points)

    def test_difficulty_grows_with_time_and_score(self) -> None:
        early = difficulty_multiplier(10.0, 200)
        late = difficulty_multiplier(120.0, 8000)
        self.assertGreater(late, early)


if __name__ == "__main__":
    unittest.main()

