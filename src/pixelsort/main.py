from PIL import Image
import numpy as np
from pixelsort.gui import GUI
from pixelsort.pixelsorter import PixelSorter

def main():
    ps = PixelSorter()
    ps.image = Image.open('/home/roland/pixelsort/src/pixelsort/mountains.png').convert("RGB")
    print(np.array(ps.image).shape)
    sorted = ps.sortImage()
    sorted.show()

if __name__ == "__main__":
    main()