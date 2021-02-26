#!/usr/bin/python3.7
# -*- coding: utf-8 -*-

"""

Internal OpenGL Renderer Plugin
Extended to Interpolate features.

**Project Name:**      MakeHuman

**Product Home Page:** http://www.makehuman.org/

**Code Home Page:**    https://bitbucket.org/MakeHuman/makehuman/

**Authors:**           Thanasis Papoutsidakis (Original Render Code)
                        Jason Hays (Skin change)

"""
import log
from . import makehuman_difference
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

class DifferenceModelTaskView(gui3d.TaskView):

    def __init__(self, category):
        gui3d.TaskView.__init__(self, category, 'Difference Model')

        settingsBox = self.addLeftWidget(gui.GroupBox('Settings'))

        self.pathM1 = ""
        self.pathM1_button = settingsBox.addWidget(gui.BrowseButton('open', "Select the average Model"))
        self.pathM1Box = settingsBox.addWidget(gui.TextEdit(self.pathM1))
        @self.pathM1_button.mhEvent
        def onClicked(path):
            self.pathM1 = path
            self.pathM1Box.setText(self.pathM1)

        self.pathE1 = "None"
        self.pathE1_button = settingsBox.addWidget(gui.BrowseButton('open', "Select an expression"))
        self.pathE1Box = settingsBox.addWidget(gui.TextEdit(self.pathE1))
        @self.pathE1_button.mhEvent
        def onClicked(path):
            self.pathE1 = path
            self.pathE1Box.setText(self.pathE1)

        self.pathM2 = ""
        self.pathM2_button = settingsBox.addWidget(gui.BrowseButton('open', "Select another Model"))
        self.pathM2Box = settingsBox.addWidget(gui.TextEdit(self.pathM2))
        @self.pathM2_button.mhEvent
        def onClicked(path):
            self.pathM2 = path
            self.pathM2Box.setText(self.pathM2)

        self.pathE2 = "None"
        self.pathE2_button = settingsBox.addWidget(gui.BrowseButton('open', "Select an expression"))
        self.pathE2Box = settingsBox.addWidget(gui.TextEdit(self.pathE2))
        @self.pathE2_button.mhEvent
        def onClicked(path):
            self.pathE2 = path
            self.pathE2Box.setText(self.pathE2)
        
        
        self.goButton = settingsBox.addWidget(gui.Button('Start'))

        self.save_button = settingsBox.addWidget(gui.BrowseButton("save", "Save Difference JSON"))
        self.load_button = settingsBox.addWidget(gui.BrowseButton('open', 'Load Difference JSON'))
        
        self.difference_skin = None

        @self.goButton.mhEvent
        def onClicked(event):
            model1 = self.pathM1
            model2 = self.pathM2
            expression1 = self.pathE1
            expression2 = self.pathE2
            self.difference_skin = makehuman_difference.difference_models(model1, expression1, model2, expression2)
        
        @self.load_button.mhEvent
        def onClicked(path):
            # set the average model and the skin
            with open(path, 'r') as f:
                d = json.load(f)
                model = d[0]
                expression = d[1]
                self.difference_skin = np.array(d[2], dtype=np.uint8)
                # load model and set expression
                gui3d.app.loadHumanMHM(model)
                makehuman_difference.setExpression(expression)

                human = G.app.objects[0]
                # get rid of the skin
                human.material.diffuseTexture=None
                # set the colors
                human.mesh.r_color = self.difference_skin
                # update the color
                human.mesh.sync_color()
            
            
        @self.save_button.mhEvent
        def onClicked(path):
            # make it serializable
            l = [[int(k) for k in x] for x in self.difference_skin]
            '''for i in range(len(l)):
                for k in range(len(l[i])):
                    l[i][k] = int(l[i][k])'''

            with open(path, 'w') as f:
                json.dump([self.pathM1, self.pathE1, l], f)

    
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
    taskview = DifferenceModelTaskView(category)
    taskview.sortOrder = 1.3
    category.addTask(taskview)


def unload(app):
    pass
