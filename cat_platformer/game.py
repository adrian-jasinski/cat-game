"""
Cat Platformer Game Module
This module contains the game mechanics for the Cat Platformer.
"""

import pygame
import glob
import logging
import math
import os
import random
import sys
from typing import List  # Only keep the types we're actually using

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cat_platformer.game")

# Initialize pygame
pygame.init()
try:
    # Initialize the mixer for sound - handle potential attribute errors
    if hasattr(pygame, "mixer"):
        pygame.mixer.init()
except Exception as e:
    logging.warning(f"Could not initialize sound mixer: {e}")

# Game constants
SCREEN_SIZE = (800, 600)
WIDTH, HEIGHT = SCREEN_SIZE
GROUND_LEVEL = HEIGHT - 100
FPS = 60

# Physics constants
GRAVITY = 1
JUMP_FORCE = -20
OBSTACLE_SPEED = 7
ANIMATION_SPEED = 6  # Frames per animation change
BULLET_SPEED = 15  # Speed of bullets for shooting
SHOOT_THRESHOLD = 20  # Score needed to earn a shot

# Difficulty progression
DIFFICULTY_INCREASE_RATE = 0.2  # How much to increase speed per 10 points
MAX_OBSTACLE_SPEED = 15  # Maximum speed for obstacles
MIN_OBSTACLE_FREQUENCY = 800  # Minimum time between obstacles (milliseconds)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BROWN = (139, 69, 19)
SKY_BLUE = (100, 180, 255)  # Much deeper blue for background
YELLOW = (255, 255, 0)  # Yellow for bullet effects

# Set up the display
screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption("Cat Platformer")
try:
    # Create clock instance for time tracking
    clock = pygame.time.Clock()
except Exception as e:
    logging.error(f"Error creating pygame clock: {e}")
    clock = None  # Fallback if Clock is not available

# Create game directory for assets if it doesn't exist
if not os.path.exists("assets"):
    os.makedirs("assets")


# Bullet class for shooting ability
class Bullet(pygame.sprite.Sprite):
    """Bullet sprite that can destroy obstacles."""

    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((15, 15), pygame.SRCALPHA)
        pygame.draw.circle(self.image, YELLOW, (7, 7), 7)  # Yellow ball

        # Add a glowing effect
        glow_surf = pygame.Surface((25, 25), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 255, 100, 100), (12, 12), 12)

        # Apply the glow to our bullet
        final_surf = pygame.Surface((25, 25), pygame.SRCALPHA)
        final_surf.blit(glow_surf, (0, 0))
        final_surf.blit(self.image, (5, 5))

        self.image = final_surf
        self.rect = self.image.get_rect()
        # Position the bullet at the middle of the cat
        self.rect.center = (x, y)
        self.speed = BULLET_SPEED

    def update(self):
        """Move the bullet and check if it's off-screen."""
        self.rect.x += self.speed
        # Remove bullet if it goes off screen
        if self.rect.left > WIDTH:
            self.kill()


class ParallaxBackground:
    """A class to manage scrolling parallax background for the game."""

    def __init__(self):
        """Initialize the background with multiple parallax layers."""
        self.scroll_speeds = [
            0.0,
            0.1,
            0.2,
            0.4,
            0.7,
        ]  # Different speeds for each layer
        self.scroll_positions = [0, 0, 0, 0, 0]  # Initial scroll positions
        self.layers = []  # Will store the background layers

        # Background styles
        self.background_styles = [
            self.create_blue_background_layers,  # Default blue background
            self.create_sunset_background_layers,  # Sunset theme
            self.create_night_background_layers,  # Night theme
            self.create_dawn_background_layers,  # Dawn theme
        ]

        self.current_style = 0  # Start with blue background

        # Create procedural blue background layers
        print("Creating procedural blue sky background.")
        self.background_styles[self.current_style]()

    def cycle_background(self):
        """Change to the next background style."""
        self.current_style = (self.current_style + 1) % len(self.background_styles)
        self.background_styles[self.current_style]()
        # Return the style index for other components to use
        return self.current_style

    def create_sunset_background_layers(self):
        """Create sunset-themed background layers."""
        # Layer 1 - Sunset gradient with stars
        layer1 = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
        for y in range(HEIGHT):
            # Create a sunset gradient from deep orange to yellow to light blue
            ratio = y / HEIGHT
            r = int(220 - ratio * 100)  # Red-orange fading to blue
            g = int(150 - ratio * 50)  # Medium amount fading down
            b = int(50 + ratio * 150)  # Blue increases toward bottom
            pygame.draw.line(layer1, (r, g, b), (0, y), (WIDTH * 2, y))

        # Add stars (fewer, since it's sunset)
        for _ in range(120):  # Half as many stars
            star_x = random.randint(0, WIDTH * 2)
            star_y = random.randint(
                0, int(HEIGHT * 0.4)
            )  # Stars only in upper 40% of sky
            star_size = random.randint(1, 2)
            # Stars with orange tint
            pygame.draw.circle(
                layer1,
                (255, 220, 200),
                (star_x, star_y),
                star_size,
            )

        # Layer 2 - Distant mountains (orange tinted)
        layer2 = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
        mountain_color = (80, 40, 60)  # Purple-red distant mountains

        for i in range(10):
            mountain_width = random.randint(200, 350)
            mountain_height = random.randint(100, 180)
            mountain_x = random.randint(0, WIDTH * 2)

            # Draw mountain with sunset coloring
            pygame.draw.polygon(
                layer2,
                mountain_color,
                [
                    (mountain_x - mountain_width // 2, GROUND_LEVEL),
                    (mountain_x, GROUND_LEVEL - mountain_height),
                    (mountain_x + mountain_width // 2, GROUND_LEVEL),
                ],
            )

            # Add highlight to mountain peaks (sunset glow)
            highlight_color = (150, 70, 60)  # Orange-red highlight
            pygame.draw.polygon(
                layer2,
                highlight_color,
                [
                    (
                        mountain_x - mountain_width // 4,
                        GROUND_LEVEL - mountain_height // 2,
                    ),
                    (mountain_x, GROUND_LEVEL - mountain_height),
                    (
                        mountain_x + mountain_width // 4,
                        GROUND_LEVEL - mountain_height // 2,
                    ),
                ],
            )

        # Layer 3 - Middle mountains (warm tints)
        layer3 = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
        mid_mountain_color = (100, 60, 80)  # Medium purple-red mountains

        for i in range(14):
            mountain_width = random.randint(150, 300)
            mountain_height = random.randint(80, 150)
            mountain_x = random.randint(0, WIDTH * 2)

            # Draw mountain
            pygame.draw.polygon(
                layer3,
                mid_mountain_color,
                [
                    (mountain_x - mountain_width // 2, GROUND_LEVEL),
                    (mountain_x, GROUND_LEVEL - mountain_height),
                    (mountain_x + mountain_width // 2, GROUND_LEVEL),
                ],
            )

            # Add slight texture to mountains
            for j in range(3):
                texture_x = mountain_x + random.randint(
                    -mountain_width // 3, mountain_width // 3
                )
                texture_y = GROUND_LEVEL - random.randint(10, mountain_height - 10)
                texture_size = random.randint(5, 15)
                texture_color = (120, 80, 90)  # Slightly lighter warm color

                pygame.draw.circle(
                    layer3,
                    texture_color,
                    (texture_x, texture_y),
                    texture_size,
                )

        # Layer 4 - Forest silhouette (dark purple)
        layer4 = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
        tree_color = (50, 30, 60)  # Dark purple silhouette

        # Draw tree line
        for i in range(80):
            tree_x = i * (WIDTH * 2 // 40)
            tree_height = random.randint(70, 130)
            tree_width = int(tree_height // 2)

            # Draw pine tree silhouette
            for j in range(3):
                size = tree_width - j * 5
                height = tree_height // 3
                y_pos = GROUND_LEVEL - height * (j + 1)
                pygame.draw.polygon(
                    layer4,
                    tree_color,
                    [
                        (tree_x, y_pos - height),
                        (tree_x - size // 2, y_pos),
                        (tree_x + size // 2, y_pos),
                    ],
                )

        # Layer 5 - Foreground trees (very dark purple)
        layer5 = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
        fg_tree_color = (30, 20, 40)  # Very dark purple

        for i in range(30):
            tree_x = random.randint(0, WIDTH * 2)
            tree_height = random.randint(120, 200)
            tree_width = int(tree_height // 1.5)

            # Draw larger foreground pine tree silhouette
            for j in range(4):
                size = tree_width - j * 8
                height = tree_height // 4
                y_pos = GROUND_LEVEL - height * (j + 1)
                pygame.draw.polygon(
                    layer5,
                    fg_tree_color,
                    [
                        (tree_x, y_pos - height),
                        (tree_x - size // 2, y_pos),
                        (tree_x + size // 2, y_pos),
                    ],
                )

            # Add slight variance to foreground trees
            branch_color = (40, 25, 50)  # Slightly lighter
            for _ in range(3):
                branch_x = tree_x + random.randint(-tree_width // 3, tree_width // 3)
                branch_y = GROUND_LEVEL - random.randint(20, tree_height - 20)
                branch_size = random.randint(10, 25)

                pygame.draw.circle(
                    layer5,
                    branch_color,
                    (branch_x, branch_y),
                    branch_size,
                )

        # Add sunset haze effect
        for _ in range(40):
            mist_x = random.randint(0, WIDTH * 2)
            mist_y = random.randint(GROUND_LEVEL - 100, GROUND_LEVEL - 10)
            mist_width = random.randint(100, 300)
            mist_height = random.randint(20, 60)

            mist_surface = pygame.Surface((mist_width, mist_height), pygame.SRCALPHA)
            for y in range(mist_height):
                alpha = 60 - int(abs(y - mist_height // 2) * 100 / mist_height)
                pygame.draw.line(
                    mist_surface,
                    (240, 180, 120, alpha),  # Orange haze
                    (0, y),
                    (mist_width, y),
                )

            layer5.blit(mist_surface, (mist_x, mist_y))

        # Add orange-tinted clouds
        self._add_clouds_to_layer(
            layer2, 3, light_color=(200, 150, 120), dark_color=(160, 100, 80)
        )
        self._add_clouds_to_layer(
            layer3, 5, light_color=(230, 180, 150), dark_color=(180, 120, 100)
        )

        # Add all layers in order of depth
        self.layers = [layer1, layer2, layer3, layer4, layer5]

    def create_night_background_layers(self):
        """Create night-themed background layers."""
        # Layer 1 - Night sky gradient with stars
        layer1 = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
        for y in range(HEIGHT):
            # Create a dark blue to black gradient
            ratio = y / HEIGHT
            r = int(10 + ratio * 20)  # Very little red
            g = int(20 + ratio * 30)  # Small amount of green
            b = int(60 + ratio * 30)  # More blue, fading to darker
            pygame.draw.line(layer1, (r, g, b), (0, y), (WIDTH * 2, y))

        # Add many bright stars
        for _ in range(500):  # More stars for night sky
            star_x = random.randint(0, WIDTH * 2)
            star_y = random.randint(0, int(HEIGHT * 0.85))  # Stars throughout sky

            # Vary star brightness and size
            brightness = random.randint(180, 255)
            star_size = random.random() * 2

            # Occasionally make a larger star with color
            if random.random() < 0.05:
                star_size = random.uniform(2, 3)
                # Random star colors (white, blue-white, yellow)
                colors = [(255, 255, 255), (200, 220, 255), (255, 240, 180)]
                color = random.choice(colors)
            else:
                color = (brightness, brightness, brightness)

            pygame.draw.circle(
                layer1,
                color,
                (star_x, star_y),
                star_size,
            )

        # Add a moon
        moon_x = random.randint(WIDTH // 4, WIDTH * 2 - WIDTH // 4)
        moon_y = random.randint(HEIGHT // 6, HEIGHT // 3)
        moon_radius = random.randint(30, 40)

        # Draw moon glow
        for r in range(moon_radius + 20, moon_radius - 1, -1):
            alpha = max(0, 80 - (moon_radius + 20 - r) * 4)
            pygame.draw.circle(layer1, (200, 200, 180, alpha), (moon_x, moon_y), r)

        # Draw moon
        pygame.draw.circle(layer1, (230, 230, 210), (moon_x, moon_y), moon_radius)

        # Maybe add a few moon craters
        for _ in range(3):
            crater_x = moon_x + random.randint(-moon_radius // 2, moon_radius // 2)
            crater_y = moon_y + random.randint(-moon_radius // 2, moon_radius // 2)

            # Only draw crater if it's within the moon
            if (crater_x - moon_x) ** 2 + (crater_y - moon_y) ** 2 < (
                moon_radius - 5
            ) ** 2:
                crater_size = random.randint(4, 8)
                pygame.draw.circle(
                    layer1, (200, 200, 180), (crater_x, crater_y), crater_size
                )

        # Layer 2 - Distant mountains (dark blue)
        layer2 = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
        mountain_color = (20, 30, 50)  # Very dark blue mountains

        for i in range(10):
            mountain_width = random.randint(200, 350)
            mountain_height = random.randint(100, 180)
            mountain_x = random.randint(0, WIDTH * 2)

            # Draw dark mountains
            pygame.draw.polygon(
                layer2,
                mountain_color,
                [
                    (mountain_x - mountain_width // 2, GROUND_LEVEL),
                    (mountain_x, GROUND_LEVEL - mountain_height),
                    (mountain_x + mountain_width // 2, GROUND_LEVEL),
                ],
            )

            # Add very subtle moonlight highlight
            highlight_color = (30, 40, 60)  # Slightly lighter blue
            pygame.draw.polygon(
                layer2,
                highlight_color,
                [
                    (
                        mountain_x - mountain_width // 4,
                        GROUND_LEVEL - mountain_height // 2,
                    ),
                    (mountain_x, GROUND_LEVEL - mountain_height),
                    (
                        mountain_x + mountain_width // 4,
                        GROUND_LEVEL - mountain_height // 2,
                    ),
                ],
            )

        # Layer 3 - Middle mountains (slightly lighter blue)
        layer3 = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
        mid_mountain_color = (25, 35, 60)  # Dark blue middle mountains

        for i in range(14):
            mountain_width = random.randint(150, 300)
            mountain_height = random.randint(80, 150)
            mountain_x = random.randint(0, WIDTH * 2)

            # Draw mountain
            pygame.draw.polygon(
                layer3,
                mid_mountain_color,
                [
                    (mountain_x - mountain_width // 2, GROUND_LEVEL),
                    (mountain_x, GROUND_LEVEL - mountain_height),
                    (mountain_x + mountain_width // 2, GROUND_LEVEL),
                ],
            )

        # Layer 4 - Forest silhouette (nearly black)
        layer4 = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
        tree_color = (10, 15, 30)  # Very dark blue, almost black

        # Draw tree line
        for i in range(80):
            tree_x = i * (WIDTH * 2 // 40)
            tree_height = random.randint(70, 130)
            tree_width = int(tree_height // 2)

            # Draw pine tree silhouette
            for j in range(3):
                size = tree_width - j * 5
                height = tree_height // 3
                y_pos = GROUND_LEVEL - height * (j + 1)
                pygame.draw.polygon(
                    layer4,
                    tree_color,
                    [
                        (tree_x, y_pos - height),
                        (tree_x - size // 2, y_pos),
                        (tree_x + size // 2, y_pos),
                    ],
                )

        # Layer 5 - Foreground trees (black)
        layer5 = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
        fg_tree_color = (5, 10, 20)  # Almost black

        for i in range(30):
            tree_x = random.randint(0, WIDTH * 2)
            tree_height = random.randint(120, 200)
            tree_width = int(tree_height // 1.5)

            # Draw larger foreground pine tree silhouette
            for j in range(4):
                size = tree_width - j * 8
                height = tree_height // 4
                y_pos = GROUND_LEVEL - height * (j + 1)
                pygame.draw.polygon(
                    layer5,
                    fg_tree_color,
                    [
                        (tree_x, y_pos - height),
                        (tree_x - size // 2, y_pos),
                        (tree_x + size // 2, y_pos),
                    ],
                )

        # Add very subtle night fog
        for _ in range(20):
            mist_x = random.randint(0, WIDTH * 2)
            mist_y = random.randint(GROUND_LEVEL - 100, GROUND_LEVEL - 10)
            mist_width = random.randint(100, 300)
            mist_height = random.randint(20, 60)

            mist_surface = pygame.Surface((mist_width, mist_height), pygame.SRCALPHA)
            for y in range(mist_height):
                alpha = 40 - int(abs(y - mist_height // 2) * 80 / mist_height)
                pygame.draw.line(
                    mist_surface,
                    (40, 50, 80, alpha),  # Dark blue-gray fog
                    (0, y),
                    (mist_width, y),
                )

            layer5.blit(mist_surface, (mist_x, mist_y))

        # Add all layers in order of depth
        self.layers = [layer1, layer2, layer3, layer4, layer5]

    def create_dawn_background_layers(self):
        """Create dawn/morning-themed background layers."""
        # Layer 1 - Dawn sky gradient
        layer1 = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
        for y in range(HEIGHT):
            # Create a dawn gradient - pink to light blue
            ratio = y / HEIGHT
            r = int(200 - ratio * 120)  # Pink fading to blue
            g = int(160 - ratio * 40)  # Medium fading to blue
            b = int(180 + ratio * 40)  # Light purple to blue
            pygame.draw.line(layer1, (r, g, b), (0, y), (WIDTH * 2, y))

        # Add a few stars fading out
        for _ in range(80):  # Fewer stars at dawn
            star_x = random.randint(0, WIDTH * 2)
            star_y = random.randint(0, int(HEIGHT * 0.3))  # Stars only at top
            star_size = random.randint(1, 2)
            # Fading stars
            star_alpha = max(0, 150 - (star_y * 2))
            pygame.draw.circle(
                layer1,
                (255, 255, 255, star_alpha),
                (star_x, star_y),
                star_size,
            )

        # Add a sun/glow
        sun_x = random.randint(WIDTH // 4, WIDTH // 2)
        sun_y = random.randint(HEIGHT // 4, HEIGHT // 3)

        # Draw sun glow
        for r in range(80, 30, -1):
            alpha = max(0, 120 - (r - 30) * 2)
            color = (255, 220 - (80 - r) // 2, 150 - (80 - r) // 2, alpha)
            pygame.draw.circle(layer1, color, (sun_x, sun_y), r)

        # Draw sun
        pygame.draw.circle(layer1, (255, 220, 150), (sun_x, sun_y), 30)

        # Layer 2 - Distant mountains (pink tinted)
        layer2 = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
        mountain_color = (90, 70, 100)  # Purple-pink distant mountains

        for i in range(10):
            mountain_width = random.randint(200, 350)
            mountain_height = random.randint(100, 180)
            mountain_x = random.randint(0, WIDTH * 2)

            # Draw mountain with dawn lighting
            pygame.draw.polygon(
                layer2,
                mountain_color,
                [
                    (mountain_x - mountain_width // 2, GROUND_LEVEL),
                    (mountain_x, GROUND_LEVEL - mountain_height),
                    (mountain_x + mountain_width // 2, GROUND_LEVEL),
                ],
            )

            # Add highlight - dawn light on mountain peaks
            highlight_color = (180, 140, 160)  # Pink highlight
            pygame.draw.polygon(
                layer2,
                highlight_color,
                [
                    (
                        mountain_x - mountain_width // 4,
                        GROUND_LEVEL - mountain_height // 1.2,
                    ),
                    (mountain_x, GROUND_LEVEL - mountain_height),
                    (
                        mountain_x + mountain_width // 4,
                        GROUND_LEVEL - mountain_height // 1.2,
                    ),
                ],
            )

        # Layer 3 - Middle mountains (lavender tints)
        layer3 = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
        mid_mountain_color = (70, 80, 110)  # Lavender-blue mountains

        for i in range(14):
            mountain_width = random.randint(150, 300)
            mountain_height = random.randint(80, 150)
            mountain_x = random.randint(0, WIDTH * 2)

            # Draw mountain
            pygame.draw.polygon(
                layer3,
                mid_mountain_color,
                [
                    (mountain_x - mountain_width // 2, GROUND_LEVEL),
                    (mountain_x, GROUND_LEVEL - mountain_height),
                    (mountain_x + mountain_width // 2, GROUND_LEVEL),
                ],
            )

        # Layer 4 - Forest silhouette (deep blue-purple)
        layer4 = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
        tree_color = (50, 50, 80)  # Deep blue-purple silhouette

        # Draw tree line
        for i in range(80):
            tree_x = i * (WIDTH * 2 // 40)
            tree_height = random.randint(70, 130)
            tree_width = int(tree_height // 2)

            # Draw pine tree silhouette
            for j in range(3):
                size = tree_width - j * 5
                height = tree_height // 3
                y_pos = GROUND_LEVEL - height * (j + 1)
                pygame.draw.polygon(
                    layer4,
                    tree_color,
                    [
                        (tree_x, y_pos - height),
                        (tree_x - size // 2, y_pos),
                        (tree_x + size // 2, y_pos),
                    ],
                )

        # Layer 5 - Foreground trees (dark blue-purple)
        layer5 = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
        fg_tree_color = (40, 40, 70)  # Dark blue-purple

        for i in range(30):
            tree_x = random.randint(0, WIDTH * 2)
            tree_height = random.randint(120, 200)
            tree_width = int(tree_height // 1.5)

            # Draw larger foreground pine tree silhouette
            for j in range(4):
                size = tree_width - j * 8
                height = tree_height // 4
                y_pos = GROUND_LEVEL - height * (j + 1)
                pygame.draw.polygon(
                    layer5,
                    fg_tree_color,
                    [
                        (tree_x, y_pos - height),
                        (tree_x - size // 2, y_pos),
                        (tree_x + size // 2, y_pos),
                    ],
                )

        # Add dawn mist
        for _ in range(40):
            mist_x = random.randint(0, WIDTH * 2)
            mist_y = random.randint(GROUND_LEVEL - 120, GROUND_LEVEL - 10)
            mist_width = random.randint(100, 300)
            mist_height = random.randint(20, 70)

            mist_surface = pygame.Surface((mist_width, mist_height), pygame.SRCALPHA)
            for y in range(mist_height):
                alpha = 70 - int(abs(y - mist_height // 2) * 120 / mist_height)
                pygame.draw.line(
                    mist_surface,
                    (220, 200, 230, alpha),  # Light pink-white mist
                    (0, y),
                    (mist_width, y),
                )

            layer5.blit(mist_surface, (mist_x, mist_y))

        # Add pink clouds
        self._add_clouds_to_layer(
            layer2, 4, light_color=(230, 190, 210), dark_color=(180, 150, 180)
        )
        self._add_clouds_to_layer(
            layer3, 6, light_color=(200, 180, 210), dark_color=(150, 130, 170)
        )

        # Add all layers in order of depth
        self.layers = [layer1, layer2, layer3, layer4, layer5]

    def update(self):
        """Update the positions of the background layers."""
        for i in range(len(self.layers)):
            self.scroll_positions[i] -= self.scroll_speeds[i]
            # Wrap around when needed
            if self.scroll_positions[i] <= -self.layers[i].get_width():
                self.scroll_positions[i] = 0

    def draw(self, surface):
        """Draw the background layers with parallax effect."""
        for i, layer in enumerate(self.layers):
            # Draw the layer twice to create seamless scrolling
            surface.blit(layer, (int(self.scroll_positions[i]), 0))
            surface.blit(layer, (int(self.scroll_positions[i]) + layer.get_width(), 0))

    def _add_clouds_to_layer(self, layer, cloud_count, light_color, dark_color):
        """Add clouds to a background layer"""
        for _ in range(cloud_count):
            cloud_x = random.randint(0, WIDTH * 2)
            cloud_y = random.randint(50, GROUND_LEVEL - 250)
            cloud_width = random.randint(80, 200)
            cloud_height = random.randint(30, 70)

            # Draw main cloud shape
            for i in range(3):
                ellipse_width = random.randint(cloud_width // 2, cloud_width)
                ellipse_height = random.randint(cloud_height // 2, cloud_height)
                ellipse_x = cloud_x + random.randint(
                    -cloud_width // 4, cloud_width // 4
                )
                ellipse_y = cloud_y + random.randint(
                    -cloud_height // 4, cloud_height // 4
                )

                # Choose between light and dark parts of the cloud
                cloud_color = light_color if random.random() > 0.4 else dark_color

                pygame.draw.ellipse(
                    layer,
                    cloud_color,
                    (ellipse_x, ellipse_y, ellipse_width, ellipse_height),
                )

    def create_blue_background_layers(self):
        """Create default blue-themed background layers if files aren't found."""
        # Layer 1 - Deep blue sky gradient with stars
        layer1 = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
        for y in range(HEIGHT):
            # Create a blue gradient from deep blue to lighter blue
            ratio = y / HEIGHT
            r = int(30 + ratio * 60)  # Small amount of red - darker at top
            g = int(80 + ratio * 100)  # Medium amount of green - darker at top
            b = int(180 - ratio * 60)  # Lots of blue - lighter at top
            pygame.draw.line(layer1, (r, g, b), (0, y), (WIDTH * 2, y))

        # Add stars/small white dots to the sky
        for _ in range(240):  # Double the stars for wider background
            star_x = random.randint(0, WIDTH * 2)
            star_y = random.randint(0, int(HEIGHT * 0.7))  # Stars in upper 70% of sky
            star_size = random.randint(1, 3)
            # Bluish white stars
            pygame.draw.circle(
                layer1,
                (200, 220, 255),
                (star_x, star_y),
                star_size,
            )

        # Layer 2 - Distant mountains (dark blue)
        layer2 = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
        mountain_color = (40, 60, 120)  # Dark blue distant mountains

        for i in range(10):  # Draw more mountains for wider layer
            mountain_width = random.randint(200, 350)
            mountain_height = random.randint(100, 180)
            mountain_x = random.randint(0, WIDTH * 2)

            # Draw mountain with slight texture
            pygame.draw.polygon(
                layer2,
                mountain_color,
                [
                    (mountain_x - mountain_width // 2, GROUND_LEVEL),
                    (mountain_x, GROUND_LEVEL - mountain_height),
                    (mountain_x + mountain_width // 2, GROUND_LEVEL),
                ],
            )

            # Add slight highlights to mountain peaks
            highlight_color = (50, 70, 140)  # Slightly lighter blue
            pygame.draw.polygon(
                layer2,
                highlight_color,
                [
                    (
                        mountain_x - mountain_width // 4,
                        GROUND_LEVEL - mountain_height // 2,
                    ),
                    (mountain_x, GROUND_LEVEL - mountain_height),
                    (
                        mountain_x + mountain_width // 4,
                        GROUND_LEVEL - mountain_height // 2,
                    ),
                ],
            )

        # Layer 3 - Middle mountains (medium blue)
        layer3 = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
        mid_mountain_color = (50, 80, 150)  # Medium blue mountains

        for i in range(14):  # Draw more mountains for wider layer
            mountain_width = random.randint(150, 300)
            mountain_height = random.randint(80, 150)
            mountain_x = random.randint(0, WIDTH * 2)

            # Draw mountain
            pygame.draw.polygon(
                layer3,
                mid_mountain_color,
                [
                    (mountain_x - mountain_width // 2, GROUND_LEVEL),
                    (mountain_x, GROUND_LEVEL - mountain_height),
                    (mountain_x + mountain_width // 2, GROUND_LEVEL),
                ],
            )

            # Add slight texture to mountains
            for j in range(3):
                texture_x = mountain_x + random.randint(
                    -mountain_width // 3, mountain_width // 3
                )
                texture_y = GROUND_LEVEL - random.randint(10, mountain_height - 10)
                texture_size = random.randint(5, 15)
                texture_color = (55, 85, 160)  # Slightly lighter blue

                pygame.draw.circle(
                    layer3,
                    texture_color,
                    (texture_x, texture_y),
                    texture_size,
                )

        # Layer 4 - Forest silhouette (navy blue)
        layer4 = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
        tree_color = (20, 40, 100)  # Navy blue silhouette

        # Draw tree line
        for i in range(80):  # Draw more trees for wider layer
            tree_x = i * (WIDTH * 2 // 40)
            tree_height = random.randint(70, 130)
            tree_width = int(tree_height // 2)  # Convert to int explicitly

            # Draw pine tree silhouette
            for j in range(3):
                size = tree_width - j * 5
                height = tree_height // 3
                y_pos = GROUND_LEVEL - height * (j + 1)
                pygame.draw.polygon(
                    layer4,
                    tree_color,
                    [
                        (tree_x, y_pos - height),
                        (tree_x - size // 2, y_pos),
                        (tree_x + size // 2, y_pos),
                    ],
                )

        # Layer 5 - Foreground trees (dark navy)
        layer5 = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
        fg_tree_color = (10, 20, 60)  # Dark navy blue

        for i in range(30):  # Draw more trees for wider layer
            tree_x = random.randint(0, WIDTH * 2)
            tree_height = random.randint(120, 200)
            tree_width = int(tree_height // 1.5)  # Convert to int explicitly

            # Draw larger foreground pine tree silhouette
            for j in range(4):
                size = tree_width - j * 8
                height = tree_height // 4
                y_pos = GROUND_LEVEL - height * (j + 1)
                pygame.draw.polygon(
                    layer5,
                    fg_tree_color,
                    [
                        (tree_x, y_pos - height),
                        (tree_x - size // 2, y_pos),
                        (tree_x + size // 2, y_pos),
                    ],
                )

            # Add slight variance to foreground trees
            branch_color = (15, 25, 70)  # Slightly lighter
            for _ in range(3):
                branch_x = tree_x + random.randint(-tree_width // 3, tree_width // 3)
                branch_y = GROUND_LEVEL - random.randint(20, tree_height - 20)
                branch_size = random.randint(10, 25)

                # Draw small branch
                pygame.draw.circle(
                    layer5,
                    branch_color,
                    (branch_x, branch_y),
                    branch_size,
                )

        # Add some misty effect in the foreground
        for _ in range(60):
            mist_x = random.randint(0, WIDTH * 2)
            mist_y = random.randint(GROUND_LEVEL - 100, GROUND_LEVEL - 10)
            mist_width = random.randint(100, 300)
            mist_height = random.randint(20, 60)

            mist_surface = pygame.Surface((mist_width, mist_height), pygame.SRCALPHA)
            for y in range(mist_height):
                alpha = 80 - int(abs(y - mist_height // 2) * 120 / mist_height)
                pygame.draw.line(
                    mist_surface,
                    (180, 200, 255, alpha),
                    (0, y),
                    (mist_width, y),
                )

            layer5.blit(mist_surface, (mist_x, mist_y))

        # Add clouds to layers 2 and 3
        self._add_clouds_to_layer(
            layer2, 5, light_color=(70, 90, 160), dark_color=(40, 60, 140)
        )
        self._add_clouds_to_layer(
            layer3, 7, light_color=(80, 100, 180), dark_color=(50, 70, 160)
        )

        # Add all layers in order of depth
        self.layers = [layer1, layer2, layer3, layer4, layer5]


def load_animation_frames(animation_name, cat_type="cat"):
    """Load animation frames from the graphics directory.

    Args:
        animation_name: The name of the animation to load (e.g., 'Idle', 'Run')
        cat_type: The cat sprite variant to use ('cat' or 'cat2')
    """
    frames = []
    path_pattern = f"assets/graphics/{cat_type}/{animation_name} (*).png"
    matching_files = sorted(
        glob.glob(path_pattern), key=lambda x: int(x.split("(")[1].split(")")[0])
    )

    if not matching_files:
        logger.warning(
            f"No animation frames found for {animation_name} in {cat_type}. Using fallback."
        )
        # Create a simple colored square as fallback
        fallback = pygame.Surface((50, 50), pygame.SRCALPHA)
        if animation_name == "Dead":
            pygame.draw.rect(fallback, (255, 0, 0), fallback.get_rect())  # Red for dead
        else:
            pygame.draw.rect(
                fallback, (255, 165, 0), fallback.get_rect()
            )  # Orange for others
        return [fallback]

    try:
        for frame_path in matching_files:
            try:
                frame = pygame.image.load(frame_path).convert_alpha()
                # Scale the image to a suitable size for the game
                frame = pygame.transform.scale(frame, (100, 100))
                frames.append(frame)
            except pygame.error as e:
                logger.error(f"Error loading frame {frame_path}: {e}")
                # Skip problematic frames
                continue
    except Exception as e:
        logger.error(f"Unexpected error loading {animation_name} frames: {e}")

    # If we couldn't load any frames, create a simple colored rectangle
    if not frames:
        fallback = pygame.Surface((50, 50), pygame.SRCALPHA)
        pygame.draw.rect(fallback, (255, 165, 0), fallback.get_rect())
        frames = [fallback]

    return frames


# Load obstacle images
def load_obstacle_images():
    """Create procedurally generated PIXEL ART obstacles for the game."""
    obstacles = {
        "stone": [],
        "cactus": [],
        "bush": [],
        "balloon": None,
        "glow_balloon": None,  # Add entry for the new balloon
        "glowing_obstacle": None,  # Add entry for our new glowing obstacle
    }

    # Create several stone variants
    for _ in range(3):
        stone = create_pixel_stone(random_variant=True)
        obstacles["stone"].append(stone)

    # Create several cactus variants
    for _ in range(2):
        cactus = create_pixel_cactus(random_variant=True)
        obstacles["cactus"].append(cactus)

    # Create several bush variants
    for _ in range(3):
        bush = create_pixel_bush(random_variant=True)
        obstacles["bush"].append(bush)

    # Create balloon (maybe variants later if needed)
    obstacles["balloon"] = create_pixel_balloon(random_variant=True)

    # Create the glowing balloon
    obstacles["glow_balloon"] = create_pixel_glow_balloon()

    # Create the glowing obstacle
    obstacles["glowing_obstacle"] = create_pixel_glowing_obstacle()

    logger.info("Pixel art obstacle graphics generated successfully")
    return obstacles


def _create_pixel_rect(surface, x, y, scale, color):
    """Helper function to draw a pixel rectangle at the specified position."""
    pygame.draw.rect(surface, color, (x, y, scale, scale))


def create_pixel_stone(random_variant=False):
    """Creates a pixel art stone obstacle."""
    width, height = 52, 52  # Slightly larger base size
    surface = pygame.Surface((width, height), pygame.SRCALPHA)

    # Color palettes
    palettes = [
        # Gray stone
        [(90, 90, 90), (120, 120, 120), (150, 150, 150), (60, 60, 60)],
        # Brown stone
        [(115, 90, 60), (145, 115, 80), (175, 140, 100), (85, 70, 45)],
        # Mossy stone
        [(80, 100, 70), (110, 130, 90), (140, 160, 110), (60, 80, 55)],
    ]

    palette = random.choice(palettes) if random_variant else palettes[0]
    base, mid, light, dark = palette

    # Basic stone shape (can randomize shape more if needed)
    shape = [
        "  xxxxxx  ",
        " xxxxxxxx ",
        "xxxxxxxxxx",
        "xxxxxxxxxx",
        "xxxxxxxxxx",
        "xxxxxxxxxx",
        " xxxxxxxx ",
        "  xxxxxx  ",
    ]

    scale = 6  # Size of each 'pixel'

    for y, row in enumerate(shape):
        for x, char in enumerate(row):
            if char == "x":
                rect_x = x * scale
                rect_y = y * scale

                # Basic shading
                color = mid
                if y < 2 or x < 2:
                    color = light
                if y > 5 or x > len(row) - 3:
                    color = base

                # Add darker cracks/details
                if random.random() < 0.1:
                    color = dark

                _create_pixel_rect(surface, rect_x, rect_y, scale, color)

    return surface


def create_pixel_cactus(random_variant=False):
    """Creates a pixel art cactus obstacle."""
    width, height = 40, 80  # Tall and thin base
    surface = pygame.Surface((width, height), pygame.SRCALPHA)

    # Color palettes
    palettes = [
        # Standard green
        [
            (40, 100, 30),
            (60, 140, 50),
            (80, 180, 70),
            (200, 200, 180),
        ],  # Base, Mid, Light, Spine
        # Bluish green
        [(30, 90, 80), (50, 120, 110), (70, 150, 140), (210, 210, 190)],
    ]
    palette = random.choice(palettes) if random_variant else palettes[0]
    base, mid, light, spine_color = palette

    scale = 6

    # Main stalk
    stalk_width = 3
    for y in range(height // scale):
        for x in range(stalk_width):
            px = (width // scale // 2 - stalk_width // 2 + x) * scale
            py = y * scale

            # Shading
            color = mid
            if x == 0:
                color = base
            elif x == stalk_width - 1:
                color = light

            _create_pixel_rect(surface, px, py, scale, color)

    # Arms (optional randomization)
    arm_height1 = random.randint(3, 5) if random_variant else 4
    arm_len1 = random.randint(2, 3) if random_variant else 2

    # Left arm
    for i in range(arm_len1):
        px = (width // scale // 2 - stalk_width // 2 - 1 - i) * scale
        py = arm_height1 * scale
        _create_pixel_rect(surface, px, py, scale, base)  # Darker side

    for i in range(arm_len1 // 2 + 1):
        px = (width // scale // 2 - stalk_width // 2 - arm_len1) * scale
        py = (arm_height1 + i + 1) * scale
        _create_pixel_rect(surface, px, py, scale, mid)  # Upward part

    # Right arm
    arm_height2 = random.randint(5, 7) if random_variant else 6
    arm_len2 = random.randint(2, 3) if random_variant else 2

    for i in range(arm_len2):
        px = (width // scale // 2 + stalk_width // 2 + i) * scale
        py = arm_height2 * scale
        _create_pixel_rect(surface, px, py, scale, light)  # Lighter side

    for i in range(arm_len2 // 2 + 1):
        px = (width // scale // 2 + stalk_width // 2 + arm_len2 - 1) * scale
        py = (arm_height2 + i + 1) * scale
        _create_pixel_rect(surface, px, py, scale, mid)  # Upward part

    # Spines
    for y in range(1, height // scale, 2):
        # Main stalk spines
        px1 = (width // scale // 2 - stalk_width // 2 - 1) * scale
        px2 = (width // scale // 2 + stalk_width // 2) * scale
        py = y * scale

        pygame.draw.rect(surface, spine_color, (px1, py, 2, 2))
        pygame.draw.rect(surface, spine_color, (px2, py, 2, 2))

        # Arm spines
        if y > arm_height1 and y < arm_height1 + arm_len1 // 2 + 2:
            px = (width // scale // 2 - stalk_width // 2 - arm_len1 - 1) * scale
            pygame.draw.rect(surface, spine_color, (px, py, 2, 2))

        if y > arm_height2 and y < arm_height2 + arm_len2 // 2 + 2:
            px = (width // scale // 2 + stalk_width // 2 + arm_len2) * scale
            pygame.draw.rect(surface, spine_color, (px, py, 2, 2))

    return surface


def create_pixel_bush(random_variant=False):
    """Creates a pixel art bush obstacle."""
    width, height = 66, 42  # Increased size: low and wide base
    surface = pygame.Surface((width, height), pygame.SRCALPHA)

    # Color palettes
    palettes = [
        # Green bush
        [
            (30, 80, 25),
            (50, 110, 40),
            (70, 140, 60),
            (100, 170, 80),
        ],  # Dark, Base, Mid, Light
        # Autumn bush
        [(100, 70, 20), (130, 90, 30), (160, 110, 40), (190, 140, 60)],
        # Berry bush
        [
            (30, 80, 25),
            (50, 110, 40),
            (70, 140, 60),
            (180, 40, 40),
        ],  # Dark, Base, Mid, BerryColor
    ]
    palette = random.choice(palettes) if random_variant else palettes[0]
    dark, base, mid, detail_color = palette

    scale = 6

    # Basic shape - wider design
    shape = [
        "   xxxxxx   ",
        "  xxxxxxxx  ",
        " xxxxxxxxxx ",
        "xxxxxxxxxxxx",
        "xxxxxxxxxxxx",
        "xxxxxxxxxxxx",
        " xxxxxxxxxx ",
    ]

    offset_x = (width - len(shape[0]) * scale) // 2

    for y, row in enumerate(shape):
        for x, char in enumerate(row):
            if char == "x":
                rect_x = offset_x + x * scale
                rect_y = y * scale

                # Basic shading / texture
                color = base
                if y < 2 or x < 2 or x > len(row) - 3:
                    color = mid
                if y > 4 and random.random() < 0.3:
                    color = dark

                # Add detail color (light green or berries)
                if random.random() < 0.15:
                    pygame.draw.rect(
                        surface,
                        detail_color,
                        (
                            rect_x + scale // 3,
                            rect_y + scale // 3,
                            scale // 2,
                            scale // 2,
                        ),
                    )

                pygame.draw.rect(surface, color, (rect_x, rect_y, scale, scale))

    # Add a few darker pixels at the bottom for grounding
    for x in range(len(shape[-1])):
        if shape[-1][x] == "x":
            rect_x = offset_x + x * scale
            rect_y = (len(shape) - 1) * scale
            if random.random() < 0.5:
                pygame.draw.rect(surface, dark, (rect_x, rect_y, scale, scale))

    return surface


def create_pixel_balloon(random_variant=False):
    """Creates a pixel art balloon obstacle."""
    width, height = 48, 84  # Slightly taller balloon (shape + string)
    surface = pygame.Surface((width, height), pygame.SRCALPHA)

    # Bright color palettes
    palettes = [
        # Red
        [
            (220, 40, 40),
            (255, 80, 80),
            (255, 255, 255),
            (80, 80, 80),
        ],  # Base, Highlight, Shine, String
        # Blue
        [(40, 80, 220), (80, 120, 255), (255, 255, 255), (80, 80, 80)],
        # Yellow
        [(230, 210, 50), (255, 240, 90), (255, 255, 255), (80, 80, 80)],
        # Green
        [(40, 180, 50), (80, 220, 90), (255, 255, 255), (80, 80, 80)],
        # Purple (new option)
        [(160, 40, 190), (200, 100, 230), (255, 255, 255), (80, 80, 80)],
    ]
    palette = random.choice(palettes) if random_variant else palettes[0]
    base, highlight, shine, string_color = palette

    scale = 6
    balloon_height = 9  # in pixels - slightly taller
    balloon_width = 7  # in pixels - slightly wider
    center_x = width // 2

    # Balloon shape (oval)
    for y in range(balloon_height):
        # Calculate width at this y level (simple oval approximation)
        dy = abs(y - balloon_height / 2 + 0.5)
        w = int(balloon_width * math.sqrt(max(0, 1 - (dy / (balloon_height / 2)) ** 2)))

        for x in range(w):
            px = center_x - (w // 2 * scale) + x * scale
            py = y * scale
            rect = pygame.Rect(px, py, scale, scale)

            # Shading
            color = base
            if y < balloon_height // 3 or (x < w // 3 and y < balloon_height * 0.7):
                color = highlight

            pygame.draw.rect(surface, color, rect)

    # Shine spots - slightly larger and more defined
    pygame.draw.rect(surface, shine, (center_x - scale * 1.5, scale, scale, scale))
    pygame.draw.rect(surface, shine, (center_x - scale * 0.5, scale * 2, scale, scale))
    pygame.draw.rect(surface, shine, (center_x - scale, scale * 1.5, scale, scale))

    # Add balloon knot at bottom
    knot_y = balloon_height * scale
    pygame.draw.rect(surface, base, (center_x - scale // 2, knot_y, scale, scale))

    # String
    string_start_x = center_x - scale // 2
    string_start_y = (balloon_height + 1) * scale
    string_end_y = height - scale

    # Draw jagged string line
    current_x = string_start_x
    for y in range(string_start_y, string_end_y, scale // 2):
        pygame.draw.rect(surface, string_color, (current_x, y, 2, scale // 2))
        current_x += random.randint(-1, 1) * (scale // 3)
        current_x = max(string_start_x - scale, min(string_start_x + scale, current_x))

    return surface


def create_pixel_glow_balloon(random_variant=False):
    """Creates a glowing balloon power-up obstacle that changes colors."""
    # Start with a regular balloon
    balloon = create_pixel_balloon(random_variant=True)

    # The color-changing functionality will be handled in update method
    # Return the normal balloon without the glow sphere
    return balloon


def create_pixel_glowing_obstacle(random_variant=False):
    """Creates a glowing obstacle that changes color and gives a shot when collected."""
    width, height = 50, 50  # Square shape
    surface = pygame.Surface((width, height), pygame.SRCALPHA)

    # Base color will be modified in the update method
    # Just create the basic shape here
    center = (width // 2, height // 2)
    outer_radius = width // 2 - 2
    inner_radius = outer_radius // 2

    # Create a star shape
    star_points = []
    for i in range(10):  # 5 points with 10 vertices
        angle = math.pi / 2 + i * math.pi * 2 / 10
        radius = outer_radius if i % 2 == 0 else inner_radius
        x_point = center[0] + radius * math.cos(angle)
        y_point = center[1] - radius * math.sin(angle)
        star_points.append((x_point, y_point))

    # Initial color (will change during gameplay)
    color = (255, 255, 0)  # Yellow
    pygame.draw.polygon(surface, color, star_points)

    # Add a glow effect
    for r in range(1, 4):
        glow_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.polygon(glow_surface, (*color, 100 - r * 25), star_points)
        # Scale the glow slightly larger
        scale_factor = 1.0 + (r * 0.1)
        scaled_size = (int(width * scale_factor), int(height * scale_factor))
        scaled_surface = pygame.transform.scale(glow_surface, scaled_size)
        # Center the scaled surface
        pos = ((width - scaled_size[0]) // 2, (height - scaled_size[1]) // 2)
        surface.blit(scaled_surface, pos, special_flags=pygame.BLEND_ALPHA_SDL2)

    return surface


# Global variable to store obstacle images
OBSTACLE_IMAGES = load_obstacle_images()


class Particle:
    """A simple particle effect for visual flair."""

    def __init__(self, x, y, color, speed_x, speed_y, size, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.size = size
        self.lifetime = lifetime
        self.age = 0

    def update(self):
        """Update particle position and age."""
        self.x += self.speed_x
        self.y += self.speed_y
        self.speed_y += 0.1  # Gravity
        self.age += 1
        # Gradually reduce size as particle ages
        if self.age > self.lifetime * 0.7:
            self.size = max(1, self.size - 0.5)

    def draw(self, surface):
        """Draw the particle as a circle."""
        alpha = int(255 * (1 - self.age / self.lifetime))
        color_with_alpha = (*self.color, alpha)

        # Create a surface with per-pixel alpha
        particle_surface = pygame.Surface(
            (self.size * 2, self.size * 2), pygame.SRCALPHA
        )
        pygame.draw.circle(
            particle_surface, color_with_alpha, (self.size, self.size), self.size
        )
        surface.blit(
            particle_surface, (int(self.x - self.size), int(self.y - self.size))
        )

    def is_dead(self):
        """Check if the particle has expired."""
        return self.age >= self.lifetime


class ParticleSystem:
    """Manages multiple particles for effects."""

    def __init__(self):
        self.particles = []

    def add_particles(
        self, x, y, count, color_range, speed_range, size_range, lifetime_range
    ):
        """Add multiple particles at once with random properties within ranges."""
        for _ in range(count):
            # Calculate random values within ranges
            color = (
                random.randint(*color_range[0]),
                random.randint(*color_range[1]),
                random.randint(*color_range[2]),
            )
            speed_x = random.uniform(*speed_range[0])
            speed_y = random.uniform(*speed_range[1])
            size = random.uniform(*size_range)
            lifetime = random.randint(*lifetime_range)

            # Create and add particle
            self.particles.append(
                Particle(x, y, color, speed_x, speed_y, size, lifetime)
            )

    def add_jump_particles(self, x, y):
        """Add particles for a jump effect."""
        # Dust particles
        self.add_particles(
            x,
            y,
            count=15,
            color_range=[(200, 230), (200, 230), (180, 220)],  # Light brown/tan
            speed_range=[(-2, 2), (-1, -3)],  # Spray upward and sideways
            size_range=(2, 5),
            lifetime_range=(20, 40),
        )

    def add_impact_particles(self, x, y):
        """Add particles for impact/death effect."""
        # Impact particles
        self.add_particles(
            x,
            y,
            count=30,
            color_range=[(200, 255), (50, 150), (50, 100)],  # Orange/red
            speed_range=[(-3, 3), (-5, 1)],  # Explode in all directions
            size_range=(3, 7),
            lifetime_range=(30, 60),
        )

    def update(self):
        """Update all particles and remove dead ones."""
        for particle in self.particles[:]:
            particle.update()
            if particle.is_dead():
                self.particles.remove(particle)

    def draw(self, surface):
        """Draw all active particles."""
        for particle in self.particles:
            particle.draw(surface)


# Cat class
class Cat(pygame.sprite.Sprite):
    """Cat sprite that the player controls."""

    def __init__(self, cat_type="cat"):
        super().__init__()

        # Cat sprite type
        self.cat_type = cat_type

        # Load all animation frames
        self.animations = {}
        try:
            self.animations = {
                "idle": load_animation_frames("Idle", self.cat_type),
                "run": load_animation_frames("Run", self.cat_type),
                "jump": load_animation_frames("Jump", self.cat_type),
                "fall": load_animation_frames("Fall", self.cat_type),
                "dead": load_animation_frames("Dead", self.cat_type),
                "slide": load_animation_frames(
                    "Slide", self.cat_type
                ),  # Add slide animation
            }
            logger.info(f"Cat animations for {self.cat_type} loaded successfully")
        except Exception as e:
            logger.error(f"Error loading cat animations for {self.cat_type}: {e}")
            # Create fallback animations with colored rectangles
            fallback = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.rect(fallback, (255, 0, 0), fallback.get_rect())  # Red
            self.animations = {
                state: [fallback]
                for state in ["idle", "run", "jump", "fall", "dead", "slide"]
            }

        # Set initial animation state
        self.current_animation = "idle"
        self.frame_index = 0
        self.animation_timer = 0

        # Set initial image and rect
        self.image = self.animations[self.current_animation][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.bottomleft = (100, GROUND_LEVEL)

        # Original rect height (for collision detection during sliding)
        self.normal_height = self.rect.height
        self.normal_bottom = self.rect.bottom

        # Physics attributes
        self.velocity_y = 0
        self.on_ground = True
        self.is_dead = False
        self.double_jumps_available = 0  # Counter for double jumps
        self.shots_available = 0  # Counter for available shots

        # Sliding state
        self.is_sliding = False
        self.slide_timer = 0
        self.slide_duration = 45  # Frames to stay in slide (about 0.75 seconds)
        self.slide_cooldown = 0
        self.slide_cooldown_duration = 30  # Frames of cooldown

    def change_cat_type(self, new_cat_type):
        """Change the cat sprite type and reload animations."""
        if self.cat_type == new_cat_type:
            return  # No change needed

        # Save current position and state
        current_pos = self.rect.bottomleft
        current_animation = self.current_animation

        # Update cat type
        self.cat_type = new_cat_type

        # Reload animations
        try:
            self.animations = {
                "idle": load_animation_frames("Idle", self.cat_type),
                "run": load_animation_frames("Run", self.cat_type),
                "jump": load_animation_frames("Jump", self.cat_type),
                "fall": load_animation_frames("Fall", self.cat_type),
                "dead": load_animation_frames("Dead", self.cat_type),
                "slide": load_animation_frames("Slide", self.cat_type),
            }
            logger.info(f"Cat animations changed to {self.cat_type}")
        except Exception as e:
            logger.error(f"Error changing cat animations to {self.cat_type}: {e}")

        # Reset animation state
        self.frame_index = 0
        self.current_animation = current_animation
        self.image = self.animations[self.current_animation][self.frame_index]

        # Restore position
        self.rect = self.image.get_rect()
        self.rect.bottomleft = current_pos

        # Create a sparkle effect when changing cat
        game_instance = Game.get_instance()
        if game_instance:
            game_instance.particle_system.add_particles(
                self.rect.centerx,
                self.rect.centery,
                count=30,
                color_range=[(200, 255), (200, 255), (200, 255)],  # White/gold sparkle
                speed_range=[(-2, 2), (-2, 2)],
                size_range=(3, 7),
                lifetime_range=(30, 50),
            )
            # Play sound effect
            game_instance.play_sound("powerup")

    def slide(self):
        """Make the cat slide if on the ground and not already sliding."""
        if (
            self.is_dead
            or self.is_sliding
            or not self.on_ground
            or self.slide_cooldown > 0
        ):
            return

        game_instance = Game.get_instance()

        # Start sliding
        self.is_sliding = True
        self.slide_timer = 0
        self.current_animation = "slide"
        self.frame_index = 0

        # Store original height
        self.normal_height = self.rect.height
        self.normal_bottom = self.rect.bottom

        # Adjust hitbox height to be lower when sliding
        self.rect.height = self.normal_height * 0.6
        self.rect.bottom = self.normal_bottom  # Keep bottom position the same

        # Create slide dust effect
        if game_instance:
            game_instance.particle_system.add_particles(
                self.rect.right,
                self.rect.bottom,
                count=8,
                color_range=[(100, 120), (100, 120), (100, 120)],  # Gray dust
                speed_range=[(-1, -3), (-0.5, 0.5)],
                size_range=(2, 4),
                lifetime_range=(10, 20),
            )
            game_instance.play_sound("slide")  # Play slide sound

    def die(self):
        """Make the cat die."""
        if not self.is_dead:
            self.is_dead = True
            self.current_animation = "dead"
            self.frame_index = 0
            self.velocity_y = JUMP_FORCE * 0.5  # Small bounce on death

            # Reset sliding state
            self.is_sliding = False
            self.rect.height = self.normal_height

    def update_animation(self):
        """Update the cat's animation frame."""
        self.animation_timer += 1
        if self.animation_timer >= ANIMATION_SPEED:
            self.animation_timer = 0
            frames = self.animations[self.current_animation]
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.image = frames[self.frame_index]

    def update(self):
        """Update the cat's position and animation."""
        if self.is_dead:
            self.velocity_y += GRAVITY
            self.rect.y += self.velocity_y
            self.update_animation()
            return

        # Handle sliding
        if self.is_sliding:
            self.slide_timer += 1
            if self.slide_timer >= self.slide_duration:
                # End slide
                self.is_sliding = False
                self.slide_cooldown = self.slide_cooldown_duration
                self.rect.height = self.normal_height

        # Update slide cooldown
        if self.slide_cooldown > 0:
            self.slide_cooldown -= 1

        # Apply gravity if not on ground
        if not self.on_ground:
            self.velocity_y += GRAVITY

            # Set falling animation if velocity is positive and not dead
            if self.velocity_y > 0 and self.current_animation != "fall":
                self.current_animation = "fall"
                self.frame_index = 0

        # Update position
        self.rect.y += self.velocity_y

        # Check for ground collision
        if self.rect.bottom >= GROUND_LEVEL:
            self.rect.bottom = GROUND_LEVEL
            self.velocity_y = 0
            self.on_ground = True

            # Set animation state if landing and not sliding or dead
            if not self.is_sliding and self.current_animation not in ["idle", "run"]:
                self.current_animation = "run"
                self.frame_index = 0

        # Update animation
        self.update_animation()

    def check_collisions(self):
        """Check for collisions with obstacles."""
        if self.is_dead:
            return False

        game = Game.get_instance()
        if not game:
            return False

        for obstacle in game.obstacles:
            if not self.rect.colliderect(obstacle.rect):
                continue

            # Special handling for glowing obstacles - give a shot and remove obstacle
            if obstacle.type == "glowing_obstacle":
                self.shots_available += 1
                # Add sparkle particles
                game.particle_system.add_particles(
                    x=obstacle.rect.centerx,
                    y=obstacle.rect.centery,
                    count=25,
                    color_range=[
                        (220, 255),
                        (220, 255),
                        (100, 200),
                    ],  # Colorful sparkles
                    speed_range=[(-3, 3), (-3, 3)],
                    size_range=(3, 8),
                    lifetime_range=(20, 40),
                )
                # Show notification popup
                game.score_popups.append(
                    {
                        "text": "+1 SHOT!",
                        "pos": (self.rect.centerx, self.rect.y - 30),
                        "lifetime": 60,
                        "color": YELLOW,
                        "size": 28,
                    }
                )
                game.play_sound("powerup")
                obstacle.kill()
                return False

            # Check if this is a balloon obstacle that can be slid under
            if hasattr(obstacle, "requires_slide") and obstacle.requires_slide:
                # If we're sliding, we can pass under it
                if self.is_sliding:
                    continue

            # Check if this is a glow balloon (power-up)
            if obstacle.type == "glow_balloon":
                self.double_jumps_available += 1
                game.particle_system.add_particles(
                    x=obstacle.rect.centerx,
                    y=obstacle.rect.centery,
                    count=25,
                    color_range=[(255, 255), (200, 255), (0, 100)],  # Bright yellow
                    speed_range=[(-2, 2), (-2, 2)],
                    size_range=(4, 8),
                    lifetime_range=(40, 70),
                )
                game.play_sound("powerup")
                obstacle.kill()  # Remove the balloon power-up
                return False

            # Collision occurred with a harmful obstacle
            self.die()
            game.play_sound("hit")
            game.game_over = True
            return True

        return False

    def jump(self):
        """Make the cat jump if it's on the ground or has a double jump available."""
        if self.is_dead:
            return

        game_instance = Game.get_instance()

        # Standard jump from ground
        if self.on_ground:
            if game_instance:
                game_instance.particle_system.add_jump_particles(
                    self.rect.centerx, self.rect.bottom
                )
                game_instance.play_sound("jump")  # Play regular jump sound

            self.velocity_y = JUMP_FORCE
            self.on_ground = False
            self.current_animation = "jump"
            self.frame_index = 0

            # Cancel slide if jumping
            self.is_sliding = False
            self.rect.height = self.normal_height
            self.rect.bottom = self.normal_bottom

        # Double jump from air
        elif self.double_jumps_available > 0:
            self.double_jumps_available -= 1
            self.velocity_y = JUMP_FORCE * 0.9  # Make double jump slightly weaker
            self.current_animation = "jump"  # Restart jump animation
            self.frame_index = 0
            if game_instance:
                # Add different particles/sound for double jump
                game_instance.particle_system.add_particles(
                    self.rect.centerx,
                    self.rect.centery,
                    count=10,
                    color_range=[
                        (220, 255),
                        (180, 230),
                        (50, 150),
                    ],  # Yellow/Gold particles
                    speed_range=[(-1.5, 1.5), (-1, -2.5)],
                    size_range=(3, 6),
                    lifetime_range=(15, 30),
                )
                game_instance.play_sound("double_jump")  # Play double jump sound

    def shoot(self):
        """Make the cat shoot a bullet if shots are available."""
        if self.is_dead or self.shots_available <= 0:
            return False

        # Consume a shot and return True to indicate success
        self.shots_available -= 1
        return True


# Obstacle class
class Obstacle(pygame.sprite.Sprite):
    """Obstacle sprites that the cat must avoid."""

    # Class variable to track the last few obstacle types to avoid repetition
    _last_obstacles: List[str] = []  # Add type annotation
    _max_history = 3  # Remember the last 3 obstacles

    # Predefined color palette for color-changing obstacles
    COLOR_PALETTE = [
        (255, 0, 0),  # Red
        (255, 165, 0),  # Orange
        (255, 255, 0),  # Yellow
        (0, 255, 0),  # Green
        (0, 0, 255),  # Blue
        (128, 0, 128),  # Purple
    ]

    # Default color change speed (frames between changes)
    DEFAULT_COLOR_CHANGE_SPEED = 3

    @classmethod
    def reset_history(cls):
        """Reset obstacle history to prevent exploits."""
        cls._last_obstacles = []

    def __init__(self):
        super().__init__()

        # Define obstacle types with their weights for random selection
        obstacle_types = [
            {"type": "stone", "weight": 28},
            {"type": "cactus", "weight": 23},
            {"type": "bush", "weight": 18},
            {"type": "balloon", "weight": 15},
            {"type": "low_balloon", "weight": 10},  # Low-flying balloon type
            {
                "type": "glow_balloon",
                "weight": 15,
            },  # Increased weight for easier testing
            {"type": "glowing_obstacle", "weight": 6},  # Glowing star obstacle
        ]

        # Choose obstacle type based on weights, avoiding recent types
        self._choose_obstacle_type(obstacle_types)

        # Initialize obstacle properties
        self._initialize_obstacle()

        # Position the obstacle
        self._position_obstacle()

    def _choose_obstacle_type(self, obstacle_types):
        """Choose obstacle type based on weights, avoiding recent types."""
        # Extract weights for random selection
        weights = [item["weight"] for item in obstacle_types]

        # Adjust weights to avoid repeating recent obstacles
        adjusted_weights = weights.copy()
        for i, item in enumerate(obstacle_types):
            if item["type"] in Obstacle._last_obstacles:
                # Reduce weight of recently seen obstacles
                adjusted_weights[i] = max(1, weights[i] // 2)

        # Choose obstacle type based on adjusted weights
        self.type = random.choices(
            [item["type"] for item in obstacle_types], weights=adjusted_weights
        )[0]

        # Update the history of obstacle types
        Obstacle._last_obstacles.append(self.type)
        if len(Obstacle._last_obstacles) > Obstacle._max_history:
            Obstacle._last_obstacles.pop(0)  # Remove oldest obstacle type

    def _initialize_obstacle(self):
        """Initialize the obstacle based on its type."""
        # Set up the obstacle based on type
        if self.type == "stone":
            self._setup_stone_obstacle()
        elif self.type == "cactus":
            self._setup_cactus_obstacle()
        elif self.type == "bush":
            self._setup_bush_obstacle()
        elif self.type == "balloon":
            self._setup_balloon_obstacle()
        elif self.type == "low_balloon":
            self._setup_low_balloon_obstacle()
        elif self.type == "glow_balloon":
            self._setup_glow_balloon_obstacle()
        elif self.type == "glowing_obstacle":
            self._setup_glowing_obstacle()

        # Set common properties
        self.speed = OBSTACLE_SPEED
        self.already_passed = False

    def _position_obstacle(self):
        """Position the obstacle based on its type."""
        # Position the obstacle off-screen to the right
        self.rect.x = SCREEN_SIZE[0]

        # Set vertical position based on type
        if self.type not in [
            "balloon",
            "low_balloon",
            "glow_balloon",
            "glowing_obstacle",
        ]:
            # Ground-based obstacles
            self.rect.bottom = GROUND_LEVEL
        elif self.type == "balloon":
            # Standard balloon is closer to the ground
            self.rect.y = GROUND_LEVEL - self.rect.height - random.randint(100, 180)
        elif self.type == "low_balloon":
            # Low balloon requires sliding under it - keep very low
            self.rect.y = GROUND_LEVEL - self.rect.height - random.randint(50, 90)
        elif self.type == "glow_balloon":
            # Glow balloon is in jumping range - slightly higher than regular balloons
            self.rect.y = GROUND_LEVEL - self.rect.height - random.randint(120, 160)
        elif self.type == "glowing_obstacle":
            # Glowing obstacle in middle range - can be jumped over or slid under
            self.rect.y = GROUND_LEVEL - self.rect.height - random.randint(90, 130)

    def _setup_low_balloon_obstacle(self):
        """Set up a low-flying balloon obstacle that requires sliding under."""
        # Use the same balloon image but position it lower
        self.image = create_pixel_balloon(random_variant=True)
        self.rect = self.image.get_rect()

        # Tag this as a slide-under obstacle
        self.requires_slide = True

    def _setup_stone_obstacle(self):
        """Setup a stone obstacle."""
        if "stone" in OBSTACLE_IMAGES and OBSTACLE_IMAGES["stone"]:
            variant = random.randint(0, len(OBSTACLE_IMAGES["stone"]) - 1)
            self.image = OBSTACLE_IMAGES["stone"][variant].copy()
        else:
            self.image = create_pixel_stone()

        scale_factor = random.uniform(0.9, 1.3)  # Larger stones
        target_width = int(52 * scale_factor)
        target_height = int(52 * scale_factor)
        self.image = pygame.transform.scale(self.image, (target_width, target_height))

        self.rect = self.image.get_rect()
        self.rect.bottomleft = (WIDTH, GROUND_LEVEL)

    def _setup_cactus_obstacle(self):
        """Setup a cactus obstacle."""
        if "cactus" in OBSTACLE_IMAGES and OBSTACLE_IMAGES["cactus"]:
            variant = random.randint(0, len(OBSTACLE_IMAGES["cactus"]) - 1)
            self.image = OBSTACLE_IMAGES["cactus"][variant].copy()
        else:
            self.image = create_pixel_cactus()

        scale_factor = random.uniform(0.9, 1.3)  # Larger cacti
        target_width = int(40 * scale_factor)
        target_height = int(80 * scale_factor)
        self.image = pygame.transform.scale(self.image, (target_width, target_height))

        self.rect = self.image.get_rect()
        self.rect.bottomleft = (WIDTH, GROUND_LEVEL)

    def _setup_bush_obstacle(self):
        """Setup a bush obstacle."""
        if "bush" in OBSTACLE_IMAGES and OBSTACLE_IMAGES["bush"]:
            variant = random.randint(0, len(OBSTACLE_IMAGES["bush"]) - 1)
            self.image = OBSTACLE_IMAGES["bush"][variant].copy()
        else:
            self.image = create_pixel_bush()

        scale_factor = random.uniform(0.9, 1.3)  # Larger bushes
        target_width = int(66 * scale_factor)
        target_height = int(42 * scale_factor)
        self.image = pygame.transform.scale(self.image, (target_width, target_height))

        self.rect = self.image.get_rect()
        self.rect.bottomleft = (WIDTH, GROUND_LEVEL)

    def _setup_balloon_obstacle(self):
        """Setup a balloon obstacle."""
        if "balloon" in OBSTACLE_IMAGES and OBSTACLE_IMAGES["balloon"]:
            self.image = OBSTACLE_IMAGES["balloon"].copy()
        else:
            self.image = create_pixel_balloon()

        scale_factor = random.uniform(0.9, 1.3)  # Slightly larger balloons
        target_width = int(48 * scale_factor)
        target_height = int(84 * scale_factor)
        self.image = pygame.transform.scale(self.image, (target_width, target_height))

        self.rect = self.image.get_rect()
        # Position balloon lower - closer to ground level
        balloon_height = random.randint(60, 120)
        self.rect.bottomleft = (WIDTH, GROUND_LEVEL - balloon_height)

    def _setup_glow_balloon_obstacle(self):
        """Setup a glowing balloon power-up obstacle that changes color."""
        if "glow_balloon" in OBSTACLE_IMAGES and OBSTACLE_IMAGES["glow_balloon"]:
            self.image = OBSTACLE_IMAGES["glow_balloon"].copy()
        else:
            self.image = create_pixel_glow_balloon()

        # Scale it slightly larger than regular balloons
        scale_factor = random.uniform(1.1, 1.4)
        target_width = int(54 * scale_factor)
        target_height = int(90 * scale_factor)
        self.image = pygame.transform.scale(self.image, (target_width, target_height))

        self.rect = self.image.get_rect()
        # Position slightly higher than normal balloons, but still reachable
        balloon_height = random.randint(80, 140)
        self.rect.bottomleft = (WIDTH, GROUND_LEVEL - balloon_height)

        # Add attributes for color-changing effect
        self.color_timer = 0
        self.color_change_speed = (
            self.DEFAULT_COLOR_CHANGE_SPEED
        )  # How fast the color changes
        self.current_color_index = 0
        # Store the original balloon for recoloring
        self.original_balloon = self.image.copy()

    def _setup_glowing_obstacle(self):
        """Setup a glowing obstacle that changes color and gives a shot when collected."""
        if (
            "glowing_obstacle" in OBSTACLE_IMAGES
            and OBSTACLE_IMAGES["glowing_obstacle"]
        ):
            self.image = OBSTACLE_IMAGES["glowing_obstacle"].copy()
        else:
            self.image = create_pixel_glowing_obstacle()

        self.rect = self.image.get_rect()
        self.rect.bottomleft = (WIDTH, GROUND_LEVEL)

        # Add attributes specific to the glowing obstacle
        self.gives_shot = True  # This obstacle gives a shot when touched
        self.color_timer = 0
        self.color_change_speed = (
            self.DEFAULT_COLOR_CHANGE_SPEED
        )  # How fast the color changes
        self.current_color_index = 0

    def update(self):
        """Move the obstacle and check if it's off-screen."""
        # Move obstacle to the left
        self.rect.x -= self.speed

        # Handle color changing effects
        self._update_color_effects()

        # Remove if off-screen
        if self.rect.right < 0:
            self.kill()

    def _update_color_effects(self):
        """Handle color changing effects for special obstacles."""
        # Only process color changes for special obstacle types
        if self.type not in ["glowing_obstacle", "glow_balloon"]:
            return

        # Update color timer
        self.color_timer += 1
        if self.color_timer >= self.color_change_speed:
            # Reset timer and advance to next color
            self.color_timer = 0
            self.current_color_index = (self.current_color_index + 1) % len(
                self.COLOR_PALETTE
            )

            # Update the appearance based on obstacle type
            if self.type == "glowing_obstacle":
                self._update_glowing_obstacle_color()
            elif self.type == "glow_balloon":
                self._update_glow_balloon_color()

    def _update_glow_balloon_color(self):
        """Update the color of the glowing balloon."""
        if self.type != "glow_balloon":
            return

        # Get the current color from the palette
        new_color = self.COLOR_PALETTE[self.current_color_index]

        # Create a new tinted version of the balloon
        width, height = (
            self.original_balloon.get_width(),
            self.original_balloon.get_height(),
        )
        tinted_surface = pygame.Surface((width, height), pygame.SRCALPHA)

        # Copy the original balloon
        tinted_surface.blit(self.original_balloon, (0, 0))

        # Create a colored overlay with some transparency for tinting
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((*new_color, 150))  # Semi-transparent color overlay

        # Apply the tint to the balloon
        tinted_surface.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # Add some bright spots to make it look like it's glowing
        self._add_glow_spots(tinted_surface, width, height)

        # Update the image
        self.image = tinted_surface

    def _add_glow_spots(self, surface, width, height):
        """Add glowing spots to a surface to enhance the glow effect."""
        for _ in range(3):
            # Random position for the glow spot
            spot_x = random.randint(width // 4, width * 3 // 4)
            spot_y = random.randint(height // 4, height * 3 // 5)  # Mostly upper part

            # Random size for the glow spot
            spot_size = random.randint(2, 5)

            # Semi-transparent white for the glow effect
            spot_color = (255, 255, 255, 150)

            # Create the glow spot
            spot_surface = pygame.Surface(
                (spot_size * 2, spot_size * 2), pygame.SRCALPHA
            )
            pygame.draw.circle(
                spot_surface, spot_color, (spot_size, spot_size), spot_size
            )

            # Add the glow spot to the surface with additive blending
            surface.blit(
                spot_surface,
                (spot_x - spot_size, spot_y - spot_size),
                special_flags=pygame.BLEND_RGBA_ADD,
            )

    def _update_glowing_obstacle_color(self):
        """Update the color of the glowing obstacle."""
        if self.type != "glowing_obstacle":
            return

        # Get the current color from the palette
        new_color = self.COLOR_PALETTE[self.current_color_index]

        # Create a new surface with the updated color
        width, height = self.image.get_width(), self.image.get_height()
        surface = pygame.Surface((width, height), pygame.SRCALPHA)

        # Create a star shape
        center = (width // 2, height // 2)
        outer_radius = width // 2 - 2
        inner_radius = outer_radius // 2

        # Build the star shape points
        star_points = []
        for i in range(10):  # 5 points with 10 vertices
            angle = math.pi / 2 + i * math.pi * 2 / 10
            radius = outer_radius if i % 2 == 0 else inner_radius
            x_point = center[0] + radius * math.cos(angle)
            y_point = center[1] - radius * math.sin(angle)
            star_points.append((x_point, y_point))

        # Draw the star with the new color
        pygame.draw.polygon(surface, new_color, star_points)

        # Add a glow effect
        for r in range(1, 4):
            glow_surface = pygame.Surface((width, height), pygame.SRCALPHA)
            # Make the glow match the current color
            glow_color = (*new_color, 100 - r * 25)
            pygame.draw.polygon(glow_surface, glow_color, star_points)

            # Scale the glow slightly larger
            scale_factor = 1.0 + (r * 0.1)
            scaled_size = (int(width * scale_factor), int(height * scale_factor))
            scaled_surface = pygame.transform.scale(glow_surface, scaled_size)

            # Center the scaled surface
            pos = ((width - scaled_size[0]) // 2, (height - scaled_size[1]) // 2)
            surface.blit(scaled_surface, pos, special_flags=pygame.BLEND_ALPHA_SDL2)

        self.image = surface


class Ground:
    """Ground platform for the game - green grass terrain."""

    def __init__(self):
        """Initialize the ground."""
        self.surface = pygame.Surface((WIDTH, HEIGHT - GROUND_LEVEL))
        self.rect = self.surface.get_rect(topleft=(0, GROUND_LEVEL))
        self.color_seed = random.randint(0, 1000)  # Seed for consistent random colors

        # Define color ranges for ground (green tones)
        self.dark_grass = (25, 80, 20)  # Dark green for shadows
        self.main_grass = (40, 120, 30)  # Main green color
        self.light_grass = (65, 150, 45)  # Light green for highlights
        self.dirt_color = (101, 67, 33)  # Brown dirt color

        # Generate the ground with base colors and texture
        self._generate_ground()

    def _generate_ground(self):
        """Generate the ground with grass and dirt layers."""
        # Fill the ground with dirt color
        self.surface.fill(self.dirt_color)

        # Create a grass layer on top
        grass_height = 15
        grass_rect = pygame.Rect(0, 0, WIDTH, grass_height)
        pygame.draw.rect(self.surface, self.main_grass, grass_rect)

        # Add texture to the grass (small random vertical lines for grass blades)
        for x in range(0, WIDTH, 2):
            random.seed(self.color_seed + x)  # Use seed for consistent randomness

            # Random grass blade height
            height = random.randint(2, 8)
            # Randomly choose grass color (dark, main, or light)
            color_choice = random.random()
            if color_choice < 0.2:
                color = self.dark_grass
            elif color_choice < 0.7:
                color = self.main_grass
            else:
                color = self.light_grass

            # Draw grass blade
            pygame.draw.line(self.surface, color, (x, 0), (x, height), 1)

        # Add some random patches of lighter/darker grass
        for _ in range(40):
            random.seed(self.color_seed + _ * 10)  # Consistent randomness
            patch_x = random.randint(0, WIDTH - 30)
            patch_y = random.randint(0, 10)
            patch_width = random.randint(20, 50)
            patch_height = random.randint(3, 8)

            # Randomly choose patch color
            if random.random() < 0.5:
                patch_color = self.light_grass
            else:
                patch_color = self.dark_grass

            pygame.draw.ellipse(
                self.surface, patch_color, (patch_x, patch_y, patch_width, patch_height)
            )

        # Add dirt texture - small dots and variations
        for _ in range(300):
            random.seed(self.color_seed + _ * 5)  # Consistent randomness
            dirt_x = random.randint(0, WIDTH - 1)
            dirt_y = random.randint(grass_height, self.surface.get_height() - 1)

            # Random dirt color variation
            color_var = random.randint(-15, 15)
            dirt_color = (
                max(0, min(255, self.dirt_color[0] + color_var)),
                max(0, min(255, self.dirt_color[1] + color_var // 2)),
                max(0, min(255, self.dirt_color[2] + color_var // 2)),
            )

            # Draw dirt particle
            size = random.randint(1, 4)
            pygame.draw.circle(self.surface, dirt_color, (dirt_x, dirt_y), size)

        # Add some small rocks in the dirt
        for _ in range(20):
            random.seed(self.color_seed + _ * 25)  # Consistent randomness
            rock_x = random.randint(0, WIDTH - 10)
            rock_y = random.randint(grass_height + 5, self.surface.get_height() - 10)
            rock_size = random.randint(2, 5)

            # Grey rock color with slight variation
            grey_var = random.randint(-20, 20)
            rock_color = (120 + grey_var, 120 + grey_var, 120 + grey_var)

            pygame.draw.circle(self.surface, rock_color, (rock_x, rock_y), rock_size)

        # Add some roots/cracks in the dirt
        for _ in range(10):
            random.seed(self.color_seed + _ * 50)  # Consistent randomness
            start_x = random.randint(0, WIDTH)
            start_y = grass_height + random.randint(5, 10)

            # Darker dirt color for roots
            root_color = (
                max(0, self.dirt_color[0] - 20),
                max(0, self.dirt_color[1] - 15),
                max(0, self.dirt_color[2] - 15),
            )

            # Create a branching pattern
            self._draw_root(self.surface, start_x, start_y, 90, 15, 3, root_color)

    def _draw_root(self, surface, x, y, angle, length, depth, color):
        """Recursively draw a root/crack pattern in the dirt."""
        if depth <= 0 or length < 3:
            return

        # Calculate endpoint
        end_x = x + int(math.cos(math.radians(angle)) * length)
        end_y = y + int(math.sin(math.radians(angle)) * length)

        # Draw the line
        pygame.draw.line(surface, color, (x, y), (end_x, end_y), 1)

        # Create branches with some randomness
        random.seed(self.color_seed + x + y + angle)  # Consistent randomness

        # Left branch
        new_angle = angle - random.randint(20, 40)
        new_length = length * 0.7
        self._draw_root(surface, end_x, end_y, new_angle, new_length, depth - 1, color)

        # Right branch
        new_angle = angle + random.randint(20, 40)
        new_length = length * 0.7
        self._draw_root(surface, end_x, end_y, new_angle, new_length, depth - 1, color)

    def update(self):
        """Update the ground (currently static, but could be animated)."""
        pass

    def draw(self, screen):
        """Draw the ground on the screen."""
        screen.blit(self.surface, self.rect)

    def update_theme(self, style_index):
        """Update the ground theme based on the background style index."""
        # Update colors based on background style
        if style_index == 0:  # Blue Sky
            self.dark_grass = (25, 80, 20)
            self.main_grass = (40, 120, 30)
            self.light_grass = (65, 150, 45)
            self.dirt_color = (101, 67, 33)
        elif style_index == 1:  # Sunset
            self.dark_grass = (80, 40, 60)
            self.main_grass = (100, 60, 80)
            self.light_grass = (139, 69, 19)
            self.dirt_color = (160, 100, 80)
        elif style_index == 2:  # Night
            self.dark_grass = (20, 30, 50)
            self.main_grass = (25, 35, 60)
            self.light_grass = (40, 50, 80)
            self.dirt_color = (50, 70, 160)
        elif style_index == 3:  # Dawn
            self.dark_grass = (200, 120, 150)
            self.main_grass = (220, 160, 180)
            self.light_grass = (240, 180, 210)
            self.dirt_color = (180, 150, 180)

        # Regenerate the ground with new colors
        self._generate_ground()


class LightingEffect:
    """Creates a dynamic lighting effect for the game."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.time = 0

        # Set brightness to max (completely disables darkening effects)
        self.brightness = 1.0

        # Empty surfaces for lighting - no actual effect at maximum brightness
        self.day_overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        self.vignette = pygame.Surface((width, height), pygame.SRCALPHA)

    def update(self):
        """Update lighting effects."""
        # Just increment time for possible future use - no actual effect
        self.time += 0.005
        if self.time > 2:
            self.time = 0

    def draw(self, surface):
        """Apply lighting effects to the scene."""
        # At brightness 1.0, this does nothing (completely transparent overlay)
        pass


# Game class
class Game:
    """Main game class that manages the game state and rendering."""

    # Class variable to hold the singleton instance
    _instance = None

    @classmethod
    def get_instance(cls):
        """Get the current Game instance for use by other classes."""
        return cls._instance

    def __init__(self):
        """Initialize the game state."""
        # Set this instance as the current one
        Game._instance = self

        # Available cat types and current selection
        self.available_cat_types = ["cat", "cat2"]
        self.current_cat_type = random.choice(
            self.available_cat_types
        )  # Randomly select initial cat

        self.cat = Cat(self.current_cat_type)
        self.all_sprites = pygame.sprite.Group(self.cat)
        self.obstacles = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()  # Group for bullets

        # Create splash screen cat
        self.splash_cat = Cat(self.current_cat_type)
        self.splash_cat.rect.bottomleft = (20, GROUND_LEVEL)  # Start near left edge
        self.splash_cat.current_animation = "idle"  # Start in idle state
        self.splash_cat_moving_right = True
        self.splash_cat_facing_right = True  # Track which way cat is facing
        self.splash_cat_speed = 2  # Slower speed for splash screen

        # Animation state tracking
        self.splash_cat_state = "idle"  # Current state: "idle" or "run"
        self.splash_cat_state_timer = 0
        self.splash_cat_idle_duration = 120  # Frames to stay idle (about 2 seconds)
        self.splash_cat_run_duration = 180  # Frames to stay running (about 3 seconds)

        # Create particle system
        self.particle_system = ParticleSystem()

        # Create parallax background
        self.background = ParallaxBackground()

        # Create ground
        self.ground = Ground()

        # Game state variables
        self.score = 0
        self.combo_counter = 0
        self.high_score = self._load_high_score()
        self.game_over = False
        self.show_splash = True

        # Timing and difficulty variables
        self.obstacle_timer = 0
        self.current_speed = OBSTACLE_SPEED
        self.last_obstacle = pygame.time.get_ticks()
        self.obstacle_frequency = 1500  # milliseconds

        # Load fonts
        self.font = pygame.font.SysFont("Arial", 24)
        self.title_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.combo_font = pygame.font.SysFont("Arial", 36, bold=True)

        # Create lighting effects (but set to maximum brightness)
        self.lighting = LightingEffect(WIDTH, HEIGHT)
        self.brightness_levels = [1.0]  # Only one level - maximum brightness
        self.current_brightness_index = 0
        self.lighting.brightness = 1.0
        self.brightness_change_time = 0

        # Score popup animation
        self.score_popups = []

        # Sound effects
        self._load_sounds()

        self.last_shot_score = 0  # Track score for shot availability

    def change_cat_type(self, cat_type_index):
        """Switch to a different cat sprite."""
        if cat_type_index < 0 or cat_type_index >= len(self.available_cat_types):
            return  # Invalid index

        new_cat_type = self.available_cat_types[cat_type_index]
        if new_cat_type == self.current_cat_type:
            return  # No change needed

        self.current_cat_type = new_cat_type

        # Update the cat sprite
        self.cat.change_cat_type(new_cat_type)

        # Also update splash cat if showing splash screen
        if self.show_splash:
            self.splash_cat.change_cat_type(new_cat_type)

        # Add a notification popup
        self.score_popups.append(
            {
                "text": f"CAT SPRITE: {cat_type_index + 1}",
                "pos": (WIDTH // 2, HEIGHT // 3),
                "lifetime": 90,
                "color": (255, 255, 100),  # Yellow
                "size": 32,
            }
        )

    def _load_high_score(self):
        """Load the high score from a file."""
        try:
            if os.path.exists("assets/highscore.txt"):
                with open("assets/highscore.txt", "r") as f:
                    return int(f.read().strip())
        except (IOError, ValueError) as e:
            logger.error(f"Error loading high score: {e}")
        return 0

    def _save_high_score(self):
        """Save the high score to a file."""
        try:
            with open("assets/highscore.txt", "w") as f:
                f.write(str(self.high_score))
        except IOError as e:
            logger.error(f"Error saving high score: {e}")

    def _load_sounds(self):
        """Load all game sound effects."""
        self.sounds = {}
        try:
            # We'll implement actual sound loading when we have sound files
            # For now, we'll just set up the structure
            self.sounds_enabled = True
        except Exception as e:
            logger.error(f"Error loading sounds: {e}")
            self.sounds_enabled = False

        # Add placeholders for new sounds
        # Example:
        # self.sounds["powerup"] = pygame.mixer.Sound("path/to/powerup.wav")
        self.sounds["powerup"] = None
        self.sounds["double_jump"] = None
        self.sounds["jump"] = None  # Assume jump sound exists
        self.sounds["hit"] = None  # Assume hit sound exists
        self.sounds["point"] = None  # Assume point sound exists
        self.sounds["bonus"] = None  # Assume bonus sound exists
        self.sounds["slide"] = None  # Add slide sound

    def play_sound(self, sound_name):
        """Play a sound effect if sounds are enabled and the sound exists."""
        if self.sounds_enabled and sound_name in self.sounds:
            sound = self.sounds[sound_name]
            if sound:  # Check if the sound object is not None
                try:
                    sound.play()
                except Exception as e:
                    logger.error(f"Error playing sound {sound_name}: {e}")
            else:
                # Optionally log that the sound is missing, but don't raise an error
                # logger.warning(f"Sound '{sound_name}' not loaded, skipping playback.")
                pass

    def draw_splash_screen(self):
        """Draw the splash screen with title and instructions."""
        # Semi-transparent background for better text visibility
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))  # Semi-transparent black
        screen.blit(overlay, (0, 0))

        # Title with shadow for better visibility
        shadow_offset = 3
        title_shadow = self.title_font.render(
            "CAT GAME by MIŁOSZ", True, (20, 20, 20)
        )  # Updated Title
        title_shadow_rect = title_shadow.get_rect(
            center=(WIDTH // 2 + shadow_offset, HEIGHT // 3 + shadow_offset)
        )
        screen.blit(title_shadow, title_shadow_rect)

        title_text = self.title_font.render(
            "CAT GAME by MIŁOSZ", True, (240, 200, 80)
        )  # Updated Title & Bright gold color
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
        screen.blit(title_text, title_rect)

        # Instructions with text boxes for better visibility
        instructions = [
            "Help the cat survive the run!",  # Updated description
            "UP ARROW - Jump | DOWN ARROW - Slide",
            "SPACE - Shoot (destroys obstacles)",
            "1/2 KEYS - Switch cat sprite",
            "Avoid hitting obstacles while advancing!",
            "Earn 1 shot for every 20 points scored",
            "Jump into GLOWING balloons for a double jump!",
            "Press any key to start your adventure!",
        ]

        for i, line in enumerate(instructions):
            # Text box background
            text = self.font.render(line, True, BLACK)
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + i * 40))
            bg_rect = text_rect.inflate(20, 10)  # Make bg slightly larger than text
            pygame.draw.rect(screen, (255, 255, 255, 180), bg_rect, border_radius=5)
            pygame.draw.rect(screen, (100, 100, 100), bg_rect, width=2, border_radius=5)

            # Text
            screen.blit(text, text_rect)

        # Draw the splash cat
        screen.blit(self.splash_cat.image, self.splash_cat.rect)

        # Draw cat sprite indicator
        cat_type_text = self.font.render(
            f"Current Cat: {self.available_cat_types.index(self.current_cat_type) + 1}",
            True,
            (255, 255, 100),
        )
        cat_type_rect = cat_type_text.get_rect(
            center=(WIDTH // 2, HEIGHT // 2 + len(instructions) * 40 + 20)
        )
        # Text box background
        bg_rect = cat_type_rect.inflate(20, 10)
        pygame.draw.rect(screen, (255, 255, 255, 180), bg_rect, border_radius=5)
        pygame.draw.rect(screen, (255, 200, 0), bg_rect, width=2, border_radius=5)
        screen.blit(cat_type_text, cat_type_rect)

    def update_difficulty(self):
        """Increase game difficulty based on score."""
        # Calculate new speed based on score
        self.current_speed = min(
            OBSTACLE_SPEED + (self.score // 10) * DIFFICULTY_INCREASE_RATE,
            MAX_OBSTACLE_SPEED,
        )

        # Reduce time between obstacles as score increases
        self.obstacle_frequency = max(
            1500 - (self.score // 5) * 50,  # Reduce by 50ms every 5 points
            MIN_OBSTACLE_FREQUENCY,  # Don't go below minimum
        )

    def spawn_obstacle(self):
        """Spawn a new obstacle if it's time."""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_obstacle > self.obstacle_frequency:
            obstacle = Obstacle()
            # Set obstacle speed based on current difficulty
            obstacle.speed = self.current_speed + random.uniform(-0.5, 0.5)
            self.obstacles.add(obstacle)
            self.all_sprites.add(obstacle)
            self.last_obstacle = current_time

    def check_collisions(self):
        """Check for collisions with obstacles."""
        # Cat-obstacle collision check from the Cat class
        if self.cat.check_collisions():
            self.game_over = True

        # Bullet-obstacle collision
        collisions = pygame.sprite.groupcollide(
            self.bullets, self.obstacles, True, True
        )
        if collisions:
            # Add score for obstacles destroyed by bullets
            for bullet, obstacles_hit in collisions.items():
                for obstacle in obstacles_hit:
                    if not obstacle.already_passed:
                        self.add_score(1)
                        # Add explosion particles
                        self.particle_system.add_particles(
                            obstacle.rect.centerx,
                            obstacle.rect.centery,
                            count=30,
                            color_range=[
                                (220, 255),
                                (180, 230),
                                (50, 150),
                            ],  # Yellow explosion
                            speed_range=[(-3, 3), (-3, 3)],
                            size_range=(3, 8),
                            lifetime_range=(20, 40),
                        )
                        # Play explosion sound
                        self.play_sound("jump")  # Reuse existing sound

    def update_score(self):
        """Update score when passing obstacles."""
        for obstacle in list(self.obstacles):
            if obstacle.rect.right < self.cat.rect.left and not obstacle.already_passed:
                self.add_score(1)
                obstacle.already_passed = True

    def add_score(self, points):
        """Add points to the score and check if a new shot is earned."""
        self.score += points
        self.score_display_value = self.score

        # Update score popup
        self.score_popups.append(
            {
                "text": f"+{points}",
                "pos": (
                    self.cat.rect.x + random.randint(-20, 20),
                    self.cat.rect.y - 40,
                ),
                "lifetime": 45,
                "color": WHITE,
                "size": 24,
            }
        )

        # Check if player earns a new shot
        if self.score >= self.last_shot_score + SHOOT_THRESHOLD:
            self.cat.shots_available += 1
            self.last_shot_score = self.score

            # Show a notification for new shot
            self.score_popups.append(
                {
                    "text": "+1 SHOT!",
                    "pos": (WIDTH // 2, HEIGHT // 2 - 50),
                    "lifetime": 60,
                    "color": YELLOW,
                    "size": 28,
                }
            )

        # Update difficulty based on score
        self.update_difficulty()

    def update_score_popups(self):
        """Update the score popup animations."""
        for popup in self.score_popups[:]:
            popup["lifetime"] -= 1

            # Move the popup upward
            popup["pos"] = (popup["pos"][0], popup["pos"][1] - 1)

            # Remove if expired
            if popup["lifetime"] <= 0:
                self.score_popups.remove(popup)

    def draw_score(self):
        """Draw the current score and other game information."""
        icon_size = 24  # Size of the icons
        padding = 5  # Padding between icon and text

        # Helper function to draw small icons
        def draw_icon(x, y, icon_type):
            icon_surface = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)

            if icon_type == "score":
                # Score icon (star)
                star_points = []
                center = (icon_size // 2, icon_size // 2)
                outer_radius = icon_size // 2 - 2
                inner_radius = outer_radius // 2

                for i in range(10):  # 5 points with 10 vertices
                    angle = math.pi / 2 + i * math.pi * 2 / 10
                    radius = outer_radius if i % 2 == 0 else inner_radius
                    x_point = center[0] + radius * math.cos(angle)
                    y_point = center[1] - radius * math.sin(angle)
                    star_points.append((x_point, y_point))

                pygame.draw.polygon(
                    icon_surface, (255, 215, 0), star_points
                )  # Gold star

            elif icon_type == "high_score":
                # Trophy icon
                # Trophy cup
                pygame.draw.rect(icon_surface, (255, 215, 0), (8, 4, 8, 12))  # Cup body
                pygame.draw.rect(icon_surface, (255, 215, 0), (5, 4, 14, 4))  # Cup top
                pygame.draw.rect(
                    icon_surface, (255, 215, 0), (10, 16, 4, 4)
                )  # Cup base
                pygame.draw.rect(
                    icon_surface, (255, 215, 0), (8, 20, 8, 2)
                )  # Base plate

            elif icon_type == "double_jump":
                # Double jump icon (two up arrows)
                arrow_color = (255, 165, 0)  # Orange color
                # First arrow
                pygame.draw.polygon(
                    icon_surface, arrow_color, [(6, 16), (12, 6), (18, 16)]
                )
                # Second arrow (slightly lower)
                pygame.draw.polygon(
                    icon_surface, arrow_color, [(6, 22), (12, 12), (18, 22)]
                )

            elif icon_type == "shots":
                # Bullet icon
                bullet_color = YELLOW
                # Bullet shape
                pygame.draw.circle(
                    icon_surface,
                    bullet_color,
                    (icon_size // 2, icon_size // 2),
                    icon_size // 3,
                )
                # Glow effect
                for r in range(icon_size // 3 + 1, icon_size // 2):
                    alpha = 255 - (r - icon_size // 3) * 200 // (icon_size // 6)
                    glow_color = (
                        bullet_color[0],
                        bullet_color[1],
                        bullet_color[2],
                        alpha,
                    )
                    pygame.draw.circle(
                        icon_surface, glow_color, (icon_size // 2, icon_size // 2), r, 1
                    )

            elif icon_type == "speed":
                # Speed icon (sideways lightning bolt)
                bolt_color = (100, 100, 255)  # Blue lightning
                pygame.draw.polygon(
                    icon_surface,
                    bolt_color,
                    [
                        (4, 12),  # Left point
                        (14, 6),  # Top right
                        (12, 12),  # Middle indent
                        (20, 12),  # Right point
                        (10, 18),  # Bottom left
                        (12, 12),  # Middle indent again
                    ],
                )

            screen.blit(icon_surface, (x, y))
            return (
                x + icon_size + padding
            )  # Return position after the icon for text alignment

        # Main score with icon
        text_x = draw_icon(10, 10, "score")
        score_text = self.font.render(f"Score: {self.score}", True, BLACK)
        screen.blit(score_text, (text_x, 10))

        # High score with icon
        high_score_text = self.font.render(
            f"High Score: {self.high_score}", True, (100, 50, 150)
        )
        text_x = draw_icon(
            WIDTH - high_score_text.get_width() - icon_size - padding - 10,
            10,
            "high_score",
        )
        screen.blit(high_score_text, (text_x, 10))

        # Double Jumps Available with icon
        dj_text = self.font.render(
            f"Double Jumps: {self.cat.double_jumps_available}", True, (255, 165, 0)
        )  # Orange color
        text_x = draw_icon(
            WIDTH - dj_text.get_width() - icon_size - padding - 10, 40, "double_jump"
        )
        screen.blit(dj_text, (text_x, 40))

        # Shots Available with icon
        shots_text = self.font.render(
            f"Shots: {self.cat.shots_available}", True, YELLOW
        )
        text_x = draw_icon(
            WIDTH - shots_text.get_width() - icon_size - padding - 10, 70, "shots"
        )
        screen.blit(shots_text, (text_x, 70))

        # Current speed with icon
        text_x = draw_icon(10, 40, "speed")
        speed_text = self.font.render(f"Speed: {self.current_speed:.1f}", True, BLACK)
        screen.blit(speed_text, (text_x, 40))

        # Draw score popups
        for popup in self.score_popups:
            # Create text with size from popup
            font_size = popup.get("size", 24)
            popup_font = pygame.font.SysFont("Arial", font_size)

            # Determine color with proper fade out
            color = popup["color"]

            # Apply fading for last 20 frames
            if popup["lifetime"] < 20:
                # Calculate alpha based on remaining lifetime (used for color calculation)
                alpha_factor = popup["lifetime"] / 20
                # We can't change text alpha directly, so we'll just make the color lighter
                if isinstance(color, tuple) and len(color) == 3:
                    # Convert RGB to a lighter version based on lifetime
                    fade_factor = alpha_factor
                    r = int(color[0] + (255 - color[0]) * (1 - fade_factor))
                    g = int(color[1] + (255 - color[1]) * (1 - fade_factor))
                    b = int(color[2] + (255 - color[2]) * (1 - fade_factor))
                    color = (r, g, b)

            popup_text = popup_font.render(popup["text"], True, color)
            popup_rect = popup_text.get_rect(center=popup["pos"])
            screen.blit(popup_text, popup_rect)

    def draw_game_over(self):
        """Draw the game over screen."""
        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Semi-transparent black
        screen.blit(overlay, (0, 0))

        # Game over text
        game_over_text = self.title_font.render("GAME OVER!", True, (255, 50, 50))
        game_over_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
        screen.blit(game_over_text, game_over_rect)

        # Final score
        final_score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
        final_score_rect = final_score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(final_score_text, final_score_rect)

        # High score notification
        if self.score > self.high_score:
            new_high_text = self.font.render("NEW HIGH SCORE!", True, (255, 220, 0))
            new_high_rect = new_high_text.get_rect(
                center=(WIDTH // 2, HEIGHT // 2 + 40)
            )
            screen.blit(new_high_text, new_high_rect)

        # Restart instruction
        restart_text = self.font.render("Press R to restart", True, WHITE)
        restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80))
        screen.blit(restart_text, restart_rect)

    def reset(self):
        """Reset the entire game state."""
        # Check for high score before resetting
        if self.score > self.high_score:
            self.high_score = self.score
            self._save_high_score()

        # Re-initialize game state
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
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                    elif (
                        event.key == pygame.K_UP and not self.game_over
                    ):  # Up arrow for jump
                        self.cat.jump()
                        self.play_sound("jump")
                    elif (
                        event.key == pygame.K_DOWN and not self.game_over
                    ):  # Down arrow for slide
                        self.cat.slide()
                    elif (
                        event.key == pygame.K_SPACE and not self.game_over
                    ):  # Space to shoot
                        self.shoot_bullet()
                    elif event.key == pygame.K_r and self.game_over:
                        self.reset()
                    elif event.key == pygame.K_m:  # Mute toggle
                        self.sounds_enabled = not self.sounds_enabled
                    elif event.key == pygame.K_b:  # Background cycle
                        new_style = self.background.cycle_background()
                        # Change the ground to match
                        self.ground.update_theme(new_style)

                        # Reset random seed for obstacle generation to prevent exploit
                        # This ensures pressing B repeatedly doesn't result in the same obstacles
                        # We'll use a mix of current time and score to create a unique seed
                        new_seed = int(pygame.time.get_ticks() * (self.score + 1))
                        random.seed(new_seed)

                        # Reset obstacle history tracking to prevent pattern exploitation
                        Obstacle.reset_history()
                    elif event.key == pygame.K_1:  # Switch to cat sprite 1
                        self.change_cat_type(0)
                    elif event.key == pygame.K_2:  # Switch to cat sprite 2
                        self.change_cat_type(1)

            if not self.game_over and not self.show_splash:
                # Spawn obstacles
                self.spawn_obstacle()

                # Update all sprites
                self.all_sprites.update()

                # Update background
                self.background.update()

                # Update ground with current speed factor
                self.ground.update()

                # Check for collisions
                self.check_collisions()

                # Update score
                self.update_score()

                # Update score popups
                self.update_score_popups()

                # Update particles
                self.particle_system.update()

                # Update bullets
                self.bullets.update()

            elif self.show_splash:
                # Update splash cat animation and position
                self.splash_cat_state_timer += 1

                # State transitions between idle and run
                if (
                    self.splash_cat_state == "idle"
                    and self.splash_cat_state_timer >= self.splash_cat_idle_duration
                ):
                    # Transition from idle to run
                    self.splash_cat_state = "run"
                    self.splash_cat_state_timer = 0
                    self.splash_cat.current_animation = "run"
                    self.splash_cat.frame_index = 0  # Reset animation frame index
                elif (
                    self.splash_cat_state == "run"
                    and self.splash_cat_state_timer >= self.splash_cat_run_duration
                ):
                    # Transition from run to idle
                    self.splash_cat_state = "idle"
                    self.splash_cat_state_timer = 0
                    self.splash_cat.current_animation = "idle"
                    self.splash_cat.frame_index = 0  # Reset animation frame index

                # Only move the cat when in run state
                if self.splash_cat_state == "run":
                    if self.splash_cat_moving_right:
                        self.splash_cat.rect.x += self.splash_cat_speed
                        if self.splash_cat.rect.right >= WIDTH - 20:
                            self.splash_cat_moving_right = False
                            self.splash_cat_facing_right = (
                                False  # Update facing direction
                            )
                    else:
                        self.splash_cat.rect.x -= self.splash_cat_speed
                        if self.splash_cat.rect.left <= 20:
                            self.splash_cat_moving_right = True
                            self.splash_cat_facing_right = (
                                True  # Update facing direction
                            )

                # Ensure splash cat stays on ground
                self.splash_cat.rect.bottom = GROUND_LEVEL
                self.splash_cat.on_ground = True  # Keep it grounded for animation state

                # Update the animation
                self.splash_cat.animation_timer += 1
                if self.splash_cat.animation_timer >= ANIMATION_SPEED:
                    self.splash_cat.animation_timer = 0
                    # Get the current animation frames
                    frames = self.splash_cat.animations[
                        self.splash_cat.current_animation
                    ]
                    # Increment the frame index, looping back to 0 if necessary
                    self.splash_cat.frame_index = (
                        self.splash_cat.frame_index + 1
                    ) % len(frames)
                    # Get the current frame
                    current_frame = frames[self.splash_cat.frame_index]

                    # Apply direction-based flipping
                    if not self.splash_cat_facing_right:
                        self.splash_cat.image = pygame.transform.flip(
                            current_frame, True, False
                        )
                    else:
                        self.splash_cat.image = current_frame

            elif self.game_over:
                # When game over, still update the cat for death animation
                self.cat.update()

            # Draw everything
            screen.fill(SKY_BLUE)

            # Draw parallax background
            self.background.draw(screen)

            if self.show_splash:
                self.draw_splash_screen()
            else:
                # Draw ground
                self.ground.draw(screen)

                # Draw cat and obstacles
                self.obstacles.draw(screen)
                self.bullets.draw(screen)  # Draw bullets
                screen.blit(self.cat.image, self.cat.rect)

                # Draw particles
                self.particle_system.draw(screen)

                self.draw_score()

                if self.game_over:
                    self.draw_game_over()

            # Update display
            pygame.display.flip()

            # Cap framerate
            clock.tick(FPS)

    def shoot_bullet(self):
        """Create a bullet at the cat's position if shots are available."""
        if self.cat.shoot():
            # Create a bullet at cat's position
            bullet = Bullet(self.cat.rect.centerx, self.cat.rect.centery)
            self.bullets.add(bullet)
            self.all_sprites.add(bullet)

            # Add particle effect for shooting
            self.particle_system.add_particles(
                self.cat.rect.right,
                self.cat.rect.centery,
                count=15,
                color_range=[
                    (220, 255),
                    (180, 230),
                    (50, 150),
                ],  # Yellow/gold particles
                speed_range=[(-1, 1), (-1, 1)],
                size_range=(2, 5),
                lifetime_range=(10, 20),
            )

            # Play shoot sound
            self.play_sound("powerup")  # Reuse existing sound

            return True
        return False


# Run the game directly if this file is executed
if __name__ == "__main__":
    # Redefine obstacle images with the new pixel art functions
    # Note: Previous obstacle generation functions are now replaced with pixel art versions

    # Reload OBSTACLE_IMAGES before creating Game instance
    OBSTACLE_IMAGES = load_obstacle_images()

    # Create and run the game
    game = Game()
    game.run()
