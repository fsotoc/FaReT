#!/usr/bin/python2.7
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
from guirender import RenderTaskView
import mh
import PyQt4
import numpy as np
import os
import getpath
from . import interpolate

class InterpolateOpenGLTaskView(RenderTaskView):

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
            

        interpolateSettingsBox.addWidget(gui.TextView("Expression file (or specify 'None')"))
        self.expressionBox = interpolateSettingsBox.addWidget(gui.TextEdit(""))
        self.expression_button = interpolateSettingsBox.addWidget(gui.BrowseButton('open', "Select an expression file"))
        interpolateSettingsBox.addWidget(gui.TextView("Expression Extrapolation Percentage"))
        self.expressionPercentageBox = interpolateSettingsBox.addWidget(gui.TextEdit("100"))
        
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
            selected_frame.setUserData(data={"frame":self.num(self.currentFramesBox.getText()),
                                                                   "rot_Y": self.num(self.camY.getText()),
                                                                   "rot_X": self.num(self.camX.getText()),
                                                                   "model": self.modelBox.getText()+"|"+self.modelPercentageBox.getText(),
                                                                   "expression": self.expressionBox.getText()+"|"+self.expressionPercentageBox.getText()})
            self.resort_frames()
            
        @self.addFrame.mhEvent
        def onClicked(event):
            self.interpolatedFramesList.addItem('Frame {0}'.format(self.currentFramesBox.getText()), data={"frame":self.num(self.currentFramesBox.getText()),
                                                                   "rot_Y": self.num(self.camY.getText()),
                                                                   "rot_X": self.num(self.camX.getText()),
                                                                   "model": self.modelBox.getText()+"|"+self.modelPercentageBox.getText(),
                                                                   "expression": self.expressionBox.getText()+"|"+self.expressionPercentageBox.getText()})
            self.resort_frames()
            
        @self.removeFrame.mhEvent
        def onClicked(event):
            selected_frame = self.interpolatedFramesList.selectedItems()
            if len(selected_frame) == 0:
                return
            selected_frame = selected_frame[0]
            new_items = [item for item in self.interpolatedFramesList.getItems() if item is not selected_frame]
            self.reassign(new_items)
        
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
            frameKey = PyQt4.QtCore.QString(u'frame')
            frame = self.num(data[frameKey])
            for k in data:
                if data[k] == "" or k == frameKey:
                    continue
                key = str(k)
                if key != "expression" and key != "model":
                    self.key_frames[key].append((frame, self.num(data[k])))
                elif str(data[k])[0] != "|":
                    self.key_frames[key].append((frame, str(data[k])))
                
    def num(self, value):
        if not type(value) is str and not type(value) is PyQt4.QtCore.QString:
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
            if type(k) == PyQt4.QtCore.QString:
                frames = [self.num(item.getUserData()[PyQt4.QtCore.QString(u'frame')]) for item in items]
            else:
                frames = [self.num(item.getUserData()['frame']) for item in items]
            break
        
        for i,frame in enumerate(frames):
            # integers are exact frames
            if type(frame) == float:
                frames[i] = int(np.round(frame * int(self.framesBox.getText()),0))
                
        indices = np.argsort(frames).reshape((-1,))
        # resort items without converting it to a numpy array
        items = [items[index] for index in indices]
        self.reassign(items)

    def get_data_labels(self, items):
        data = [item.getUserData() for item in items]
        labels = [item.text for item in items]
        return data, labels

    def reassign(self, items):
        data, labels = self.get_data_labels(items)
        # resetting the list clears the old C/C++ object data
        self.interpolatedFramesList.clear()
        # re add the data
        for i, d in enumerate(data):
            self.interpolatedFramesList.addItem(labels[i], data=d)

        
    def listInterpolationFrameOptions(self, settings):
        for key in self.keybox:
            other_key = key
            
            for o in settings.keys():
                if type(o) == PyQt4.QtCore.QString:
                    other_key = PyQt4.QtCore.QString(u'{0}'.format(key))
                    
            content = str(settings[other_key])
            if key == "model" or key == "expression":
                if "|" in content:
                    percent = settings[other_key][content.index("|")+1:]
                    self.keybox[key].setText("{0}".format(content[:content.index("|")]))
                    if key == "model":
                        self.modelPercentageBox.setText(percent)
                    else:
                        self.expressionPercentageBox.setText(percent)
                else:
                    self.keybox[key].setText("{0}".format(content))
            else:
                self.keybox[key].setText("{0}".format(settings[other_key]))

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
