# FlyFight

FlyFight is a 2D arcade space shooter built with Python and Pygame.
You control a player ship, dodge enemy fire, and destroy enemy ships and meteorites.

## What the game is about

- Fast wave-based space combat.
- Different enemy and meteor durability tiers:
  - weak targets: 1 base laser hit
  - medium targets: 2 base laser hits
  - strong/large targets: 3 base laser hits
- Visual feedback for stronger targets with HP bars.
- Bonus mechanics and weapon upgrades to increase firepower.

## Project structure (short)

- `game/` - core game code (entities, systems, UI, config)
- `tests/` - unit tests
- `logs/` - work/session logs from agent-driven development

## Run locally

1. Install dependencies:
   - `pip install -r requirements.txt`
2. Start the game:
   - `python run_game.py`

## Notes

- Local source asset folders are intentionally ignored by Git:
  - `IMAGES/`
  - `SoundExamples/`
