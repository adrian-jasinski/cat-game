"""Main entry point for the cat platformer game."""

from cat_platformer.game import Game


def main():
    """Run the cat platformer game."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
