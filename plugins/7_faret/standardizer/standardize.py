#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

**Authors:**           Jason Hays

"""

# common needs (without rendering)
import gui3d
from glob import glob
import os
import mh
import mhmain
import numpy as np
import log

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

def save_model(path, name):
    human = gui3d.app.selectedHuman
    filename = os.path.join(path,name + ".mhm")
    #human.save(filename,name)
    human.save(filename)




# standardize features
from glob import glob
import re
class Standardizer(object):
    reg_name = re.compile(".*(?:\\\\|/)([^\\/]+)\.mhm", re.DOTALL)
    def __init__(self, standard_keys=[]):
        self.standard_param_regex = [re.compile(r, re.DOTALL) for r in standard_keys if r != ""]
        # store the standard shape params
        self.standard_params = {}
        self.standard_param_keys = []
        
        self.model_paths = []
        self.model_params = None
        self.standard_model = None
        
        
    def load_models(self, model_directory, specific_model=None):
        # load all of the models
        # "\\" is actually only one character: \
        if model_directory[-1] != "\\" or model_directory[-1] != "/":
            model_directory+= "/"
        # get the folder and sub folders
        models = glob(model_directory+"*.mhm")+glob(model_directory+"*/*.mhm")
        
        # if no model is specified, get the first one.
        if specific_model is None:
            specific_model = models[0]
            
        # don't both standardizing the standard model
        if specific_model in models:
            models.remove(specific_model)
        
        self.standard_model = specific_model
        self.model_paths = models
        
        self.model_params = {}
        
        for mp in self.model_paths:
            gui3d.app.loadHumanMHM(mp)
            self.model_params[mp] = get_shape_params()
            
        gui3d.app.loadHumanMHM(self.standard_model)
        self.standard_params = get_shape_params()
        # remove nonstandard params
        keys = [k for k in self.standard_params.keys()]
        for key in keys:
            for regex in self.standard_param_regex:
                if re.search(regex, key):
                    #log.message("Standard Matched "+str(regex)+" "+str(key))
                    if not key in self.standard_param_keys:
                        self.standard_param_keys.append(key)
                    break
                #else:
                #    log.message("Didn't Match "+str(regex)+" "+str(key))
            if not key in self.standard_param_keys:
                del self.standard_params[key]
        
        
    def standardize_shape(self, outdir = None):
        # standardize external features (head shape, neck shape, ear shape)
        # load the model to which you want to standardize
        
        for mp in self.model_paths:
            gui3d.app.loadHumanMHM(mp)
            
            for key in self.standard_params:
                self.model_params[mp][key] = self.standard_params[key]
            updateModelingParameters(self.model_params[mp])
            
            if outdir is not None:
                # save model
                name = re.search(Standardizer.reg_name, mp).group(1)
                save_model(outdir, name)
            
    
    def standardize_geometries(self, outdir = None):
        # standardize all geometries (skin, eyes, teeth, tongue, brows, etc)
        gui3d.app.loadHumanMHM(self.standard_model)
        
        for mp in self.model_paths:
            updateModelingParameters(self.model_params[mp])
        
            if outdir is not None:
                print("name",mp)
                # save model
                name = re.search(Standardizer.reg_name, mp).group(1)
                save_model(outdir, name)
    
    def standardize_all(self, outdir):
        # don't save the models yet
        self.standardize_shape(None)
        # save the models
        self.standardize_geometries(outdir)
