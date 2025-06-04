"""World generation tool with ASCII and graphical output."""

from __future__ import annotations

import argparse
import math
import random
import shutil
import sys
from typing import Tuple

try:
    from noise import pnoise2
except ImportError:  # pragma: no cover - fallback if noise isn't available
    pnoise2 = None

try:
    from PIL import Image
except ImportError:  # pragma: no cover - should raise at runtime when graphics selected
    Image = None


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
        heightmap = self.generate_heightmap()
        dryness_noise = [[self._noise(x + 1024, y + 1024) * 0.5 + 0.5 for x in range(self.width)]
                          for y in range(self.height)]
        river_noise = [[abs(self._noise(x + 2048, y + 2048)) for x in range(self.width)]
                       for y in range(self.height)]
        road_noise = [[abs(self._noise(x + 4096, y + 4096)) for x in range(self.width)]
                      for y in range(self.height)]
        feature_noise = [[self._noise(x + 8192, y + 8192) * 0.5 + 0.5 for x in range(self.width)]
                         for y in range(self.height)]

        lines = []
        for y, row in enumerate(heightmap):
            lat_factor = 1 - abs((y / (self.height - 1)) - 0.5) * 2
            line = []
            for x, h in enumerate(row):
                base_d = dryness_noise[y][x]
                d = min(1.0, base_d * 0.6 + lat_factor * 0.4)
                r = river_noise[y][x]
                road = road_noise[y][x]
                f = feature_noise[y][x]
                char = ""
                if h < 0.3:
                    char = "\x1b[34m~\x1b[0m"  # ocean
                elif r < 0.02 and h >= 0.35 and d < 0.7:
                    char = "\x1b[96m≋\x1b[0m"  # river
                elif h > 0.85 and f > 0.92:
                    char = "\x1b[31m⛰\x1b[0m"  # volcano
                elif h >= 0.75:
                    char = "\x1b[37m▲\x1b[0m"  # mountain
                elif road > 0.48 and road < 0.52:
                    char = "\x1b[90m═\x1b[0m"  # road
                elif f > 0.75 and 0.4 < h < 0.7 and d < 0.7:
                    char = "\x1b[35m¤\x1b[0m"  # city
                elif d > 0.7:
                    char = "\x1b[33m░\x1b[0m"  # desert
                else:
                    char = "\x1b[32m·\x1b[0m"  # grass/land
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
        img = img.resize((self.width * 4, self.height * 4), Image.NEAREST)
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
