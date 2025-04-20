import dearpygui.dearpygui as dpg
import numpy as np
from PIL import Image
import os, threading
from pixelsort.masking import Mask
from pixelsort.vectorfield import VectorField
from pixelsort.vectorfieldgallery import VectorFieldGallery
from pixelsort.pixelsmear import PixelSmear

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
    dpg.delete_item("registry_BaseImg", children_only=True)
    dpg.delete_item("panel_BaseImg", children_only=True)
    #dpg.delete_item("panel_MaskImg", children_only=True)
    #dpg.delete_item("panel_VectorField", children_only=True)
    #dpg.delete_item("panel_OutputImg", children_only=True)

    dpg.add_dynamic_texture(width=width, height=height, default_value=data, tag="baseImg", parent="registry_BaseImg") 

    # print("trying to add to registry")
    w, h, x, y = get_scaling("panel_BaseImg",(width,height))
    print(f"showImage | w={w} h={h} x={x} y={y}")

    dpg.add_image("baseImg", width=w, height=h, parent="panel_BaseImg", pos=[x,y], tag="image_Base")
    self._loadedImages.setdefault("panel_BaseImg", {})["image_Base"] = (width,height)
    dpg.set_value("tabBar_Images","tab_BaseImg")

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
    if(not os.path.isdir('src/pixelsort/mask/')):
        os.mkdir('src/pixelsort/mask/')
    maskPath = 'src/pixelsort/mask/mask.png'
    newMask.save(maskPath)
    maskWidth, maskHeight, _, maskData = dpg.load_image(maskPath)
    
    dpg.delete_item("registry_MaskImg", children_only=True)
    dpg.delete_item("panel_MaskImg", children_only=True)

    dpg.add_dynamic_texture(width=maskWidth, height=maskHeight, default_value=maskData, tag="maskImg", parent="registry_MaskImg")

    w, h, x, y = get_scaling("panel_MaskImg",(maskWidth,maskHeight))

    dpg.add_image("maskImg", width=w, height=h, parent="panel_MaskImg", pos=[x,y], tag="image_Mask")
    self._loadedImages.setdefault("panel_MaskImg", {})["image_Mask"] = (maskWidth,maskHeight)
    im.close()
    return maskPath
    
def get_scaling(panel_tag,img_dimensions):
    """
    Returns the scaled width and height, along with the middle position
    to place the given img dimensions in the the middle of the panel
    """
    width, height = img_dimensions

    panel_height = dpg.get_item_height(panel_tag)
    panel_width = dpg.get_item_width(panel_tag)

    scaling = min(panel_width/width, panel_height/height)

    additional_padding = 0.95

    scaled_width = scaling * width * additional_padding
    scaled_height = scaling * height * additional_padding

    position = [(panel_width-scaled_width)/2, (panel_height-scaled_height)/2]

    return scaled_width, scaled_height, position[0], position[1]

def showVF(sender, app_data, gui):
    vfGal = VectorFieldGallery("src/pixelsort/vector_fields")
    vfHeader = dpg.get_item_children("VectorField")
    selectedVF = dpg.get_value(vfHeader[1][1])
    if selectedVF == "Chaotic Spiral":
        selectedVF = "chaotic_spiral"
    
    selectedVF = selectedVF.lower()
    vfImgPath = vfGal.get_preview_image(selectedVF)
    
    vfWidth, vfHeight, _, vfData = dpg.load_image(vfImgPath)

    dpg.delete_item("registry_VF", children_only=True)
    dpg.delete_item("panel_VectorField", children_only=True)

    dpg.add_dynamic_texture(width=vfWidth, height=vfHeight, default_value=vfData, tag="vfImg", parent="registry_VF")
    # from https://github.com/hoffstadt/DearPyGui/discussions/1789#discussioncomment-2881052
    
    w, h, x, y = get_scaling("panel_VectorField",(vfWidth,vfHeight))

    dpg.add_image("vfImg", width=w , height=h, parent="panel_VectorField", pos=[x,y], tag="image_VF")
    gui._loadedImages.setdefault("panel_VectorField", {})["image_VF"] = (vfWidth, vfHeight)
    dpg.set_value("tabBar_Images","tab_VFImg")

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
    vfGal = VectorFieldGallery("src/pixelsort/vector_fields")
    vecField = VectorField(0,0)

    # If doVF is true, load the Vector Field into the Vector Field Window
    # Get the .npz file as well
    activateVF = dpg.get_value("doVectorField")
    if activateVF == True:
        # vfImgPath = vfGal.get_preview_image(selectedVF)
        vecField = vfGal.get_vector_field(selectedVF)
        
        # vfWidth, vfHeight, _, vfData = dpg.load_image(vfImgPath)

        # dpg.delete_item("registry_VF", children_only=True)
        # dpg.delete_item("panel_VectorField", children_only=True)

        # dpg.add_dynamic_texture(width=vfWidth, height=vfHeight, default_value=vfData, tag="vfImg", parent="registry_VF")
        # dpg.add_image("vfImg", parent="panel_VectorField", pos=[10,10])

    # Initialize variables for PixelSmear
    imgPath = self._currentFile
    outPath = 'src/pixelsort/results/out.png'
    maskPath = self._maskPath
    t = self._maxFrames
    #smeared = PixelSmear(imgPath, outPath, maskPath, num_steps=int(t+1), dx_expr = strX, dy_expr = strY, doVF = activateVF, vf = vecField)

    self.smear_runner = SmearRunner(imgPath, outPath, maskPath, num_steps=int(t+1), dx_expr = strX, dy_expr = strY, doVF = activateVF, vf = vecField)

    dpg.delete_item("panel_OutputImg", children_only=True)
    dpg.delete_item("registry_OutputImg", children_only=True)

    self.smear_runner.run()

    #self.poll_smear_handler = dpg.add_handler_registry(tag="poll_handler")
    #dpg.add_handler(dpg.mvHandlerFrame, callback=poll_smear, user_data=self, parent="poll_handler")

    #dpg.set_value("smearProgress", smeared.progress)
    #dpg.configure_item("smearProgress", overlay=f"{smeared.progress}%")
    
    # Store all the frames into the registry
    # frameNum = None
    # for frame in range(t):
    #     frameNum = str(frame)
    #     smearFrame = smeared.frame_stack[frame]
    #     smeared_data = np.asarray(smearFrame, dtype=np.float32)  # change data type to 32bit floats
    #     texture_data = np.true_divide(smeared_data, 255.0)
    #     imgHeight, imgWidth = smeared.height, smeared.width
    #     dpg.add_raw_texture(width=imgWidth, height=imgHeight, default_value=texture_data, tag="frame"+frameNum, 
    #                         parent="registry_OutputImg",format=dpg.mvFormat_Float_rgba)
    
    # dpg.add_image("frame"+frameNum, parent="panel_OutputImg", pos=[10,10])
    # print("Finished")
    # return smeared.frame_stack

# Select a frame from Frame Selector
def selectFrame(sender, app_data, gui):
    dpg.delete_item("panel_OutputImg", children_only=True)
    frameNum = str(app_data-1)

    width = gui._frameWidth 
    height = gui._frameHeight

    w, h, x, y = get_scaling("panel_OutputImg",(width,height))

    dpg.add_image("frame"+frameNum, width=w, height=h, parent="panel_OutputImg", pos=[x,y], tag="image_Output")
    gui._loadedImages.setdefault("panel_OutputImg", {})["image_Output"] = (width,height)

class SmearRunner:
    """
    Initializes a PixelSmear instance with the provided variables, and runs it in a separate thread.
    Has functions to provide status about the current computation, including blocking functions.
    """
    def __init__(self,imgPath,outPath,maskPath,num_steps,dx_expr,dy_expr,doVF,vf):
        # just a translation layer between the main thread and the smearing thread.
        self.imgPath = imgPath
        self.outPath = outPath
        self.maskPath = maskPath
        self.numSteps = num_steps
        self.dx_expr = dx_expr
        self.dy_expr = dy_expr
        self.doVF = doVF
        self.vf = vf
        
        self._smear = None
        self._runner = None
        self._lock = threading.Lock()
        self._finished = False
        self._frames = None
    
    def _runnerFn(self):
        self._smear.run()
        # should be blocking here until the computation is finished.
        self._finished = True        

    def run(self):
        with self._lock:
            self._smear = PixelSmear(self.imgPath, self.outPath, self.maskPath, num_steps=self.numSteps, 
                            dx_expr=self.dx_expr, dy_expr=self.dy_expr, doVF=self.doVF, vf=self.vf)
            self._runner = threading.Thread(target=self._runnerFn)
            self._runner.start()

    def is_running(self):
        with self._lock:
            return self._runner and not self._finished

    def is_finished(self):
        with self._lock:
            return self._finished

    def wait_for_completion(self):
        if self._runner:
            self._runner.join()
        pass

    def get_shape(self):
        with self._lock:
            return (self._smear.height,self._smear.width)

    def get_progress(self):
        with self._lock:
            return self._smear.progress

    def get_frame_stack(self):
        with self._lock:
            return self._smear.frame_stack
