# Jason Hays, 2018

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

def make_average(path="F:/makehuman/identity_models/"):
    models = glob(os.path.join(path, "*.mhm"))
    # subdirectories
    models += glob(os.path.join(path, "*/*.mhm"))
    avg_params = {}
    param_counts = {}
    params_min = {}
    params_max = {}
    sd_params = {}
    for model in models:
        gui3d.app.loadHumanMHM(model)
        params = get_shape_params()
        for param in params:
            if not param in avg_params:
                avg_params[param] = params[param]
                param_counts[param] = 1
                sd_params[param] = [params[param]]
                params_min[param] = params[param]
                params_max[param] = params[param]
            else:
                avg_params[param] += params[param]
                sd_params[param].append(params[param])
                param_counts[param] += 1
                params_min[param] = min(params[param], params_min[param])
                params_max[param] = max(params[param], params_max[param])
                
    for param in avg_params:
        avg_params[param] /= param_counts[param]
        sd_params[param] = float(np.std(sd_params[param]))
    updateModelingParameters(avg_params)
    return avg_params, sd_params, params_min, params_max
    