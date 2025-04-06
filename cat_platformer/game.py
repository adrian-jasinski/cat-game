"""
Cat Platformer Game Module
This module contains the game mechanics for the Cat Platformer.
"""

import os
import sys
import math
import random
import logging
import pygame
import glob
import json
from collections import deque
from typing import List, Dict, Optional, Any, Tuple, Union

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize pygame
pygame.init()
try:
    pygame.mixer.init()  # Initialize the mixer for sound
except pygame.error:
    logging.warning("Could not initialize sound mixer")

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

# Set up the display
screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption("Cat Platformer")
clock = pygame.time.Clock()  # Create clock instance for time tracking

# Create game directory for assets if it doesn't exist
if not os.path.exists("assets"):
    os.makedirs("assets")


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


def load_animation_frames(animation_name):
    """Load animation frames from the graphics directory."""
    frames = []
    path_pattern = f"graphics/cat/{animation_name} (*).png"
    matching_files = sorted(
        glob.glob(path_pattern), key=lambda x: int(x.split("(")[1].split(")")[0])
    )

    if not matching_files:
        logger.warning(
            f"No animation frames found for {animation_name}. Using fallback."
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
    """Creates a glowing pixel art balloon power-up."""
    width, height = 54, 90  # Slightly larger base
    surface = pygame.Surface((width, height), pygame.SRCALPHA)

    # Gold/Yellow glowing palette
    base = (255, 200, 0)  # Bright yellow-gold base
    highlight = (255, 230, 100)  # Lighter highlight
    shine = (255, 255, 220)  # Near white shine
    string_color = (200, 200, 200)  # Light gray string
    glow_color = (255, 220, 50, 100)  # Semi-transparent outer glow

    scale = 6
    balloon_height = 10  # in pixels
    balloon_width = 8  # in pixels
    center_x = width // 2

    # Outer glow (drawn first)
    glow_radius_x = (balloon_width // 2 + 1) * scale
    glow_radius_y = (balloon_height // 2 + 1) * scale
    glow_rect = pygame.Rect(0, 0, glow_radius_x * 2, glow_radius_y * 2)
    glow_rect.center = (center_x, balloon_height * scale // 2)

    # Create a temporary surface for the glow ellipse
    temp_glow_surf = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
    pygame.draw.ellipse(
        temp_glow_surf, glow_color, (0, 0, glow_rect.width, glow_rect.height)
    )
    surface.blit(temp_glow_surf, glow_rect.topleft)

    # Balloon shape (oval)
    for y in range(balloon_height):
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

    # Shine spots
    pygame.draw.rect(surface, shine, (center_x - scale * 1.5, scale, scale, scale))
    pygame.draw.rect(surface, shine, (center_x - scale * 0.5, scale * 2, scale, scale))
    pygame.draw.rect(surface, shine, (center_x - scale, scale * 1.5, scale, scale))

    # Add inner yellow glow lines for effect
    inner_glow_color = (255, 240, 150, 150)
    pygame.draw.line(
        surface,
        inner_glow_color,
        (center_x - scale, scale * 3),
        (center_x - scale, scale * (balloon_height - 3)),
        2,
    )
    pygame.draw.line(
        surface,
        inner_glow_color,
        (center_x + scale // 2, scale * 3),
        (center_x + scale // 2, scale * (balloon_height - 3)),
        2,
    )

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

    def __init__(self):
        super().__init__()

        # Load all animation frames
        self.animations = {}
        try:
            self.animations = {
                "idle": load_animation_frames("Idle"),
                "run": load_animation_frames("Run"),
                "jump": load_animation_frames("Jump"),
                "fall": load_animation_frames("Fall"),
                "dead": load_animation_frames("Dead"),
                "slide": load_animation_frames("Slide"),  # Add slide animation
            }
            logger.info("Cat animations loaded successfully")
        except Exception as e:
            logger.error(f"Error loading cat animations: {e}")
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

        # Physics attributes
        self.velocity_y = 0
        self.on_ground = True
        self.is_dead = False
        self.double_jumps_available = 0  # Counter for double jumps

        # Sliding state
        self.is_sliding = False
        self.slide_timer = 0
        self.slide_duration = 45  # Frames to stay in slide (about 0.75 seconds)
        self.slide_cooldown = 0  # Cooldown between slides
        self.slide_cooldown_duration = 30  # Frames of cooldown

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

        # Adjust hitbox height to be lower when sliding
        self.rect.height = self.normal_height * 0.6

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


# Obstacle class
class Obstacle(pygame.sprite.Sprite):
    """Obstacle sprites that the cat must avoid."""

    def __init__(self):
        super().__init__()

        obstacle_types = [
            {"type": "stone", "weight": 30},
            {"type": "cactus", "weight": 25},
            {"type": "bush", "weight": 20},
            {"type": "balloon", "weight": 15},
            {"type": "low_balloon", "weight": 10},  # New low-flying balloon type
            {"type": "glow_balloon", "weight": 5},  # Keep the power-up balloon
        ]

        # Choose obstacle type based on weights
        weights = [item["weight"] for item in obstacle_types]
        self.type = random.choices(
            [item["type"] for item in obstacle_types], weights=weights
        )[0]

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
            self._setup_low_balloon_obstacle()  # New setup for low balloon
        elif self.type == "glow_balloon":
            self._setup_glow_balloon_obstacle()

        # Set common properties
        self.speed = OBSTACLE_SPEED
        self.already_passed = False

        # Ground-based obstacles position
        if self.type not in ["balloon", "low_balloon", "glow_balloon"]:
            self.rect.bottom = GROUND_LEVEL
        # If it's a balloon, adjust y position to be in the air
        elif self.type == "balloon":
            # Standard balloon is high in the air
            self.rect.y = GROUND_LEVEL - self.rect.height - random.randint(200, 250)
        elif self.type == "low_balloon":
            # Low balloon requires sliding under it
            self.rect.y = GROUND_LEVEL - self.rect.height - random.randint(70, 120)
        elif self.type == "glow_balloon":
            # Glow balloon should be in jumping range
            self.rect.y = GROUND_LEVEL - self.rect.height - random.randint(150, 180)

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
        # Position balloon higher up - requires player NOT to jump
        balloon_height = random.randint(80, 140)
        self.rect.bottomleft = (WIDTH, GROUND_LEVEL - balloon_height)

    def _setup_glow_balloon_obstacle(self):
        """Setup a glowing balloon power-up obstacle."""
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
        balloon_height = random.randint(100, 160)
        self.rect.bottomleft = (WIDTH, GROUND_LEVEL - balloon_height)

    def _setup_low_balloon_obstacle(self):
        """Set up a low-flying balloon obstacle that requires sliding under."""
        # Use the same balloon image but position it lower
        self.image = create_pixel_balloon(random_variant=True)
        self.rect = self.image.get_rect()

        # Set position at right edge of screen
        self.rect.x = SCREEN_SIZE[0]

        # Tag this as a slide-under obstacle
        self.requires_slide = True

    def update(self):
        """Move the obstacle and check if it's off-screen."""
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()


# Cloud class for background
class Cloud(pygame.sprite.Sprite):
    """Decorative blue clouds that move in the background."""

    def __init__(self):
        super().__init__()
        self.width = random.randint(80, 180)  # Slightly wider clouds possible
        self.height = random.randint(40, 80)  # Slightly taller clouds possible
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Create varying shades of blue clouds - some darker, some lighter
        base_alpha = 180  # Base transparency
        cloud_base_color = random.choice(
            [
                (150, 170, 230, base_alpha),  # Light blue-purple
                (130, 160, 220, base_alpha),  # Mid blue
                (170, 200, 255, base_alpha),  # Very light blue
                (100, 140, 210, base_alpha),  # Darker blue
            ]
        )

        # Determine highlight color based on base color
        highlight_color = (
            min(cloud_base_color[0] + 30, 255),
            min(cloud_base_color[1] + 30, 255),
            min(cloud_base_color[2] + 30, 255),
            base_alpha - 20,  # Slightly less transparent highlight
        )

        # Create a fluffier cloud shape using multiple overlapping circles
        num_circles_main = random.randint(4, 7)  # Main large puffs
        num_circles_detail = random.randint(3, 6)  # Smaller detail puffs
        center_x = self.width // 2
        center_y = self.height // 2

        # Draw main puffs (larger, form the core shape)
        for i in range(num_circles_main):
            # Larger radius for main puffs
            radius = random.randint(int(self.width * 0.20), int(self.width * 0.45))
            # Wider horizontal offset, slightly lower vertical offset bias for base
            offset_x = random.randint(-self.width // 3, self.width // 3)
            offset_y = random.randint(
                -self.height // 6, self.height // 4
            )  # Bias slightly downwards

            circle_x = center_x + offset_x
            circle_y = center_y + offset_y

            # Color based on vertical position (darker lower down)
            # Calculate vertical position relative to the cloud height (0=top, 1=bottom)
            # We use circle_y + radius as the bottom of the current circle for shading
            effective_y = circle_y + radius
            bottom_offset = effective_y - (center_y - self.height // 2)
            vertical_ratio = max(0, min(1, bottom_offset / self.height))

            r_base, g_base, b_base, a_base = cloud_base_color
            r_high, g_high, b_high, a_high = highlight_color

            # Interpolate between base and highlight based on height
            mix_ratio = max(0, 1 - vertical_ratio * 1.2)
            r = int(r_base + (r_high - r_base) * mix_ratio)
            g = int(g_base + (g_high - g_base) * mix_ratio)
            b = int(b_base + (b_high - b_base) * mix_ratio)
            alpha = int(a_base + (a_high - a_base) * mix_ratio)

            # Make bottom part darker explicitly
            if vertical_ratio > 0.65:
                r = max(0, r - 25)
                g = max(0, g - 25)
                b = max(0, b - 20)
                alpha = min(255, alpha + 15)

            color = (r, g, b, alpha)

            pygame.draw.circle(
                self.image,
                color,
                (circle_x, circle_y),
                radius,
            )

        # Draw smaller detail puffs (add texture)
        for i in range(num_circles_detail):
            # Smaller radius for detail
            radius = random.randint(int(self.width * 0.10), int(self.width * 0.25))
            # Allow wider offset for detail puffs, slightly biased upwards
            offset_x = random.randint(-self.width // 2, self.width // 2)
            offset_y = random.randint(-self.height // 3, self.height // 4)

            circle_x = center_x + offset_x
            circle_y = center_y + offset_y

            # Use highlight color mostly for detail puffs, slightly more transparent
            detail_alpha = max(0, highlight_color[3] - 40)
            color = (*highlight_color[:3], detail_alpha)

            pygame.draw.circle(
                self.image,
                color,
                (circle_x, circle_y),
                radius,
            )

        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH)
        self.rect.y = random.randint(
            20, GROUND_LEVEL - 250
        )  # Keep clouds higher in the sky
        self.speed = random.uniform(0.3, 0.8)  # Slower cloud movement

    def update(self):
        """Move the cloud and wrap around when off-screen."""
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.rect.left = WIDTH
            self.rect.y = random.randint(20, GROUND_LEVEL - 250)
            self.speed = random.uniform(0.3, 0.8)


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

    def update_theme(self, new_style):
        """Update the ground theme based on the new background style."""
        if new_style == "Blue Sky":
            self.dark_grass = (25, 80, 20)
            self.main_grass = (40, 120, 30)
            self.light_grass = (65, 150, 45)
            self.dirt_color = (101, 67, 33)
        elif new_style == "Sunset":
            self.dark_grass = (80, 40, 60)
            self.main_grass = (100, 60, 80)
            self.light_grass = (139, 69, 19)
            self.dirt_color = (160, 100, 80)
        elif new_style == "Night":
            self.dark_grass = (20, 30, 50)
            self.main_grass = (25, 35, 60)
            self.light_grass = (40, 50, 80)
            self.dirt_color = (50, 70, 160)
        elif new_style == "Dawn":
            self.dark_grass = (200, 120, 150)
            self.main_grass = (220, 160, 180)
            self.light_grass = (240, 180, 210)
            self.dirt_color = (180, 150, 180)


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

        self.cat = Cat()
        self.all_sprites = pygame.sprite.Group(self.cat)
        self.obstacles = pygame.sprite.Group()
        self.clouds = pygame.sprite.Group()

        # Create splash screen cat
        self.splash_cat = Cat()
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

        # Create initial clouds
        for _ in range(5):
            cloud = Cloud()
            self.clouds.add(cloud)
            self.all_sprites.add(cloud)

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
            "CAT GAME", True, (20, 20, 20)
        )  # Updated Title
        title_shadow_rect = title_shadow.get_rect(
            center=(WIDTH // 2 + shadow_offset, HEIGHT // 3 + shadow_offset)
        )
        screen.blit(title_shadow, title_shadow_rect)

        title_text = self.title_font.render(
            "CAT GAME", True, (240, 200, 80)
        )  # Updated Title & Bright gold color
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
        screen.blit(title_text, title_rect)

        # Instructions with text boxes for better visibility
        instructions = [
            "Help the cat survive the run!",  # Updated description
            "Press SPACE to jump",
            "Avoid hitting normal balloons while jumping!",  # Updated rule
            "Jump into GLOWING balloons for a double jump!",  # New rule
            "Press R to restart after game over",
            "Press any key to start your adventure!",  # Improved text
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
        """Check if the cat has collided with any obstacles."""
        return self.cat.check_collisions()

    def update_score(self):
        """Update the score when obstacles are passed."""
        for obstacle in self.obstacles:
            if obstacle.rect.right < self.cat.rect.left and not obstacle.already_passed:
                # Add base score
                score_to_add = 1

                # Give bonus points for balloon obstacles as they're harder to avoid
                if obstacle.type == "balloon":
                    score_to_add = 2
                    self.combo_counter += 1

                    # Create bonus score popup
                    self.score_popups.append(
                        {
                            "text": f"+{score_to_add} BONUS!",
                            "pos": (self.cat.rect.centerx, self.cat.rect.top - 20),
                            "color": (200, 50, 50),
                            "life": 60,  # frames
                        }
                    )

                    # Play bonus sound
                    self.play_sound("bonus")
                else:
                    # Regular obstacle, reset combo
                    self.combo_counter = 0

                # Apply combo bonus if applicable
                if self.combo_counter > 1:
                    combo_bonus = (
                        self.combo_counter // 2
                    )  # Every 2 balloons in a row gives bonus point
                    score_to_add += combo_bonus

                    # Create combo popup for big combos
                    if self.combo_counter >= 3:
                        self.score_popups.append(
                            {
                                "text": f"COMBO x{self.combo_counter}!",
                                "pos": (self.cat.rect.centerx, self.cat.rect.top - 40),
                                "color": (200, 200, 50),
                                "life": 60,  # frames
                            }
                        )

                # Update score and check for background change
                old_score = self.score
                self.score += score_to_add

                # Check if we crossed a 50-point threshold and change background
                if old_score // 50 < self.score // 50:
                    new_style = self.background.cycle_background()
                    style_name = ["Blue Sky", "Sunset", "Night", "Dawn"][new_style]
                    self.score_popups.append(
                        {
                            "text": f"NEW BACKGROUND: {style_name}!",
                            "pos": (WIDTH // 2, HEIGHT // 2 - 50),
                            "color": (50, 200, 200),
                            "life": 90,  # frames
                        }
                    )

                obstacle.already_passed = True

                # Update difficulty whenever score increases
                self.update_difficulty()

                # Play point sound
                self.play_sound("point")

    def update_score_popups(self):
        """Update the score popup animations."""
        for popup in self.score_popups[:]:
            popup["pos"] = (popup["pos"][0], popup["pos"][1] - 1)  # Move up
            popup["life"] -= 1

            # Remove if expired
            if popup["life"] <= 0:
                self.score_popups.remove(popup)

    def draw_score(self):
        """Draw the current score and other game information."""
        # Main score
        score_text = self.font.render(f"Score: {self.score}", True, BLACK)
        screen.blit(score_text, (10, 10))

        # High score
        high_score_text = self.font.render(
            f"High Score: {self.high_score}", True, (100, 50, 150)
        )
        high_score_rect = high_score_text.get_rect(topright=(WIDTH - 10, 10))
        screen.blit(high_score_text, high_score_rect)

        # Double Jumps Available
        dj_text = self.font.render(
            f"Double Jumps: {self.cat.double_jumps_available}", True, (255, 165, 0)
        )  # Orange color
        dj_rect = dj_text.get_rect(topright=(WIDTH - 10, 40))
        screen.blit(dj_text, dj_rect)

        # Current speed as an indicator of difficulty
        speed_text = self.font.render(f"Speed: {self.current_speed:.1f}", True, BLACK)
        screen.blit(speed_text, (10, 40))

        # Combo counter if active
        if self.combo_counter > 1:
            combo_text = self.combo_font.render(
                f"Combo: {self.combo_counter}x", True, (200, 50, 50)
            )
            combo_rect = combo_text.get_rect(midtop=(WIDTH // 2, 10))
            screen.blit(combo_text, combo_rect)

        # Draw score popups
        for popup in self.score_popups:
            # Determine color with proper fade out
            color = popup["color"]
            if popup["life"] < 20:
                # Apply fading by creating a color with adjusted alpha
                popup_text = self.font.render(popup["text"], True, color)
                # No need to change alpha since we're not using a surface with per-pixel alpha
            else:
                popup_text = self.font.render(popup["text"], True, color)

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
                    elif event.key == pygame.K_r and self.game_over:
                        self.reset()
                    elif event.key == pygame.K_m:  # Mute toggle
                        self.sounds_enabled = not self.sounds_enabled
                    elif event.key == pygame.K_b:  # Background cycle
                        new_style = self.background.cycle_background()
                        # Change the ground to match
                        self.ground.update_theme(new_style)

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

            elif self.show_splash:
                # Only update clouds during splash screen
                self.clouds.update()

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

                # Flipping now happens during the animation update

            elif self.game_over:
                # When game over, still update the cat for death animation
                self.cat.update()

            # Draw everything
            screen.fill(SKY_BLUE)

            # Draw parallax background
            self.background.draw(screen)

            # Draw clouds
            self.clouds.draw(screen)

            if self.show_splash:
                self.draw_splash_screen()
            else:
                # Draw ground
                self.ground.draw(screen)

                # Draw cat and obstacles
                self.obstacles.draw(screen)
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


# Run the game directly if this file is executed
if __name__ == "__main__":
    # Redefine obstacle images with the new pixel art functions
    # Note: Previous obstacle generation functions are now replaced with pixel art versions

    # Reload OBSTACLE_IMAGES before creating Game instance
    OBSTACLE_IMAGES = load_obstacle_images()

    # Create and run the game
    game = Game()
    game.run()
