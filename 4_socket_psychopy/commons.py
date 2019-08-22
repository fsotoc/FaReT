# common needs
import gui3d
from glob import glob
import os
import mh
import mhmain
import numpy as np
from . import mh2opengl

# straight from MakeHuman's scripting plugin
def updateModelingParameters(dictOfParameterNameAndValue):
    human = gui3d.app.selectedHuman
    for key, value in dictOfParameterNameAndValue.iteritems():
        modifier = human.getModifier(key)
        modifier.setValue(value)
    human.applyAllTargets()
    mhmain.SymmetryAction(human, 1).do()
    mh.redraw()

def get_shape_params():
    human = gui3d.app.selectedHuman
    
    param_dict = {}
    for key in human.modifierNames:
        param_dict[key] = human.getModifier(key).getValue()
    return param_dict

def save_model(path, name):
    human = gui3d.app.selectedHuman
    filename = os.path.join(path,name + ".mhm")
    human.save(filename,name)
    
def render(out_path, settings, image_count=0):
    img = mh2opengl.Render(settings)
    img_path = os.path.join(out_path, "render_{0}.png".format(image_count))
    img.save(img_path)
    return img_path