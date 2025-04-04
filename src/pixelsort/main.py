from PIL import Image
import numpy as np
from pixelsort.gui import GUI
from pixelsort.pixelsorter import PixelSorter
from pixelsort.vectorfield import VectorField

def main():
    mountainIm = Image.open('/home/roland/pixelsort/src/pixelsort/mountains.png').convert("RGB")
    gui = GUI()
    #ps.image = Image.open('src/pixelsort/mountains.png').convert("RGB")
    #print(np.array(ps.image).shape)
    #sorted = ps.sortImage(80, 160)
    #sorted.show()
    w = mountainIm.width
    h = mountainIm.height
    vf = VectorField(w,h)
    strength = 50
    distance = 100
    mode = "exponential"
    tl = (0,0)
    tr = (w,0)
    bl = (0,h)
    br = (w,h)
    wm = w/2
    hm = h/2
    # vf.move_towards_point((wm,hm))
    # vf.spline_transform(tl,tr,br,bl,100,1,distance,"linear")
    # vf.spline_transform(br,bl,tl,tr,100,ustrength,distance,mode)
    vf.line_transform(tl,br,strength,distance,mode)
    vf.line_transform(tr,bl,strength,distance,mode)
    vf.line_transform((wm,h),(wm,0),strength,distance,mode)
    # vf.line_transform((0,height/2),(width,height/2),strength,distance,"exponential")
    # vf.line_transform((0,hm),(w,hm),strength,distance,"gaussian")
    # vf.line_transform((0,h/2),(w,h/2),strength+1,distance,mode)
    # vf.line_transform((wm,0),(wm,h),strength,distance,"exponential")
    vf.output_hsv_image()
    im = Image.fromarray(vf.warp_image(mountainIm,1,0.5,0.2))
    im.show()
from gui import GUI
from pixelsorter import PixelSorter

if __name__ == "__main__":
    main()