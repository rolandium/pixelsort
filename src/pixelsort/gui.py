from PIL import Image
import dearpygui.dearpygui as dpg
import dearpygui.demo as demo

class GUI:
    def __init__(self):
        # constructor
        print("init gui")
        self._control = []
        self._windowLabel = 'guiWindow'
        self._paramLabel = 'guiParams'
        self._screenLabel = "guiScreen"
        self._initDPG()

    def _initDPG(self):
        dpg.create_context()
        dpg.create_viewport(title='pixelsorter',width=600,height=300)
        # with dpg.window(label=self.__windowLabel,no_collapse=True):
        #     dpg.add_text("Hello, world")
        #     dpg.add_button(label="Save")
        #     dpg.add_input_text(label="string", default_value="Quick brown fox")
        #     dpg.add_slider_float(label="float", default_value=0.273, max_value=1)
        demo.show_demo()
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()


    def drawScreen(self, image: Image):
        """
        Draws the given image to the main window screen thing

        :param image: The image to be drawn
        """
        # TODO: will likely need to use dynamic texture
        pass

    def updateParameters(self):
        """
        Updates the GUI to reflect the current list of controlled parameters.
        """
        pass

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
        
    
