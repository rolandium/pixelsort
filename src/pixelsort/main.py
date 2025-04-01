from PIL import Image
import numpy as np
from gui import GUI
from pixelsorter import PixelSorter
from vectorfield import VectorField

def main():
    # ps = PixelSorter()
    # ps.image = Image.open('/home/roland/pixelsort/src/pixelsort/lenna.png').convert("RGB")
    # print(np.array(ps.image).shape)
    # sorted = ps.sortImage()
    # sorted.show()
    vf = VectorField(256,256)
    vf.move_towards_point(256/2,256/2)
    vf.line_transform(0,0,256,256,50,60)
    vf.line_transform(256,256/2,256/2,256,50,60)
    vf.output_hsv_image()

if __name__ == "__main__":
    main()