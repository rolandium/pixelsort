# Curved Pixel Sorting via Simple Equations and Vector Fields

Base Image           |  Gradient Smear via Vector Field (Orbit, 25 Frames)
:-------------------------:|:-------------------------:
| ![image of mount everest, shutterstock 1589688670](samples/base_images/mountains.png) | ![orbit smear of the image](samples/out_images/mountains_orbitsmear.png) |

While most pixel sorters solve for the problem of sorted straight lines across the image, the domain of curved and other non-straight lines is not well defined. This project is an investigation into one particular way of pixelsorting an image using defined equations for dx and dy, or through per-pixel vector fields.

This is delivered using a DearPyGUI interface that allows the user to load in an image, adjust masking settings, define their pixel line transformations, and finally sort[^1] an image. 

[^1]: Note that the current implementation uses a linear min to max gradient on each pixel line, therefore the current results aren't technically pixel sorting.

## Installation

Download an executable from [releases](https://github.com/rolandium/pixelsort/releases). Or if you'd prefer to run to code yourself...

## Manual Installation

To handle dependancies, install [poetry](https://python-poetry.org/docs/), download the source code, navigate to the root folder of this project, and enter the command:

```
poetry install
```

This will handle the installation of all packages used in this project.

To run the interactive pixel sorter, navigate to the root folder of this project and enter the command:

```
poetry run python ./src/pixelsort/main.py
```

or if you're using Windows:
```
poetry run python .\src\pixelsort\main.py
```

## Usage

**explain general usage here**