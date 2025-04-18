from PIL import Image, ImageFilter
import numpy as np
from gui import GUI
from pixelsorter import PixelSorter
from vectorfield import VectorField
from image_smear import ImageSmearer

def main():

    gui = GUI()
    
    # TODO:
    # linear smear inputs
    # 
    
    
    '''
    num_steps = 5

    # in terms of t
    stringX = "2**t"
    y = "5"

    def string_to_function(expression):
        def function(t):
            return eval(expression)
        return np.frompyfunc(function, 1, 1)

    functionX = string_to_function(stringX)
     
    for t in range(1, num_steps):
        resultX = functionX(t)
        dx = resultX
        dy = 2*t/5

        print(dx)
    '''

    
if __name__ == "__main__":
    main()