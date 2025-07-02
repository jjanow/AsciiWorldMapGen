# AsciiWorldMapGen

A Python tool to generate colorful world maps. The maps can be produced as
ANSI colored ASCII text in the style of Dwarf Fortress or saved as a PNG image.
The ASCII output now includes features such as deserts, rivers, volcanoes,
roads and cities using extended characters for extra flair. The generator uses
a latitudinal climate gradient combined with noise-based variation so biomes
appear in larger, more coherent regions similar to classic roguelike worlds.

## Requirements

### Core Dependencies
- Python 3.7+ (uses type hints and modern syntax)

### Optional Dependencies
The tool gracefully handles missing optional dependencies:

- **`noise` library**: Used for Perlin noise generation. If not available, falls back to simple random noise.
- **`Pillow` library**: Required for graphics mode (PNG output). If not available, graphics mode will fail with a clear error message.

## Installation

### Basic Installation
The tool works out of the box with just Python standard library:

```bash
# Clone or download the repository
cd AsciiWorldMapGen

# Test ASCII mode (works without additional dependencies)
python3 world_generator.py ascii
```

### Full Installation (Recommended)
For the best experience with Perlin noise and graphics support:

```bash
# Install optional dependencies
pip3 install -r requirements.txt

# Or install manually
pip3 install noise Pillow
```

## Usage

### ASCII Mode (Default)
Generate an ASCII world map (defaults to your terminal size when width and
height are not specified):

```bash
python3 world_generator.py ascii
```

You can still specify `--width` and `--height` if desired:
```bash
python3 world_generator.py ascii --width 80 --height 40
```

### Graphics Mode
Generate a PNG image (requires Pillow):

```bash
python3 world_generator.py graphics --width 200 --height 100 --output map.png
```

### Advanced Options
You can also provide a random seed and adjust the scale of the noise to produce
consistent results:

```bash
python3 world_generator.py ascii --seed 123 --scale 0.05
```

## Troubleshooting

### Linter Errors
If you see linter errors about missing imports:
- **"Import 'noise' could not be resolved"**: This is expected if the `noise` library isn't installed. The code handles this gracefully.
- **"Import 'PIL' could not be resolved"**: This is expected if Pillow isn't installed. Graphics mode will fail at runtime with a clear error.

### Runtime Errors
- **"Pillow is required for graphics mode"**: Install Pillow with `pip3 install Pillow`
- **ASCII mode works without any additional dependencies**

## Features

- **Latitudinal Climate Zones**: Realistic biome distribution based on latitude
- **Multiple Terrain Types**: Oceans, mountains, forests, deserts, swamps, tundra
- **Special Features**: Rivers, roads, cities, volcanoes
- **ANSI Color Support**: Rich terminal output with colors
- **Flexible Output**: ASCII for terminals, PNG for images
- **Configurable**: Adjustable size, seed, and noise scale
- **Graceful Degradation**: Works with or without optional dependencies
