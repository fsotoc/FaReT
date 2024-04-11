# Jason Hays, 2021

import gui3d
from glob import glob
import os
import mh
import numpy as np

# straight from MakeHuman's scripting plugin
# changed iteritems for python 3
def updateModelingParameters(dictOfParameterNameAndValue):
    human = gui3d.app.selectedHuman
    for key, value in iter(dictOfParameterNameAndValue.items()):
        modifier = human.getModifier(key)
        modifier.setValue(value)
    human.applyAllTargets()
    mh.redraw()

def get_shape_params():
    human = gui3d.app.selectedHuman
    
    param_dict = {}
    for key in human.modifierNames:
        param_dict[key] = human.getModifier(key).getValue()
    return param_dict


import json
from collections import OrderedDict
import animation
import bvh
import getpath
from core import G

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

def setExpression(expression):
    if expression == "None":
        modifiers, _ = get_blank_pose()
        return modifiers
    with open(expression, 'r') as f:
        human = G.app.objects[0]
        base_bvh = bvh.load(getpath.getSysDataPath('poseunits/face-poseunits.bvh'), allowTranslation="none")
        base_anim = base_bvh.createAnimationTrack(human.getBaseSkeleton(), name="Expression-Face-PoseUnits")

        poseunit_json = json.load(open(getpath.getSysDataPath('poseunits/face-poseunits.json'),'rb'), object_pairs_hook=OrderedDict)
        # the names of the changeable facial expression features
        poseunit_names = poseunit_json['framemapping']
        modifiers = dict(zip(poseunit_names, len(poseunit_names)*[0.0]))
        base_poseunit = animation.PoseUnit(base_anim.name, base_anim.data[:base_anim.nBones*len(poseunit_names)], poseunit_names)

        pose_modifiers = json.load(f, object_pairs_hook=OrderedDict)['unit_poses']

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
        return modifiers
    

def difference_models(model1, expression1, model2, expression2):

    # loadModel(<model name>,[path])
    #
    # This will load a human model from an MHM file. The <model name> part should be a string without spaces
    # and without the .MHM extension. The [path] part defaults to the user's makehuman/models directory.

    gui3d.app.loadHumanMHM(model2)
    human = G.app.objects[0]
    setExpression(expression2)
    c2 = human.mesh.r_coord*1

    # load the original (the average, presumably)
    gui3d.app.loadHumanMHM(model1)
    human = G.app.objects[0]
    setExpression(expression1)
    c1 = human.mesh.r_coord*1

    # load a built-in skin that supports changing the colors (default does not!)
    human.mesh.material.fromFile(os.path.join(getpath.getSysDataPath(), "skins/young_caucasian_male/young_caucasian_male2.mhmat"))
    # get rid of the skin properties
    human.material.diffuseTexture=None

    vf = np.zeros(human.mesh.r_color.shape)
    # set the rgb of the skin to the difference
    channel = 0
    for k,v in enumerate(human.mesh.r_color):
        # alphas don't contribute because they're always 255
        #vf[k][i] = np.sum((c1[k]-c2[k])**2)
        vf[k,channel] = np.sum((c1[k]-c2[k])**2)
    # the difference spans from 128 to 255
    mx = np.max(vf[:,channel])
    if mx != 0:
        vf/=mx
    vf *= 135
    vf += 120
    # no floats allowed on the colors.
    human.mesh.r_color = np.array(np.round(vf,0), dtype=np.uint8)
    
    # set the alpha
    human.mesh.r_color[:,3] = 255

    # update the color
    human.mesh.sync_color()
    return human.mesh.r_color


def RGB_difference_models(model1, expression1, model2, expression2):

    # loadModel(<model name>,[path])
    #
    # This will load a human model from an MHM file. The <model name> part should be a string without spaces
    # and without the .MHM extension. The [path] part defaults to the user's makehuman/models directory.

    gui3d.app.loadHumanMHM(model2)
    human = G.app.objects[0]
    setExpression(expression2)
    c2 = human.mesh.r_coord*1

    # load the original (the average, presumably)
    gui3d.app.loadHumanMHM(model1)
    human = G.app.objects[0]
    setExpression(expression1)
    c1 = human.mesh.r_coord*1

    # load a built-in skin that supports changing the colors (default does not!)
    human.mesh.material.fromFile(os.path.join(getpath.getSysDataPath(), "skins/young_caucasian_male/young_caucasian_male2.mhmat"))
    # get rid of the skin properties
    human.material.diffuseTexture=None

    vf = np.zeros(human.mesh.r_color.shape)
    # set the rgb of the skin to the difference
    for k,v in enumerate(human.mesh.r_color):
        for i in range(len(v)-1):
            # alphas don't contribute because they're always 255
            vf[k,:3] = np.abs(c2[k]-c1[k])
    # the difference spans from 0 to 255, with 128 being the middle
    vf[:,3]=0
    mx = np.max(vf[:].reshape(-1))
    if mx != 0:
        vf/=mx
    # range of colors
    vf *= 135
    # dark grey
    vf += 120
    # no floats allowed on the colors.
    human.mesh.r_color = np.array(np.round(vf,0), dtype=np.uint8)
    # set the alpha
    human.mesh.r_color[:,3] = 255

    # update the color
    human.mesh.sync_color()
    return human.mesh.r_color
    
def closeness_to_target(model1, expression1, model2, expression2, model_target, expression_target, mx=.00001):
    
    # load the target
    gui3d.app.loadHumanMHM(model_target)
    human = G.app.objects[0]
    setExpression(expression_target)
    c_target = human.mesh.r_coord*1
    
    # load model1 (reference)
    gui3d.app.loadHumanMHM(model1)
    human = G.app.objects[0]
    setExpression(expression1)
    c1 = human.mesh.r_coord*1
    
    # load model2
    gui3d.app.loadHumanMHM(model2)
    human = G.app.objects[0]
    setExpression(expression2)
    c2 = human.mesh.r_coord*1
    
    # load a built-in skin that supports changing the colors (default does not!)
    human.mesh.material.fromFile(os.path.join(getpath.getSysDataPath(), "skins/young_caucasian_male/young_caucasian_male2.mhmat"))
    # get rid of the skin properties
    human.material.diffuseTexture=None
    
    # first we get a vector with values and standardize them to go from 0 to 255
    vals = np.zeros(human.mesh.r_color.shape[0])
    for k in np.arange(human.mesh.r_color.shape[0]):
        # distance to target
        # model1 is taken as a reference, so positive values means model2 is closer to target than reference,
        # negative values means model 2 is farther to target than reference
        d_1 = np.sum((c1[k]-c_target[k])**2)
        d_2 = np.sum((c2[k]-c_target[k])**2)
        vals[k] = d_1-d_2
    
    
    # we get sign of values
    vsign = np.sign(vals)
    
    if mx != 0:
        vals = vals/mx
    
    
    # now we transform the values to rgb according to our colormap
    vf = np.zeros(human.mesh.r_color.shape)
    # set the rgb of the skin to the difference
    for k,v in enumerate(human.mesh.r_color):

        # we paint red if positive, blue if negative
        if vsign[k]>0:
            vf[k,0] = np.abs(vals[k])
        elif vsign[k]<0:
            vf[k,2] = np.abs(vals[k])
    # the difference spans from 0 to 255, with 128 being the middle
    # range of colors
    vf *= 135
    # dark grey
    vf += 120
    # no floats allowed on the colors.
    human.mesh.r_color = np.array(np.round(vf,0), dtype=np.uint8)
    # set the alpha
    human.mesh.r_color[:,3] = 255
        
    # update the color
    human.mesh.sync_color()
    return human.mesh.r_color
