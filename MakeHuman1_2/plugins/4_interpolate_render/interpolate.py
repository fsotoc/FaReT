#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
import beta
beta_cdf = beta.beta_cdf



# every parameter, whether shape, expression, camera, etc
#  should be in key_frames and might have
# different Beta CDF rates at different times
# except for the frames key, which is an integer, key_frames is laid out like
#  {frames: int, key1: [(frame_data, value), keyframe2], key2:...}
# Adding a single pair of Alpha/Beta parameters per key frame is insufficient 
#  because the "model" and "expression" keys have unlisted subcomponents.
# Thus, all of the alpha/beta parameters need to be added as extensions to key_frames.
#  {frames: int, key1: [keyframe1, (frame_data, value, alpha_beta={"subcomponent1":(a,b)})], key2:...}
# Note that the first keyframe should never have alpha_beta: the thing you are changing _to_ determines the params.


def do_op(key_frames, starting_view, save_path = "./tmp", render_function = None):
    all_params = interpolate_all(key_frames)
    #with open("/home/jason/all_params.json", 'w') as f:
    #    json.dump(all_params, f)
    create_images(all_params, starting_view, save_path, render_function)

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
    

def interpolate_all(key_frames):
    all_params = {}
    frames = int(key_frames["frames"])

    # store the original in case the user wants to affect the onscreen model.
    starting_point = {}
    for change_key in key_frames:
        if change_key is "frames":
            continue
        starting_point[change_key] = get_params(change_key)

    # loop through each type of change
    for change_key in key_frames:
        if change_key is "frames":
            continue
        my_keys = None
        if change_key == "model":
            my_keys = model_keys
        elif change_key == "expression":
            my_keys = expression_keys
        # get the first value for the change type
        # for the starting_point
        current_index = 0
        # see if there is a predefined first frame value
        a, fA, _ = get_change(key_frames, change_key, current_index, frames)
        
        if fA > 0 or a is None:
            # otherwise, get the params "as is"
            a = starting_point[change_key]
            fA = 0.
        #else:
        current_index += 1
        frame_values = [a]

        # go through the remaining values
        for current_key_idx in range(current_index, len(key_frames[change_key])):
            # each one is b at frame fB.
            b, fB, extraB = get_change(key_frames, change_key, current_index, frames)
            # skip over any "no data" entries
            if b is not None:    
                #create the difference vector b-a
                # if b has a negative interpolation percentage value (extraB), 
                # then b is actually a-(b-a) (and b should be stored as such for later interpolations)
                difference_vector = difference(b, a, extraB)
                # b is actually on the other side of a
                if extraB is not None and extraB < 0:
                    b = add(a, difference_vector)
                #print("new b:",b)
                # how many frames do you have to change
                delta_frames = (fB-fA) # i.e., 3-0 == 3
                #print("delta frames:",delta_frames)
                # the step-by-step change vector
                change_vector = divide(difference_vector, delta_frames)

                #print("change_vector:",change_vector)

                initial_length = len(frame_values)
                # apply the changes
                for _ in range(delta_frames):
                    frame_values.append(add(frame_values[-1], change_vector))
                # apply special cases (beta-distribution)
                if my_keys:
                    alpha_beta = key_frames[change_key][current_key_idx][1][-1]
                    for abr in alpha_beta:
                        #log.message("Seeking key "+ abr)
                        # make abr of say: "^head,ear" to regex of "(^head|ear)"
                        regex_abr = abr
                        if "," in abr:
                            tmp = abr.split(",")
                            regex_abr = "("
                            ltmp = len(tmp)
                            for si,s in enumerate(tmp):
                                regex_abr += s
                                if si < ltmp:
                                    regex_abr+="|"
                            regex_abr+=")"
                        # the same regex and alpha/beta values are used for every frame
                        ab_regex = re.compile(regex_abr, flags=re.DOTALL)
                        alpha,beta = alpha_beta[abr]
                        
                        # no need to do the last frame (it is the same whether linear or not)
                        for delta_frame in range(delta_frames-1):
                            x = (delta_frame+1)/delta_frames
                            bcdf = beta_cdf(x, alpha,beta)
                            for ab_key in my_keys:
                                if re.match(ab_regex, ab_key):
                                    #log.message("Matched "+ ab_key)
                                    frame_values[initial_length + delta_frame][ab_key] = add(frame_values[initial_length-1][ab_key], multiply(difference_vector[ab_key], bcdf))

                #reassign a for next time: 
                a=b
                fA = fB
            # prep for getting the next frame
            current_index += 1

        # assign the rest of the frames to the previous/last value.
        for _ in range(len(frame_values), frames):
            frame_values.append(frame_values[-1])
        # store the changes
        all_params[change_key] = frame_values
    return all_params

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

def create_images(all_params, start_view = "Front", save_path="./tmp", render_function = None):
    if start_view == "Front":
        gui3d.app.setFaceCamera()
    rotation = gui3d.app.modelCamera.getRotation()
    frames = len(all_params['rot_X'])
    # make frame '-1' be the current rotation so that it can be 
    #  set to the correct rotation on start
    all_params['rot_X'].append(rotation[0])
    all_params['rot_Y'].append(rotation[1])
    for i in range(frames):
        for key in all_params:
            if key == 'expression':
                if type(all_params[key][i]) != int and type(all_params[key][i]) != float:
                    set_pose(all_params[key][i])
            elif key == "model":
                updateModelingParameters(all_params[key][i])
            elif key == 'rot_X':
                gui3d.app.rotateCamera(0,all_params[key][i]-all_params[key][i-1])
            elif key == 'rot_Y':
                gui3d.app.rotateCamera(1,all_params[key][i]-all_params[key][i-1])
        gui3d.app.redraw()
        # get the picture
        #surface = grabScreen(0,0, G.windowWidth, G.windowHeight)#, 'F:/MH_screenshot.png')
        img = render_function[0](render_function[1])
        img.save(os.path.join(save_path, "MH_{0:06d}.png".format(i)))

        save_models = render_function[1]['saveModels']
        if save_models:
            save_model_special(save_path, "MH_{0:06d}".format(i), all_params, i)
        #indices = np.where(img.data[:,:,3] == 0)
        #indices = indices[0:2]
        #img.data[indices] = (0,0,0,255)
        #grabScreen(0,0, G.windowWidth, G.windowHeight, 'F:/makehuman/video_frames/MH_vid_frame{0}.png'.format(i))
        if i == 0:
            all_params['rot_X'].pop(-1)
            all_params['rot_Y'].pop(-1)
def updatePose():
    human = gui3d.app.selectedHuman
    panim.disableBaking = True  # Faster for realtime updating a single pose
    human.refreshPose()

model_keys = tuple([key for key in get_shape_params()])
model_data_length = len(model_keys)

expression_keys = ("LeftBrowDown", "RightBrowDown", "LeftOuterBrowUp", "RightOuterBrowUp", "LeftInnerBrowUp", "RightInnerBrowUp", "NoseWrinkler", "LeftUpperLidOpen", "RightUpperLidOpen", "LeftUpperLidClosed", "RightUpperLidClosed", "LeftLowerLidUp", "RightLowerLidUp", "LeftEyeDown", "RightEyeDown", "LeftEyeUp", "RightEyeUp", "LeftEyeturnRight", "RightEyeturnRight", "LeftEyeturnLeft", "RightEyeturnLeft", "LeftCheekUp", "RightCheekUp", "CheeksPump", "CheeksSuck", "NasolabialDeepener", "ChinLeft", "ChinRight", "ChinDown", "ChinForward", "lowerLipUp", "lowerLipDown", "lowerLipBackward", "lowerLipForward", "UpperLipUp", "UpperLipBackward", "UpperLipForward", "UpperLipStretched", "JawDrop", "JawDropStretched", "LipsKiss", "MouthMoveLeft", "MouthMoveRight", "MouthLeftPullUp", "MouthRightPullUp", "MouthLeftPullSide", "MouthRightPullSide", "MouthLeftPullDown", "MouthRightPullDown", "MouthLeftPlatysma", "MouthRightPlatysma", "TongueOut", "TongueUshape", "TongueUp", "TongueDown", "TongueLeft", "TongueRight", "TonguePointUp", "TonguePointDown")
expression_data_length = len(expression_keys)
camera_data_length = 2