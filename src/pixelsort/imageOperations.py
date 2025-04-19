import dearpygui.dearpygui as dpg
import numpy as np
from PIL import Image
from masking import Mask
from vectorfield import VectorField
from vectorfieldgallery import VectorFieldGallery
from pixelsmear import PixelSmear

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
    dpg.delete_item(44, children_only=True)
    #dpg.delete_item(46, children_only=True)
    #dpg.delete_item(48, children_only=True)
    #dpg.delete_item(50, children_only=True)

    dpg.add_dynamic_texture(width=width, height=height, default_value=data, tag="baseImg", parent=22) 

    # print("trying to add to registry")
    dpg.add_image("baseImg", parent=44, pos=[10,10])

# Depending on the type of save, do the following
def saveImage(self, folderPath, typeSave):
    if typeSave == "saveMask":
        print("Saving a mask!")
        maskImg = Image.open(self._maskPath)
        maskImg.save(folderPath + "/mask.png")

    if typeSave == "saveResult":
        print("Saving result!")
        resultImg = self._currentResult
        resultImg = Image.fromarray(resultImg)
        resultImg.save(folderPath + "/result.png")

    if typeSave == "saveFrames":
        print("Saving frames!")
        for frame in range(self._maxFrames):
            frameNum = str(frame)
            currFrame = self._currentFrames[frame]
            currFrame = Image.fromarray(currFrame)
            currFrame.save(folderPath + "/frame" + frameNum + ".png")         


def makeMask(self, sender):
   # Get all the parameters required for masking 
    maskButtonID = dpg.get_alias_id(sender)
    maskContainer = dpg.get_item_children(dpg.get_item_parent(maskButtonID))
    typeMask = dpg.get_value(maskContainer[1][1])
    minThresh = int(dpg.get_value(maskContainer[1][4]))
    maxThresh = int(dpg.get_value(maskContainer[1][6]))
    threshold = (minThresh, maxThresh)

    doGaussian = dpg.get_value(maskContainer[1][8])
    gauss_strength = dpg.get_value(maskContainer[1][10])

    # If the user wants boxes, create a matrix to store 
    # the bounding boxes    
    doBox = dpg.get_value(maskContainer[1][12])
    numBoxes = self._numBox
    boxLoc = []
    if doBox == True:
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
    
    # Send into Mask function
    im = Image.open(self._currentFile)
    mask = Mask(im, doGaussian, threshold, doBox, boxLoc, invertBox)
    newMask = mask.getMask(typeMask, gauss_strength)

    # Save the image internally and update the Mask Window
    maskPath = 'src/pixelsort/mask/mask.png'
    newMask.save(maskPath)
    maskWidth, maskHeight, _, maskData = dpg.load_image(maskPath)
    
    dpg.delete_item(23, children_only=True)
    dpg.delete_item(46, children_only=True)

    dpg.add_dynamic_texture(width=maskWidth, height=maskHeight, default_value=maskData, tag="maskImg", parent=23)

    dpg.add_image("maskImg", parent=46, pos=[10,10])
    
    im.close()
    return maskPath
    
def doSmear(self, sender):

    # Gets the Direction + VectorField windows
    directHeader = dpg.get_item_children("Direction")
    vfHeader = dpg.get_item_children("VectorField")

    # Initialize Direction and other related variables
    direction = dpg.get_value(directHeader[1][1])
    userDeg = 0
    strX = None
    strY = None
    pi = np.pi

    # Depending on the direction, set strX and strY
    if direction == "Left":
        strX = str(-1.0)
        strY = str(0.0)
    if direction == "Right":
        strX = str(1.0)
        strY = str(0.0)
    if direction == "Down":
        strX = str(0.0)
        strY = str(1.0)
    if direction == "Up":
        strX = str(0.0)
        strY = str(-1.0)
    if direction == "Custom":
        userDeg = dpg.get_value(directHeader[1][3])
        strX = str(np.cos((pi/180)*userDeg))
        strY = str(np.sin((pi/180)*userDeg))
    if direction == "None":
        strX = dpg.get_value(directHeader[1][8])
        strY = dpg.get_value(directHeader[1][10])
    
    # Get the selected Vector Field
    selectedVF = dpg.get_value(vfHeader[1][1])
    if selectedVF == "Chaotic Spiral":
        selectedVF = "chaotic_spiral"
    
    selectedVF = selectedVF.lower()
    vfGal = VectorFieldGallery("src/pixelsort/vector fields")
    vecField = VectorField(0,0)

    # If doVF is true, load the Vector Field into the Vector Field Window
    # Get the .npz file as well
    activateVF = dpg.get_value("doVectorField")
    if activateVF == True:
        vfImgPath = vfGal.get_preview_image(selectedVF)
        vecField = vfGal.get_vector_field(selectedVF)
        
        vfWidth, vfHeight, _, vfData = dpg.load_image(vfImgPath)

        dpg.delete_item(24, children_only=True)
        dpg.delete_item(48, children_only=True)

        dpg.add_dynamic_texture(width=vfWidth, height=vfHeight, default_value=vfData, tag="vfImg", parent=24)
        dpg.add_image("vfImg", parent=48, pos=[10,10])

    # Initialize variables for PixelSmear
    imgPath = self._currentFile
    outPath = 'src/pixelsort/result/out.png'
    maskPath = self._maskPath
    t = self._maxFrames
    smeared = PixelSmear(imgPath, outPath, maskPath, num_steps=int(t+1), dx_expr = strX, dy_expr = strY, doVF = activateVF, vf = vecField)

    dpg.delete_item(50, children_only=True)
    dpg.delete_item("OutputImgRegistry", children_only=True)

    smeared.run()
    dpg.set_value("smearProgress", smeared.progress)
    dpg.configure_item("smearProgress", overlay=f"{smeared.progress}%")
    
    # Store all the frames into the registry
    frameNum = None
    for frame in range(t):
        frameNum = str(frame)
        smearFrame = smeared.frame_stack[frame]
        smeared_data = np.asarray(smearFrame, dtype=np.float32)  # change data type to 32bit floats
        texture_data = np.true_divide(smeared_data, 255.0)
        imgHeight, imgWidth = smeared.height, smeared.width
        dpg.add_raw_texture(width=imgWidth, height=imgHeight, default_value=texture_data, tag="frame"+frameNum, 
                            parent="OutputImgRegistry",format=dpg.mvFormat_Float_rgba)
    
    dpg.add_image("frame"+frameNum, parent=50, pos=[10,10])
    print("Finished")
    return smeared.frame_stack

# Select a frame from Frame Selector
def selectFrame(sender, app_data):
    dpg.delete_item(50, children_only=True)
    frameNum = str(app_data-1)
    dpg.add_image("frame"+frameNum, parent=50, pos=[10,10])


