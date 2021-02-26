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
    human.mesh.material.fromFile("./data/skins/young_caucasian_male/young_caucasian_male2.mhmat")
    # get rid of the skin properties
    human.material.diffuseTexture=None

    vf = np.zeros(human.mesh.r_color.shape)
    # set the rgb of the skin to the difference
    for k,v in enumerate(human.mesh.r_color):
        for i in range(len(v)-1):
            # alphas don't contribute because they're always 255
            vf[k][i] = np.sum((c1[k]-c2[k])**2)*255.0
    # the difference spans from 0 to 255
    mx = np.max(vf)
    vf/=mx
    vf*=255
    # no floats allowed on the colors.
    human.mesh.r_color = np.array(np.round(vf,0), dtype=np.uint8)
    # set the alpha
    human.mesh.r_color[:,3] = 255

    # update the color
    human.mesh.sync_color()
    return human.mesh.r_color
