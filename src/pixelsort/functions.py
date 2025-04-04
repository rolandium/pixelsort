import dearpygui.dearpygui as dpg
import cv2 as cv
from PIL import Image

def callback(sender, app_data, user_data):
    print('OK was clicked.')
    print("Sender: ", sender)
    print("App Data: ", app_data)
    print("user data:", user_data)

def cancel_callback(sender, app_data):
    print('Cancel was clicked.')
    print("Sender: ", sender)
    print("App Data: ", app_data)

def openFile(sender, app_data):
    imagePath = app_data.get("file_path_name")
    showImage(imagePath)
    #print('OK was clicked.')
    print("Sender: ", sender)
    print("App Data: ", app_data)

def showImage(imagePath):
    width, height, channels, data = dpg.load_image(imagePath)
    with dpg.texture_registry(show=False):
        dpg.add_dynamic_texture(width=width, height=height, default_value=data, tag="texture_tag")
    dpg.add_image("texture_tag", parent="image display")
    

def update_dynamic_textures(sender, app_data, user_data):
    new_texture_data = dpg.get_value(sender)

    dpg.set_value("texture_tag", new_texture_data)

def saveImage():
    dpg.save_image
    print("blank")

def print_me(sender):
    print(f"Menu Item: {sender}")

