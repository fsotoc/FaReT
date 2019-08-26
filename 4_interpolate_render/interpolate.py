#!/usr/bin/python2.7
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

from glmodule import grabScreen
import gui3d
import animation
import bvh
import numpy as np
from collections import OrderedDict
import json

def do_op(key_frames, starting_view, save_path = "./tmp", render_function = None):
    all_params = interpolate_all(key_frames)
    #with open("/home/jason/all_params.json", 'w') as f:
    #    json.dump(all_params, f)
    create_images(all_params, starting_view, save_path, render_function)

def get_shape_params():
    human = gui3d.app.selectedHuman
    
    param_dict = {}
    for key in human.modifierNames:
        param_dict[key] = human.getModifier(key).getValue()
    return param_dict

def load_pose_modifiers(filename):
    if filename is None or filename == "None":
        modifiers, _ = get_blank_pose()
        return modifiers
    with open(filename, 'r') as f:
        return json.load(f, object_pairs_hook=OrderedDict)['unit_poses']
    return None

def delta_pose(pose_a, pose_b, over_frames, percentage):
    pose_delta = {}
    for key in pose_b:
        if not key in pose_a:
            pose_a[key] = 0

    for key in pose_a:
        if not key in pose_b:
            pose_b[key] = 0
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
    frame_data, value = key_frames[change_key][current_index]
    extra = None
    frame = get_frame(frame_data, frames)
    if change_key == 'expression':
        current_percent = int(value[value.index("|")+1:])
        value = value[:value.index("|")]
        # there is no expression
        if value == "":
            data = None
        else:
            data = load_pose_modifiers(value)
            extra = current_percent
    elif change_key == "model":
        current_percent = int(value[value.index("|")+1:])
        value = value[:value.index("|")]
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

from numbers import Number

def add(a, change):
    # just numbers
    if isinstance(a, Number):
        return a + change
    
    summed = {}
    for key in a:
        summed[key] = a[key] + change[key]
    return summed

def divide(a, change):
    # just numbers
    if isinstance(a, Number):
        if change != 0:
            return a / change
        else:
            return a
    # dictionaries
    quo = {}
    for key in a:
        if isinstance(change, Number):
            if change != 0:
                quo[key] = a[key] / change
            else:
                quo[key] = a[key]
        else:
            if change[key] != 0:
                quo[key] = a[key] / change[key]
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
        # get the first value for the change type
        # for the starting_point
        current_index = 0
        # see if there is a predefined first frame value
        a, fA, _ = get_change(key_frames, change_key, current_index, frames)

        if fA > 0 or a is None:
            # otherwise, get the params "as is"
            a = starting_point[change_key]
            fA = 0
        else:
            current_index += 1
        frame_values = [a]

        # go through the remaining values
        for _ in range(current_index, len(key_frames[change_key])):
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
                print("new b:",b)
                # how many frames do you have to change
                delta_frames = (fB-fA) # i.e., 3-0 == 3
                print("delta frames:",delta_frames)
                # the step-by-step change vector
                change_vector = divide(difference_vector, delta_frames)

                print("change_vector:",change_vector)

                # apply the changes
                for _ in range(delta_frames):
                    frame_values.append(add(frame_values[-1], change_vector))
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

def interpolate_all_old(key_frames):

    original_shape_params = get_shape_params()
    frames = int(key_frames['frames'])
    # stores that change that occurs at every frame
    all_params = {'rot_X':[0]*frames, 'rot_Y':[0]*frames,
                    'expression':[0]*frames, "model":[0]*frames}
    delta_params = {'rot_X':None, 'rot_Y':None,
                    'expression': None, "model":None}
    current_index = {'rot_X':0, 'rot_Y':0, 
                    'expression':0, "model":0}

    for i in range(frames):
        # freeze values for a frame when they are assigned by a keyframe
        fix = {'rot_X':0, 'rot_Y':0,
                'expression':0, "model":0}
        for key in current_index:
            if len(key_frames[key]) <= current_index[key]:
                continue

            # the frame at which the next event occurs
            frame = get_frame(key_frames[key][current_index[key]][0], frames)
            value = key_frames[key][current_index[key]][1]
            current_percent = 100
            if i == frame:
                if key == 'expression':
                    current_percent = int(value[value.index("|")+1:])
                    value = value[:value.index("|")]
                    if value == "":
                        continue
                    else:
                        value = load_pose_modifiers(value)
                elif key == "model":
                    current_percent = int(value[value.index("|")+1:])
                    value = value[:value.index("|")]
                    if value != "":
                        gui3d.app.loadHumanMHM(value)
                    value = get_shape_params()
                # set the current value
                if (key == 'expression' or key == "model") and abs(current_percent) != 100:
                    if delta_params[key] is None:
                        if type(value) is dict or type(value) is OrderedDict:
                            all_params[key][frame] = value
                        elif type(all_params[key][frame-1]) is dict or type(all_params[key][frame-1]) is OrderedDict:
                            all_params[key][frame] = all_params[key][frame-1]
                        else:
                            print("VALUE", type(value), value)
                            all_params[key][frame] = {}
                    else:
                        if type(all_params[key][frame]) != dict and type(all_params[key][frame]) != OrderedDict:
                            all_params[key][frame] = {}
                        # keep the interpolated/extrapolated data if it is available
                        if type(all_params[key][frame-1]) != dict and type(all_params[key][frame-1]) != OrderedDict:
                            all_params[key][frame-1] = {}
                        for k in delta_params[key]:
                            if not k in all_params[key][frame-1]:
                                all_params[key][frame-1][k] = 0
                            all_params[key][frame][k] = all_params[key][frame-1][k]+delta_params[key][k]
                            value = all_params[key][frame][k]
                else:
                    all_params[key][frame] = value
                    
                fix[key] = True
                # start tracking new changes, if applicable
                current_index[key]+=1
                if len(key_frames[key]) > current_index[key]:
                    next_frame = get_frame(key_frames[key][current_index[key]][0], frames)
                    delta_frames = (next_frame - frame)#-1
                    next_value = key_frames[key][current_index[key]][1]

                    if key == 'expression':
                        next_percent = float(next_value[next_value.index("|")+1:])
                        next_value = next_value[:next_value.index("|")]
                        if type(value) is dict or type(value) is OrderedDict:
                            next_value = load_pose_modifiers(next_value)
                            delta_params[key] = delta_pose(value, next_value, delta_frames, next_percent)
                    elif key == "model":
                        next_percent = float(next_value[next_value.index("|")+1:])
                        next_value = next_value[:next_value.index("|")]
                        if next_value != "":
                            gui3d.app.loadHumanMHM(next_value)
                            next_value = get_shape_params()
                        else:
                            next_value = {}
                            for akey in original_shape_params:
                                next_value[akey] = original_shape_params[akey]

                        delta_params[key] = delta_shape_params(value, next_value, delta_frames, next_percent)
                    else:
                        delta_params[key] = (next_value-value)/float(delta_frames)
                else:
                    # no further changes occur on this dimension -- assign later all to current
                    all_params[key][frame:] = (value,)*(frames-frame)
                    delta_params[key] = None


        for key in delta_params:
            if fix[key] or delta_params[key] is None:
                continue
            if key == 'expression' or key == "model":
                all_params[key][i] = {}
                for k in delta_params[key]:
                    if type(all_params[key][i-1]) is not dict and type(all_params[key][i-1]) is not OrderedDict:
                        all_params[key][i-1] = {}
                    if not k in all_params[key][i-1]:
                        all_params[key][i-1][k] = 0
                    all_params[key][i][k] = all_params[key][i-1][k]+delta_params[key][k]
            else:
                all_params[key][i] = all_params[key][i-1]+delta_params[key]
    #with open("F:/makehuman/all_params.json", 'w') as f:
    #    json.dump(all_params, f)
    return all_params
# straight from MakeHuman's scripting plugin
def updateModelingParameters(dictOfParameterNameAndValue):
    human = gui3d.app.selectedHuman
    log.message("SCRIPT: updateModelingParameters("+str(dictOfParameterNameAndValue)+")")
    for key, value in dictOfParameterNameAndValue.iteritems():
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


