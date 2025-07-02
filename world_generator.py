"""World generation tool with ASCII and graphical output."""

from __future__ import annotations

import argparse
import math
import random
import shutil
import sys
from typing import Tuple, TYPE_CHECKING

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
    """Generate world maps using Perlin noise."""

    def __init__(self, width: int = 80, height: int = 40, seed: int | None = None, scale: float = 0.1):
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive")
        self.width = width
        self.height = height
        self.seed = seed or random.randint(0, 100000)
        self.scale = scale
        self.random = random.Random(self.seed)

    def _noise(self, x: float, y: float) -> float:
        if pnoise2 is None:
            # fallback simple noise using random seeded per coordinate
            self.random.seed(int(x * 1000) ^ int(y * 1000) ^ self.seed)
            return self.random.random()
        return pnoise2(x * self.scale, y * self.scale, octaves=6, repeatx=1024, repeaty=1024, base=self.seed)

    def generate_heightmap(self) -> list[list[float]]:
        return [[self._noise(x, y) * 0.5 + 0.5 for x in range(self.width)] for y in range(self.height)]

    def ascii_map(self) -> str:
        """
        Generate an ANSI-colored ASCII map in the style of Dwarf Fortress.
        Biomes and features are determined by height, dryness, latitude, and noise.
        """
        heightmap: list[list[float]] = self.generate_heightmap()
        dryness_noise: list[list[float]] = [
            [self._noise(x + 1024, y + 1024) * 0.5 + 0.5 for x in range(self.width)]
            for y in range(self.height)
        ]
        river_noise: list[list[float]] = [
            [abs(self._noise(x + 2048, y + 2048)) for x in range(self.width)]
            for y in range(self.height)
        ]
        road_noise: list[list[float]] = [
            [abs(self._noise(x + 4096, y + 4096)) for x in range(self.width)]
            for y in range(self.height)
        ]
        feature_noise: list[list[float]] = [
            [self._noise(x + 8192, y + 8192) * 0.5 + 0.5 for x in range(self.width)]
            for y in range(self.height)
        ]

        lines: list[str] = []
        for y, row in enumerate(heightmap):
            lat: float = y / (self.height - 1)
            lat_factor: float = 1 - abs(lat - 0.5) * 2  # -1 (pole) to 1 (equator)
            line: list[str] = []
            for x, h in enumerate(row):
                base_d: float = dryness_noise[y][x]
                # Blend dryness with latitude for climate zones
                d: float = min(1.0, base_d * 0.6 + lat_factor * 0.4)
                r: float = river_noise[y][x]
                road: float = road_noise[y][x]
                f: float = feature_noise[y][x]
                char: str = ""

                # --- Terrain and Biome Logic ---
                if h < 0.28:
                    # Deep ocean
                    char = "\x1b[34m~\x1b[0m"
                elif h < 0.32:
                    # Shallow water/coast
                    char = "\x1b[36m≈\x1b[0m"
                elif r < 0.018 and h >= 0.33 and d < 0.7:
                    # River
                    char = "\x1b[96m≋\x1b[0m"
                elif h > 0.88 and f > 0.93:
                    # Volcano
                    char = "\x1b[31m⛰\x1b[0m"
                elif h >= 0.80:
                    # High mountains
                    char = "\x1b[37m▲\x1b[0m"
                elif h >= 0.70:
                    # Foothills
                    char = "\x1b[37m^\x1b[0m"
                elif d > 0.78 and h > 0.35:
                    # Desert
                    char = "\x1b[33m░\x1b[0m"
                elif lat < 0.13 and h > 0.33:
                    # Arctic tundra (north pole)
                    char = "\x1b[37m^\x1b[0m"
                elif lat > 0.87 and h > 0.33:
                    # Antarctic tundra (south pole)
                    char = "\x1b[37m^\x1b[0m"
                elif d < 0.32 and 0.33 < h < 0.7 and lat_factor > 0.2:
                    # Swamp
                    char = "\x1b[92m#\x1b[0m"
                elif d < 0.45 and 0.33 < h < 0.7 and lat_factor > 0.1:
                    # Forest
                    char = "\x1b[32mn\x1b[0m"
                elif d < 0.60 and 0.33 < h < 0.7:
                    # Grassland
                    char = "\x1b[32m,\x1b[0m"
                elif d < 0.75 and 0.33 < h < 0.7:
                    # Plains
                    char = "\x1b[32m.\x1b[0m"
                elif road > 0.48 and road < 0.52 and h > 0.33:
                    # Road
                    char = "\x1b[90m═\x1b[0m"
                elif f > 0.78 and 0.4 < h < 0.7 and d < 0.7:
                    # City
                    char = "\x1b[35m¤\x1b[0m"
                else:
                    # Default land
                    char = "\x1b[32m·\x1b[0m"
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
