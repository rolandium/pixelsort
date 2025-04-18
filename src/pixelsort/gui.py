from PIL import Image
from pixelsorter import PixelSorter
from image_smear import ImageSmearer
import pixelsort.imageOperations as imageOperations 
import dearpygui.dearpygui as dpg
import numpy as np

class GUI:

    # Constructor
    def __init__(self):
        
        self._paramLabel = {
            "---": 0, "Masking": 52, "Linear Smear": 87#, "Vector Field": 5000, "Frame Selector": 5000
            }
        self._currentFile = "Empty"
        self._currentMask = None
        self._numBox = 1
        self._boxHolders = {
            # [0], [1] hold the inputs; [2], [3] hold the texts
            "1": (70, 72, 69, 71), "2": (74, 76, 73, 75), "3": (78, 80, 77, 79)
        }
        self._currentFrames = None
        self._currentResult = None
        self._maxFrames = 0
        self._initDPG()

    def _initDPG(self):
        dpg.create_context()

        dpg.add_texture_registry(label="BaseImgRegistry", show=False)
        dpg.add_texture_registry(label="MaskImgRegistry", show=False)
        dpg.add_texture_registry(label="OutputImgRegistry", show=False)
        
        with dpg.file_dialog(label="Select a file to open:",
                             directory_selector=False, show=False, callback=self.getFile, tag="getFile", width=700, height=400):
            dpg.add_file_extension(".png", color=(150, 255, 150, 255))
            dpg.add_file_extension(".jpg", color=(255, 0, 255, 255), custom_text="[header]")

        dpg.add_file_dialog(label="Select a folder to save the mask:",
                            directory_selector=True, show=False, callback=self.getMaskFolder, tag="getMaskFolder", width=700, height=400)
        
        dpg.add_file_dialog(label="Select a folder to save the frames:",
                            directory_selector=True, show=False, callback=self.getFrameFolder, tag="getFrameFolder", width=700, height=400)
        
        dpg.add_file_dialog(label="Select a folder to save the result:",
                            directory_selector=True, show=False, callback=self.getResultFolder, tag="getResultFolder", width=700, height=400)
        
        with dpg.window(tag="Primary Window"):
            # the menu bar
            with dpg.menu_bar():
                with dpg.menu(label="File"):
                    dpg.add_menu_item(label="Open File", callback=lambda: dpg.show_item("getFile"))
                with dpg.menu(label="Resources"):
                    dpg.add_menu_item(label="DearPyGUI Documentation", callback= lambda: dpg.show_documentation())
                    dpg.add_menu_item(label="Item Registry", callback= lambda: dpg.show_item_registry())
                    dpg.add_menu_item(label="Texture Registry", callback=self.showTexRegistries)
            
            # Where the images are painted
            with dpg.child_window(label="image tabs", width=850, height=600,
                                  resizable_x=True, resizable_y=True,
                                  pos=[10,30]):
                with dpg.tab_bar(label = "navigate"):
                    with dpg.tab(label = "Base Image"):
                        dpg.add_child_window(label = "originalImage", width=835, height=560, horizontal_scrollbar=True)
                    with dpg.tab(label = "Mask"):
                        dpg.add_child_window(label = "maskImage", width=835, height=560, horizontal_scrollbar=True)
                    with dpg.tab(label = "Output Image"):
                        dpg.add_child_window(label = "outputImage", width=835, height=560, horizontal_scrollbar=True)
                    with dpg.tab(label = "Frames of Image"):
                        dpg.add_child_window(label = "framesImage", width=835, height=560, horizontal_scrollbar=True)

            # Functions window
            with dpg.child_window(label="Parameters", width=400, height=600, pos=[870,30]):
                funcs = ["---", "Masking", "Linear Smear", "Vector Field", "Frame Selector"]
                dpg.add_text("Select a function:", pos=[10, 5])
                dpg.add_combo(funcs, callback=self.getFunctionHeader, width=380, pos=[10, 30], default_value="---")

                with dpg.child_window(label="Masking", width=380, height=490, pos=[10, 55], show=False, tag="Masking"):
                    
                    dpg.add_text("Masking by: ", pos=[10,10])
                    typeMasks = ["Brightness", "None"]
                    dpg.add_radio_button(typeMasks, label="typeMasks", horizontal=True, pos=[10, 30], default_value="Brightness")

                    dpg.add_text("Thresholds:", pos=[10, 60])
                    dpg.add_text("Min. Thresh", pos=[10, 80])
                    dpg.add_input_text(tag="minThresh", width=50, pos=[100, 80], default_value=0)
                    dpg.add_text("Max. Thresh", pos=[160, 80])
                    dpg.add_input_text(tag="maxThresh", width=50, pos=[250, 80], default_value=0)

                    dpg.add_text("Apply Gaussian filter to image?", pos=[10, 110])
                    dpg.add_checkbox(tag="doGaussian",pos =[240, 110], callback=self.enableGaussian)
                    dpg.add_text("Strength of Gaussian:", pos=[10, 135])
                    dpg.add_input_float(tag="blurStrength", width=100, pos=[170, 135], enabled=False, default_value=0)

                    dpg.add_text("Select box(es) to bind the mask?", pos=[10, 170])
                    dpg.add_checkbox(tag="doBox",pos =[240, 170], callback=self.enableBoxes)
                    dpg.add_text("How many boxes would you like?", pos=[10, 195])
                    numBox = ["1", "2", "3"]
                    dpg.add_combo(numBox, width=50, default_value="1", pos=[240, 195], callback=self.showBoxes, tag="numBox", enabled=False)
                    dpg.add_text("Please input in form: x, y", pos=[10, 220])

                    dpg.add_text("Top Left of Box 1:", pos=[10, 240])
                    dpg.add_input_text(tag="topLeft1", width=75, pos=[180, 240], enabled=False, default_value="30, 40")
                    dpg.add_text("Bottom Right of Box 1:", pos=[10, 265])
                    dpg.add_input_text(tag="botRight1", width=75, pos=[180, 265], enabled=False, default_value="50, 80")
                    
                    dpg.add_text("Top Left of Box 2:", pos=[10, 290], show=False)
                    dpg.add_input_text(tag="topLeft2", width=75, pos=[180, 290], enabled=False, default_value="30, 40", show=False)
                    dpg.add_text("Bottom Right of Box 2:", pos=[10, 315], show=False)
                    dpg.add_input_text(tag="botRight2", width=75, pos=[180, 315], enabled=False, default_value="50, 80", show=False)
                    
                    dpg.add_text("Top Left of Box 3:", pos=[10, 340], show=False)
                    dpg.add_input_text(tag="topLeft3", width=75, pos=[180, 340], enabled=False, default_value="30, 40", show=False)
                    dpg.add_text("Bottom Right of Box 3:", pos=[10, 365], show=False)
                    dpg.add_input_text(tag="botRight3", width=75, pos=[180, 365], enabled=False, default_value="50, 80", show=False)

                    dpg.add_text("Invert Box(es)?", pos=[10, 390])
                    dpg.add_checkbox(tag="invertBox",pos =[200, 390])
                    
                    dpg.add_button(label="Create Mask", pos=[10, 0.94*dpg.get_item_height("Masking")], 
                               callback=self.makeMask, tag="makeMask")
                    dpg.add_text("No image selected.", pos=[10, 0.90*dpg.get_item_height("Masking")], show=False)
                    dpg.add_button(label="Save Mask", pos=[0.78*dpg.get_item_width("Masking"), 0.94*dpg.get_item_height("Masking")], 
                               callback=lambda: dpg.show_item(65) if self._currentMask == None else dpg.show_item("getMaskFolder"),
                                 tag="saveMask")
                    dpg.add_text("No mask exists.", pos=[0.68*dpg.get_item_width("Masking"), 0.90*dpg.get_item_height("Masking")], show=False)

                with dpg.child_window(label="Linear Smear", width=380, height=490, pos=[10, 55], show=False, tag="LinearSmear"):
                    dpg.add_text("Direction", pos=[10,10])
                    directions = ["Left", "Right", "Up", "Down", "Custom", "None"]
                    dpg.add_radio_button(directions, label="directions", horizontal=True, pos=[10, 30],
                                          callback=self.enableCustom, default_value="Left")
                    dpg.add_text("Custom Input in Degrees:", pos=[10, 55])
                    dpg.add_input_float(tag="userDegrees", width=100, pos=[200, 55], enabled=False, default_value=0,
                                        max_value=360, max_clamped=True, min_value=0, min_clamped=True)

                    dpg.add_text("When 'None', set smear path in terms of t:", pos=[10,80])
                    dpg.add_text("+: Add, -: Subtract, *: Multiply,", pos=[10,100])
                    dpg.add_text("/: Divide, **: Power", pos=[10, 120])
                    dpg.add_text("X equation:", pos=[10,140])
                    dpg.add_input_text(tag="stringX", pos=[100,140], width=200, enabled=False, default_value="5*t")
                    dpg.add_text("Y equation:", pos=[10,165])
                    dpg.add_input_text(tag="stringY", pos=[100,165], width=200, enabled=False, default_value="5*t")

                    dpg.add_text("Max Frames:", pos=[10,200])
                    dpg.add_input_int(tag="max_frames", pos=[100,200], width=75, callback = self.setMaxFrames, default_value=1,
                                      min_value=1, min_clamped=True)

                    dpg.add_button(label="Smear", pos=[10, 0.94*dpg.get_item_height("LinearSmear")], 
                               callback=self.smear, tag="smear")
                    dpg.add_text("No image selected.", pos=[10, 0.90*dpg.get_item_height("LinearSmear")], show=False)
                    dpg.add_button(label="Save Smear", pos=[0.78*dpg.get_item_width("LinearSmear"), 0.94*dpg.get_item_height("LinearSmear")], 
                               callback=lambda: dpg.show_item(102) if self._currentResult == None else dpg.show_item("getResultFolder"),
                                 tag="saveSmear")
                    dpg.add_text("No smear exists.",
                                pos=[0.68*dpg.get_item_width("LinearSmear"), 0.90*dpg.get_item_height("LinearSmear")], show=False)

                with dpg.child_window(label="Vector Field", width=380, height=490, pos=[10, 55], show=False, tag="VectorField"):
                    dpg.add_text("Select a preset vector field: ", pos=[10,10])
                    presetField = ["Border Run", "Orbit", "Spiral", "Star", "Towards Middle", "Wave"]
                    dpg.add_combo(presetField, width=200, default_value="Border Run", 
                                  pos=[10, 30], tag="presetField")
                    
                    dpg.add_button(label="Apply Field", pos=[10, 0.94*dpg.get_item_height("VectorField")], 
                               callback=self.smear, tag="field")
                    dpg.add_text("No image selected.", pos=[10, 0.90*dpg.get_item_height("VectorField")], show=False)
                    dpg.add_button(label="Save Smear", pos=[0.78*dpg.get_item_width("VectorField"), 0.94*dpg.get_item_height("VectorField")], 
                               callback=lambda: dpg.show_item(102) if self._currentResult == None else dpg.show_item("getResultFolder"),
                                 tag="saveField")
                    dpg.add_text("No smear exists.",
                                pos=[0.68*dpg.get_item_width("VectorField"), 0.90*dpg.get_item_height("VectorField")], show=False)

                with dpg.child_window(label="Frame Selector", width=380, height=490, pos=[10, 55], show=False, tag="FrameSelector"):
                    dpg.add_text("Selected Frame: ", pos=[10,10])
                    dpg.add_slider_int(tag="selectedFrame", no_input=False, pos=[10, 30],
                                        min_value=1, callback=imageOperations.selectFrame)
    
                             
                '''
                dpg.add_button(label="Update Parameters", pos=[10, 0.94*dpg.get_item_height(43)], 
                               callback=self.drawScreen, tag="update")
                dpg.add_button(label="Reset Parameters", pos=[0.675*dpg.get_item_width(43), 0.94*dpg.get_item_height(43)], 
                               callback=self.resetImage, tag="reset")
                ''' 
                #dpg.add_text("No image selected!", parent=36, pos=[10, 0.97*dpg.get_item_height(36)], show=False)
                #dpg.add_text("Empty parameters!", parent=36, pos=[10, 0.97*dpg.get_item_height(36)], show=False)
            
            '''
            with dpg.window(label="Test", width=400, height=600, pos=[630,30]): 
                with dpg.tab_bar(label = "what is this"):
                    dpg.add_tab(label="horny")
                keywords = ["left", "right", "up", "down"]
                dpg.add_radio_button(keywords, horizontal=True)
                dpg.add_input_text(label="testing", width=100, height=100)
                dpg.add_input_text(label="e", width=100)
                dpg.add_input_text(label="ew", width=100, height=100)
                dpg.add_input_text(label="tting", width=100, height=100)
                dpg.add_input_text(label="ting", width=100, height=100)
            '''    
        '''      
        with dpg.texture_registry(label="Testing Facility", show=True):
            photos = ['src/pixelsort/test photos/anime.png', 'src/pixelsort/test photos/emoji.png',
                      'src/pixelsort/test photos/lion.png', 'src/pixelsort/test photos/ripndip.png',
                      'src/pixelsort/test photos/soup.png', 'src/pixelsort/test photos/unflag.png']
            
            for i in range(6):

                width, height, _, data = dpg.load_image(photos[i])
                tagNum = str(i)
                dpg.add_dynamic_texture(width=width, height=height, default_value=data, tag="texture_tag"+tagNum, parent=64)
            '''  

        dpg.create_viewport(title='Pixelsorting', width=1300, height=700)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("Primary Window", True)
        dpg.start_dearpygui()
        dpg.destroy_context()

    # Get the file and shows it in the appropriate window
    def getFile(self, sender, app_data):
        imagePath = app_data.get("file_path_name")     
        self._currentFile = imagePath
        print("Getting file: ", imagePath)
        imageOperations.showImage(imagePath, self)

    def getMaskFolder(self, sender, app_data):
        dpg.hide_item("getMaskFolder")
        folderPath = app_data.get("file_path_name")
        print("saving mask!")
        imageOperations.saveImage(self, folderPath, "saveMask")

    def getFrameFolder(self, sender, app_data):
        dpg.hide_item("getFrameFolder")
        folderPath = app_data.get("file_path_name")
        print("saving frames!")
        imageOperations.saveImage(folderPath, "saveFrames")

    def getResultFolder(self, sender, app_data):
        dpg.hide_item("getResultFolder")
        folderPath = app_data.get("file_path_name")
        print("saving result!")
        imageOperations.saveImage(folderPath, "saveResult")

    # Get the selected function and shows the appropriate window
    def getFunctionHeader(self, sender, app_data):
        selected = self._paramLabel.get(app_data)
        for function in self._paramLabel:
            current = self._paramLabel[function]
            if current == 0:
                pass
            elif selected != current:
                dpg.hide_item(current)
            else:
                dpg.show_item(current)


    def drawScreen(self, sender):
        """
        Draws the given image to the main window screen thing

        :param image: The image to be drawn
        """
        # TO DO: update this when finalized parameters
        '''
        if (self._currentFile == "Empty"):
            dpg.show_item(59)
        else:
            dpg.hide_item(59)
        '''    
        # TO DO: add notif for if missing parameters!
        #params = dpg.get_item_children(37)
        #print(params)
        img = Image.open(self._currentFile)
        imSmear = ImageSmearer(img)
        
        brightMin, brightMax = self.updateParameters()
        smeared = imSmear.brightness_smear(threshold=(brightMin, brightMax))
        smeared_data = np.asarray(smeared, dtype=np.float32)  # change data type to 32bit floats
        texture_data = np.true_divide(smeared_data, 255.0)
        imgHeight, imgWidth = smeared.height, smeared.width
        texture_data = texture_data.reshape(-1)
        smeared.show()
        dpg.add_raw_texture(width=imgWidth, height=imgHeight, default_value=texture_data, tag="texture_tag1", parent=45,format=dpg.mvFormat_Float_rgb)
        
        #dpg.set_value("texture_tag", texture_data)
        #functions.update_dynamic_textures(smeared_data)
        img.close() #test this
        dpg.delete_item(35, children_only=True)
        dpg.add_image("texture_tag1", parent="image display")

    def enableGaussian(object, sender, app_data):
        if app_data == True:
            dpg.configure_item(63, enabled=True)
        else:
            dpg.configure_item(63, enabled=False)

    def enableBoxes(self, sender, app_data):
        if app_data == True:
            for boxNum in self._boxHolders:
                boxControls = self._boxHolders[boxNum]
                dpg.configure_item(boxControls[0], enabled=True)
                dpg.configure_item(boxControls[1], enabled=True)
            dpg.configure_item("numBox", enabled=True)
        else:
            for boxNum in self._boxHolders:
                boxControls = self._boxHolders[boxNum]
                dpg.configure_item(boxControls[0], enabled=False)
                dpg.configure_item(boxControls[1], enabled=False)
            dpg.configure_item("numBox", enabled=False)

    def showBoxes(self, sender, app_data):
        numBoxes = int(app_data)
        self._numBox = numBoxes
        for boxNum in self._boxHolders:
            boxControls = self._boxHolders[boxNum]
            if int(boxNum) <= numBoxes:
                dpg.show_item(boxControls[0])
                dpg.show_item(boxControls[1])
                dpg.show_item(boxControls[2])
                dpg.show_item(boxControls[3])
            else:
                dpg.hide_item(boxControls[0])
                dpg.hide_item(boxControls[1])
                dpg.hide_item(boxControls[2])
                dpg.hide_item(boxControls[3])

    def makeMask(self, sender):
        if (self._currentFile == "Empty"):
            dpg.show_item(84)
            print("NO FILE!!")
        else:
            dpg.hide_item(84)
            print("Masking: ", self._currentFile)
            self._currentMask = imageOperations.makeMask(self, sender)

    def enableCustom(self, sender, app_data):
        if app_data == "Custom":
            dpg.configure_item("userDegrees", enabled=True)
        else:
            dpg.configure_item("userDegrees", enabled=False)

        if app_data == "None":
            dpg.configure_item("stringX", enabled=True)
            dpg.configure_item("stringY", enabled=True)
        else:
            dpg.configure_item("stringX", enabled=False)
            dpg.configure_item("stringY", enabled=False)

    def smear(self, sender):
        if (self._currentFile == "Empty"):
            dpg.show_item(100)
            print("NO FILE!!")
        else:
            dpg.hide_item(100)
            print("Smearing: ", self._currentFile)
            self._currentResult = imageOperations.doSmear(self, sender)

    def showTexRegistries(sender):
        dpg.show_item(22)
        dpg.show_item(23)
        dpg.show_item(24)

    def updateParameters(sender):
        """
        Updates the GUI to reflect the current list of controlled parameters.
        """
        
        brightness = dpg.get_item_children(38)

        brightThreshMin = brightness[1][1]
        brightThreshMax = brightness[1][3]
        #print(dpg.get_value(brightThreshMin))
        #print(dpg.get_value(brightThreshMax))
        brightMin = int(dpg.get_value(brightThreshMin))
        brightMax = int(dpg.get_value(brightThreshMax))
        
        return brightMin, brightMax

    def controlParameter(self, getterFn, setterFn, controlType):
        """
        Marks that a parameter is to be controlled by the GUI.  

        :param getterFn: The getter function of the desired parameter.
        :param setterFn: The setter function of the desired parameter.
        :param controlType: How the parameter will be controlled in the GUI.
        """
        self.__control.append({
                'getter': getterFn, 
                'setter': setterFn, 
                'control': controlType
        })

    def setMaxFrames(self, sender, app_data):
        self._maxFrames = app_data
        #dpg.configure_item(63, max_value = self._maxFrames)

    
