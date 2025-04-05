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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize pygame
pygame.init()

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
clock = pygame.time.Clock()  # Fixed linter error: proper instantiation

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

        # Create procedural blue background layers
        print("Creating procedural blue sky background.")
        self.create_blue_background_layers()

    def load_background_layers(self):
        """Load background image layers for the parallax effect."""
        # List of all the background layers we want to load
        bg_files = [
            "parallax-mountain-bg.png",
            "parallax-mountain-mountain-far.png",
            "parallax-mountain-mountains.png",
            "parallax-mountain-trees.png",
            "parallax-mountain-foreground-trees.png",
        ]

        self.layers = []

        # Relative path to the background assets
        base_path = "assets/backgrounds/mountain_dusk"

        # Load each layer with error handling for each file
        for filename in bg_files:
            try:
                # Construct the full path
                file_path = os.path.join(base_path, filename)

                # Load the image and scale it to match the game window
                layer = pygame.image.load(file_path).convert_alpha()

                # Scale the image to the game dimensions, preserving aspect ratio
                aspect_ratio = layer.get_width() / layer.get_height()
                new_height = HEIGHT
                new_width = int(new_height * aspect_ratio)

                # If the image is too narrow, scale based on width instead
                if new_width < WIDTH * 2:
                    new_width = WIDTH * 2
                    new_height = int(new_width / aspect_ratio)

                # Scale the image
                layer = pygame.transform.scale(layer, (new_width, new_height))

                # Add the layer to our list
                self.layers.append(layer)
                print(f"Loaded background layer: {filename}")

            except Exception as e:
                print(f"Error loading background layer {filename}: {e}")
                # If we fail to load any layer, use our procedural layers instead
                self.create_blue_background_layers()
                return

        # If we have fewer layers than speeds, adjust the speeds
        if len(self.layers) < len(self.scroll_speeds):
            self.scroll_speeds = self.scroll_speeds[: len(self.layers)]

        # If we have more layers than speeds, add more speeds
        while len(self.scroll_speeds) < len(self.layers):
            self.scroll_speeds.append(self.scroll_speeds[-1] * 1.5)

        # Initialize scroll positions for each layer
        self.scroll_positions = [0] * len(self.layers)

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
            }
            logger.info("Cat animations loaded successfully")
        except Exception as e:
            logger.error(f"Error loading cat animations: {e}")
            # Create fallback animations with colored rectangles
            fallback = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.rect(fallback, (255, 0, 0), fallback.get_rect())  # Red
            self.animations = {
                state: [fallback] for state in ["idle", "run", "jump", "fall", "dead"]
            }

        # Set initial animation state
        self.current_animation = "idle"
        self.frame_index = 0
        self.animation_timer = 0

        # Set initial image and rect
        self.image = self.animations[self.current_animation][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.bottomleft = (100, GROUND_LEVEL)

        # Physics attributes
        self.velocity_y = 0
        self.on_ground = True
        self.is_dead = False

    def jump(self):
        """Make the cat jump if it's on the ground."""
        if self.on_ground and not self.is_dead:
            # Create jump particles at the cat's feet
            game_instance = Game.get_instance()
            if game_instance:
                game_instance.particle_system.add_jump_particles(
                    self.rect.centerx, self.rect.bottom
                )

            self.velocity_y = JUMP_FORCE
            self.on_ground = False
            self.current_animation = "jump"
            self.frame_index = 0

    def die(self):
        """Change to death animation when the cat dies."""
        if not self.is_dead:
            # Create impact particles
            game_instance = Game.get_instance()
            if game_instance:
                game_instance.particle_system.add_impact_particles(
                    self.rect.centerx, self.rect.centery
                )

            self.is_dead = True
            self.current_animation = "dead"
            self.frame_index = 0

    def update_animation(self):
        """Update the cat's animation frame."""
        # Increment animation timer
        self.animation_timer += 1

        # Change frame when timer reaches threshold
        if self.animation_timer >= ANIMATION_SPEED:
            self.animation_timer = 0

            # Determine appropriate animation based on state
            if self.is_dead:
                self.current_animation = "dead"
            elif not self.on_ground:
                if self.velocity_y < 0:
                    self.current_animation = "jump"
                else:
                    self.current_animation = "fall"
            else:
                # When on ground and not dead, use running animation
                self.current_animation = "run"

            # Update frame index, looping back if needed
            # For death animation, stay on last frame
            if (
                self.current_animation == "dead"
                and self.frame_index >= len(self.animations[self.current_animation]) - 1
            ):
                self.frame_index = len(self.animations[self.current_animation]) - 1
            else:
                self.frame_index = (self.frame_index + 1) % len(
                    self.animations[self.current_animation]
                )

            # Update the image
            self.image = self.animations[self.current_animation][self.frame_index]

    def update(self):
        """Update the cat's position and animation."""
        if not self.is_dead:
            # Apply gravity
            self.velocity_y += GRAVITY
            self.rect.y += self.velocity_y

            # Check if cat is on ground
            if self.rect.bottom >= GROUND_LEVEL:
                self.rect.bottom = GROUND_LEVEL
                self.velocity_y = 0
                self.on_ground = True

        # Update animation regardless of movement status
        self.update_animation()


# Obstacle class
class Obstacle(pygame.sprite.Sprite):
    """Obstacles that the cat must jump over or avoid."""

    def __init__(self):
        super().__init__()

        # Choose obstacle type with more naturalistic options
        obstacle_types = ["stone", "cactus", "bush", "balloon"]

        # Adjust probabilities: make balloon rarer (it requires different gameplay)
        weights = [0.3, 0.3, 0.25, 0.15]  # stone, cactus, bush, balloon
        obstacle_type = random.choices(obstacle_types, weights=weights, k=1)[0]

        # Use the appropriate image based on type
        if obstacle_type == "stone":
            self._setup_stone_obstacle()
        elif obstacle_type == "cactus":
            self._setup_cactus_obstacle()
        elif obstacle_type == "bush":
            self._setup_bush_obstacle()
        elif obstacle_type == "balloon":
            self._setup_balloon_obstacle()
        else:
            # Fallback to stone if something goes wrong
            self._setup_stone_obstacle()
            obstacle_type = "stone"

        self.obstacle_type = obstacle_type

        # Randomize speed slightly for more variety
        self.speed = OBSTACLE_SPEED + random.uniform(-0.5, 0.5)
        self.already_passed = False

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
        self.width = random.randint(80, 150)
        self.height = random.randint(40, 70)
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Draw cloud with smoother, blue-tinted color
        # Create varying shades of blue clouds - some darker, some lighter
        cloud_base_color = random.choice(
            [
                (150, 170, 230, 200),  # Light blue-purple, semi-transparent
                (130, 160, 220, 200),  # Mid blue, semi-transparent
                (170, 200, 255, 200),  # Very light blue, semi-transparent
                (100, 140, 210, 200),  # Darker blue, semi-transparent
            ]
        )

        # Draw main cloud body
        pygame.draw.ellipse(
            self.image,
            cloud_base_color,
            (0, self.height // 4, self.width // 1.5, self.height // 1.5),
        )
        pygame.draw.ellipse(
            self.image,
            cloud_base_color,
            (self.width // 3, self.height // 6, self.width // 2, self.height // 1.2),
        )
        pygame.draw.ellipse(
            self.image,
            cloud_base_color,
            (self.width // 2, self.height // 3, self.width // 2.5, self.height // 1.5),
        )

        # Soften the edges with small circles and add highlights
        lighter_color = (
            min(cloud_base_color[0] + 30, 255),
            min(cloud_base_color[1] + 30, 255),
            min(cloud_base_color[2] + 30, 255),
            cloud_base_color[3],
        )

        for _ in range(7):
            x = random.randint(0, self.width - 20)
            y = random.randint(5, self.height - 20)
            radius = random.randint(8, 18)

            # Use lighter color on the top side of clouds
            use_color = lighter_color if y < self.height // 2 else cloud_base_color
            pygame.draw.circle(self.image, use_color, (x, y), radius)

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
        """Load game sound effects."""
        self.sounds = {}
        try:
            # Create a sounds directory if it doesn't exist
            if not os.path.exists("assets/sounds"):
                os.makedirs("assets/sounds")

            # We'll implement actual sound loading when we have sound files
            # For now, we'll just set up the structure
            self.sounds_enabled = True
        except Exception as e:
            logger.error(f"Error loading sounds: {e}")
            self.sounds_enabled = False

    def play_sound(self, sound_name):
        """Play a sound effect if sounds are enabled."""
        if self.sounds_enabled and sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except Exception as e:
                logger.error(f"Error playing sound {sound_name}: {e}")

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
            "Avoid balloons (don't jump)",
            "Press R to restart after game over",
            "Press any key to start",
        ]

        for i, line in enumerate(instructions):
            text = self.font.render(line, True, BLACK)
            rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + i * 40))
            screen.blit(text, rect)

        # Display high score
        if self.high_score > 0:
            high_score_text = self.font.render(
                f"High Score: {self.high_score}", True, (100, 50, 150)
            )
            high_score_rect = high_score_text.get_rect(
                center=(WIDTH // 2, HEIGHT // 2 + len(instructions) * 40 + 20)
            )
            screen.blit(high_score_text, high_score_rect)

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
        if not self.cat.is_dead:
            for obstacle in self.obstacles:
                if self.cat.rect.colliderect(obstacle.rect):
                    # Special handling for balloon - only die if the cat is jumping
                    if obstacle.obstacle_type == "balloon":
                        if not self.cat.on_ground:  # Cat is jumping and hit balloon
                            self.game_over = True
                            self.cat.die()
                            self.play_sound("hit")
                    else:
                        # For all other obstacles, die on collision
                        self.game_over = True
                        self.cat.die()
                        self.play_sound("hit")

    def update_score(self):
        """Update the score when obstacles are passed."""
        for obstacle in self.obstacles:
            if obstacle.rect.right < self.cat.rect.left and not obstacle.already_passed:
                # Add base score
                score_to_add = 1

                # Give bonus points for balloon obstacles as they're harder to avoid
                if obstacle.obstacle_type == "balloon":
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

                self.score += score_to_add
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
                    elif event.key == pygame.K_SPACE and not self.game_over:
                        self.cat.jump()
                        self.play_sound("jump")
                    elif event.key == pygame.K_r and self.game_over:
                        self.reset()
                    elif event.key == pygame.K_m:  # Mute toggle
                        self.sounds_enabled = not self.sounds_enabled

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
            elif self.game_over:
                # When game over, still update the cat for death animation
                self.cat.update()
                self.clouds.update()
                # Background still moves a bit even when game over
                self.background.update()

                # Check for high score
                if self.score > self.high_score:
                    self.high_score = self.score
                    self._save_high_score()

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
