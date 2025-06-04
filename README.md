# AsciiWorldMapGen

A Python tool to generate colorful world maps. The maps can be produced as
ANSI colored ASCII text in the style of Dwarf Fortress or saved as a PNG image.
The ASCII output now includes features such as deserts, rivers, volcanoes,
roads and cities using extended characters for extra flair. The generator uses
a latitudinal climate gradient combined with noise-based variation so biomes
appear in larger, more coherent regions similar to classic roguelike worlds.

## Requirements

The optional `noise` library is used to generate Perlin noise. If it is not
available, random noise is used instead. Pillow is required for graphics mode.
Install them with:

```bash
pip install noise Pillow
```

## Usage

Generate an ASCII world map (defaults to your terminal size when width and
height are not specified):

```bash
python world_generator.py ascii
```
You can still specify `--width` and `--height` if desired:
```bash
python world_generator.py ascii --width 80 --height 40
```

Generate a PNG image:

```bash
python world_generator.py graphics --width 200 --height 100 --output map.png
```

You can also provide a random seed and adjust the scale of the noise to produce
consistent results:

```bash
python world_generator.py ascii --seed 123 --scale 0.05
```
