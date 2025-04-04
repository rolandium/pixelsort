from PIL import Image
from pixelsorter import PixelSorter
import functions
import dearpygui.dearpygui as dpg
import numpy as np

class GUI:
    
    def __init__(self):
        # constructor
        print("init gui")
        self._control = []
        self._windowLabel = 'guiWindow'
        self._paramLabel = 'guiParams'
        self._screenLabel = "guiScreen"
        self._currentFile = ""
        self._initDPG()

    def _initDPG(self):
        dpg.create_context()
        
        with dpg.file_dialog(directory_selector=False, show=False, callback=self.getFile, id="file_dialog", width=700 ,height=400):
            #callback=functions.openFile
            dpg.add_file_extension(".png", color=(150, 255, 150, 255))
            dpg.add_file_extension(".jpg", color=(255, 0, 255, 255), custom_text="[header]")
        
        with dpg.window(tag="Primary Window"):
            with dpg.menu_bar():
                with dpg.menu(label="File"):
                    dpg.add_menu_item(label="Open", callback=lambda: dpg.show_item("file_dialog"))
                    dpg.add_menu_item(label="Save", callback=functions.saveImage())
                with dpg.menu(label="Resources"):
                    dpg.add_menu_item(label="Documentation", callback= lambda: dpg.show_documentation())
                    dpg.add_menu_item(label="Item Registry", callback= lambda: dpg.show_item_registry())
                    dpg.add_menu_item(label="Texture Registry", callback= lambda: dpg.texture_registry())
            dpg.add_child_window(tag="image display",
                                  resizable_x=True, resizable_y=True,
                                  pos=[0,30])
            
            with dpg.child_window(label="parameters",width=400, height=700,
                                  resizable_x=True, resizable_y=True,
                                  auto_resize_x=True, auto_resize_y=True,
                                  pos=[460,30]):
                dpg.add_text("Parameters")
                dpg.add_text("Brightness Threshold:", tag="bright_thresh", parent="update")
                dpg.add_text("Min", pos=[10,55])
                dpg.add_input_text(tag="bright_threshMin", pos=[40,55], width=30)
                dpg.add_text("Max", pos=[90,55])
                dpg.add_input_text(tag="bright_threshMax", pos=[120,55], width=30)
                dpg.add_button(label="Update Parameters", pos=[10, 70], callback=self.updateParameters, tag="update")
                dpg.add_button(label="Reset Parameters", pos=[10, 100], callback=self.resetImage, tag="reset")
        dpg.show_item_registry()

        dpg.create_viewport(title='Pixelsorting', width=1200, height=700)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("Primary Window", True)
        dpg.start_dearpygui()
        dpg.destroy_context()

    def getFile(self, sender, app_data):
        imagePath = app_data.get("file_path_name")
        self._currentFile = imagePath
        #showImage(imagePath)
        #print('OK was clicked.')
        print("Sender: ", sender)
        print("App Data: ", app_data)


    def drawScreen(self, image: Image):
        """
        Draws the given image to the main window screen thing

        :param image: The image to be drawn
        """
        # TODO: will likely need to use dynamic texture


    def updateParameters(sender):
        """
        Updates the GUI to reflect the current list of controlled parameters.
        """
        parameters = dpg.get_item_children(34)

        brightThreshMin = parameters[1][3]
        brightThreshMax = parameters[1][5]
        print(dpg.get_value(brightThreshMin))
        print(dpg.get_value(brightThreshMax))
        brightMin = int(dpg.get_value(brightThreshMin))
        brightMax = int(dpg.get_value(brightThreshMax))
        ps = PixelSorter()
        ps.image = Image.open('src/pixelsort/mountains.png').convert("RGB")
        print(np.array(ps.image).shape)
        sorted = ps.sortImage(brightMin, brightMax)
        sorted.show()

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
    
    def resetImage(self):
        print(self._currentFile)
    
