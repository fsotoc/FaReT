#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

Internal OpenGL Renderer Plugin
Extended to Interpolate features.

**Project Name:**      MakeHuman

**Product Home Page:** http://www.makehuman.org/

**Code Home Page:**    https://bitbucket.org/MakeHuman/makehuman/

**Authors:**           Thanasis Papoutsidakis (Original Render Code)
                        Jason Hays (Interpolation)

"""

from . import mh2opengl
import json
from core import G
import gui
import gui3d
from guirender import RenderTaskView
import mh
import numpy as np
import os
import getpath
from . import interpolate
import log
mhapi = gui3d.app.mhapi

class InterpolateOpenGLTaskView(RenderTaskView):
    def _onModelGroupChange(self,newValue):
        text = self.modelFeatureBox.getText()
        if text == ".*":
            text = ""
        elif text != "":
            #add a comma if something else is already there
            text+=","

        if newValue == "all":
            text = ".*"
        elif newValue == "head":
            text += "^head"
        else:
            # the other types can be taken literally
            text += newValue
        self.modelFeatureBox.setText(text)
    
    def _onExpressionGroupChange(self,newValue):
        #Cheek, (Chin, Jaw), Brow, (Eye, Lid), (Lip, Mouth, Tongue), (Naso, Nose), 
        # "all", "nose", "eyebrow", "eye", "mouth", "ear", "chin", "cheek"
        text = self.expressionFeatureBox.getText()
        if text == ".*":
            text = ""
        elif text != "":
            #add a comma if something else is already there
            text+=","

        if newValue == "all":
            text = ".*"
        elif newValue == "Eyebrow":
            text += "Brow"
        elif newValue == "Chin":
            text += "Chin,Jaw"
        elif newValue == "Eye":
            text += "Eye,Lid"
        elif newValue == "Mouth":
            text += "Mouth,Lip,Tongue"
        elif newValue == "Nose":
            text += "Nose,Naso"
        else:
            # the other types can be taken literally
            text += newValue
        self.expressionFeatureBox.setText(text)

    def __init__(self, category):
        RenderTaskView.__init__(self, category, 'Interpolation Render')

        # Declare settings
        G.app.addSetting('GL_RENDERER_SSS', False)
        G.app.addSetting('GL_RENDERER_AA', True)

        # Don't change shader for this RenderTaskView.
        self.taskViewShader = G.app.selectedHuman.material.shader

        settingsBox = self.addLeftWidget(gui.GroupBox('Settings'))
        settingsBox.addWidget(gui.TextView("Resolution"))
        self.resBox = settingsBox.addWidget(gui.TextEdit(
            "x".join([str(self.renderingWidth), str(self.renderingHeight)])))
        self.AAbox = settingsBox.addWidget(gui.CheckBox("Anti-aliasing"))
        self.AAbox.setSelected(G.app.getSetting('GL_RENDERER_AA'))
        
        self.path = ""
        self.path_button = settingsBox.addWidget(gui.BrowseButton('dir', "Select an output directory"))
        self.pathBox = settingsBox.addWidget(gui.TextEdit(self.path))

        self.save_models = gui.CheckBox("Save a Model per Frame")
        settingsBox.addWidget(self.save_models)

        @self.path_button.mhEvent
        def onClicked(path):
            self.path = path
            self.pathBox.setText(self.path)
        
        
        self.renderButton = settingsBox.addWidget(gui.Button('Render'))

        self.lightmapSSS = gui.CheckBox("Lightmap SSS")
        self.lightmapSSS.setSelected(G.app.getSetting('GL_RENDERER_SSS'))

        self.optionsBox = self.addLeftWidget(gui.GroupBox('Options'))
        self.optionsWidgets = []

        renderMethodBox = self.addRightWidget(gui.GroupBox('Rendering methods'))
        self.renderMethodList = renderMethodBox.addWidget(gui.ListView())
        self.renderMethodList.setSizePolicy(
            gui.SizePolicy.Ignored, gui.SizePolicy.Preferred)

        # Rendering methods
        self.renderMethodList.addItem('Quick Render')
        self.renderMethodList.addItem('Advanced Render',
            data=[self.lightmapSSS])

        if not mh.hasRenderToRenderbuffer():
            self.firstTimeWarn = True
            # Can only use screen grabbing as fallback,
            # resolution option disabled
            self.resBox.setEnabled(False)
            self.AAbox.setEnabled(False)

        self.listOptions(None)
        
        # add interpolation settings to the right pane        
        interpolateFrameBox = self.addRightWidget(gui.GroupBox('Total Frames'))
        interpolateFrameBox.addWidget(gui.TextView("Frames"))
        self.framesBox = interpolateFrameBox.addWidget(gui.TextEdit("120"))
        
        interpolatedFramesBox = self.addRightWidget(gui.GroupBox('Interpolated Frames'))
        self.interpolatedFramesList = interpolatedFramesBox.addWidget(gui.ListView())
        self.interpolatedFramesList.setSizePolicy(
            gui.SizePolicy.Ignored, gui.SizePolicy.Preferred)
        self.interpolatedFramesList.setVerticalScrollingEnabled(True)
        self.addFrame = interpolatedFramesBox.addWidget(gui.Button('Add Frame'))
        self.removeFrame = interpolatedFramesBox.addWidget(gui.Button('Remove Frame'))
        self.save_button = interpolatedFramesBox.addWidget(gui.BrowseButton('save', "Save As.."))
        self.load_button = interpolatedFramesBox.addWidget(gui.BrowseButton('open', 'Load JSON'))
        
        self.key_frames = None
        
        @self.load_button.mhEvent
        def onClicked(path):
            with open(path, 'r') as f:
                self.key_frames = json.load(f)
                self.GUItize_key_frames()
                self.resort_frames()

        @self.save_button.mhEvent
        def onClicked(path):
            self.generate_key_frames()
                    
            with open(path, 'w') as f:
                json.dump(self.key_frames, f)
        
        
        interpolateSettingsBox = self.addRightWidget(gui.GroupBox('Interpolation Settings'))
        interpolateSettingsBox.addWidget(gui.TextView("Current Frame (integer frame # or float proportion)"))
        self.currentFramesBox = interpolateSettingsBox.addWidget(gui.TextEdit("0.0"))
        interpolateSettingsBox.addWidget(gui.TextView("Orbit Camera Y (left-right)"))
        self.camY = interpolateSettingsBox.addWidget(gui.TextEdit(""))
        interpolateSettingsBox.addWidget(gui.TextView("Oribt Camera X (up-down)"))
        self.camX = interpolateSettingsBox.addWidget(gui.TextEdit(""))

        interpolateSettingsBox.addWidget(gui.TextView("Model File"))
        self.modelBox = interpolateSettingsBox.addWidget(gui.TextEdit(""))
        self.model_button = interpolateSettingsBox.addWidget(gui.BrowseButton('open', "Select a model file"))
        @self.model_button.mhEvent
        def onClicked(path):
            self.modelBox.setText(path)
        interpolateSettingsBox.addWidget(gui.TextView("Model Extrapolation Percentage"))
        self.modelPercentageBox = interpolateSettingsBox.addWidget(gui.TextEdit("100"))
        # allow alpha beta parameters
        self.modelAlphaBetaList = interpolateSettingsBox.addWidget(gui.ListView())
        interpolateSettingsBox.addWidget(gui.TextView("Features"))
        self.modelFeatureBox = interpolateSettingsBox.addWidget(gui.TextEdit(".*"))
        # recommended groups
        self.modelGroups = ["all", "nose", "head", "forehead", "eyebrow", "eyes", "mouth", "ear", "chin", "cheek"]
        self.modelGroupBox = mhapi.ui.createComboBox(self.modelGroups, self._onModelGroupChange)
        interpolateSettingsBox.addWidget(self.modelGroupBox)

        interpolateSettingsBox.addWidget(gui.TextView("Alpha"))
        self.modelAlphaBox = interpolateSettingsBox.addWidget(gui.TextEdit("1.0"))
        interpolateSettingsBox.addWidget(gui.TextView("Beta"))
        self.modelBetaBox = interpolateSettingsBox.addWidget(gui.TextEdit("1.0"))
        self.modelAddButton = interpolateSettingsBox.addWidget(gui.Button("Add"))
        self.modelRemoveButton = interpolateSettingsBox.addWidget(gui.Button("Remove"))



        interpolateSettingsBox.addWidget(gui.TextView("Expression file (or specify 'None')"))
        self.expressionBox = interpolateSettingsBox.addWidget(gui.TextEdit(""))
        self.expression_button = interpolateSettingsBox.addWidget(gui.BrowseButton('open', "Select an expression file"))
        interpolateSettingsBox.addWidget(gui.TextView("Expression Extrapolation Percentage"))
        self.expressionPercentageBox = interpolateSettingsBox.addWidget(gui.TextEdit("100"))
        # alphas and betas for expressions
        self.expressionAlphaBetaList = interpolateSettingsBox.addWidget(gui.ListView())
        interpolateSettingsBox.addWidget(gui.TextView("Features"))
        self.expressionFeatureBox = interpolateSettingsBox.addWidget(gui.TextEdit(".*"))
        # recommended groups
        self.expressionGroups = ["all", "Nose", "Eyebrow", "Eye", "Mouth", "Ear", "Chin", "Cheek"]
        self.expressionGroupBox = mhapi.ui.createComboBox(self.expressionGroups, self._onExpressionGroupChange)
        interpolateSettingsBox.addWidget(self.expressionGroupBox)
        
        interpolateSettingsBox.addWidget(gui.TextView("Alpha"))
        self.expressionAlphaBox = interpolateSettingsBox.addWidget(gui.TextEdit("1.0"))
        interpolateSettingsBox.addWidget(gui.TextView("Beta"))
        self.expressionBetaBox = interpolateSettingsBox.addWidget(gui.TextEdit("1.0"))
        self.expressionAddButton = interpolateSettingsBox.addWidget(gui.Button("Add"))
        self.expressionRemoveButton = interpolateSettingsBox.addWidget(gui.Button("Remove"))

        

        @self.modelAddButton.mhEvent
        def onClicked(event):
            features = self.modelFeatureBox.getText()
            alpha = float(self.modelAlphaBox.getText())
            beta = float(self.modelBetaBox.getText())
            self.modelAlphaBetaList.addItem('{0}: ({1:0.2f}, {2:0.2f})'.format(features, alpha, beta), data=dict(features=features, alpha=alpha, beta=beta))

        @self.modelRemoveButton.mhEvent
        def onClicked(event):
            selected_frame = self.modelAlphaBetaList.selectedItems()
            if len(selected_frame) == 0:
                return
            selected_frame = selected_frame[0]
            new_items = [item for item in self.modelAlphaBetaList.getItems() if item is not selected_frame]
            self.reassign(self.modelAlphaBetaList, new_items)

        @self.expressionAddButton.mhEvent
        def onClicked(event):
            features = self.expressionFeatureBox.getText()
            alpha = float(self.expressionAlphaBox.getText())
            beta = float(self.expressionBetaBox.getText())
            self.expressionAlphaBetaList.addItem('{0}: ({1:0.2f}, {2:0.2f})'.format(features, alpha, beta), data=dict(features=features, alpha=alpha, beta=beta))

        @self.expressionRemoveButton.mhEvent
        def onClicked(event):
            selected_frame = self.expressionAlphaBetaList.selectedItems()
            if len(selected_frame) == 0:
                return
            selected_frame = selected_frame[0]
            new_items = [item for item in self.expressionAlphaBetaList.getItems() if item is not selected_frame]
            self.reassign(self.expressionAlphaBetaList, new_items)

        @self.expression_button.mhEvent
        def onClicked(path):
            self.expressionBox.setText(path)
            
        self.updateFrame = interpolateSettingsBox.addWidget(gui.Button('Update Frame'))
        
        self.keybox = {"frame": self.currentFramesBox,
                       "rot_Y" : self.camY,
                       "rot_X" : self.camX,
                       "model" : self.modelBox,
                       "expression" : self.expressionBox}

        @self.framesBox.mhEvent
        def onChange(value):
            try:
                tmp = 1 / int(value)
                self.resort_frames()
            except:
                pass
            
        # save the values back to the selected frame
        @self.updateFrame.mhEvent
        def onClicked(event):
            selected_frame = self.interpolatedFramesList.selectedItems()
            if len(selected_frame) == 0:
                return
            selected_frame = selected_frame[0]
            selected_frame.setText('Frame {0}'.format(self.currentFramesBox.getText()))

            
            # each item has a Regular expression and the alpha beta values
            model_extra = {}
            for item in self.modelAlphaBetaList.getItems():
                d = item.getUserData()
                model_extra[d['features']] = (d['alpha'], d['beta'])

            expression_extra = {}
            for item in self.expressionAlphaBetaList.getItems():
                d = item.getUserData()
                expression_extra[d['features']] = (d['alpha'], d['beta'])


            selected_frame.setUserData(data={"frame":self.num(self.currentFramesBox.getText()),
                                                                   "rot_Y": self.num(self.camY.getText()),
                                                                   "rot_X": self.num(self.camX.getText()),
                                                                   "model": (self.modelBox.getText(), self.num(self.modelPercentageBox.getText()), model_extra),
                                                                   "expression": (self.expressionBox.getText(), self.num(self.expressionPercentageBox.getText()), expression_extra)})
            self.resort_frames()
            self.generate_key_frames()
            
        @self.addFrame.mhEvent
        def onClicked(event):
            # each item has a Regular expression and the alpha beta values
            model_extra = {}
            for item in self.modelAlphaBetaList.getItems():
                d = item.getUserData()
                model_extra[d['features']] = (d['alpha'], d['beta'])

            expression_extra = {}
            for item in self.expressionAlphaBetaList.getItems():
                d = item.getUserData()
                expression_extra[d['features']] = (d['alpha'], d['beta'])

            self.interpolatedFramesList.addItem('Frame {0}'.format(self.currentFramesBox.getText()),data={"frame":self.num(self.currentFramesBox.getText()),
                                                                   "rot_Y": self.num(self.camY.getText()),
                                                                   "rot_X": self.num(self.camX.getText()),
                                                                   "model": (self.modelBox.getText(), self.num(self.modelPercentageBox.getText()), model_extra),
                                                                   "expression": (self.expressionBox.getText(), self.num(self.expressionPercentageBox.getText()), expression_extra)})
            self.resort_frames()
            
        @self.removeFrame.mhEvent
        def onClicked(event):
            selected_frame = self.interpolatedFramesList.selectedItems()
            if len(selected_frame) == 0:
                return
            selected_frame = selected_frame[0]
            new_items = [item for item in self.interpolatedFramesList.getItems() if item is not selected_frame]
            self.reassign(self.interpolatedFramesList, new_items)
        
        @self.interpolatedFramesList.mhEvent
        def onClicked(item):
            self.listInterpolationFrameOptions(item.getUserData())
            
        @self.resBox.mhEvent
        def onChange(value):
            try:
                value = value.replace(" ", "")
                res = [int(x) for x in value.split("x")]
                self.renderingWidth = res[0]
                self.renderingHeight = res[1]
            except:  # The user hasn't typed the value correctly yet.
                pass

        @self.AAbox.mhEvent
        def onClicked(value):
            G.app.setSetting('GL_RENDERER_AA', self.AAbox.selected)

        @self.lightmapSSS.mhEvent
        def onClicked(value):
            G.app.setSetting('GL_RENDERER_SSS', self.lightmapSSS.selected)
            
        @self.renderMethodList.mhEvent
        def onClicked(item):
            self.listOptions(item.getUserData())

        @self.renderButton.mhEvent
        def onClicked(event):
            settings = dict()
            settings['scene'] = G.app.scene
            settings['AA'] = self.AAbox.selected
            settings['dimensions'] = (self.renderingWidth, self.renderingHeight)
            settings['lightmapSSS'] = self.lightmapSSS.selected and self.lightmapSSS in self.optionsWidgets
            settings['saveModels'] = self.save_models.selected
            # change the timing of the render
            # add path output
            self.generate_key_frames()
            interpolate.do_op(self.key_frames, "Front", save_path = self.pathBox.getText(), render_function = (mh2opengl.Render, settings))
            #img = mh2opengl.Render(settings)
            #img.save(path)

            
    def GUItize_key_frames(self):
        if self.key_frames is None:
            return
        self.interpolatedFramesList.clear()
        # go from a feature centric space to a frame-centric space
        candidates = {}
        for key in self.key_frames:
            if key == 'frames':
                self.framesBox.setText("{0}".format(self.key_frames['frames']))
                continue
                
            for change in self.key_frames[key]:
                frame = change[0]
                if not frame in candidates:
                    candidates[frame] = {'frame':frame, 'rot_X':"", 'rot_Y':"", 'model':"", 'expression':""}
                value = change[1]
                candidates[frame][key] = value
        for frame in candidates:
            self.interpolatedFramesList.addItem("Frame {0}".format(frame), data=candidates[frame])
        
    def generate_key_frames(self):
        # generate the keyframes from the current data.
        self.key_frames = {'frames':self.num(self.framesBox.getText()), 'rot_X':[], 'rot_Y':[], 'model':[], 'expression':[]}
        for item in self.interpolatedFramesList.getItems():
            data = item.getUserData()
            frameKey = 'frame'
            frame = self.num(data[frameKey])
            for k in data:
                if data[k] == "" or k == frameKey:
                    continue
                key = str(k)
                if key == "expression" or key == "model":
                    self.key_frames[key].append((frame, data[k]))
                else:
                    self.key_frames[key].append((frame, self.num(data[k])))
                
    def num(self, value):
        if not type(value) is str:
            return value
        if value == "":
            return ""
        if "." in value:
            return float(value)
        return int(value)
        
    def resort_frames(self):
        items = self.interpolatedFramesList.getItems()
        
        data = items[0].getUserData()
        for k in data:
            frames = [self.num(item.getUserData()['frame']) for item in items]
            break
        
        for i,frame in enumerate(frames):
            # integers are exact frames
            if type(frame) == float:
                frames[i] = int(np.round(frame * int(self.framesBox.getText()),0))
                
        indices = np.argsort(frames).reshape((-1,))
        # resort items without converting it to a numpy array
        items = [items[index] for index in indices]
        self.reassign(self.interpolatedFramesList, items)

    def get_data_labels(self, items):
        data = [item.getUserData() for item in items]
        labels = [item.text for item in items]
        return data, labels

    def reassign(self, my_list, items):
        data, labels = self.get_data_labels(items)
        # resetting the list clears the old C/C++ object data
        #self.interpolatedFramesList.clear()
        my_list.clear()
        # re add the data
        for i, d in enumerate(data):
            #self.interpolatedFramesList.addItem(labels[i], data=d)
            my_list.addItem(labels[i], data=d)
        
    def listInterpolationFrameOptions(self, settings):
        for key in self.keybox:
            log.message("SCRIPT: ("+key+" "+str(settings)+")")
                    
            content = settings[key]
            
            if key == "model" or key == "expression":
                alphaBeta = content[2]
                percent = str(content[1])
                content = str(content[0])
                # add to corresponding list GUI
                my_list = None
                self.keybox[key].setText(content)
                if key == "model":
                    my_list = self.modelAlphaBetaList
                    self.modelPercentageBox.setText(percent)
                else:
                    my_list = self.expressionAlphaBetaList
                    self.expressionPercentageBox.setText(percent)
                
                if my_list is not None:
                    #log.message("SCRIPT: alphaBeta List("+str(alphaBeta)+")")
                    my_list.clear()
                    for key in alphaBeta:
                        features = key
                        alpha = alphaBeta[key][0]
                        beta = alphaBeta[key][1]
                        label = '{0}: ({1:0.2f}, {2:0.2f})'.format(features, alpha, beta)
                        #log.message("SCRIPT: Adding("+label+")")
                        my_list.addItem(label, data=dict(features=features, alpha=alpha, beta=beta))
            else:
                self.keybox[key].setText("{0}".format(content))

    def onShow(self, event):
        RenderTaskView.onShow(self, event)
        self.renderButton.setFocus()
        if not mh.hasRenderToRenderbuffer() and self.firstTimeWarn:
            self.firstTimeWarn = False
            G.app.prompt('Lack of 3D hardware support',
                'Your graphics card lacks support for proper rendering.\nOnly limited functionality will be available.',
                'Ok', None, None, None, 'renderingGPUSupportWarning')

    def onHide(self, event):
        RenderTaskView.onHide(self, event)

    def listOptions(self, widgets):
        for child in self.optionsBox.children[:]:
            self.optionsBox.removeWidget(child)

        if widgets:
            self.optionsWidgets = widgets
            self.optionsBox.show()
            for widget in widgets:
                self.optionsBox.addWidget(widget)
        else:
            self.optionsWidgets = []
            self.optionsBox.hide()


def load(app):
    category = app.getCategory('Rendering')
    taskview = InterpolateOpenGLTaskView(category)
    taskview.sortOrder = 1.3
    category.addTask(taskview)


def unload(app):
    pass
