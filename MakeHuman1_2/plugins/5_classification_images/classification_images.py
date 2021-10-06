#!/usr/bin/env python3
# -*- coding: utf-8 -*-


######################## _Add_ left/right to expression dropdown


"""

**Authors:**           Jason Hays

"""

import os

import algos3d
import animation

import gui
import getpath
import mh
import log
from core import G
import re

from glmodule import grabScreen
import gui3d
import animation
import bvh
import numpy as np
from collections import OrderedDict
import json

#from scipy.stats import beta
# https://people.sc.fsu.edu/~jburkardt/py_src/prob/prob.html

# make human doesn't have pandas by default, so
# make a simple one for this.
class DataFrame(object):
    def __init__(self):
        self.data = OrderedDict()
    def append(self, dictionary):
        for key in dictionary:
            if not key in self.data:
                self.data[key] = []
            self.data[key].append(dictionary[key])

    def to_csv(self, filename):
        with open(filename, 'w') as f:
            # headers
            for key in self.data:
                f.write("{},".format(key))
            f.write("\n")
            # contents
            rows = len(self.data[key])
            for row in range(rows):
                for key in self.data:
                    f.write("{},".format(self.data[key][row]))
                f.write("\n")


def do_op(classification_image_settings, save_path = "./tmp", render_function = None):
    generate_CI_info(save_path=save_path, render_function=render_function, **classification_image_settings)
    

def get_keys(pre_regex_parameters, my_keys):
    keys = []
    for shapes in pre_regex_parameters:
        regex_shapes = shapes
        if "," in shapes:
            tmp = shapes.split(",")
            regex_shapes = "("
            ltmp = len(tmp)
            for si,s in enumerate(tmp):
                regex_shapes += s
                if si < ltmp-1:
                    regex_shapes+="|"
            regex_shapes+=")"
        regex = re.compile(regex_shapes, flags=re.DOTALL)

        for key in my_keys:
            if re.search(regex, key):
                keys.append(key)
    return keys


def get_range(shape_parameter):
    # pose parameters are all 0 to 1
    #  shape parameters are sometimes -1 to 1
    if "|" in shape_parameter:
        return -1.0, 1.0
    return 0.0, 1.0

def generate_CI_info(base_model, trials, shape_parameters, pose_parameters, save_path, SD=.3, rot_X=0, rot_Y=0, material_file="young_caucasian_avg", render_function=None):
    # the base_model is a path to the model
    # the shape parameters and pose_parameters are lists of parameters to use (convert to regex)
    gui3d.app.loadHumanMHM(base_model)
    human = G.app.selectedHuman
    mat = human.material
    mat.fromFile(getpath.getSysDataPath('skins/'+material_file+"/"+material_file+".mhmat"))
    
    gui3d.app.setFaceCamera()
    rotation = gui3d.app.modelCamera.getRotation()
    gui3d.app.rotateCamera(0,rot_X-rotation[0])
    gui3d.app.rotateCamera(1,rot_Y-rotation[1])

    shapes = get_listed_shape_params(model_keys)#get_shape_params()
    poses,_ = get_blank_pose()
    shape_keys_to_jitter = get_keys(shape_parameters, model_keys)
    expression_keys_to_jitter = get_keys(pose_parameters, expression_keys)
    #shapes = merge_dictionaries(shapes, dict(zip(model_keys, [0]*model_data_length)))
    poses = merge_dictionaries(poses, dict(zip(expression_keys, [0]*expression_data_length)))

    df = DataFrame()

    for trial in range(trials):
        # the sample
        my_shapes = shapes.copy()
        my_poses = poses.copy()
        # the row to add to the data frame
        all_data = OrderedDict()
        all_data["anti"] = False
        all_data["trial"] = trial
        for key in my_shapes:
            if key in shape_keys_to_jitter:
                start, end = get_range(key)
                if my_shapes[key] == start or my_shapes[key] == end:
                    log.message("Unable to alter shape parameter at the edge of its space: "+key)
                else:
                    while True:
                        value = my_shapes[key]
                        alter = np.random.normal(0, SD*(end-start))
                        if value+alter >= start and value+alter <= end and value-alter >= start and value-alter <= end:
                            my_shapes[key] += alter
                            break
                    
            all_data[key] = my_shapes[key]
        
        start, end = 0.0,1.0
        frac_range = SD*(end-start)
        for key in my_poses:
            if key in expression_keys_to_jitter:
                if my_poses[key] == start or my_poses[key] == end:
                    log.message("Unable to alter pose parameter at the edge of its space: "+key)
                else:
                    while True:
                        value = my_poses[key]
                        alter = np.random.normal(0, frac_range)
                        if value+alter >= start and value+alter <= end and value-alter >= start and value-alter <= end:
                            my_poses[key] += alter
                            break
                        
            all_data[key] = my_poses[key]
        
        df.append(all_data)
        updateModelingParameters(my_shapes)
        set_pose(poses)
        gui3d.app.redraw()

        if render_function:
            img = render_function[0](render_function[1])
            img.save(os.path.join(save_path, "{0:04d}_sample.png".format(trial)))

        # make the antisample
        sample_shapes = my_shapes.copy()
        sample_poses = my_poses.copy()
        my_shapes = shapes.copy()
        my_poses = poses.copy()
        # the row to add to the data frame
        all_data = OrderedDict()
        all_data["anti"] = True
        all_data["trial"] = trial
        for key in my_shapes:
            if key in shape_keys_to_jitter:
                start, end = get_range(key)
                if my_shapes[key] == start or my_shapes[key] == end:
                    pass
                else:
                    my_shapes[key] -= sample_shapes[key]-my_shapes[key]
                    
            all_data[key] = my_shapes[key]
        
        start, end = 0.0,1.0
        frac_range = SD*(end-start)
        for key in my_poses:
            if key in expression_keys_to_jitter:
                if my_poses[key] == start or my_poses[key] == end:
                    pass
                else:
                    my_poses[key] -= sample_poses[key]-my_poses[key]
                        
            all_data[key] = my_poses[key]

        df.append(all_data)
        updateModelingParameters(my_shapes)
        set_pose(poses)
        gui3d.app.redraw()

        if render_function:
            img = render_function[0](render_function[1])
            img.save(os.path.join(save_path, "{0:04d}_antisample.png".format(trial)))

    df.to_csv(os.path.join(save_path, "CI_data.csv"))

def save_model_special(path, name, all_params, i):
    human = gui3d.app.selectedHuman
    filename = os.path.join(path,name + ".mhm")
    human.save(filename)
    # also save mhpose file if it is applicable
    if 'expression' in all_params:
        with open(os.path.join(path,name + ".mhpose"), 'w') as f:
            expression = all_params['expression'][i]
            json.dump({"unit_poses":expression}, f)

def get_shape_params():
    human = gui3d.app.selectedHuman
    
    param_dict = {}
    for key in human.modifierNames:
        param_dict[key] = human.getModifier(key).getValue()
    return param_dict

def get_listed_shape_params(my_list):
    human = gui3d.app.selectedHuman
    
    param_dict = {}
    for key in my_list:
        param_dict[key] = human.getModifier(key).getValue()
    return param_dict

def merge_dictionaries(d1, d2):
    for key in d1:
        if not key in d2:
            d2[key] = d1[key]
    return d2

def load_pose_modifiers(filename):
    modifiers, _ = get_blank_pose()
    if filename is None or filename == "None":
        
        return modifiers
    with open(filename, 'r') as f:
        # need to keep all keys available from neutral expression for interpolation
        return merge_dictionaries(modifiers, json.load(f, object_pairs_hook=OrderedDict)['unit_poses'])
    return None

def delta_pose(pose_a, pose_b, over_frames, percentage):
    pose_delta = {}
    for key in pose_b:
        if not key in pose_a:
            pose_a[key] = 0.

    for key in pose_a:
        if not key in pose_b:
            pose_b[key] = 0.
        pose_delta[key] = (pose_b[key]-pose_a[key])*(percentage/100.)/float(over_frames)

    return pose_delta

def get_blank_pose():
    human = gui3d.app.selectedHuman
    base_bvh = bvh.load(getpath.getSysDataPath('poseunits/face-poseunits.bvh'), allowTranslation="none")
    base_anim = base_bvh.createAnimationTrack(human.getBaseSkeleton(), name="Expression-Face-PoseUnits")

    poseunit_json = json.load(open(getpath.getSysDataPath('poseunits/face-poseunits.json'),'rb'), object_pairs_hook=OrderedDict)
    # the names of the changeable facial expression features
    poseunit_names = poseunit_json['framemapping']
    modifiers = dict(zip(poseunit_names, len(poseunit_names)*[0.0]))
    base_poseunit = animation.PoseUnit(base_anim.name, base_anim.data[:base_anim.nBones*len(poseunit_names)], poseunit_names)
    return modifiers, base_poseunit

def set_pose(pose_modifiers):
    human = gui3d.app.selectedHuman
    modifiers, base_poseunit = get_blank_pose()

    for key in modifiers:
        if key in pose_modifiers:
            modifiers[key] = pose_modifiers[key]
    # see which values are different so only those are updated
    posenames = []
    posevalues = []
    for pname, pval in modifiers.items():
        #if pval != 0:
        posenames.append(pname)
        posevalues.append(pval)
    if len(posenames) > 0:
        panim = base_poseunit.getBlendedPose(posenames, posevalues)
        panim.disableBaking = False

        human.addAnimation(panim)
        human.setActiveAnimation(panim.name)
        human.refreshPose()

def get_frame(val, frames):
    frame = val
    if type(frame) == float:
        frame *= frames
        frame = min(int(np.round(frame,0)), frames-1)
    return frame

def delta_shape_params(params_dict1, params_dict2, over_frames, percentage):
    shape_delta = {}

    for key in params_dict1:
        shape_delta[key] = (params_dict2[key]-params_dict1[key])*(percentage/100.)/float(over_frames)

    return shape_delta

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

def get_change(key_frames, change_key, current_index, frames):
    #print(key_frames)
    #print(change_key)
    #print(current_index)
    #print(key_frames[change_key])
    frame_data, value = key_frames[change_key][current_index]
    extra = None
    frame = get_frame(frame_data, frames)
    if change_key == 'expression':
        current_percent = value[1]
        value = value[0]
        # there is no expression
        if value == "":
            data = None
        else:
            data = load_pose_modifiers(value)
            extra = current_percent
    elif change_key == "model":
        current_percent = value[1]
        value = value[0]
        # it's a model name
        if value != "":
            gui3d.app.loadHumanMHM(value)
        data = get_shape_params()
        extra = current_percent
    else:
        data = value
    return data, frame, extra

def difference(b, a, bPercent):
    # get the difference between the values
    # if the values are dictionaries, make sure to assign values of 0 when the keys do not exist
    if (isNumberType is not None and isNumberType(a)) or (Number is not None and isinstance(a, Number)):
        return b-a

    diff = {}
    for key in b:
        if not key in a:
            a[key] = 0.
    for key in a:
        if not key in b:
            b[key] = 0.
        
        diff[key] = (b[key] - a[key])*(bPercent/100.)
    return diff


isNumberType = None
Number = None
try:
    from numbers import Number
except:
    import operator
    isNumberType = operator.isNumberType


def add(a, change):
    # just numbers
    if (isNumberType is not None and isNumberType(a)) or (Number is not None and isinstance(a, Number)):
        return a + change
    
    summed = {}
    for key in a:
        summed[key] = a[key] + change[key]
    return summed

def multiply(a, change):
    # just numbers
    if (isNumberType is not None and isNumberType(a)) or (Number is not None and isinstance(a, Number)):
        return a * change
    
    prod = {}
    for key in a:
        if (isNumberType is not None and isNumberType(change)) or (Number is not None and isinstance(change, Number)):
            prod[key] = a[key] * change
        else:
            prod[key] = a[key] * change[key]
    return prod

def divide(a, change):
    # just numbers
    if (isNumberType is not None and isNumberType(a)) or (Number is not None and isinstance(a, Number)):
        if change != 0:
            return a / float(change)
        else:
            return a
    # dictionaries
    quo = {}
    for key in a:
        if (isNumberType is not None and isNumberType(change)) or (Number is not None and isinstance(change, Number)):
            if change != 0:
                quo[key] = a[key] / float(change)
            else:
                quo[key] = a[key]
        else:
            if change[key] != 0:
                quo[key] = a[key] / float(change[key])
            else:
                quo[key] = a[key]
    return quo
    


# straight from MakeHuman's scripting plugin
# changed iteritems for python 3
def updateModelingParameters(dictOfParameterNameAndValue):
    human = gui3d.app.selectedHuman
    #log.message("SCRIPT: updateModelingParameters("+str(dictOfParameterNameAndValue)+")")
    for key, value in iter(dictOfParameterNameAndValue.items()):
        modifier = human.getModifier(key)
        modifier.setValue(value)
    human.applyAllTargets()
    mh.redraw()

def updatePose():
    human = gui3d.app.selectedHuman
    human.refreshPose()

model_keys = tuple([key for key in get_shape_params()])
model_data_length = len(model_keys)

expression_keys = ("LeftBrowDown", "RightBrowDown", "LeftOuterBrowUp", "RightOuterBrowUp", "LeftInnerBrowUp", "RightInnerBrowUp", "NoseWrinkler", "LeftUpperLidOpen", "RightUpperLidOpen", "LeftUpperLidClosed", "RightUpperLidClosed", "LeftLowerLidUp", "RightLowerLidUp", "LeftEyeDown", "RightEyeDown", "LeftEyeUp", "RightEyeUp", "LeftEyeturnRight", "RightEyeturnRight", "LeftEyeturnLeft", "RightEyeturnLeft", "LeftCheekUp", "RightCheekUp", "CheeksPump", "CheeksSuck", "NasolabialDeepener", "ChinLeft", "ChinRight", "ChinDown", "ChinForward", "lowerLipUp", "lowerLipDown", "lowerLipBackward", "lowerLipForward", "UpperLipUp", "UpperLipBackward", "UpperLipForward", "UpperLipStretched", "JawDrop", "JawDropStretched", "LipsKiss", "MouthMoveLeft", "MouthMoveRight", "MouthLeftPullUp", "MouthRightPullUp", "MouthLeftPullSide", "MouthRightPullSide", "MouthLeftPullDown", "MouthRightPullDown", "MouthLeftPlatysma", "MouthRightPlatysma", "TongueOut", "TongueUshape", "TongueUp", "TongueDown", "TongueLeft", "TongueRight", "TonguePointUp", "TonguePointDown")
expression_data_length = len(expression_keys)
camera_data_length = 2