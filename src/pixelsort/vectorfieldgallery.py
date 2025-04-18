import os
import numpy as np
from PIL import Image
from pixelsort.vectorfield import Vector, VectorField

DIRECTORY = "vector_fields"

class VectorFieldGallery:
    def __init__(self, directory=DIRECTORY):
        self.directory = directory
        self.index = {}
        self._scan_directory()

    def _scan_directory(self):
        for filename in os.listdir(self.directory):
            name, extension = os.path.splitext(filename)
            full = os.path.join(self.directory, filename)
            if extension.lower() == ".npz":
                entry = self.index.setdefault(name, {})
                entry['npz'] = full
            elif extension.lower() == ".png":
                entry = self.index.setdefault(name, {})
                entry['png'] = full

    def get_vector_field(self, name) -> VectorField:
        info = self.index.get(name)
        vf = VectorField(0,0)
        vf.load(info['npz'])
        return vf
    
    def get_preview_image(self, name) -> Image:
        info = self.index.get(name)
        return Image.open(info['png'])
    
    def list_fields(self):
        return sorted(self.index.keys())
    
# ------------- begin vector field generation code ----------------- #

HEIGHT = 1024
WIDTH = 1024

def vfg_make_and_save(gen_fn, name):
    # generates a vector field using the function provided
    # and saves it and its preview image to disk via its name
    path = os.path.join(DIRECTORY,name)
    vf = VectorField(HEIGHT,WIDTH)
    vf = gen_fn(vf)
    vf.save(path,True)
    pass

def vfg_gen_towardsmiddle(vf:VectorField) -> VectorField:
    middle = (vf.height/2,vf.width/2)
    max_dist = np.hypot(middle[0],middle[1])
    vf.move_towards_point(middle,max_dist)
    return vf

def vfg_gen_borderrun(vf:VectorField) -> VectorField:
    # four exponential line transforms
    # all on the edges of the image
    tl = (0,0)
    tr = (0,vf.width)
    bl = (vf.height,0)
    br = (vf.height,vf.width)
    strength = 1
    mode = "exponential"
    h_falloff = vf.height/10
    v_falloff = vf.width/10
    vf.line_transform(tr,tl,strength,h_falloff,mode) # top edge
    vf.line_transform(tl,bl,strength,v_falloff,mode) # left edge
    vf.line_transform(bl,br,strength,h_falloff,mode) # bottom edge
    vf.line_transform(br,tr,strength,v_falloff,mode) # right edge
    return vf

def vfg_gen_eightstar(vf:VectorField) -> VectorField:
    # four line transforms
    # going through each cardinal and intercard
    tl = (0,0)
    tr = (0,vf.width)
    bl = (vf.height,0)
    br = (vf.height,vf.width)
    hm = vf.height/2
    wm = vf.width/2
    strength = 1
    falloff = max(vf.height,vf.width)/20
    mode = "exponential"
    vf.line_transform((hm,0),(hm,vf.width),strength,falloff,mode)
    vf.line_transform((0,wm),(vf.height,wm),strength,falloff,mode)
    vf.line_transform(tl,br,strength,falloff,mode)
    vf.line_transform(tr,bl,strength,falloff,mode)
    return vf

def vfg_gen_spiral(vf:VectorField) -> VectorField:
    middle = (vf.height/2,vf.width/2)
    max_dist = np.hypot(middle[0],middle[1])
    vf.spiral_transform(middle,max_dist,spiral_strength=0.01)
    return vf

def vfg_gen_orbit(vf:VectorField) -> VectorField:
    vf.orbit_transform()
    return vf

# TODO: change frequencies to produce a better field
def vfg_gen_wave(vf:VectorField) -> VectorField:
    vf.wave_transform(0.005,0.05)
    return vf

if __name__ == "__main__":
    # generate all vector fields and save them into the vector_fields folder
    #vfg_make_and_save(vfg_gen_towardsmiddle,"towards_middle")
    vfg_make_and_save(vfg_gen_borderrun,"border_run")
    vfg_make_and_save(vfg_gen_eightstar,"star")
    #vfg_make_and_save(vfg_gen_spiral,"spiral")
    #vfg_make_and_save(vfg_gen_orbit,"orbit")
    vfg_make_and_save(vfg_gen_wave,"wave")