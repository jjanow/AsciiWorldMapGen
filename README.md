# AsciiWorldMapGen

A Python tool to generate colorful world maps. The maps can be produced as
ANSI colored ASCII text in the style of Dwarf Fortress or saved as a PNG image.

## Requirements

The optional `noise` library is used to generate Perlin noise. If it is not
available, random noise is used instead. Pillow is required for graphics mode.
Install them with:

```bash
pip install noise Pillow
```

## Usage

Generate an ASCII world map:

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
