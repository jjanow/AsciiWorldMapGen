"""World generation tool with ASCII and graphical output."""

from __future__ import annotations

import argparse
import math
import random
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
        lines = []
        for row in heightmap:
            line = []
            for h in row:
                if h < 0.3:
                    line.append("\x1b[34m~\x1b[0m")  # blue water
                elif h < 0.5:
                    line.append("\x1b[33m.\x1b[0m")  # sand
                elif h < 0.7:
                    line.append("\x1b[32m,\x1b[0m")  # grass
                else:
                    line.append("\x1b[37m^\x1b[0m")  # mountain
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
    parser.add_argument("--width", type=int, default=80, help="Map width")
    parser.add_argument("--height", type=int, default=40, help="Map height")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--scale", type=float, default=0.1, help="Noise scale")
    parser.add_argument("--output", default="world.png", help="Output image path for graphics mode")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    generator = WorldGenerator(args.width, args.height, args.seed, args.scale)
    if args.mode == "ascii":
        print(generator.ascii_map())
    else:
        generator.save_image(args.output)
        print(f"Saved image to {args.output}")


if __name__ == "__main__":
    main()
