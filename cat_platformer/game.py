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
import glob
import logging
import math
from typing import Dict, List, Tuple, Optional, Union, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
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
    """A parallax scrolling background using blue color schemes."""

    def __init__(self):
        self.layers = []
        self.load_layers()
        self.positions = [0, 0, 0, 0, 0]  # X positions for each layer
        self.speeds = [
            0.1,  # Background (sky)
            0.2,  # Far mountains
            0.4,  # Mountains
            0.7,  # Trees
            0.9,  # Foreground trees
        ]  # Different speeds for parallax effect

    def load_layers(self):
        """Load background layers from the mountain dusk background and apply blue tint."""
        try:
            # Path to the mountain dusk background layers
            layers_path = os.path.join(
                "graphics",
                "backgrounds",
                "new_backgrounds",
                "mountain_dusk",
                "parallax_mountain_pack",
                "layers",
            )

            # Layer files in order from back to front
            layer_files = [
                "parallax-mountain-bg.png",  # Sky background
                "parallax-mountain-montain-far.png",  # Far mountains
                "parallax-mountain-mountains.png",  # Middle mountains
                "parallax-mountain-trees.png",  # Trees
                "parallax-mountain-foreground-trees.png",  # Foreground trees
            ]

            loaded_any = False
            for layer_file in layer_files:
                try:
                    file_path = os.path.join(layers_path, layer_file)
                    if os.path.exists(file_path):
                        # Load the layer
                        layer = pygame.image.load(file_path).convert_alpha()

                        # Scale to fit screen height while maintaining aspect ratio
                        scale_factor = HEIGHT / layer.get_height()
                        new_width = int(
                            layer.get_width() * scale_factor * 1.5
                        )  # Make wider for better scrolling
                        layer = pygame.transform.scale(layer, (new_width, HEIGHT))

                        # Create a blue-tinted copy of the layer
                        layer_copy = layer.copy()

                        # Apply blue tint to all layers
                        for y in range(layer.get_height()):
                            for x in range(layer.get_width()):
                                color = layer.get_at((x, y))
                                if color.a > 0:  # Only process non-transparent pixels
                                    # Enhance blue component and reduce red/green
                                    r = min(int(color.r * 0.7), 255)  # Reduce red
                                    g = min(
                                        int(color.g * 0.8), 255
                                    )  # Slightly reduce green
                                    b = min(int(color.b * 1.3), 255)  # Enhance blue
                                    layer_copy.set_at((x, y), (r, g, b, color.a))

                        self.layers.append(layer_copy)
                        loaded_any = True
                        logger.info(
                            f"Loaded and blue-tinted background layer: {layer_file}"
                        )
                    else:
                        logger.warning(f"Background layer file not found: {file_path}")
                except pygame.error as e:
                    logger.error(f"Error loading background layer {layer_file}: {e}")

            if loaded_any:
                logger.info(f"Loaded {len(self.layers)} blue-tinted background layers")
            else:
                logger.warning(
                    "No background layers loaded, creating default blue background layers"
                )
                self.create_blue_background_layers()
        except Exception as e:
            logger.error(f"Error loading background layers: {e}")
            self.create_blue_background_layers()

    def create_blue_background_layers(self):
        """Create default blue-themed background layers if files aren't found."""
        # Layer 1 - Deep blue sky gradient
        layer1 = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for y in range(HEIGHT):
            # Create a blue gradient from deep blue to lighter blue
            ratio = y / HEIGHT
            r = int(30 + ratio * 60)  # Small amount of red - darker at top
            g = int(80 + ratio * 100)  # Medium amount of green - darker at top
            b = int(180 - ratio * 60)  # Lots of blue - lighter at top
            pygame.draw.line(layer1, (r, g, b), (0, y), (WIDTH, y))

        # Add stars/small white dots to the sky
        for _ in range(120):
            star_x = random.randint(0, WIDTH)
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
        layer2 = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        mountain_color = (40, 60, 120)  # Dark blue distant mountains

        for i in range(5):  # Draw 5 mountains
            mountain_width = random.randint(200, 350)
            mountain_height = random.randint(100, 180)
            mountain_x = random.randint(0, WIDTH)

            # Draw mountain
            pygame.draw.polygon(
                layer2,
                mountain_color,
                [
                    (mountain_x - mountain_width // 2, GROUND_LEVEL),
                    (mountain_x, GROUND_LEVEL - mountain_height),
                    (mountain_x + mountain_width // 2, GROUND_LEVEL),
                ],
            )

        # Layer 3 - Middle mountains (medium blue)
        layer3 = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        mid_mountain_color = (50, 80, 150)  # Medium blue mountains

        for i in range(7):  # Draw several mountains
            mountain_width = random.randint(150, 300)
            mountain_height = random.randint(80, 150)
            mountain_x = random.randint(0, WIDTH)

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

        # Layer 4 - Forest silhouette (navy blue)
        layer4 = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        tree_color = (20, 40, 100)  # Navy blue silhouette

        # Draw tree line
        for i in range(40):  # Draw many trees
            tree_x = i * (WIDTH // 20)
            tree_height = random.randint(70, 130)
            tree_width = tree_height // 2

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
        layer5 = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        fg_tree_color = (10, 20, 60)  # Dark navy blue

        for i in range(15):
            tree_x = random.randint(0, WIDTH)
            tree_height = random.randint(120, 200)
            tree_width = tree_height // 1.5

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

        # Add all layers in order of depth
        self.layers = [layer1, layer2, layer3, layer4, layer5]

    def update(self):
        """Update the positions of the background layers."""
        for i in range(len(self.layers)):
            self.positions[i] -= self.speeds[i]
            # Wrap around when needed
            if self.positions[i] <= -self.layers[i].get_width():
                self.positions[i] = 0

    def draw(self, surface):
        """Draw the background layers with parallax effect."""
        for i, layer in enumerate(self.layers):
            # Draw the layer twice to create seamless scrolling
            surface.blit(layer, (int(self.positions[i]), 0))
            surface.blit(layer, (int(self.positions[i]) + layer.get_width(), 0))


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
    """A scrolling ground with blue-themed colors."""

    def __init__(self):
        self.position = 0
        self.speed = 5  # Base speed for ground scrolling

        # Create a textured ground surface
        self.width = WIDTH * 2  # Make it wider for smooth scrolling
        self.height = HEIGHT - GROUND_LEVEL + 10  # Add a bit of overlap

        # Create the base ground surface
        self.surface = pygame.Surface((self.width, self.height))

        # Fill with blue-themed base color
        self.surface.fill((60, 100, 140))  # Cool blue base

        # Create a darker top soil layer
        pygame.draw.rect(
            self.surface,
            (45, 80, 120),  # Darker blue soil
            (0, 0, self.width, 15),
        )

        # Add natural texture with varied blue tones
        for _ in range(200):
            # Soil variations
            spot_x = random.randint(0, self.width)
            spot_y = random.randint(5, self.height)
            spot_size = random.randint(3, 12)

            # Randomly choose between dark and light blue patches
            if random.random() < 0.6:
                # Darker blue patches
                color = (
                    random.randint(35, 50),  # R
                    random.randint(60, 90),  # G
                    random.randint(100, 130),  # B
                )
            else:
                # Lighter blue patches
                color = (
                    random.randint(70, 100),  # R
                    random.randint(110, 140),  # G
                    random.randint(160, 190),  # B
                )

            pygame.draw.circle(self.surface, color, (spot_x, spot_y), spot_size)

        # Add small rocks scattered throughout - blue-gray tones
        for _ in range(40):
            rock_size = random.randint(2, 6)
            rock_x = random.randint(0, self.width)
            rock_y = random.randint(10, self.height - 10)
            rock_color = (
                random.randint(70, 90),
                random.randint(90, 120),
                random.randint(130, 160),
            )  # Blue-gray variations
            pygame.draw.circle(self.surface, rock_color, (rock_x, rock_y), rock_size)

        # Add blue-toned vegetation along the top
        for _ in range(150):
            grass_x = random.randint(0, self.width)
            grass_height = random.randint(5, 12)
            grass_width = random.randint(1, 3)

            # Blue-tinted vegetation colors
            grass_color = (
                random.randint(20, 40),
                random.randint(70, 100),
                random.randint(130, 170),
            )

            # Draw individual vegetation strands
            if random.random() < 0.7:
                # Straight strands
                pygame.draw.line(
                    self.surface,
                    grass_color,
                    (grass_x, 0),
                    (grass_x, grass_height),
                    grass_width,
                )
            else:
                # Curved strands
                pygame.draw.arc(
                    self.surface,
                    grass_color,
                    (grass_x - 5, -5, 10, 20),
                    0,
                    3.14,
                    grass_width,
                )

        # Add occasional small flowers/crystals in blue tones
        for _ in range(20):
            flower_x = random.randint(0, self.width)
            flower_y = random.randint(3, 8)

            # Choose random blue-themed crystal colors
            flower_colors = [
                (150, 200, 255),  # Light blue
                (100, 150, 255),  # Medium blue
                (70, 100, 220),  # Darker blue
                (200, 220, 255),  # White-blue
            ]
            flower_color = random.choice(flower_colors)

            # Draw tiny crystal/flower shape
            pygame.draw.circle(self.surface, flower_color, (flower_x, flower_y), 2)
            pygame.draw.circle(
                self.surface, flower_color, (flower_x - 2, flower_y + 1), 1
            )
            pygame.draw.circle(
                self.surface, flower_color, (flower_x + 2, flower_y + 1), 1
            )
            pygame.draw.circle(self.surface, flower_color, (flower_x, flower_y + 3), 1)
            # Crystal stem
            pygame.draw.line(
                self.surface,
                (40, 80, 160),
                (flower_x, flower_y + 3),
                (flower_x, flower_y + 7),
                1,
            )

        # Define top edge more clearly
        pygame.draw.line(self.surface, (30, 60, 100), (0, 0), (self.width, 0), 2)

    def update(self, speed_factor=1.0):
        """Update ground position based on game speed."""
        self.position -= self.speed * speed_factor
        if self.position <= -self.width // 2:
            self.position = 0

    def draw(self, surface):
        """Draw the scrolling ground."""
        # Draw ground at current position and repeated for seamless scrolling
        surface.blit(self.surface, (int(self.position), GROUND_LEVEL))
        surface.blit(self.surface, (int(self.position + self.width // 2), GROUND_LEVEL))


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
            # Fade out near the end of life
            alpha = (
                min(255, int(255 * popup["life"] / 20)) if popup["life"] < 20 else 255
            )
            color = popup["color"]

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
                speed_factor = self.current_speed / OBSTACLE_SPEED
                self.ground.update(speed_factor)

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
