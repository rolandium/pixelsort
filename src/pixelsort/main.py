from PIL import Image
import numpy as np
from pixelsort.gui import GUI
from pixelsort.pixelsorter import PixelSorter
from pixelsort.vectorfield import VectorField

def main():
    # ps = PixelSorter()
    # ps.image = Image.open('/home/roland/pixelsort/src/pixelsort/lenna.png').convert("RGB")
    # print(np.array(ps.image).shape)
    # sorted = ps.sortImage()
    # sorted.show()
    width = 256
    height = 256
    vf = VectorField(width,height)
    strength = 2
    distance = 40
    mode = "linear"
    tl = (0,0)
    tr = (width,0)
    bl = (0,height)
    br = (width,height)
    wm = width/2
    hm = height/2
    vf.move_towards_point((wm,hm))
    vf.spline_transform(tl,tr,br,bl,100,strength/10,distance,"exponential")
    # vf.spline_transform(br,bl,tl,tr,100,strength,distance,mode)
    # vf.line_transform((width/2,0),(width/2,height),strength,distance,"gaussian")
    # vf.line_transform((0,0),(256,256),strength,distance,mode)
    # vf.line_transform((0,256/2),(256,256/2),strength+1,distance,mode)
    # vf.line_transform(256,256/2,256/2,256,strength,distance)
    vf.output_hsv_image()

if __name__ == "__main__":
    main()