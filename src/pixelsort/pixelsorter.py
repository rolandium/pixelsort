import PIL.Image
import PIL.ImageFilter
import PIL.ImageOps
import numpy as np
from PIL import Image
import PIL, cv2

class PixelSorter:
    def __init__(self):
        self._image = None
        self.threshold = (70,160)
        self.sortType = 'brightness'
        pass

    @property
    def image(self):
        """
        Returns the current unsorted image.
        """
        return self._image

    @image.setter
    def image(self,newImage: Image):
        """
        Sets the image to be sorted by sortImage().
        """
        self._image = newImage
        
    def sortImage(self, brightMin, brightMax) -> Image:
        """
        Draws the current pixel sorted image given the current parameters.
        """
        print("this is brightmax")
        print(brightMax)
        arr = np.array(self._image)
        copyArr = np.array(self._image)
        # thresholding
        preMask = self._image
        # blur the image first 
        #preMask = preMask.filter(PIL.ImageFilter.GaussianBlur(3))
        greyscale = np.array(PIL.ImageOps.grayscale(preMask))
        mask = (greyscale >= brightMin) & (greyscale <= brightMax)
        # print(mask)
        # sorting
         # Convert RGB to HSV for sorting
        
        def rgb_to_hsv(pixel):
            return Image.fromarray(np.uint8([[pixel]])).convert("HSV").getpixel((0, 0))

        def hsv_to_rgb(pixel):
            return Image.fromarray(np.uint8([[pixel]])).convert("RGB").getpixel((0, 0))
        

        print(arr.shape[1])

        if self.sortType == 'brightness':
            def sort_func(pixels):
                return sorted(pixels, key=lambda px: sum(px)/3) # TODO: define the gradient better

         
        gradient = arr[6, 6:6+15]
        minPixelIndex = 0
        minValue = 1023

        for i in range(gradient.shape[0]):
            currPixel = int(gradient[i, 0]) + int(gradient[i, 1]) + int(gradient[i, 2])
            if currPixel < minValue:
                minPixelIndex = i
                minValue = currPixel
        
        smallest = gradient[minPixelIndex]
        tarR = smallest[0]
        tarG = smallest[1]
        tarB = smallest[2]
        
        #for i in range(14):
         #   print(gradient[i])
        
        #pixel loop
        for y in range(arr.shape[0]):
            x_start = None
            for x in range(arr.shape[1]-15):
                # if pixel is in the range of the image, and is found in the mask
                if (x < arr.shape[1] - 1) & (mask[y][x]):

                    #takes x position if no position
                    if x_start is None:
                        x_start = x
                
                #if pixel is not in the mask
                else:
                    if x_start is not None:
                        segment = arr[y,x_start:x]
                        sorted_segment = sort_func(segment)
                        arr[y][x_start:x] = sorted_segment
                        x_start = None
        Image.fromarray(mask).show()
        return Image.fromarray(copyArr)
    
    