"""World generation tool with ASCII and graphical output."""

from __future__ import annotations

import argparse
import math
import random
import shutil
import sys
from typing import Tuple, TYPE_CHECKING, List, Set

# Try to import noise library for Perlin noise
try:
    from noise import pnoise2
except ImportError:  # pragma: no cover - fallback if noise isn't available
    pnoise2 = None

# Try to import PIL for image generation
try:
    from PIL import Image
    if TYPE_CHECKING:
        from PIL.Image import Image as PILImage
except ImportError:  # pragma: no cover - should raise at runtime when graphics selected
    Image = None
    if TYPE_CHECKING:
        PILImage = None


class WorldGenerator:
    """Generate world maps using Perlin noise and advanced continent/mountain/biome logic."""

    def __init__(self, width: int = 80, height: int = 40, seed: int | None = None, scale: float = 0.1):
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive")
        self.width = width
        self.height = height
        self.seed = seed or random.randint(0, 100000)
        self.scale = scale
        self.random = random.Random(self.seed)

    def _perlin(self, x: float, y: float, scale: float, octaves: int = 1, base: int = 0) -> float:
        if pnoise2 is None:
            self.random.seed(int(x * 1000) ^ int(y * 1000) ^ self.seed ^ base)
            return self.random.random()
        val = pnoise2(x * scale, y * scale, octaves=octaves, repeatx=4096, repeaty=4096, base=self.seed + base)
        if val is None:
            return 0.0
        return val

    def generate_heightmap(self) -> List[List[float]]:
        """
        Generate a heightmap with continent mask and layered noise for realistic landmasses.
        """
        heightmap: List[List[float]] = []
        for y in range(self.height):
            row: List[float] = []
            for x in range(self.width):
                nx = x / self.width - 0.5
                ny = y / self.height - 0.5
                # Continent mask: large scale, centered
                continent = self._perlin(nx, ny, scale=0.7, octaves=2, base=100) * 0.7
                # Small scale details
                detail = self._perlin(nx, ny, scale=3.0, octaves=6, base=200) * 0.3
                # Edge falloff (to create more ocean at map edges)
                dist = math.sqrt(nx * nx + ny * ny) / 0.7
                edge = max(0.0, 1.0 - dist)
                h = continent + detail
                h = h * edge + 0.15 * edge  # More land in center
                # Normalize to 0..1
                h = (h + 1) / 2
                if h is None:
                    h = 0.0
                row.append(h)
            assert isinstance(row, list), f"Row {y} in heightmap is not a list: {row}"
            heightmap.append(row)
        assert all(isinstance(r, list) for r in heightmap), "Heightmap contains non-list rows"
        return heightmap

    def _generate_moisture(self) -> List[List[float]]:
        """Generate a moisture map for biome assignment."""
        moisture: List[List[float]] = []
        for y in range(self.height):
            row: List[float] = []
            for x in range(self.width):
                m = self._perlin(x / self.width, y / self.height, scale=2.0, octaves=4, base=300) * 0.5 + 0.5
                if m is None:
                    m = 0.0
                row.append(m)
            assert isinstance(row, list), f"Row {y} in moisture is not a list: {row}"
            moisture.append(row)
        assert all(isinstance(r, list) for r in moisture), "Moisture map contains non-list rows"
        return moisture

    def _find_rivers(self, heightmap: List[List[float]], num_rivers: int = 12) -> Set[Tuple[int, int]]:
        """
        Generate river paths by simulating water flow from high elevation to sea.
        Returns a set of (x, y) coordinates for river tiles.
        """
        rivers: Set[Tuple[int, int]] = set()
        for _ in range(num_rivers):
            # Start at a random high elevation point
            attempts = 0
            while attempts < 100:
                x = self.random.randint(0, self.width - 1)
                y = self.random.randint(0, self.height - 1)
                if heightmap[y][x] > 0.7:
                    break
                attempts += 1
            else:
                continue
            path = []
            for _ in range(self.width + self.height):
                path.append((x, y))
                rivers.add((x, y))
                # Find lowest neighbor
                min_h = heightmap[y][x]
                next_x, next_y = x, y
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if heightmap[ny][nx] < min_h:
                            min_h = heightmap[ny][nx]
                            next_x, next_y = nx, ny
                if (next_x, next_y) == (x, y) or heightmap[next_y][next_x] < 0.28:
                    break  # Reached sea or local minimum
                x, y = next_x, next_y
        return rivers

    def ascii_map(self) -> str:
        """
        Generate an ANSI-colored ASCII map in the style of Dwarf Fortress, with improved continents, mountains, rivers, and biomes.
        """
        heightmap = self.generate_heightmap()
        moisture = self._generate_moisture()
        rivers = self._find_rivers(heightmap)
        assert all(isinstance(row, list) for row in heightmap), "Heightmap contains non-list rows in ascii_map"
        assert all(isinstance(row, list) for row in moisture), "Moisture map contains non-list rows in ascii_map"
        lines: List[str] = []
        for y in range(self.height):
            lat = y / (self.height - 1)
            lat_factor = 1 - abs(lat - 0.5) * 2  # -1 (pole) to 1 (equator)
            line: List[str] = []
            if heightmap[y] is None:
                raise RuntimeError(f"heightmap[{y}] is None")
            if moisture[y] is None:
                raise RuntimeError(f"moisture[{y}] is None")
            for x in range(self.width):
                if heightmap[y][x] is None:
                    raise RuntimeError(f"heightmap[{y}][{x}] is None")
                if moisture[y][x] is None:
                    raise RuntimeError(f"moisture[{y}][{x}] is None")
                h = heightmap[y][x]
                m = moisture[y][x]
                is_river = (x, y) in rivers
                char = ""
                # --- Terrain and Biome Logic ---
                if h < 0.28:
                    char = "\x1b[34m~\x1b[0m"  # Deep ocean
                elif h < 0.32:
                    char = "\x1b[36m≈\x1b[0m"  # Shallow water/coast
                elif is_river:
                    char = "\x1b[96m≋\x1b[0m"  # River
                elif h > 0.88:
                    char = "\x1b[37m▲\x1b[0m"  # High mountains
                elif h > 0.78:
                    char = "\x1b[37m^\x1b[0m"  # Foothills
                elif lat < 0.13 and h > 0.33:
                    char = "\x1b[37m^\x1b[0m"  # Arctic tundra (north pole)
                elif lat > 0.87 and h > 0.33:
                    char = "\x1b[37m^\x1b[0m"  # Antarctic tundra (south pole)
                elif m > 0.78 and h > 0.35:
                    char = "\x1b[33m░\x1b[0m"  # Desert
                elif m < 0.32 and 0.33 < h < 0.7 and lat_factor > 0.2:
                    char = "\x1b[92m#\x1b[0m"  # Swamp
                elif m < 0.45 and 0.33 < h < 0.7 and lat_factor > 0.1:
                    char = "\x1b[32mn\x1b[0m"  # Forest
                elif m < 0.60 and 0.33 < h < 0.7:
                    char = "\x1b[32m,\x1b[0m"  # Grassland
                elif m < 0.75 and 0.33 < h < 0.7:
                    char = "\x1b[32m.\x1b[0m"  # Plains
                else:
                    char = "\x1b[32m·\x1b[0m"  # Default land
                line.append(char)
            lines.append("".join(line))
        return "\n".join(lines)

    def save_image(self, path: str) -> None:
        if Image is None:
            raise RuntimeError("Pillow is required for graphics mode")
        heightmap = self.generate_heightmap()
        img = Image.new("RGB", (self.width, self.height))
        pixels = img.load()
        for y, row in enumerate(heightmap):
            for x, h in enumerate(row):
                if h < 0.3:
                    color = (0, 0, int(200 + 55 * h / 0.3))
                elif h < 0.5:
                    color = (194, 178, 128)  # sand
                elif h < 0.7:
                    green = int(120 + 80 * (h - 0.5) / 0.2)
                    color = (34, green, 34)
                else:
                    gray = int(180 + 75 * (h - 0.7) / 0.3)
                    gray = min(gray, 255)
                    color = (gray, gray, gray)
                pixels[x, y] = color
        img = img.resize((self.width * 4, self.height * 4), Image.Resampling.NEAREST)
        img.save(path)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate world maps in ASCII or graphics.")
    parser.add_argument("mode", choices=["ascii", "graphics"], help="Output mode")
    parser.add_argument("--width", type=int, default=None, help="Map width")
    parser.add_argument("--height", type=int, default=None, help="Map height")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--scale", type=float, default=0.1, help="Noise scale")
    parser.add_argument("--output", default="world.png", help="Output image path for graphics mode")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.width is None or args.height is None:
        size = shutil.get_terminal_size(fallback=(80, 24))
        width = args.width or size.columns
        height = args.height or size.lines - 1
    else:
        width = args.width
        height = args.height

    generator = WorldGenerator(width, height, args.seed, args.scale)
    if args.mode == "ascii":
        try:
            sys.stdout.write(generator.ascii_map() + "\n")
        except BrokenPipeError:
            # stdout was closed (e.g. piped command like `head`)
            pass
    else:
        generator.save_image(args.output)
        print(f"Saved image to {args.output}")


if __name__ == "__main__":
    main()
