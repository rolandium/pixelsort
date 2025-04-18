import dearpygui.dearpygui as dpg
import cv2 as cv
import numpy as np
from PIL import Image
from masking import Mask

# callback + cancel_callback use to find sender, app_data, and user_data
def callback(sender, app_data, user_data):
    print('OK was clicked.')
    print("Sender: ", sender)
    print("App Data: ", app_data)
    print("App Data Type: ", type(app_data))
    print("user data:", user_data)

def cancel_callback(sender, app_data):
    print('Cancel was clicked.')
    print("Sender: ", sender)
    print("App Data: ", app_data)

def showImage(imagePath, self):
    #print("in showImage")
    
    # Get the image data
    width, height, _, data = dpg.load_image(imagePath)

    # On each "Open", reset all the texture libraries and the "Base Image" window
    dpg.delete_item(22, children_only=True)
    dpg.delete_item(42, children_only=True)
    #dpg.delete_item(43, children_only=True)
    #dpg.delete_item(45, children_only=True)

    dpg.add_dynamic_texture(width=width, height=height, default_value=data, tag="baseImg", parent=22) 

    print("trying to add to registry")
    dpg.add_image("baseImg", parent=42, pos=[10,10])

def saveImage(self, folderPath, typeSave):
    if typeSave == "saveMask":
        print("Saving a mask!")
        maskImg = self._currentMask
        maskImg.save(folderPath + "/mask.png")

    if typeSave == "saveResult":
        print("Saving result!")
        resultImg = self._currentResult
        resultImg.save(folderPath + "/result.png")

    if typeSave == "saveFrames":
        print("Saving frames!")
        print(self._currentFrames.shape)
        #for frame in range(self._maxFrames):
            

def makeMask(self, sender):
    maskButtonID = dpg.get_alias_id(sender)
    maskContainer = dpg.get_item_children(dpg.get_item_parent(maskButtonID))
    
    typeMask = dpg.get_value(maskContainer[1][1])
    minThresh = int(dpg.get_value(maskContainer[1][4]))
    maxThresh = int(dpg.get_value(maskContainer[1][6]))
    threshold = (minThresh, maxThresh)

    doGaussian = dpg.get_value(maskContainer[1][8])
    gauss_strength = dpg.get_value(maskContainer[1][10])
    
    doBox = dpg.get_value(maskContainer[1][12])
    numBoxes = self._numBox
    boxLoc = []

    for box in range(numBoxes):
        boxKey = str(box+1)
        boxPositions = self._boxHolders.get(boxKey)
        topLeft = dpg.get_value(boxPositions[0])
        topLeft = topLeft.split(",")
        topLeftY = int(topLeft[1].strip())
        topLeftX = int(topLeft[0].strip())

        botRight = dpg.get_value(boxPositions[1])
        botRight = botRight.split(",")
        botRightY = int(botRight[1].strip())
        botRightX = int(botRight[0].strip())

        bbox = np.array([
            [topLeftY, topLeftX, botRightY, botRightX]
        ])

        boxLoc.append(bbox)

    boxLoc = np.concatenate(boxLoc, axis=0)
    invertBox = dpg.get_value(maskContainer[1][29])
    
    im = Image.open(self._currentFile)
    
    mask = Mask(im, doGaussian, threshold, doBox, boxLoc, invertBox)
    newMask = mask.getMask(typeMask, gauss_strength)

    maskPath = 'src/pixelsort/mask/mask.png'
    newMask.save(maskPath)
    maskWidth, maskHeight, _, maskData = dpg.load_image(maskPath)
    
    dpg.delete_item(23, children_only=True)
    dpg.delete_item(44, children_only=True)

    dpg.add_dynamic_texture(width=maskWidth, height=maskHeight, default_value=maskData, tag="maskImg", parent=23)

    dpg.add_image("maskImg", parent=44, pos=[10,10])
    
    im.close()
    return newMask
    
def doSmear(self, sender):
    smearButtonID = dpg.get_alias_id(sender)
    smearContainer = dpg.get_item_children(dpg.get_item_parent(smearButtonID))

    direction = dpg.get_value(smearContainer[1][1])
    userDeg = 0
    strX = None
    strY = None
    pi = np.pi

    if direction == "Left":
        strX = str(-1.0)
        strY = str(0.0)
    if direction == "Right":
        strX = str(1.0)
        strY = str(0.0)
    if direction == "Down":
        strX = str(0.0)
        strY = str(-1.0)
    if direction == "Up":
        strX = str(0.0)
        strY = str(1.0)
    if direction == "Custom":
        userDeg = dpg.get_value(smearContainer[1][3])
        strX = str(np.cos((pi/180)*userDeg))
        strY = str(np.sin((pi/180)*userDeg))
    if direction == "None":
        strX = dpg.get_value(smearContainer[1][8])
        strY = dpg.get_value(smearContainer[1][10])
    
    numSteps = self._maxFrames
    im = Image.open(self._currentFile)
    #smeared = image_smear(im, strX, strY, numSteps)

def selectFrame(sender, app_data):
    dpg.delete_item(35, children_only=True)
    texNum = str(app_data-1)
    dpg.add_image("texture_tag"+texNum, parent="image display")


