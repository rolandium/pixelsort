import os, threading
import numpy as np
from PIL import Image
from pixelsort.vectorfield import Vector, VectorField

DIRECTORY = "src/pixelsort/vector_fields"

class VectorFieldGallery:
    """
    Class that includes functions for loading pre rendered vector fields from disk
    Also provides a function to generate the vector fields in a background thread
    """
    def __init__(self, directory=DIRECTORY):
        self.directory = directory
        self.index = {}
        self._scan_directory()

        self._gen_progress = 0.0
        self._gen_runner = None
        self._gen_lock = threading.Lock()
        self._gen_finished = False

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
    
    def get_preview_image(self, name) -> str:
        info = self.index.get(name)
        return info['png']
    
    def list_fields(self):
        return sorted(self.index.keys())
    
    # -- generation thread --

    def generate_all_fields(self):
        with self._gen_lock:
            self._gen_runner = threading.Thread(target=self._gen_runnerFn)
            self._gen_runner.start()

    def get_generation_progress(self):
        with self._gen_lock:
            return self._gen_progress

    def generation_is_finished(self):
        with self._gen_lock:
            return self._gen_finished

    def generation_is_running(self):
        with self._gen_lock:
            return not self._gen_finished

    def _gen_runnerFn(self):
        self._gen_fields()
        # blocking until finished
        self._gen_finished = True

    def _gen_fields(self):
        self._gen_progress = 0.0
        vfg_make_and_save(vfg_gen_collapse,"collapse")
        self._gen_progress = 0.1
        vfg_make_and_save(vfg_gen_explosion,"explosion")
        self._gen_progress = 0.2
        vfg_make_and_save(vfg_gen_borderrun,"border")
        self._gen_progress = 0.3
        vfg_make_and_save(vfg_gen_plus,"plus")
        self._gen_progress = 0.4
        vfg_make_and_save(vfg_gen_cross,"cross")
        self._gen_progress = 0.5
        vfg_make_and_save(vfg_gen_eightstar,"star")
        self._gen_progress = 0.6
        vfg_make_and_save(vfg_gen_spiral,"spiral")
        self._gen_progress = 0.7
        vfg_make_and_save(vfg_gen_chaotic_spiral,"chaotic_spiral")
        self._gen_progress = 0.8
        vfg_make_and_save(vfg_gen_orbit,"orbit")
        self._gen_progress = 0.9
        vfg_make_and_save(vfg_gen_wave,"wave")
        self._gen_progress = 1.0
    
# ------------- begin vector field generation code ----------------- #

HEIGHT = 1024
WIDTH = 1024

def vfg_make_and_save(gen_fn, name):
    # generates a vector field using the function provided
    # and saves it and its preview image to disk via its name
    if(not os.path.isdir(DIRECTORY)):
        os.mkdir(DIRECTORY)
    path = os.path.join(DIRECTORY,name)
    vf = VectorField(HEIGHT,WIDTH)
    vf = gen_fn(vf)
    vf.save(path,True)
    pass

def vfg_gen_collapse(vf:VectorField) -> VectorField:
    middle = (vf.height/2,vf.width/2)
    max_dist = np.hypot(middle[0],middle[1])
    vf.move_towards_point(middle,max_dist)
    return vf

def vfg_gen_explosion(vf:VectorField) -> VectorField:
    middle = (vf.height/2, vf.width/2)
    middle = (vf.height/2,vf.width/2)
    max_dist = np.hypot(middle[0],middle[1])*2
    vf.move_away_from_point(middle,max_dist)
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

def vfg_gen_plus(vf:VectorField) -> VectorField:
    hm = vf.height/2
    wm = vf.width/2
    strength = 1
    falloff = max(vf.height,vf.width)/20
    mode = "exponential"
    vf.line_transform((hm,0),(hm,vf.width),strength,falloff,mode)
    vf.line_transform((0,wm),(vf.height,wm),strength,falloff,mode)
    return vf

def vfg_gen_cross(vf:VectorField) -> VectorField:
    tl = (0,0)
    tr = (0,vf.width)
    bl = (vf.height,0)
    br = (vf.height,vf.width)
    strength = 1
    falloff = max(vf.height,vf.width)/20
    mode = "exponential"
    vf.line_transform(tl,br,strength,falloff,mode)
    vf.line_transform(tr,bl,strength,falloff,mode)
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
    vf.spiral_transform(middle)
    return vf

def vfg_gen_chaotic_spiral(vf:VectorField) -> VectorField:
    middle = (vf.height/2,vf.width/2)
    max_dist = np.hypot(middle[0],middle[1])
    vf.chaotic_spiral_transform(middle,max_dist,spiral_strength=0.01)
    return vf

def vfg_gen_orbit(vf:VectorField) -> VectorField:
    vf.orbit_transform()
    return vf

def vfg_gen_wave(vf:VectorField) -> VectorField:
    vf.wave_transform(0.025,40)
    return vf

if __name__ == "__main__":
    # generate all vector fields and save them into the vector_fields folder
    vfg_make_and_save(vfg_gen_collapse,"collapse")
    vfg_make_and_save(vfg_gen_explosion,"explosion")
    vfg_make_and_save(vfg_gen_borderrun,"border")
    vfg_make_and_save(vfg_gen_plus,"plus")
    vfg_make_and_save(vfg_gen_cross,"cross")
    vfg_make_and_save(vfg_gen_eightstar,"star")
    vfg_make_and_save(vfg_gen_spiral,"spiral")
    vfg_make_and_save(vfg_gen_chaotic_spiral,"chaotic_spiral")
    vfg_make_and_save(vfg_gen_orbit,"orbit")
    vfg_make_and_save(vfg_gen_wave,"wave")