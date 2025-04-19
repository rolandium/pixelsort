import numpy as np
from PIL import Image, ImageOps, ImageFilter

class Mask:

    def __init__(self, image: Image.Image, stateGaussian, threshold, stateBox, boxLoc, stateBoxInv):
        self._image = image
        self._doGaussian = stateGaussian
        self._threshold = threshold
        self._doBox = stateBox
        self._boxLoc = boxLoc 
        self._boxInv = stateBoxInv

    # MAIN FUNCTION: gets a mask based on what user selected in "Masking" window     
    def getMask(self, typeMask, blurStrength):
        print("RUNNING: getMask")

        if self._image.mode != "RGBA":
            self._image = self._image.convert("RGBA")
        
        # If the user selected "Brightness", makes a mask based on the thresholds
        # Returns the mask as an Image object
        if typeMask == "Brightness":
            if self._doGaussian == True:
                self._image = self.getGaussianBlur(blurStrength)
            
            greyscale = np.array(ImageOps.grayscale(self._image))
            mask = (greyscale >= self._threshold[0]) & (greyscale <= self._threshold[1])
            if self._doBox == True:
                boxMask = self.getBoxMask()
                mask = mask & boxMask

            mask_im = Image.fromarray((mask*255).astype(np.uint8))
            return mask_im
        
        # If the user selected "None", makes a mask based on the whole image
        # Returns the mask as an Image object
        if typeMask == "None":
            imgHeight = self._image.height
            imgWidth = self._image.width
            mask = np.ones((imgHeight, imgWidth), dtype=np.uint8)
            if self._doGaussian == True:
                self._image = self.getGaussianBlur(blurStrength)

            if self._doBox == True:
                boxMask = self.getBoxMask()
                mask = mask & boxMask
                
            mask_im = Image.fromarray((mask*255).astype(np.uint8))
            
            return mask_im
    
    def getGaussianBlur(self, blurStrength):
        blurred = self._image.filter(ImageFilter.GaussianBlur(blurStrength))
        return blurred
    
    def getBoxMask(self):
        # Given the user selected box regions, create a mask with the bounding boxes
        boxLoc = self._boxLoc
        imgHeight = self._image.height
        imgWidth = self._image.width
        boxMask = np.zeros((imgHeight, imgWidth), dtype=np.uint8)
        numBox, _ = boxLoc.shape 
        for box in range(numBox):
            topLeftY = boxLoc[box, 0]
            topLeftX = boxLoc[box, 1]
            botRightY = boxLoc[box, 2]
            botRightX = boxLoc[box, 3]

            boxMask[topLeftY:botRightY, topLeftX:botRightX] = 1  

        # Inverts the box mask
        if self._boxInv == True:
            boxMask = boxMask^1

        return boxMask

    def maskImageToArray(image: Image.Image):
        return(np.array(image))