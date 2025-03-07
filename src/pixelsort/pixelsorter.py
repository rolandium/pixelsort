import PIL.Image
import PIL.ImageFilter
import PIL.ImageOps
import numpy as np
from PIL import Image
import PIL, cv2

class PixelSorter:
    def __init__(self):
        self._image = None
        self.threshold = (70,170)
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

    def sortImage(self) -> Image:
        """
        Draws the current pixel sorted image given the current parameters.
        """
        arr = np.array(self._image)
        # thresholding
        preMask = self._image
        # blur the image first 
        #preMask = preMask.filter(PIL.ImageFilter.GaussianBlur(3))
        greyscale = np.array(PIL.ImageOps.grayscale(preMask))
        mask = (greyscale >= self.threshold[0]) & (greyscale <= self.threshold[1])
        print(mask)
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
        for y in range(arr.shape[0]):
            x_start = None
            for x in range(arr.shape[1]):
                if (x < arr.shape[1] - 1) & (mask[y][x]):
                    if x_start is None:
                        x_start = x
                else:
                    if x_start is not None:
                        segment = arr[y,x_start:x]
                        sorted_segment = sorted(segment, key=lambda px: rgb_to_hsv(px)[0])
                        arr[y][x_start:x] = sorted_segment
                        x_start = None
        Image.fromarray(mask).show()
        return Image.fromarray(arr)