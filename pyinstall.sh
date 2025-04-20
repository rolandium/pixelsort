#!/bin/bash
# Script to package the program as an executable

# On Windows, first activate the poetry env using 
#    Invoke-Expression (poetry env activate)
# then manually run the first command in powershell, and then manually remove the build folder and files in the rm command

eval $(poetry env activate)
pyinstaller --onefile --windowed --icon=assets/cpssevf_icon.ico --name pixelsort src/pixelsort/main.py 
cp dist/pixelsort* .
rm -rf build dist pixelsort.spec