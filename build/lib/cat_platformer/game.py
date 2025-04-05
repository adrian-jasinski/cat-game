"""Cat platformer game implementation.

This game requires Python 3.12 exactly. If you encounter errors, please check your Python version:
    python --version

Installation instructions:
1. Make sure you're using Python 3.12
2. Install the game with: pip install -e .
   or with uv: uv pip install -e .
3. Run the game with: python cat_platformer_game.py
"""

import pygame
import random
import sys
import os

# Initialize pygame
pygame.init()

# Game constants
WIDTH, HEIGHT = 800, 600
GROUND_LEVEL = HEIGHT - 100
FPS = 60
GRAVITY = 1
JUMP_FORCE = -20
OBSTACLE_SPEED = 7

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BROWN = (139, 69, 19)
SKY_BLUE = (135, 206, 235)

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cat Platformer")
clock = pygame.time.Clock()

# Create game directory for assets if it doesn't exist
if not os.path.exists("assets"):
    os.makedirs("assets")


# Cat class
class Cat(pygame.sprite.Sprite):
    """Cat sprite that the player controls."""

    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((50, 50), pygame.SRCALPHA)

        # Draw a cat-like shape instead of just a red rectangle
        # Body
        pygame.draw.ellipse(self.image, RED, (0, 10, 40, 30))
        # Head
        pygame.draw.circle(self.image, RED, (42, 15), 12)
        # Ears
        pygame.draw.polygon(self.image, RED, [(38, 5), (42, 0), (46, 5)])
        pygame.draw.polygon(self.image, RED, [(48, 5), (52, 0), (52, 8)])
        # Legs
        pygame.draw.rect(self.image, RED, (5, 35, 5, 15))
        pygame.draw.rect(self.image, RED, (20, 35, 5, 15))
        # Eyes
        pygame.draw.circle(self.image, BLACK, (38, 12), 2)
        pygame.draw.circle(self.image, BLACK, (46, 12), 2)

        self.rect = self.image.get_rect()
        self.rect.bottomleft = (100, GROUND_LEVEL)
        self.velocity_y = 0
        self.on_ground = True

    def jump(self):
        """Make the cat jump if it's on the ground."""
        if self.on_ground:
            self.velocity_y = JUMP_FORCE
            self.on_ground = False

    def update(self):
        """Update the cat's position."""
        # Apply gravity
        self.velocity_y += GRAVITY
        self.rect.y += self.velocity_y

        # Check if cat is on ground
        if self.rect.bottom >= GROUND_LEVEL:
            self.rect.bottom = GROUND_LEVEL
            self.velocity_y = 0
            self.on_ground = True


# Obstacle class
class Obstacle(pygame.sprite.Sprite):
    """Obstacles that the cat must jump over."""

    def __init__(self):
        super().__init__()
        self.height = random.randint(30, 70)
        self.width = random.randint(20, 40)
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Different obstacle types
        obstacle_type = random.choice(["cactus", "rock", "spike"])

        if obstacle_type == "cactus":
            # Draw a cactus-like obstacle
            color = (0, 100, 0)  # Dark green
            pygame.draw.rect(
                self.image, color, (self.width // 3, 0, self.width // 3, self.height)
            )
            # Arms
            pygame.draw.rect(
                self.image,
                color,
                (0, self.height // 3, self.width // 2, self.height // 6),
            )
            pygame.draw.rect(
                self.image,
                color,
                (
                    self.width // 2,
                    self.height // 1.5,
                    self.width // 2,
                    self.height // 6,
                ),
            )

        elif obstacle_type == "rock":
            # Draw a rock-like obstacle
            color = (100, 100, 100)  # Gray
            pygame.draw.polygon(
                self.image,
                color,
                [
                    (0, self.height),
                    (self.width // 4, self.height // 2),
                    (self.width // 2, self.height // 4),
                    (3 * self.width // 4, self.height // 2),
                    (self.width, self.height),
                ],
            )

        else:  # spike
            # Draw a spike-like obstacle
            color = (139, 0, 0)  # Dark red
            pygame.draw.polygon(
                self.image,
                color,
                [(0, self.height), (self.width // 2, 0), (self.width, self.height)],
            )

        self.rect = self.image.get_rect()
        self.rect.bottomleft = (WIDTH, GROUND_LEVEL)
        self.speed = OBSTACLE_SPEED
        self.already_passed = False

    def update(self):
        """Move the obstacle and check if it's off-screen."""
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()


# Cloud class for background
class Cloud(pygame.sprite.Sprite):
    """Decorative clouds that move in the background."""

    def __init__(self):
        super().__init__()
        self.width = random.randint(60, 120)
        self.height = random.randint(30, 50)
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Draw cloud
        for i in range(3):
            radius = random.randint(15, 25)
            x = random.randint(0, self.width - radius)
            y = random.randint(0, self.height - radius)
            pygame.draw.circle(self.image, WHITE, (x, y), radius)

        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH)
        self.rect.y = random.randint(50, GROUND_LEVEL - 100)
        self.speed = random.uniform(0.5, 1.5)

    def update(self):
        """Move the cloud and wrap around when off-screen."""
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.rect.left = WIDTH
            self.rect.y = random.randint(50, GROUND_LEVEL - 100)
            self.speed = random.uniform(0.5, 1.5)


# Game class
class Game:
    """Main game class that manages the game state and rendering."""

    def __init__(self):
        """Initialize the game state."""
        self.cat = Cat()
        self.all_sprites = pygame.sprite.Group(self.cat)
        self.obstacles = pygame.sprite.Group()
        self.clouds = pygame.sprite.Group()

        # Create initial clouds
        for _ in range(5):
            cloud = Cloud()
            self.clouds.add(cloud)
            self.all_sprites.add(cloud)

        self.score = 0
        self.game_over = False
        self.show_splash = True
        self.obstacle_timer = 0
        self.last_obstacle = pygame.time.get_ticks()
        self.obstacle_frequency = 1500  # milliseconds
        self.font = pygame.font.SysFont("Arial", 24)
        self.title_font = pygame.font.SysFont("Arial", 48, bold=True)

    def draw_splash_screen(self):
        """Draw the splash screen with title and instructions."""
        # Title
        title_text = self.title_font.render("CAT PLATFORMER", True, (70, 30, 20))
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
        screen.blit(title_text, title_rect)

        # Instructions
        instructions = [
            "Help the red cat jump over obstacles!",
            "Press SPACE to jump",
            "Press R to restart after game over",
            "Press any key to start",
        ]

        for i, line in enumerate(instructions):
            text = self.font.render(line, True, BLACK)
            rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + i * 40))
            screen.blit(text, rect)

    def spawn_obstacle(self):
        """Spawn a new obstacle if it's time."""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_obstacle > self.obstacle_frequency:
            obstacle = Obstacle()
            self.obstacles.add(obstacle)
            self.all_sprites.add(obstacle)
            self.last_obstacle = current_time

    def check_collisions(self):
        """Check if the cat has collided with any obstacles."""
        if pygame.sprite.spritecollide(self.cat, self.obstacles, False):
            self.game_over = True

    def update_score(self):
        """Update the score when obstacles are passed."""
        for obstacle in self.obstacles:
            if obstacle.rect.right < self.cat.rect.left and not obstacle.already_passed:
                self.score += 1
                obstacle.already_passed = True

    def draw_score(self):
        """Draw the current score."""
        score_text = self.font.render(f"Score: {self.score}", True, BLACK)
        screen.blit(score_text, (10, 10))

    def draw_game_over(self):
        """Draw the game over screen."""
        game_over_text = self.font.render("GAME OVER! Press R to restart", True, BLACK)
        screen.blit(game_over_text, (WIDTH // 2 - 150, HEIGHT // 2))

        final_score_text = self.font.render(f"Final Score: {self.score}", True, BLACK)
        screen.blit(final_score_text, (WIDTH // 2 - 70, HEIGHT // 2 + 40))

    def reset(self):
        """Reset the entire game state."""
        self.__init__()

    def run(self):
        """Run the main game loop."""
        # Game loop
        running = True
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if self.show_splash:
                        self.show_splash = False
                    elif event.key == pygame.K_SPACE and not self.game_over:
                        self.cat.jump()
                    elif event.key == pygame.K_r and self.game_over:
                        self.reset()

            if not self.game_over and not self.show_splash:
                # Spawn obstacles
                self.spawn_obstacle()

                # Update all sprites
                self.all_sprites.update()

                # Check for collisions
                self.check_collisions()

                # Update score
                self.update_score()
            elif self.show_splash:
                # Only update clouds during splash screen
                self.clouds.update()

            # Draw everything
            screen.fill(SKY_BLUE)

            # Draw clouds
            self.clouds.draw(screen)

            if self.show_splash:
                self.draw_splash_screen()
            else:
                # Draw ground
                pygame.draw.rect(
                    screen, BROWN, (0, GROUND_LEVEL, WIDTH, HEIGHT - GROUND_LEVEL)
                )
                pygame.draw.line(
                    screen,
                    (0, 200, 0),
                    (0, GROUND_LEVEL - 5),
                    (WIDTH, GROUND_LEVEL - 5),
                    10,
                )  # Grass

                # Draw cat and obstacles
                self.obstacles.draw(screen)
                screen.blit(self.cat.image, self.cat.rect)

                self.draw_score()

                if self.game_over:
                    self.draw_game_over()

            # Update display
            pygame.display.flip()

            # Cap framerate
            clock.tick(FPS)


# Run the game directly if this file is executed
if __name__ == "__main__":
    game = Game()
    game.run()
