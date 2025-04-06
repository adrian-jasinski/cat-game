# Cat Platformer Game

A simple 2D platformer game built with Pygame where a cat jumps over obstacles.

## Features

- Animated cat character with different animations for running, jumping, falling, and death
- Beautiful multi-layered mountain background with parallax scrolling
- Various obstacles to avoid (rocks, cacti, bushes, and balloons)
- Detailed ground with grass, soil texture, and small flowers
- Particle effects for jumps and impacts
- Increasing difficulty as you progress
- Score tracking
- Death animations when you collide with obstacles
- Shooting ability that destroys obstacles (earn a shot for every 20 points)

## Screenshots

The game features:
- Atmospheric dusk mountain background with parallax scrolling
- Silhouetted forest treeline against a dusk/night sky
- Detailed pixel-art animation for the cat character
- Dynamic lighting and particle effects
- Richly textured ground with details

## Requirements

- Python 3.12 (exact version, not higher)
- Pygame 2.5.2

## Python Version

This project requires **exactly Python 3.12**, not higher or lower. A `.python-version` file is included for tools like pyenv to automatically select the correct version.

You can verify your Python version with:

```bash
python --version
```

Or use the included version check script:

```bash
python check_python_version.py
```

## Quick Start

The easiest way to play is using the play.py script, which checks Python version and handles pygame installation:

```bash
./play.py
```

OR

```bash
python play.py
```

## Running the Game

After installation, you can run the game in several ways:

1. Using the executable script in the project root:
   ```bash
   ./cat_platformer_game.py
   ```

2. As a Python module:
   ```bash
   python -m cat_platformer
   ```

3. Running the main script directly:
   ```bash
   python cat_platformer_game.py
   ```

## Setup with pip

1. Make sure you have Python 3.12 installed
2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate the virtual environment:
   - On Linux/macOS:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
4. Install from pyproject.toml:
   ```bash
   pip install -e .
   ```
5. Run the game:
   ```bash
   python cat_platformer_game.py
   ```

## File Structure

The game files are organized as follows:

```
cat-game/
├── assets/                  # Game assets
│   ├── graphics/           # All graphical assets
│   │   ├── cat/            # Cat animation frames
│   │   ├── ground/         # Ground textures
│   │   └── obstacles/      # Obstacle images
│   ├── backgrounds/        # Background images
│   ├── sounds/             # Sound effects
│   └── highscore.txt       # Saved high score
├── cat_platformer/         # Game code
│   ├── __init__.py         
│   ├── __main__.py        
│   └── game.py             # Main game logic
├── cat_platformer_game.py  # Game launcher
├── play.py                 # Launcher with version check
└── ... other config files
```

## Controls

- **UP ARROW**: Jump
- **DOWN ARROW**: Slide
- **SPACE**: Shoot (when shots are available)
- **R**: Restart game after game over
- **M**: Toggle sound
- **B**: Cycle through background styles

## Visibility Settings

The game has been optimized for visibility with:
- Bright, contrasting colors for the cat and obstacles
- Silhouetted foreground elements against the dusk sky
- Enhanced obstacle outlines for better gameplay visibility

## Game Mechanics

- Control a red cat on a platform
- Press space to jump over approaching obstacles
- Score increases for each obstacle you successfully avoid
- Game ends if you collide with an obstacle
- Press R to restart the game after a game over 