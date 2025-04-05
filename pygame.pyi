from typing import Any, Tuple, List, Dict, Callable, Union, Optional, Sequence

# Core pygame functionality
def init() -> Tuple[int, int]: ...
def quit() -> None: ...
def get_init() -> bool: ...

# Time management
def time() -> Any: ...

class Clock:
    def tick(self, framerate: int) -> int: ...
    def get_fps(self) -> float: ...
    def get_time(self) -> int: ...

# Display functions
class display:
    @staticmethod
    def set_mode(
        resolution: Tuple[int, int], flags: int = ..., depth: int = ...
    ) -> Surface: ...
    @staticmethod
    def flip() -> None: ...
    @staticmethod
    def update(
        rectangle: Optional[
            Union[Tuple[int, int, int, int], List[Tuple[int, int, int, int]]]
        ] = ...,
    ) -> None: ...
    @staticmethod
    def get_surface() -> Surface: ...
    @staticmethod
    def set_caption(title: str, icontitle: Optional[str] = ...) -> None: ...

# Surface class for drawing
class Surface:
    def __init__(
        self, size: Tuple[int, int], flags: int = ..., depth: int = ...
    ) -> None: ...
    def blit(
        self,
        source: Surface,
        dest: Union[Tuple[int, int], Sequence[int]],
        area: Optional[Sequence[int]] = ...,
        special_flags: int = ...,
    ) -> Any: ...
    def convert(self) -> Surface: ...
    def convert_alpha(self) -> Surface: ...
    def fill(self, color: Tuple[int, int, int]) -> None: ...
    def get_rect(self, **kwargs: Any) -> Rect: ...

# Rectangle class
class Rect:
    x: int
    y: int
    width: int
    height: int
    top: int
    left: int
    bottom: int
    right: int
    topleft: Tuple[int, int]
    bottomleft: Tuple[int, int]
    topright: Tuple[int, int]
    bottomright: Tuple[int, int]
    midtop: Tuple[int, int]
    midleft: Tuple[int, int]
    midbottom: Tuple[int, int]
    midright: Tuple[int, int]
    center: Tuple[int, int]
    centerx: int
    centery: int
    size: Tuple[int, int]
    width: int
    height: int

    def __init__(self, left: int, top: int, width: int, height: int) -> None: ...
    def copy(self) -> Rect: ...
    def move(self, x: int, y: int) -> Rect: ...
    def inflate(self, x: int, y: int) -> Rect: ...
    def colliderect(self, rect: Rect) -> bool: ...
    def collidepoint(self, x: int, y: int) -> bool: ...
    def collidelist(self, list: List[Rect]) -> int: ...

# Event handling
class event:
    @staticmethod
    def get() -> List[Any]: ...
    @staticmethod
    def poll() -> Any: ...
    @staticmethod
    def wait() -> Any: ...
    @staticmethod
    def clear() -> None: ...

# Key handling
class key:
    @staticmethod
    def get_pressed() -> List[bool]: ...
    @staticmethod
    def get_mods() -> int: ...
    @staticmethod
    def set_mods(int) -> None: ...

# Constants
QUIT: int
MOUSEBUTTONDOWN: int
MOUSEBUTTONUP: int
MOUSEMOTION: int
KEYDOWN: int
KEYUP: int
K_ESCAPE: int
K_RETURN: int
K_SPACE: int
K_LEFT: int
K_RIGHT: int
K_UP: int
K_DOWN: int
K_r: int
SRCALPHA: int

# Drawing functions
def draw_rect(
    surface: Surface,
    color: Tuple[int, int, int],
    rect: Union[Tuple[int, int, int, int], Rect],
    width: int = ...,
) -> Rect: ...
def draw_circle(
    surface: Surface,
    color: Tuple[int, int, int],
    center: Tuple[int, int],
    radius: int,
    width: int = ...,
) -> Rect: ...
def draw_line(
    surface: Surface,
    color: Tuple[int, int, int],
    start_pos: Tuple[int, int],
    end_pos: Tuple[int, int],
    width: int = ...,
) -> Rect: ...
def draw_lines(
    surface: Surface,
    color: Tuple[int, int, int],
    closed: bool,
    points: List[Tuple[int, int]],
    width: int = ...,
) -> Rect: ...
def draw_polygon(
    surface: Surface,
    color: Tuple[int, int, int],
    points: List[Tuple[int, int]],
    width: int = ...,
) -> Rect: ...
def draw_ellipse(
    surface: Surface,
    color: Tuple[int, int, int],
    rect: Union[Tuple[int, int, int, int], Rect],
    width: int = ...,
) -> Rect: ...

# Sprite classes
class sprite:
    class Sprite:
        def __init__(self, *groups: Any) -> None: ...
        def update(self, *args: Any) -> None: ...
        def kill(self) -> None: ...

    class Group:
        def __init__(self, *sprites: Sprite) -> None: ...
        def add(self, *sprites: Sprite) -> None: ...
        def remove(self, *sprites: Sprite) -> None: ...
        def update(self, *args: Any) -> None: ...
        def draw(self, surface: Surface) -> List[Rect]: ...
        def empty(self) -> None: ...

    @staticmethod
    def spritecollide(
        sprite: Sprite, group: Group, dokill: bool, collided: Optional[Callable] = ...
    ) -> List[Sprite]: ...

# Font rendering
class font:
    @staticmethod
    def init() -> None: ...
    @staticmethod
    def SysFont(name: str, size: int, bold: bool = ..., italic: bool = ...) -> Font: ...
    @staticmethod
    def Font(filename: Optional[str], size: int) -> Font: ...

    class Font:
        def render(
            self,
            text: str,
            antialias: bool,
            color: Tuple[int, int, int],
            background: Optional[Tuple[int, int, int]] = ...,
        ) -> Surface: ...
        def size(self, text: str) -> Tuple[int, int]: ...
        def get_height(self) -> int: ...
        def get_linesize(self) -> int: ...

# Drawing module
class draw:
    @staticmethod
    def rect(
        surface: Surface,
        color: Tuple[int, int, int],
        rect: Union[Tuple[int, int, int, int], Rect],
        width: int = ...,
    ) -> Rect: ...
    @staticmethod
    def circle(
        surface: Surface,
        color: Tuple[int, int, int],
        center: Tuple[int, int],
        radius: int,
        width: int = ...,
    ) -> Rect: ...
    @staticmethod
    def line(
        surface: Surface,
        color: Tuple[int, int, int],
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        width: int = ...,
    ) -> Rect: ...
    @staticmethod
    def lines(
        surface: Surface,
        color: Tuple[int, int, int],
        closed: bool,
        points: List[Tuple[int, int]],
        width: int = ...,
    ) -> Rect: ...
    @staticmethod
    def polygon(
        surface: Surface,
        color: Tuple[int, int, int],
        points: List[Tuple[int, int]],
        width: int = ...,
    ) -> Rect: ...
    @staticmethod
    def ellipse(
        surface: Surface,
        color: Tuple[int, int, int],
        rect: Union[Tuple[int, int, int, int], Rect],
        width: int = ...,
    ) -> Rect: ...
