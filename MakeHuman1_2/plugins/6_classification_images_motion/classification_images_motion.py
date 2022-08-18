#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# if you want to install opencv for python, from _makehuman's_ pip, pip install opencv-python.
#  MakeHuman has its own pip under makehuman-community/Python/Scripts
# you also need FFMPEG codecs (the thing that helps to save and interpret videos)
# on Windows, install to C:/ffmpeg

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

from numpy.core.fromnumeric import shape

#from scipy.stats import beta
# https://people.sc.fsu.edu/~jburkardt/py_src/prob/prob.html
import beta
beta_cdf = beta.beta_cdf

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


def do_op(classification_image_settings, save_path = "./tmp", frame_rate=30, render_function = None):
    generate_CI_info(save_path=save_path, frame_rate=frame_rate, render_function=render_function, **classification_image_settings)
    
import sys
def convert_from_mode_concentration(mode, concentration):
    # https://en.wikipedia.org/wiki/Beta_distribution#Mode_and_concentration
    alpha = max(mode*(concentration - 2) + 1, sys.float_info.min)
    beta = max((1-mode) * (concentration-2) + 1, sys.float_info.min)
    return alpha, beta

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

def generate_CI_info(base_model, end_model, base_expression, end_expression, trials, frames, shape_parameters, shape_data, pose_parameters, pose_data, save_path, SD=.3, rot_X=0, rot_Y=0, cam_Z=8.7, material_file="young_caucasian_avg", frame_rate=30, render_function=None):
    # the base_model is a path to the model
    # the shape parameters and pose_parameters are lists of parameters to use (convert to regex)
    gui3d.app.loadHumanMHM(base_model)


    shapes = get_listed_shape_params(model_keys)#get_shape_params()
    poses = load_pose_modifiers(base_expression)
    #log.message(poses)
    shape_keys_to_jitter = get_keys(shape_parameters, model_keys)
    expression_keys_to_jitter = get_keys(pose_parameters, expression_keys)
    #shapes = merge_dictionaries(shapes, dict(zip(model_keys, [0]*model_data_length)))
    #poses = merge_dictionaries(poses, dict(zip(expression_keys, [0]*expression_data_length)))


    df = DataFrame()

    #base_vertices = (np.array(human.mesh.r_coord)*1)[vertex_idx]
    if end_model == "None":
        end_model = base_model
    gui3d.app.loadHumanMHM(end_model)
    # unlike interpolation, all of them have just 1 start and end point, 
    # so just one delta shape and delta pose.
    delta_shape = difference(get_listed_shape_params(model_keys), shapes, 100)
    delta_pose = difference(load_pose_modifiers(end_expression), poses, 100)
    
    human = G.app.selectedHuman
    mat = human.material
    mat.fromFile(getpath.getSysDataPath('skins/'+material_file+"/"+material_file+".mhmat"))
    
    gui3d.app.setFaceCamera()
    rotation = gui3d.app.modelCamera.getRotation()
    gui3d.app.rotateCamera(0,rot_X-rotation[0])
    gui3d.app.rotateCamera(1,rot_Y-rotation[1])

    gui3d.app.modelCamera.setZoomFactor(cam_Z)

    # unlike normal CI's, it has trials and frames
    for trial in range(trials):
        # the sample
        my_shapes = shapes.copy()
        my_poses = poses.copy()
        
        # the antisample
        amy_shapes = shapes.copy()
        amy_poses = poses.copy()

        


        mode_con_dict = dict()
        #log.message("Doing new Trial "+str(trial))
        # get the list of shape and expression groups to make a Mode and Concentration for
        for frame in range(frames):
            all_data = OrderedDict()
            all_data["anti"] = False
            all_data["trial"] = trial
            all_data["frame"] = frame

            anti_all_data = OrderedDict()
            anti_all_data["anti"] = True
            anti_all_data["trial"] = trial
            anti_all_data["frame"] = frame

            #log.message("Doing new Frame "+str(frame))

            progress = (frame+1)/frames
            for shape in my_shapes:
                changed = False
                for dict_reg in shape_data:
                    regex = re.compile("({0})".format(dict_reg["features"]).replace(",", "|"), flags=re.DOTALL)
                    if re.search(regex, shape) is not None:
                        changed = True
                        mode, concentration = dict_reg["alpha"], dict_reg["beta"]
                        mode_sd = dict_reg["alpha_sd"]
                        concentration_sd = dict_reg["beta_sd"]
                        # change the mode and concentration
                        # remember these for the anti_sample
                        # also need to keep symmetry
                        mode2 = None
                        concentration2 = None
                        if frame == 0 and not dict_reg["features"] in mode_con_dict:
                            mode2 = np.random.normal(mode, mode_sd)
                            concentration2 = np.random.normal(concentration, concentration_sd)
                            mode_con_dict[dict_reg["features"]] = mode2, concentration2
                            # ensure symmetry
                            '''if "/r-" in shape:
                                key2 = shape.replace("/r-", "/l-")
                                if re.search(regex, key2) is not None:
                                    mode_con_dict[key2] = mode2, concentration2
                            if "/l-" in shape:
                                key2 = shape.replace("/l-", "/r-")
                                if re.search(regex, key2) is not None:
                                    mode_con_dict[key2] = mode2, concentration2'''
                        else:
                            mode2, concentration2 = mode_con_dict[dict_reg["features"]]
                        


                        #alpha,beta = convert_from_mode_concentration(mode2, concentration2)
                        alpha,beta = mode2, concentration2
                        # the nonlinear progress bar
                        progress_bcdf = beta_cdf(progress, alpha,beta)
                        # set the progress for this shape
                        all_data[shape+"_M"] = mode2
                        all_data[shape+"_C"] = concentration2
                        all_data[shape+"_A"] = alpha
                        all_data[shape+"_B"] = beta
                        all_data[shape+"_P"] = progress_bcdf
                        my_shapes[shape] = shapes[shape] + delta_shape[shape]*progress_bcdf
                        all_data[shape] = my_shapes[shape]

                        amode = mode-(mode2-mode)
                        acon = concentration-(concentration2-concentration)
                        #alpha,beta = convert_from_mode_concentration(amode, acon)
                        alpha,beta = amode, acon
                        progress_bcdf = beta_cdf(progress, alpha,beta)
                        anti_all_data[shape+"_M"] = amode
                        anti_all_data[shape+"_C"] = acon
                        anti_all_data[shape+"_A"] = alpha
                        anti_all_data[shape+"_B"] = beta
                        anti_all_data[shape+"_P"] = progress_bcdf
                        amy_shapes[shape] = shapes[shape] + delta_shape[shape]*progress_bcdf
                        anti_all_data[shape] = amy_shapes[shape]
                        break
                if not changed:
                    # linear operation based on frame progress
                    all_data[shape+"_P"] = progress
                    anti_all_data[shape+"_P"] = progress
                    my_shapes[shape] = my_shapes[shape] + delta_shape[shape]*progress
                    amy_shapes[shape] = amy_shapes[shape] + delta_shape[shape]*progress
                    all_data[shape] = my_shapes[shape]
                    anti_all_data[shape] = amy_shapes[shape]

            for pose in my_poses:
                changed = False
                for dict_reg in pose_data:
                    #log.message("Looking for pose")
                    regex = re.compile("({0})".format(dict_reg["features"]).replace(",", "|"), flags=re.DOTALL)
                    if re.search(regex, pose) is not None:
                        changed = True
                        #log.message("Found matching pose")
                        #alpha,beta = convert_from_mode_concentration(dict_reg["alpha"], dict_reg["beta"])
                        mode, concentration = dict_reg["alpha"], dict_reg["beta"]
                        mode_sd = dict_reg["alpha_sd"]
                        concentration_sd = dict_reg["beta_sd"]
                        # change the mode and concentration
                        # remember these for the anti_sample
                        # also need to keep symmetry
                        mode2 = None
                        concentration2 = None
                        if frame == 0 and not dict_reg["features"] in mode_con_dict:
                            mode2 = np.random.normal(mode, mode_sd)
                            concentration2 = np.random.normal(concentration, concentration_sd)
                            mode_con_dict[dict_reg["features"]] = mode2, concentration2
                            #log.message("Make new mode/con")
                            # ensure symmetry
                            '''if "Right" in pose:
                                key2 = pose.replace("Right", "Left")
                                if re.search(regex, key2) is not None:
                                    mode_con_dict[key2] = mode2, concentration2
                            if "Left" in pose:
                                key2 = pose.replace("Left", "Right")
                                if re.search(regex, key2) is not None:
                                    mode_con_dict[key2] = mode2, concentration2'''
                        else:
                            mode2, concentration2 = mode_con_dict[dict_reg["features"]]
                            #log.message("Retrieve old mode/con")
                        


                        #alpha,beta = convert_from_mode_concentration(mode2, concentration2)
                        alpha,beta = mode2, concentration2
                        # the nonlinear progress bar
                        progress_bcdf = beta_cdf(progress, alpha,beta)
                        # set the progress for this pose
                        all_data[pose+"_M"] = mode2
                        all_data[pose+"_C"] = concentration2
                        all_data[pose+"_A"] = alpha
                        all_data[pose+"_B"] = beta
                        all_data[pose+"_P"] = progress_bcdf
                        my_poses[pose] = poses[pose] + delta_pose[pose]*progress_bcdf
                        all_data[pose] = my_poses[pose]

                        amode = mode-(mode2-mode)
                        acon = concentration-(concentration2-concentration)
                        #alpha,beta = convert_from_mode_concentration(amode, acon)
                        alpha,beta = amode, acon
                        progress_bcdf = beta_cdf(progress, alpha,beta)
                        anti_all_data[pose+"_M"] = amode
                        anti_all_data[pose+"_C"] = acon
                        anti_all_data[pose+"_A"] = alpha
                        anti_all_data[pose+"_B"] = beta
                        anti_all_data[pose+"_P"] = progress_bcdf
                        amy_poses[pose] = poses[pose] + delta_pose[pose]*progress_bcdf
                        anti_all_data[pose] = amy_poses[pose]
                        break
                if not changed:
                    # linear operation based on frame progress
                    all_data[pose+"_P"] = progress
                    anti_all_data[pose+"_P"] = progress
                    my_poses[pose] = my_poses[pose] + delta_pose[pose]*progress
                    amy_poses[pose] = amy_poses[pose] + delta_pose[pose]*progress
                    all_data[pose] = my_poses[pose]
                    anti_all_data[pose] = amy_poses[pose]

            df.append(all_data)
            updateModelingParameters(my_shapes)
            set_pose(my_poses)
            gui3d.app.redraw()

            if render_function:
                img = render_function[0](render_function[1])
                img.save(os.path.join(save_path, "{0:04d}_{1:04d}_sample.png".format(trial, frame)))

            df.append(anti_all_data)
            updateModelingParameters(amy_shapes)
            set_pose(amy_poses)
            gui3d.app.redraw()

            if render_function:
                img = render_function[0](render_function[1])
                img.save(os.path.join(save_path, "{0:04d}_{1:04d}_anti_sample.png".format(trial, frame)))
    df.to_csv(os.path.join(save_path,"CI_motion.csv"))
    try:
        import cv2
        for trial in range(trials):
            filename = os.path.join(save_path, "trial_anti_sample_{0:04d}.mp4".format(trial))
            codec = cv2.VideoWriter_fourcc(*"mp4v")
            resolution = (200, 200)
            Output = cv2.VideoWriter(filename, codec, frame_rate, resolution)

            for frame in range(frames):
                img = cv2.imread(os.path.join(save_path, "{0:04d}_{1:04d}_anti_sample.png".format(trial, frame)))
                #cv2.imshow("test", img)
                Output.write(img)
            Output.release()




            filename = os.path.join(save_path, "trial_sample_{0:04d}.mp4".format(trial))
            Output = cv2.VideoWriter(filename, codec, frame_rate, resolution)

            for frame in range(frames):
                img = cv2.imread(os.path.join(save_path, "{0:04d}_{1:04d}_sample.png".format(trial, frame)))
                Output.write(img)
            Output.release()
            
    except:
        pass


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
    if filename is None or filename == "None" or filename == "":
        
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

    for key in pose_modifiers:
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

vertex_idx = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 266, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370, 371, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386, 387, 388, 389, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399, 400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451, 452, 453, 454, 455, 456, 457, 458, 459, 460, 461, 462, 463, 464, 465, 466, 467, 468, 469, 470, 471, 472, 473, 474, 475, 476, 477, 478, 479, 480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491, 492, 493, 494, 495, 496, 497, 498, 499, 500, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 512, 513, 514, 515, 516, 517, 518, 519, 520, 521, 522, 523, 524, 525, 526, 527, 528, 529, 530, 531, 532, 533, 534, 535, 536, 537, 538, 539, 540, 541, 542, 543, 544, 545, 546, 547, 548, 549, 550, 551, 552, 553, 554, 555, 556, 557, 558, 559, 560, 561, 562, 563, 564, 565, 566, 567, 568, 569, 570, 571, 572, 573, 574, 575, 576, 577, 578, 579, 580, 581, 582, 583, 584, 585, 586, 587, 588, 589, 590, 591, 592, 593, 594, 595, 596, 597, 598, 599, 600, 601, 602, 603, 604, 605, 606, 607, 608, 609, 610, 611, 612, 613, 614, 615, 616, 617, 618, 619, 620, 621, 622, 623, 624, 625, 626, 627, 628, 629, 630, 631, 632, 633, 634, 635, 636, 637, 638, 639, 640, 641, 642, 643, 644, 645, 646, 647, 648, 649, 650, 651, 652, 653, 654, 655, 656, 657, 658, 659, 660, 661, 662, 663, 664, 665, 666, 746, 747, 748, 749, 750, 751, 754, 755, 756, 757, 758, 759, 760, 761, 762, 763, 764, 765, 766, 767, 768, 769, 779, 782, 783, 820, 955, 960, 961, 962, 963, 964, 965, 966, 967, 968, 969, 970, 971, 972, 973, 977, 978, 979, 980, 981, 982, 983, 984, 985, 986, 1049, 1053, 1054, 1055, 1056, 1057, 1062, 1063, 1064, 1087, 1088, 1130, 1131, 1132, 1133, 1134, 1135, 1136, 1137, 1138, 1139, 1140, 1141, 1142, 1143, 1144, 1145, 1146, 1147, 1148, 1149, 1150, 1151, 1152, 1153, 1154, 1155, 1156, 1157, 1158, 1159, 1160, 1161, 1162, 1163, 1164, 1165, 1166, 1167, 1168, 1169, 1170, 1171, 1172, 1173, 1174, 1175, 1176, 1177, 1178, 1179, 1180, 1181, 1182, 1183, 1184, 1185, 1186, 1187, 1188, 1189, 1190, 1191, 1192, 1193, 1194, 1195, 1196, 1197, 1198, 1199, 1200, 1201, 1202, 1203, 1204, 1205, 1206, 1207, 1208, 1209, 1210, 1211, 1212, 1213, 1214, 1215, 1216, 1217, 1218, 1219, 1220, 1221, 1222, 1223, 1224, 1225, 1226, 1227, 1228, 1229, 1230, 1231, 1232, 1233, 1234, 1235, 1236, 1237, 1238, 1239, 1240, 1241, 1242, 1243, 1244, 1245, 1246, 1247, 1248, 1249, 1250, 1251, 1252, 1253, 1254, 1255, 1256, 1257, 1258, 1259, 1260, 1261, 1262, 1263, 1264, 1265, 1266, 1267, 1268, 1269, 1270, 1271, 1272, 1273, 1274, 1275, 1276, 1277, 1278, 1279, 1280, 1281, 1282, 1283, 1284, 1285, 1286, 1287, 1288, 1289, 1290, 1291, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299, 1300, 1301, 1302, 1303, 1304, 1305, 1306, 1307, 1308, 1309, 1310, 1311, 1312, 1313, 1314, 1315, 1316, 1317, 1318, 1319, 1320, 1321, 1322, 1323, 1324, 1325, 1326, 1327, 1328, 1329, 1330, 1331, 1332, 1333, 1334, 1335, 1336, 1337, 1338, 1339, 1340, 1341, 1342, 1343, 1344, 1345, 1346, 1347, 1348, 1349, 1350, 1351, 1352, 1353, 1354, 1355, 1356, 1357, 1358, 1359, 1360, 1361, 1362, 1363, 1364, 1365, 1366, 1367, 1368, 1369, 1370, 1371, 1372, 1373, 1374, 1375, 1376, 1377, 1378, 1379, 1380, 1381, 1382, 1383, 1384, 1385, 1386, 1387, 1388, 1389, 1390, 1391, 1392, 1393, 1394, 1395, 1396, 1397, 1398, 1399, 1400, 1401, 1402, 1403, 1404, 1405, 1406, 1407, 1408, 1409, 1410, 1411, 1412, 1413, 1414, 1415, 1416, 1417, 1418, 1419, 1420, 1421, 1422, 1423, 1424, 1425, 1426, 1427, 1428, 1429, 1430, 1431, 1432, 1433, 1434, 1435, 1436, 1437, 1438, 1439, 1440, 1441, 1442, 1443, 1444, 1445, 1446, 1447, 1448, 1449, 1450, 1451, 1452, 1453, 1454, 1455, 4025, 4026, 4027, 4028, 4029, 4030, 4031, 4032, 4033, 4034, 4035, 4036, 4037, 4038, 4039, 4040, 4041, 4042, 4043, 4053, 4054, 4055, 4056, 4057, 4058, 4059, 4060, 4061, 4062, 4063, 4064, 4065, 4066, 4067, 4068, 4069, 4070, 4071, 4072, 4073, 4074, 4075, 4076, 4077, 4078, 4079, 4080, 5282, 5283, 5284, 5285, 5286, 5287, 5288, 5289, 5290, 5291, 5292, 5293, 5294, 5295, 5296, 5297, 5298, 5299, 5300, 5301, 5302, 5303, 5304, 5305, 5306, 5307, 5308, 5309, 5310, 5311, 5312, 5313, 5314, 5315, 5316, 5317, 5318, 5319, 5320, 5321, 5322, 5323, 5324, 5325, 5326, 5327, 5328, 5329, 5330, 5331, 5332, 5333, 5507, 5508, 5509, 5510, 5511, 5512, 5513, 5514, 5515, 5516, 5517, 5518, 5519, 5520, 5521, 5522, 5523, 5524, 5525, 5526, 5527, 5528, 5529, 5530, 5531, 5532, 5533, 5534, 5535, 5536, 5537, 5538, 5539, 5540, 5541, 5542, 5543, 5544, 5545, 5546, 5547, 5548, 5549, 5551, 5552, 5553, 5554, 5557, 5558, 5559, 5560, 5561, 5562, 5563, 5564, 5565, 5566, 5567, 5568, 5569, 5570, 5571, 5572, 5573, 5574, 5575, 5576, 5577, 5578, 5579, 5580, 5581, 5582, 5583, 5584, 5585, 5586, 5587, 5588, 5589, 5590, 5591, 5592, 5593, 5594, 5595, 5596, 5597, 5598, 5599, 5600, 5601, 5602, 5603, 5604, 5605, 5606, 5607, 5608, 5609, 5610, 5611, 5612, 5613, 5614, 5615, 5616, 5617, 5618, 5619, 5620, 5621, 5622, 5623, 5624, 5625, 5626, 5627, 5628, 5629, 5630, 5631, 5632, 5633, 5634, 5635, 5636, 5637, 5638, 5639, 5640, 5641, 5642, 5644, 5645, 5647, 5650, 5651, 5652, 5653, 5654, 5656, 5657, 5660, 5666, 5667, 5668, 5669, 5670, 5671, 5672, 5673, 5674, 5675, 5676, 5677, 5678, 5679, 5680, 5681, 5682, 5683, 5684, 5685, 5686, 5687, 5688, 5689, 5690, 5691, 5692, 5703, 5704, 5705, 5707, 5708, 5709, 5710, 5711, 5712, 5713, 5714, 5715, 5716, 5717, 5718, 5719, 5720, 5721, 5722, 5723, 5724, 5725, 5748, 5749, 5750, 5751, 5752, 5753, 5754, 5755, 5756, 5757, 5758, 5759, 5760, 5761, 5762, 5763, 5764, 5765, 5766, 5767, 5768, 5769, 5770, 5771, 5772, 5773, 5774, 5775, 5776, 5777, 5778, 5779, 5780, 5781, 5782, 5783, 5784, 5785, 5786, 5787, 5788, 5789, 5790, 5791, 5792, 5793, 5794, 5795, 5796, 5797, 5798, 5799, 5800, 5801, 5802, 5803, 5804, 5805, 5806, 5807, 5808, 5809, 5810, 5811, 5812, 5813, 5814, 5815, 5816, 5819, 5820, 5821, 5822, 5823, 5824, 5825, 5826, 5827, 6017, 6022, 6023, 6024, 6028, 7364, 7365, 7366, 7367, 7368, 7369, 7370, 7371, 7372, 7373, 7374, 7375, 7376, 7377, 7378, 7379, 7380, 7381, 7382, 7383, 7384, 7385, 7386, 7387, 7388, 7389, 7390, 7391, 7392, 7393, 7394, 7395, 7396, 7397, 7398, 7399, 7400, 7401, 7402, 7403, 7404, 7405, 7406, 7407, 7408, 7409, 7410, 7411, 7412, 7413, 7414, 7415, 7416, 7417, 7418, 7419, 7420, 7421, 7422, 7423, 7424, 7425, 7426, 7427, 7428, 7429, 7430, 7431, 7432, 7433, 7434, 7435, 7436, 7437, 7438, 7439, 7440, 7441, 7442, 7443, 7444, 7445, 7446, 7447, 7448, 7449, 7450, 7451, 7452, 7453, 7454, 7455, 7456, 7457, 7458, 7459, 7460, 7461, 7462, 7463, 7464, 7465, 7466, 7467, 7468, 7469, 7470, 7471, 7472, 7473, 7474, 7475, 7476, 7477, 7478, 7479, 7480, 7481, 7482, 7483, 7484, 7485, 7486, 7487, 7488, 7489, 7490, 7491, 7492, 7493, 7494, 7495, 7496, 7497, 7498, 7499, 7500, 7501, 7502, 7503, 7504, 7505, 7506, 7507, 7508, 7509, 7510, 7511, 7512, 7513, 7514, 7515, 7516, 7517, 7518, 7519, 7520, 7521, 7522, 7523, 7524, 7525, 7526, 7527, 7528, 7529, 7530, 7531, 7532, 7533, 7534, 7535, 7536, 7537, 7538, 7539, 7540, 7541, 7542, 7543, 7544, 7545, 7546, 7547, 7548, 7549, 7550, 7551, 7552, 7553, 7554, 7555, 7556, 7557, 7558, 7559, 7560, 7561, 7562, 7563, 7564, 7565, 7566, 7567, 7568, 7569, 7570, 7571, 7572, 7573, 7574, 7575, 7576, 7577, 7578, 7579, 7580, 7581, 7582, 7583, 7584, 7585, 7586, 7587, 7588, 7589, 7590, 7591, 7592, 7593, 7594, 7595, 7596, 7597, 7598, 7599, 7600, 7601, 7602, 7603, 7604, 7605, 7606, 7607, 7608, 7609, 7610, 7611, 7612, 7613, 7614, 7615, 7616, 7617, 7618, 7619, 7620, 7621, 7622, 7623, 7624, 7625, 7626, 7628, 7629, 7630, 7631, 7632, 7633, 7634, 7635, 7636, 7637, 7638, 7639, 7640, 7643, 7651, 7652, 7653, 7654, 7655, 7656, 7657, 7658, 7659, 7660, 7661, 7662, 7663, 7664, 7665, 7666, 7667, 7668, 7669, 7670, 7671, 7672, 7673, 7674, 7675, 7676, 7677, 7678, 7679, 7680, 7681, 7682, 7683, 7684, 7685, 7686, 7687, 7688, 7689, 7690, 7691, 7692, 7693, 7694, 7695, 7696, 7697, 7698, 7699, 7700, 7701, 7702, 7703, 7704, 7705, 7706, 7707, 7708, 7709, 7710, 7711, 7712, 7713, 7714, 7715, 7716, 7717, 7718, 7719, 7720, 7721, 7722, 7723, 7724, 7725, 7726, 7727, 7728, 7729, 7730, 7731, 7732, 7733, 7734, 7735, 7736, 7737, 7738, 7739, 7740, 7741, 7742, 7743, 7744, 7745, 7746, 7747, 7748, 7749, 7750, 7751, 7752, 7753, 7754, 7755, 7756, 7757, 7758, 7759, 7760, 7761, 7762, 7763, 7764, 7765, 7766, 7767, 7768, 7769, 7770, 7771, 7772, 7773, 7774, 7775, 7776, 7777, 7778, 7779, 7780, 7781, 7782, 7783, 7784, 7785, 7786, 7787, 7788, 7789, 7790, 7791, 7792, 7793, 7794, 7795, 7796, 7797, 7798, 7799, 7800, 7801, 7802, 7803, 7804, 7805, 7806, 7807, 7808, 7809, 7810, 7811, 7812, 7813, 7814, 7815, 7816, 7817, 7818, 7819, 7820, 7821, 7822, 7823, 7824, 7825, 7826, 7827, 7828, 7829, 7830, 7831, 7832, 7833, 7834, 7835, 7836, 7837, 7838, 7839, 7840, 7841, 7842, 7843, 7844, 7845, 7846, 7847, 7848, 7849, 7850, 7851, 7852, 7853, 7854, 7855, 7856, 7857, 7858, 7859, 7860, 7861, 7862, 7863, 7864, 7865, 7866, 7867, 7868, 7869, 7870, 7871, 7872, 7873, 7874, 7875, 7876, 7877, 7878, 7879, 7880, 7881, 7882, 7883, 7884, 7885, 7886, 7887, 7888, 7889, 7890, 7891, 7892, 7893, 7894, 7895, 7896, 7897, 7898, 7899, 7900, 7901, 7902, 7903, 7904, 7905, 7906, 7907, 7908, 7909, 7910, 7911, 7912, 7913, 7914, 7915, 7916, 7917, 7918, 7919, 7920, 7921, 7922, 7923, 7924, 7925, 7926, 7927, 7928, 7929, 7930, 7931, 7932, 7933, 7934, 7935, 7936, 7937, 7938, 7939, 7940, 7941, 7942, 7943, 7944, 7945, 7946, 7947, 7948, 7949, 7950, 7951, 7952, 7953, 7954, 7955, 7956, 7957, 7958, 7959, 7960, 7961, 7962, 7963, 7964, 7965, 7966, 7967, 7968, 7969, 7970, 7971, 7972, 7973, 7974, 7975, 7976, 7977, 7978, 7979, 7980, 7981, 7982, 7983, 7984, 7985, 7986, 7987, 7988, 7989, 7990, 7991, 7992, 7993, 7994, 7995, 7996, 8063, 8064, 8065, 8066, 8067, 8068, 8071, 8072, 8073, 8074, 8075, 8076, 8077, 8078, 8079, 8080, 8081, 8082, 8083, 8093, 8096, 8239, 8244, 8245, 8246, 8247, 8248, 8249, 8250, 8251, 8252, 8253, 8254, 8255, 8256, 8257, 8261, 8262, 8263, 8264, 8265, 8266, 8267, 8268, 8269, 8270, 8321, 8325, 8326, 8327, 8328, 8333, 8334, 8356, 8398, 8399, 8400, 8401, 8402, 8403, 8404, 8405, 8406, 8407, 8408, 8409, 8410, 8411, 8412, 8413, 8414, 8415, 8416, 8417, 8418, 8419, 8420, 8421, 8422, 8423, 8424, 8425, 8426, 8427, 8428, 8429, 8430, 8431, 8432, 8433, 8434, 8435, 8436, 8437, 8438, 8439, 8440, 8441, 8442, 8443, 8444, 8445, 8446, 8447, 8448, 8449, 8450, 8451, 8452, 8453, 8454, 8455, 8456, 8457, 8458, 8459, 8460, 8461, 8462, 8463, 8464, 8465, 8466, 8467, 8468, 8469, 8470, 8471, 8472, 8473, 8474, 8475, 8476, 8477, 8478, 8479, 8480, 8481, 8482, 8483, 8484, 8485, 8486, 8487, 8488, 8489, 8490, 8491, 8492, 8493, 8494, 8495, 8496, 8497, 8498, 8499, 8500, 8501, 8502, 8503, 8504, 8505, 8506, 8507, 8508, 8509, 8510, 8511, 8512, 8513, 8514, 8515, 8516, 8517, 8518, 8519, 8520, 8521, 8522, 8523, 8524, 8525, 8526, 8527, 8528, 8529, 8530, 8531, 8532, 8533, 8534, 8535, 8536, 8537, 8538, 8539, 8540, 8541, 8542, 8543, 8544, 8545, 8546, 8547, 8548, 8549, 8550, 8551, 8552, 8553, 8554, 8555, 8556, 8557, 8558, 8559, 8560, 8561, 8562, 8563, 8564, 8565, 8566, 8567, 8568, 8569, 8570, 8571, 8572, 8573, 8574, 8575, 8576, 8577, 8578, 8579, 8580, 8581, 8582, 8583, 8584, 8585, 8586, 8587, 8588, 8589, 8590, 8591, 8592, 8593, 8594, 8595, 8596, 8597, 8598, 8599, 8600, 8601, 8602, 8603, 8604, 8605, 8606, 8607, 8608, 8609, 8610, 8611, 8612, 8613, 8614, 8615, 8616, 8617, 8618, 8619, 8620, 8621, 8622, 8623, 8624, 8625, 8626, 8627, 8628, 8629, 8630, 8631, 8632, 8633, 8634, 8635, 8636, 8637, 8638, 8639, 8640, 8641, 8642, 8643, 8644, 8645, 8646, 8647, 8648, 8649, 8650, 8651, 8652, 8653, 8654, 8655, 8656, 8657, 8658, 8659, 8660, 8661, 8662, 8663, 8664, 8665, 8666, 8667, 8668, 8669, 8670, 8671, 8672, 8673, 8674, 8675, 8676, 8677, 8678, 8679, 8680, 8681, 8682, 8683, 8684, 8685, 8686, 8687, 8688, 8689, 8690, 8691, 8692, 8693, 8694, 8695, 8696, 8697, 8698, 8699, 8700, 8701, 8702, 8703, 8704, 8705, 8706, 8707, 8708, 8709, 8710, 8711, 8712, 8713, 8714, 8715, 8716, 8717, 8718, 8719, 8720, 8721, 8722, 8723, 11258, 11259, 11260, 11261, 11262, 11263, 11264, 11265, 11266, 11267, 11268, 11269, 11270, 11271, 11272, 11273, 11274, 11275, 11276, 11286, 11287, 11288, 11289, 11290, 11291, 11292, 11293, 11294, 11295, 11296, 11297, 11298, 11299, 11300, 11301, 11302, 11303, 11304, 11305, 11306, 11307, 11308, 11309, 11310, 11311, 11312, 12435, 12436, 12437, 12438, 12439, 12440, 12441, 12442, 12443, 12444, 12445, 12446, 12447, 12448, 12449, 12450, 12451, 12452, 12453, 12454, 12455, 12456, 12457, 12458, 12459, 12460, 12461, 12462, 12463, 12464, 12465, 12466, 12467, 12468, 12469, 12470, 12471, 12472, 12473, 12474, 12475, 12476, 12477, 12478, 12479, 12480, 12481, 12482, 12483, 12484, 12485, 12486, 12660, 12661, 12662, 12663, 12664, 12665, 12666, 12667, 12668, 12669, 12670, 12671, 12672, 12673, 12674, 12675, 12676, 12677, 12678, 12679, 12680, 12681, 12682, 12683, 12684, 12685, 12686, 12687, 12688, 12689, 12690, 12691, 12692, 12693, 12694, 12695, 12696, 12697, 12698, 12699, 12701, 12702, 12703, 12704, 12707, 12708, 12709, 12710, 12711, 12712, 12713, 12714, 12715, 12716, 12717, 12718, 12719, 12720, 12721, 12722, 12723, 12724, 12725, 12726, 12727, 12728, 12729, 12730, 12731, 12732, 12733, 12734, 12735, 12736, 12737, 12738, 12739, 12740, 12741, 12742, 12743, 12744, 12745, 12746, 12747, 12748, 12749, 12750, 12751, 12752, 12753, 12754, 12755, 12756, 12757, 12758, 12759, 12760, 12761, 12762, 12763, 12764, 12765, 12766, 12767, 12768, 12769, 12770, 12771, 12772, 12773, 12774, 12775, 12776, 12777, 12778, 12779, 12780, 12781, 12782, 12783, 12784, 12785, 12786, 12787, 12788, 12789, 12791, 12792, 12794, 12797, 12798, 12799, 12800, 12802, 12803, 12806, 12812, 12813, 12814, 12815, 12816, 12817, 12818, 12819, 12820, 12821, 12822, 12823, 12824, 12825, 12826, 12827, 12828, 12829, 12830, 12831, 12832, 12833, 12834, 12835, 12836, 12847, 12848, 12850, 12851, 12852, 12853, 12854, 12855, 12856, 12857, 12858, 12859, 12860, 12861, 12862, 12863, 12864, 12865, 12866, 12867, 12868, 12887, 12888, 12889, 12890, 12891, 12892, 12893, 12894, 12895, 12896, 12897, 12898, 12899, 12900, 12901, 12902, 12903, 12904, 12905, 12906, 12907, 12908, 12909, 12910, 12911, 12912, 12913, 12914, 12915, 12916, 12917, 12918, 12919, 12920, 12921, 12922, 12923, 12924, 12925, 12926, 12927, 12928, 12929, 12930, 12931, 12932, 12933, 12934, 12935, 12936, 12937, 12938, 12939, 12940, 12941, 12942, 12943, 12944, 12945, 12946, 12947, 12948, 12949, 12950, 12951, 12954, 12955, 12956, 12957, 12958, 12959, 12960, 12961, 12962, 13144, 13149, 13150, 13154, 14489, 14490, 14491, 14492, 14493, 14494, 14495, 14496, 14497, 14498, 14499, 14500, 14501, 14502, 14503, 14504, 14505, 14506, 14507, 14508, 14509, 14510, 14511, 14512, 14513, 14514, 14515, 14516, 14517, 14518, 14519, 14520, 14521, 14522, 14523, 14524, 14525, 14526, 14527, 14528, 14529, 14530, 14531, 14536, 14537, 14538, 14539, 14564, 14565, 14566, 14567, 14568, 14569, 14570, 14572, 14573, 14578, 14579, 14580, 14583, 14584, 14585, 14586, 14587, 14588, 14589, 14590, 14591, 14592, 14593, 14594, 14595, 14596, 14597, 14598, 14599, 14600, 14601, 14602, 14603, 14604, 14605, 14606, 14607, 14608, 14609, 14610, 14611, 14612, 14613, 14614, 14615, 14616, 14617, 14618, 14619, 14620, 14621, 14622, 14623, 14624, 14625, 14626, 14627, 14628, 14629, 14630, 14631, 14632, 14633, 14634, 14635, 14636, 14637, 14638, 14639, 14640, 14641, 14642, 14647, 14649, 14650, 14652, 14653, 14654, 14677, 14678, 14679, 14680, 14681, 14682, 14683, 14685, 14686, 14691, 14692, 14693, 14696, 14697, 14698, 14699, 14700, 14701, 14702, 14703, 14704, 14705, 14706, 14707, 14708, 14709, 14710, 14711, 14712, 14713, 14714, 14715, 14716, 14717, 14718, 14719, 14720, 14721, 14722, 14723, 14724, 14725, 14726, 14727, 14728, 14729, 14730, 14731, 14732, 14733, 14734, 14735, 14736, 14737, 14738, 14739, 14740, 14741, 14742, 14743, 14744, 14745, 14746, 14747, 14748, 14749, 14750, 14751, 14752, 14753, 14754, 14755, 14760, 14762, 14763, 14765, 14766, 14767, 14770, 14771, 14772, 14773, 14774, 14775, 14776, 14777, 14778, 14779, 14780, 14781, 14782, 14783, 14784, 14785, 14786, 14787, 14788, 14789, 14790, 14791, 14792, 14793, 14794, 14795, 14796, 14797, 14798, 14799, 14800, 14801, 14802, 14803, 14804, 14805, 14806, 15605, 15606, 15607, 15608, 15609, 15610, 15611, 15612, 15613, 15614, 15615, 15616, 15617, 15618, 15619, 15620, 15621, 15622, 15623, 15624, 15625, 15626, 15627, 15628, 15629, 15630, 15631, 15632, 15633, 15634, 15635, 15636, 15637, 15638, 15639, 15640, 15641, 15642, 15643, 15644, 15645, 15646, 16820, 16821, 16822, 16823, 16824, 16825, 16826, 16827, 16828, 16829, 16830, 16831, 16832, 16833, 16834, 16835, 16836, 16837, 16838, 16839, 16840, 16841, 16842, 16843, 16844, 16845, 16846, 16847, 16848, 16849, 16850, 16851, 16852, 16853, 16854, 16855, 16856, 16857, 16858, 16859, 16860, 16861, 16862, 16863, 16864, 16865, 16866, 16867, 16868, 16869, 16870, 16871, 16872, 16873, 16874, 16875, 16876, 16877, 16878, 16879, 16880, 16881, 16882, 16883, 16884, 16885, 16886, 16887, 16888, 16903, 16904, 16905, 16906, 16907, 16908, 16909, 16910, 16911, 16912, 16913, 16914, 16915, 16916, 16917, 16918, 16919, 16920, 16921, 16922, 16923, 16924, 16925, 16926, 16927, 16928, 16929, 16930, 16931, 16932, 16933, 16934, 16935, 16936, 16937, 16938, 16939, 16940, 16941, 16942, 16943, 16944, 16966, 16967, 16971, 16972, 17001, 17002, 17003, 17004, 17005, 17006, 17007, 17008, 17009, 17010, 17011, 17012, 17013, 17014, 17015, 17016, 17017, 17018, 17019, 17020, 17021, 17022, 17023, 17024, 17025, 17026, 17027, 17028, 17029, 17030, 17031, 17032, 17033, 17034, 17035, 17036, 17037, 17038, 17039, 17040, 17041, 17042, 17043, 17044, 17045, 17046, 17047, 17048, 17049, 17050, 17051, 17052, 17053, 17054, 17055, 17056, 17057, 17058, 17059, 17060, 17061, 17062, 17063, 17064, 17065, 17066, 17067, 17068, 17069, 17070, 17071, 17072, 17073, 17074, 17075, 17076, 17077, 17078, 17079, 17080, 17081, 17082, 17083, 17084, 17085, 17086, 17087, 17088, 17089, 17090, 17091, 17092, 17093, 17094, 17095, 17096, 17097, 17098, 17099, 17100, 17101, 17102, 17103, 17104, 17105, 17106, 17107, 17108, 17109, 17110, 17111, 17112, 17113, 17114, 17115, 17116, 17117, 17118, 17119, 17120, 17121, 17122, 17123, 17124, 17125, 17126, 17127, 17128, 17129, 17130, 17131, 17132, 17133, 17134, 17135, 17136, 17137, 17138, 17139, 17140, 17141, 17142, 17143, 17144, 17145, 17146, 17147, 17148, 17149, 17150, 17151, 17152, 17153, 17154, 17155, 17156, 17157, 17158, 17159, 17160, 17161, 17162, 17163, 17164, 17165, 17166, 17167, 17168, 17169, 17170, 17171, 17172, 17173, 17174, 17175, 17176, 17177, 17178, 17179, 17180, 17181, 17182, 17183, 17184, 17185, 17186, 17187, 17188, 17189, 17190, 17191, 17192, 17193, 17194, 17195, 17196, 17197, 17198, 17199, 17200, 17201, 17202, 17203, 17204, 17205, 17206, 17207, 17208, 17209, 17210, 17211, 17212, 17213, 17214, 17215, 17216, 17217, 17218, 17219, 17220, 17221, 17222, 17223, 17224, 17225, 17226, 17227, 17228, 17229, 17230, 17231, 17232, 17233, 17234, 17235, 17236, 17237, 17238, 17239, 17240, 17241, 17242, 17243, 17244, 17245, 17246, 17247, 17248, 17249, 17250, 17251, 17252, 17253, 17254, 17255, 17256, 17257, 17258, 17259, 17260, 17261, 17262, 17263, 17264, 17265, 17266, 17267, 17268, 17269, 17270, 17271, 17272, 17273, 17274, 17275, 17276, 17277, 17278, 17279, 17280, 17281, 17282, 17283, 17284, 17285, 17286, 17287, 17288, 17289, 17290, 17291, 17292, 17293, 17294, 17295, 17296, 17297, 17298, 17299, 17300, 17301, 17302, 17303, 17304, 17305, 17306, 17307, 17308, 17309, 17310, 17311, 17312, 17313, 17314, 17315, 17316, 17317, 17318, 17319, 17320, 17321, 17322, 17323, 17324, 17325, 17326, 17327, 17328, 17329, 17330, 17331, 17332, 17333, 17334, 17335, 17336, 17337, 17338, 17339, 17340, 17341, 17342, 17343, 17344, 17345, 17346, 17347, 17348, 17349, 17350, 17351, 17352, 17353, 17354, 17355, 17356, 17357, 17358, 17359, 17360, 17361, 17362, 17363, 17364, 17365, 17366, 17367, 17368, 17369, 17370, 17371, 17372, 17373, 17374, 17375, 17376, 17377, 17378, 17379, 17380, 17381, 17382, 17383, 17384, 17385, 17386, 17387, 17388, 17389, 17390, 17391, 17392, 17393, 17394, 17395, 17396, 17397, 17398, 17399, 17400, 17401, 17402, 17403, 17404, 17405, 17406, 17407, 17408, 17409, 17410, 17411, 17412, 17413, 17414, 17415, 17416, 17417, 17420, 17421, 17422, 17423, 17424, 17425, 17429, 17430, 17431, 17432, 17433, 17434, 17435, 17436, 17438, 17439, 17440, 17441, 17442, 17443, 17446, 17447, 17448, 17449, 17450, 17451, 17452, 17455, 17456, 17457, 17458, 17459, 17460, 17464, 17465, 17466, 17467, 17468, 17469, 17471, 17472, 17473, 17474, 17475, 17476, 17479, 17480, 17481, 17482, 17483, 17484, 17485, 17488, 17489, 17490, 17491, 17492, 17493, 17494, 17496, 17497, 17498, 17502, 17503, 17504, 17505, 17506, 17507, 17508, 17510, 17511, 17513, 17514, 17515, 17516, 17517, 17518, 17519, 17520, 17523, 17524, 17525, 17526, 17527, 17528, 17530, 17531, 17535, 17536, 17537, 17538, 17539, 17540, 17542, 17543, 17545, 17546, 21391, 21392, 21393, 21394, 21395, 21396, 21397, 21398, 21399, 21400, 21401, 21402, 21403, 21404, 21405, 21406, 21407, 21408, 21409, 21410, 21411, 21412, 21413, 21414, 21415, 21416, 21417, 21418, 21419, 21420, 21421, 21422, 21423, 21424, 21425, 21426, 21447, 21459, 21460, 21463, 21465, 21467, 21469, 21471, 21473, 21475, 21497, 21605, 21606, 21607, 21608, 21609, 21610, 21611, 21612, 21613, 21614, 21615, 21616, 21617, 21618, 21619, 21620, 21621, 21622, 21623, 21624, 21625, 21626, 21627, 21628, 21629, 21630, 21631, 21632, 21633, 21634, 21635, 21636, 21637, 21638, 21639, 21640, 21661, 21673, 21674, 21677, 21679, 21681, 21683, 21685, 21687, 21689, 21711]