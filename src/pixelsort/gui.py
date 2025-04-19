from PIL import Image
import pixelsort.pixelsmear as pixelsmear
import pixelsort.imageOperations as imageOperations 
from pixelsort.imageOperations import SmearRunner
from pixelsort.imageOperations import get_scaling
import dearpygui.dearpygui as dpg
import numpy as np

import platform
if platform.system() == "Windows":
    print("OS = WINDOWS")
    from ctypes import windll
    import pywinstyles
    OS_WIN = True
else:
    print("OS != WINDOWS")
    OS_WIN = False

class GUI:

    # Constructor
    def __init__(self):
        
        self._currentFile = "Empty"

        # Holds the item number of the Operation
        self._paramLabel = {
                    "---": 0, "Masking": 54, "Transformations": 89, "Frame Selector": 119
                    }
        
        # Parameters for Masking
        self._maskPath = None
        self._numBox = 1
        self._boxHolders = {
            # [0], [1] hold the inputs; [2], [3] hold the texts
            "1": (72, 74, 71, 73), "2": (76, 78, 75, 77), "3": (80, 82, 79, 81)
        }

        # Parameters for Transformations and Frame Selector
        self._maxFrames = 1
        self._currentFrames = None
        self._currentResult = None
        self._frameHeight = 1
        self._frameWidth = 1

        self._loadedImages = {
            # panel tag : {image tag : (original width, original height)}
        }

        # hold the SmearRunner for later polling, give it garbage values to avoid crashes
        self.smear_runner = None

        self._initDPG()

    def _initDPG(self):
        dpg.create_context()

        # Initialize registries where the images will be stored
        dpg.add_texture_registry(label="BaseImgRegistry", show=False, tag="registry_BaseImg")
        dpg.add_texture_registry(label="MaskImgRegistry", show=False, tag="registry_MaskImg")
        dpg.add_texture_registry(label="VFRegistry", show=False, tag="registry_VF")
        dpg.add_texture_registry(label="OutputImgRegistry", show=False, tag="registry_OutputImg")
        
        # Unique file dialogs for each purpose 
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
            # The menu bar
            with dpg.menu_bar():
                with dpg.menu(label="File"):
                    dpg.add_menu_item(label="Open File", callback=lambda: dpg.show_item("getFile"))
                    dpg.add_menu_item(label="Save Result", callback=lambda: dpg.show_item("getResultFolder"))
                with dpg.menu(label="Resources"):
                    dpg.add_menu_item(label="DearPyGUI Documentation", callback= lambda: dpg.show_documentation())
                    dpg.add_menu_item(label="Item Registry", callback= lambda: dpg.show_item_registry())
                    dpg.add_menu_item(label="Texture Registry", callback=self.showTexRegistries)
            
            # Where the images are painted
            with dpg.child_window(label="image tabs", width=850, height=700,
                                  #resizable_x=True, resizable_y=True,
                                  pos=[10,30], tag="window_ImageTabs"):
                with dpg.tab_bar(label = "navigate"):
                    with dpg.tab(label = "Base Image"):
                        dpg.add_child_window(label = "originalImage", width=835, height=660, horizontal_scrollbar=True, tag="panel_BaseImg")
                    with dpg.tab(label = "Mask"):
                        dpg.add_child_window(label = "maskImage", width=835, height=660, horizontal_scrollbar=True, tag="panel_MaskImg")
                    with dpg.tab(label = "Vector Field"):
                        dpg.add_child_window(label = "vectorField", width=835, height=660, horizontal_scrollbar=True, tag="panel_VectorField")
                    with dpg.tab(label = "Output Image"):
                        dpg.add_child_window(label = "outputImage", width=835, height=660, horizontal_scrollbar=True, tag="panel_OutputImg")

            # Operations window
            with dpg.child_window(label="Operations", width=400, height=700, pos=[870,30], tag="window_Operations"):
                funcs = ["---", "Masking", "Transformations", "Frame Selector"]
                dpg.add_text("Select an operation:", pos=[10, 5])
                dpg.add_combo(funcs, callback=self.getFunctionHeader, width=380, pos=[10, 30], default_value="---")

                # intro window (---)
                with dpg.child_window(label="---", width=380, height=490, pos=[10,55], show=False, tag="Intro"):
                    pass

                # Masking Window
                with dpg.child_window(label="Masking", width=380, height=490, pos=[10, 55], show=False, tag="Masking"):
                    
                    # Type of Mask user wants to generate
                    dpg.add_text("Masking by: ", pos=[10,10])
                    typeMasks = ["Brightness", "None"]
                    dpg.add_radio_button(typeMasks, label="typeMasks", horizontal=True, pos=[10, 30], default_value="Brightness")

                    # Thresholds if the type of mask is "Brightness"
                    dpg.add_text("Thresholds:", pos=[10, 60])
                    dpg.add_text("Min. Thresh", pos=[10, 80])
                    dpg.add_input_text(tag="minThresh", width=50, pos=[100, 80], default_value=70)
                    dpg.add_text("Max. Thresh", pos=[160, 80])
                    dpg.add_input_text(tag="maxThresh", width=50, pos=[250, 80], default_value=120)

                    # Gaussian Filter option
                    dpg.add_text("Apply Gaussian filter to image?", pos=[10, 110])
                    dpg.add_checkbox(tag="doGaussian",pos =[240, 110], callback=self.enableGaussian)
                    dpg.add_text("Strength of Gaussian:", pos=[10, 135])
                    dpg.add_input_float(tag="blurStrength", width=100, pos=[170, 135], enabled=False, default_value=0)

                    # Box Mask option
                    dpg.add_text("Select box(es) to bind the mask?", pos=[10, 170])
                    dpg.add_checkbox(tag="doBox",pos =[240, 170], callback=self.enableBoxes)
                    dpg.add_text("How many boxes would you like?", pos=[10, 195])
                    numBox = ["1", "2", "3"]
                    dpg.add_combo(numBox, width=50, default_value="1", pos=[240, 195], callback=self.showBoxes, tag="numBox", enabled=False)
                    dpg.add_text("Please input in form: x, y", pos=[10, 220])

                    # Up to 3 boxes can be made
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

                    # Invert boxes
                    dpg.add_text("Invert Box(es)?", pos=[10, 390])
                    dpg.add_checkbox(tag="invertBox",pos =[200, 390])
                    
                    # Sends the call to make the mask given all the above information
                    # Shows a message if no image has been loaded or if no mask exists
                    dpg.add_button(label="Create Mask", pos=[10, 0.94*dpg.get_item_height("Masking")], 
                               callback=self.makeMask, tag="makeMask")
                    dpg.add_text("No image selected.", pos=[10, 0.90*dpg.get_item_height("Masking")], show=False)

                    dpg.add_button(label="Save Mask", pos=[0.78*dpg.get_item_width("Masking"), 0.94*dpg.get_item_height("Masking")], 
                               callback=lambda: dpg.show_item(88) if self._maskPath == None else dpg.show_item("getMaskFolder"),
                                 tag="saveMask")
                    dpg.add_text("No mask exists.", pos=[0.68*dpg.get_item_width("Masking"), 0.90*dpg.get_item_height("Masking")], show=False, tag="text_NoMaskError")

                # Transformation Window
                with dpg.child_window(label="Transformations", width=380, height=590, pos=[10, 55], show=False, tag="Transformations"):
                    
                    # Controls directions and allows user input for basic equations
                    with dpg.collapsing_header(label="Directions"):
                        with dpg.child_window(label="DirectionWindow", width=360, height=220, tag="Direction"):
                            dpg.add_text("Select a direction: ", pos=[10,10])
                            directions = ["Left", "Right", "Up", "Down", "Custom", "None"]
                            dpg.add_combo(directions, label="directions", pos=[10, 30],
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

                    # Takes in a number to be the max number of frames generated
                    with dpg.collapsing_header(label="Max Frames", tag="selectFrames"):
                        with dpg.child_window(label="MaxFramesWindow", width=360, height=75):
                            dpg.add_text("Set the value of max frames: ", pos=[10,10])
                            dpg.add_input_int(tag="max_frames", pos=[10,30], width=75, callback = self.setMaxFrames, default_value=10,
                                        min_value=1, min_clamped=True)
                    
                    # Selects a preset vector field and applies if it the user likes
                    # Overrides the "Directions" input
                    with dpg.collapsing_header(label="Vector Field"):
                        with dpg.child_window(label="VFWindow", width=360, height=110, tag="VectorField"):
                            dpg.add_text("Select a preset vector field: ", pos=[10,10])
                            presetField = ["Border", "Chaotic Spiral", "Collapse", "Cross", "Explosion",
                                            "Orbit", "Plus", "Spiral","Star", "Wave"]
                            dpg.add_combo(presetField, width=200, default_value="Border", callback=imageOperations.showVF, user_data=self,
                                            pos=[10, 30], tag="presetField")
                            dpg.add_text("Apply vector field?", pos=[10, 60])
                            dpg.add_checkbox(tag="doVectorField",pos =[200, 60])
                            dpg.add_text("Note: this will override 'Direction' inputs", pos=[10, 80])

                    # for some unholy reason, removing this causes the contents of frame selection to disappear
                    dpg.add_spacer(width=0, height=0) 

                    # Sends the call to smear the image given all the above information
                    # Shows a message if no image has been loaded or if no smear exists    
                    dpg.add_button(label="Smear", pos=[10, 0.94*dpg.get_item_height("Transformations")], 
                               callback=self.smear, tag="smear")
                    dpg.add_text("No image selected.", pos=[10, 0.90*dpg.get_item_height("Transformations")], show=False, tag="text_SmearNoImageError")
                    dpg.add_button(label="Save Smear", pos=[0.76*dpg.get_item_width("Transformations"), 0.94*dpg.get_item_height("Transformations")], 
                               callback=lambda: dpg.show_item("text_SmearNoSmearError") if self._currentResult is None
                                 else dpg.show_item("getResultFolder"), tag="saveSmear")
                    dpg.add_text("No smear exists.",
                                pos=[0.68*dpg.get_item_width("Transformations"), 0.90*dpg.get_item_height("Transformations")], show=False, tag="text_SmearNoSmearError")

                # Frame Selector Window
                with dpg.child_window(label="Frame Selector", width=380, height=490, pos=[10, 55], show=False, tag="FrameSelector"):
                    
                    # Allows the user to select a frame given the max number of frames they gave in "Transformations"
                    dpg.add_text("Selected Frame: ", pos=[10,10])
                    dpg.add_slider_int(tag="selectedFrame", no_input=False, pos=[10, 30],
                                        min_value=1, max_value=1, callback=imageOperations.selectFrame, user_data=self, default_value=self._maxFrames)
                    dpg.add_button(label="Save Frames", pos=[0.75*dpg.get_item_width("FrameSelector"), 0.94*dpg.get_item_height("FrameSelector")], 
                               callback=lambda: dpg.show_item("text_FrameNoSmearError") if self._currentResult is None else dpg.show_item("getFrameFolder"),
                                 tag="saveFrames")
                    dpg.add_text("No smear exists.",
                                pos=[0.68*dpg.get_item_width("FrameSelector"), 0.90*dpg.get_item_height("FrameSelector")], show=False, tag="text_FrameNoSmearError")

                dpg.add_progress_bar(default_value=0, width=-1, overlay="0%", tag="smearProgress", pos=[7, dpg.get_item_height("window_Operations")-30])

        # change child window height, width, position, on window size change
        dpg.set_viewport_resize_callback(callback=self.on_viewport_resize)

        dpg.create_viewport(title='Curved Pixel Sorting via Simple Equations and Vector Fields', width=1300, height=800, min_height=780, min_width=500)
        dpg.setup_dearpygui()

        # fire component size scaling once
        self.on_viewport_resize(None, None)

        # set icon
        dpg.set_viewport_large_icon(r"src\pixelsort\cpssevf_icon.ico")
        dpg.set_viewport_small_icon(r"src\pixelsort\cpssevf_icon.ico")

        dpg.show_viewport()
        dpg.set_primary_window("Primary Window", True)

        # windows specific titlebar styling
        if(OS_WIN):
            # hwnd = windll.user32.GetActiveWindow()
            hwnd = windll.user32.FindWindowW(None, 'Curved Pixel Sorting via Simple Equations and Vector Fields')
            #pywinstyles.change_header_color(hwnd, color="black")
            pywinstyles.apply_style(hwnd,style="acrylic")
            print("title color set")

        # dpg.start_dearpygui() 

        stack_isSet = False
        while dpg.is_dearpygui_running():
            # render loop
            # very bad hack to get the progress bar working
            if(self.smear_runner is not None): #exists
                if(self.smear_runner.is_running()):
                    self.setProgressBar(self.smear_runner.get_progress())
                    stack_isSet = False
                elif not stack_isSet: # is finished
                    self.setProgressBar(1.0)
                    frameNum = None
                    frame_stack = self.smear_runner.get_frame_stack()
                    for frame in range(self._maxFrames):
                        frameNum = str(frame)
                        smearFrame = frame_stack[frame]
                        smeared_data = np.asarray(smearFrame, dtype=np.float32)  # change data type to 32bit floats
                        texture_data = np.true_divide(smeared_data, 255.0)
                        imgHeight, imgWidth = self.smear_runner.get_shape()
                        self._frameHeight = imgHeight
                        self._frameWidth = imgWidth
                        dpg.add_raw_texture(width=imgWidth, height=imgHeight, default_value=texture_data, tag="frame"+frameNum, 
                                            parent="registry_OutputImg",format=dpg.mvFormat_Float_rgba)
                    
                    w, h, x , y = get_scaling("panel_OutputImg",(imgWidth,imgHeight))
                    dpg.add_image("frame"+frameNum, width=w, height=h, parent="panel_OutputImg", pos=[x,y], tag="image_Output")
                    self._loadedImages.setdefault("panel_OutputImg", {})["image_Output"] = (imgWidth,imgHeight)
                    self._currentFrames = frame_stack
                    self._currentResult = self._currentFrames[(self._maxFrames)-1]
                    stack_isSet = True
                    self.smear_runner = None
                    dpg.configure_item("selectedFrame", max_value = self._maxFrames)
            dpg.render_dearpygui_frame()
            pass
        dpg.destroy_context()

    def on_viewport_resize(self, sender, app_data):
        """
        Callback function to change component scaling and position on window resize
        """
        t_w = dpg.get_viewport_client_width()
        t_h = dpg.get_viewport_client_height()

        sidebar_w = 400
        margin = 10
        top_bar = 30

        i_w = t_w - sidebar_w - margin*2
        i_h = t_h - top_bar - margin

        # image tabs
        dpg.configure_item("window_ImageTabs", width = i_w, height = i_h)
        for panel_tag in ("panel_BaseImg", "panel_MaskImg", "panel_VectorField", "panel_OutputImg"):
            dpg.configure_item(panel_tag, width = i_w - 15, height= i_h - 35)
        
        # operation sidebar
        dpg.configure_item("window_Operations", pos = [i_w + margin, top_bar], width = sidebar_w, height = i_h)
        dpg.configure_item("smearProgress", pos=[7, dpg.get_item_height("window_Operations")-30])

        # rescale preview images
        for panel_tag, images in self._loadedImages.items():
            for img_tag, (origin_w, origin_h) in images.items():
                w, h, x, y = get_scaling(panel_tag, (origin_w,origin_h))
                dpg.configure_item(img_tag, width=w, height=h, pos=[x,y])

    def setProgressBar(self,progress):
        perc = f"{progress * 100:.2f}"
        if progress < 0.33:
            text = f"warping positions - {perc}%"
        elif progress < 0.66:
            text = f"smearing colors - {perc}%"
        elif progress < 1:
            text = f"rendering output - {perc}%"
        else: # >= 1
            text = f"rendering complete - {perc}%"
        dpg.set_value("smearProgress",progress)
        dpg.configure_item("smearProgress",overlay=text)

    # Get the file and shows it in the appropriate window
    def getFile(self, sender, app_data):
        imagePath = app_data.get("file_path_name")     
        self._currentFile = imagePath
        print("Getting file: ", imagePath)
        imageOperations.showImage(imagePath, self)

    # Gets the appropriate file dialog, keeps the file path, and 
    # sends in the type of save being performed
    def getMaskFolder(self, sender, app_data):
        dpg.hide_item("getMaskFolder")
        folderPath = app_data.get("file_path_name")
        print("saving mask!")
        imageOperations.saveImage(self, folderPath, "saveMask")

    def getFrameFolder(self, sender, app_data):
        dpg.hide_item("getFrameFolder")
        folderPath = app_data.get("file_path_name")
        print("saving frames!")
        imageOperations.saveImage(self, folderPath, "saveFrames")

    def getResultFolder(self, sender, app_data):
        dpg.hide_item("getResultFolder")
        folderPath = app_data.get("file_path_name")
        print("saving result!")
        imageOperations.saveImage(self, folderPath, "saveResult")

    # Get the selected operation and shows the appropriate window
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

    # Enables the interaction of the Gaussian input and Box inputs
    def enableGaussian(object, sender, app_data):
        if app_data == True:
            dpg.configure_item("blurStrength", enabled=True)
        else:
            dpg.configure_item("blurStrength", enabled=False)

    # If the user wishes to have bounding boxes, enable the text fields
    def enableBoxes(self, sender, app_data):
        if app_data == True:
            dpg.configure_item("numBox", enabled=True)
            for boxNum in self._boxHolders:
                boxControls = self._boxHolders[boxNum]
                dpg.configure_item(boxControls[0], enabled=True)
                dpg.configure_item(boxControls[1], enabled=True)
        else:
            dpg.configure_item("numBox", enabled=False)
            for boxNum in self._boxHolders:
                boxControls = self._boxHolders[boxNum]
                dpg.configure_item(boxControls[0], enabled=False)
                dpg.configure_item(boxControls[1], enabled=False)

    # Show the boxes according to the number of boxes the user desires
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

    # Make the mask and saves it to the constructor
    def makeMask(self, sender):
        if (self._currentFile == "Empty"):
            dpg.show_item("text_NoMaskError")
            print("NO FILE!!")
        else:
            dpg.hide_item("text_NoMaskError")
            print("Masking: ", self._currentFile)
            self._maskPath = imageOperations.makeMask(self, sender)

    # Enables the interaction of the custom degrees 
    # or user-inputted equations
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

    # Smears the image
    def smear(self, sender):
        if (self._maskPath == None):
            dpg.show_item("text_SmearNoImageError")
            print("NO FILE!!")
        else:
            dpg.hide_item("text_SmearNoImageError")
            print("Smearing: ", self._currentFile)
            imageOperations.doSmear(self, sender)
            # todo: refactor this
            # self._currentFrames = imageOperations.doSmear(self, sender)
            # self._currentResult = self._currentFrames[(self._maxFrames)-1]

    # Shows all the texture registries
    def showTexRegistries(sender):
        dpg.show_item("registry_BaseImg")
        dpg.show_item("registry_MaskImg")
        dpg.show_item("registry_VF")
        dpg.show_item("registry_OutputImg")

    # Sets the max frames
    def setMaxFrames(self, sender, app_data):
        self._maxFrames = app_data
        # dpg.configure_item("selectedFrame", max_value = self._maxFrames)