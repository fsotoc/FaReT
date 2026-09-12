#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""

Internal OpenGL Renderer Plugin
Extended to Interpolate features.

**Project Name:**      MakeHuman

**Product Home Page:** http://www.makehuman.org/

**Code Home Page:**    https://bitbucket.org/MakeHuman/makehuman/

**Authors:**           Thanasis Papoutsidakis (Original Render Code)
                        Jason Hays (Averaging)

"""
import log
from . import makehuman_average
import json
from core import G
import gui
import gui3d
import mh
import numpy as np
from glob import glob
import os
import mhmain
import getpath

class AverageModelTaskView(gui3d.TaskView):

    def __init__(self, category):
        gui3d.TaskView.__init__(self, category, 'Average Model')

        settingsBox = self.addLeftWidget(gui.GroupBox('Settings'))
        self.path = ""
        self.path_button = settingsBox.addWidget(gui.BrowseButton('dir', "Select an input directory"))
        self.pathBox = settingsBox.addWidget(gui.TextEdit(self.path))
        @self.path_button.mhEvent
        def onClicked(path):
            self.path = path
            self.pathBox.setText(self.path)
        
        
        self.goButton = settingsBox.addWidget(gui.Button('Start'))

        self.save_button = settingsBox.addWidget(gui.Button("Save Average JSON"))
        self.load_button = settingsBox.addWidget(gui.BrowseButton('dir', 'Load Average JSONs from Folder'))
        self.generate_button = settingsBox.addWidget(gui.Button('Generate Randomly From Average'))
        
        self.avg_params = None
        self.params_max = None
        self.params_min = None

        @self.goButton.mhEvent
        def onClicked(event):
            self.avg_params, self.sd_params, self.params_min, self.params_max = makehuman_average.make_average(self.pathBox.getText())
        
        @self.load_button.mhEvent
        def onClicked(path):
            jsons = glob(os.path.join(path, "*.json"))
            self.pathBox.setText(self.path)
            for file in jsons:
                with open(file, 'r') as f:
                    if "avg" in file:
                        self.avg_params = json.load(f)
                    elif "sd" in file:
                        self.sd_params = json.load(f)
                    elif "min" in file:
                        self.params_min = json.load(f)
                    elif "max" in file:
                        self.params_max = json.load(f)
            models = glob(os.path.join(path, "*.mhm"))
            # subdirectories
            models += glob(os.path.join(path, "*/*.mhm"))
            gui3d.app.loadHumanMHM(models[0])
            makehuman_average.updateModelingParameters(self.avg_params)
            
        @self.save_button.mhEvent
        def onClicked(event):
            path = self.pathBox.getText()
            avg_file = os.path.join(path, "avg.json")
            min_file = os.path.join(path, "min.json")
            max_file = os.path.join(path, "max.json")
            sd_file = os.path.join(path, "sd.json")
            
            with open(avg_file, 'w') as f:
                json.dump(self.avg_params, f)
            with open(sd_file, 'w') as f:
                json.dump(self.sd_params, f)
            with open(min_file, 'w') as f:
                json.dump(self.params_min, f)
            with open(max_file, 'w') as f:
                json.dump(self.params_max, f)
        
        @self.generate_button.mhEvent
        def onClicked(event):
            params = {}
            for param in self.avg_params:
                params[param] = self.random_between(self.avg_params[param], self.params_min[param], self.params_max[param], self.sd_params[param])
            makehuman_average.updateModelingParameters(params)
            human = gui3d.app.selectedHuman
            mhmain.SymmetryAction(human, 1).do()
    
    def random_between(self, avg, low, high, sd):
        #log.message(str(type(sd))+" "+ str(sd))
        #return np.random.random() * (high-low) + low
        #print(type(sd), sd)
        if sd <= 0.0:
            return avg
        return np.maximum(np.minimum(np.random.normal(loc=avg, scale=sd), high), low)
        
    def onShow(self, event):
        gui3d.TaskView.onShow(self, event)

    def onHide(self, event):
        gui3d.TaskView.onHide(self, event)


def load(app):
    category = app.getCategory('Utilities')
    taskview = AverageModelTaskView(category)
    taskview.sortOrder = 1.3
    category.addTask(taskview)


def unload(app):
    pass
