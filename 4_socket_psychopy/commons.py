# common needs
from glob import glob
import os
import json
import numpy as np
from . import mh2opengl
import bvh, getpath, gui3d, mh, mhmain, animation

from core import G
from collections import OrderedDict
# straight from MakeHuman's scripting plugin
def updateModelingParameters(dictOfParameterNameAndValue):
    human = gui3d.app.selectedHuman
    for key, value in dictOfParameterNameAndValue.iteritems():
        modifier = human.getModifier(key)
        modifier.setValue(value)
    human.applyAllTargets()
    mhmain.SymmetryAction(human, 1).do()
    mh.redraw()

def load_pose_modifiers(filename):
    if filename is None or filename == "None":
        modifiers, _ = get_blank_pose()
        return modifiers
    with open(filename, 'r') as f:
        return json.load(f, object_pairs_hook=OrderedDict)['unit_poses']
    return None

def get_blank_pose(skip_blank_pose=False):
    human = gui3d.app.selectedHuman
    base_bvh = bvh.load(getpath.getSysDataPath('poseunits/face-poseunits.bvh'), allowTranslation="none")
    base_anim = base_bvh.createAnimationTrack(human.getBaseSkeleton(), name="Expression-Face-PoseUnits")

    poseunit_json = json.load(open(getpath.getSysDataPath('poseunits/face-poseunits.json'),'rb'), object_pairs_hook=OrderedDict)
    # the names of the changeable facial expression features
    poseunit_names = poseunit_json['framemapping']
    modifiers = dict(zip(poseunit_names, len(poseunit_names)*[0.0]))
    base_poseunit = animation.PoseUnit(base_anim.name, base_anim.data[:base_anim.nBones*len(poseunit_names)], poseunit_names)
    if skip_blank_pose:
        return modifiers, None
    return modifiers, base_poseunit

def set_pose(pose_modifiers):
    human = gui3d.app.selectedHuman
    modifiers, base_poseunit = get_blank_pose()

    for key in pose_modifiers:
        modifiers[key] = pose_modifiers[key]
    # see which values are different so only those are updated
    posenames = []
    posevalues = []
    for pname, pval in modifiers.items():
        posenames.append(pname)
        posevalues.append(pval)
    if len(posenames) > 0:
        panim = base_poseunit.getBlendedPose(posenames, posevalues)
        panim.disableBaking = False

        human.addAnimation(panim)
        human.setActiveAnimation(panim.name)
        human.refreshPose()
        

def get_shape_params():
    human = gui3d.app.selectedHuman
    
    param_dict = {}
    for key in human.modifierNames:
        param_dict[key] = human.getModifier(key).getValue()
    return param_dict

def get_params(change_key):
    if change_key == 'expression':
        return load_pose_modifiers("None")
    elif change_key == 'model':
        return get_shape_params()
    elif change_key == "rot_X":
        gui3d.app.modelCamera.getRotation()[0]
    elif change_key == "rot_Y":
        gui3d.app.modelCamera.getRotation()[1]
    else:
        return 0.0

def save_model(path, name):
    human = gui3d.app.selectedHuman
    filename = os.path.join(path,name + ".mhm")
    human.save(filename,name)
    
def render(out_path, settings, image_count=0):
    if not 'scene' in settings:
        settings['scene'] = G.app.scene
    img = mh2opengl.Render(settings)
    img_path = os.path.join(out_path, "render_{0}.png".format(image_count))
    img.save(img_path)
    return img_path


from numbers import Number

def add(a, change):
    # just numbers
    if isinstance(a, Number):
        return a + change
    
    summed = {}
    for key in a:
        summed[key] = a[key] + change[key]
    return summed

def difference(b, a, bPercent):
    # get the difference between the values
    # if the values are dictionaries, make sure to assign values of 0 when the keys do not exist
    if isinstance(a, Number):
        return b-a

    diff = {}
    for key in b:
        if not key in a:
            a[key] = 0
    for key in a:
        if not key in b:
            b[key] = 0
        
        diff[key] = (b[key] - a[key])*(bPercent/100.)
    return diff