#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

Internal OpenGL Renderer Plugin
Handle classification images with random shape features and pose features.

**Project Name:**      MakeHuman

**Product Home Page:** http://www.makehuman.org/

**Code Home Page:**    https://bitbucket.org/MakeHuman/makehuman/

**Authors:**           Thanasis Papoutsidakis (Original Render Code)
                        Jason Hays (Classification image generation)

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
from . import classification_images_motion
import log
mhapi = gui3d.app.mhapi

class ClassificationImagesMotionOpenGLTaskView(RenderTaskView):
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

        elif newValue == "Left Eyebrow":
            text += "Left.*Brow"
        elif newValue == "Left Chin":
            text += "ChinLeft,Jaw"
        elif newValue == "Left Eye":
            text += "Left.*Eye,Left.*Lid"
        elif newValue == "Left Mouth":
            text += "Mouth.*Left,Lip,TongueLeft"

        elif newValue == "Right Eyebrow":
            text += "Right.*Brow"
        elif newValue == "Right Chin":
            text += "ChinRight,Jaw"
        elif newValue == "Right Eye":
            text += "Right.*Eye,Right.*Lid"
        elif newValue == "Right Mouth":
            text += "Mouth.*Right,Lip,TongueRight"

        else:
            # the other types can be taken literally
            text += newValue
        self.expressionFeatureBox.setText(text)

    def __init__(self, category):
        RenderTaskView.__init__(self, category, 'Classification Images Motion Render')

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
        
        
        
        
        classificationImagesSettingsBox = self.addRightWidget(gui.GroupBox('Classification Image Settings'))

        classificationImagesSettingsBox.addWidget(gui.TextView("The number of trials"))
        self.trialsBox = classificationImagesSettingsBox.addWidget(gui.TextEdit("1"))

        classificationImagesSettingsBox.addWidget(gui.TextView("The number of frames per trial"))
        self.framesBox = classificationImagesSettingsBox.addWidget(gui.TextEdit("30"))

        classificationImagesSettingsBox.addWidget(gui.TextView("Orbit Camera Y (left-right)"))
        self.camY = classificationImagesSettingsBox.addWidget(gui.TextEdit("0.0"))
        classificationImagesSettingsBox.addWidget(gui.TextView("Oribt Camera X (up-down)"))
        self.camX = classificationImagesSettingsBox.addWidget(gui.TextEdit("0.0"))

        classificationImagesSettingsBox.addWidget(gui.TextView("Oribt Camera Z (out-int)"))
        self.camZ = classificationImagesSettingsBox.addWidget(gui.TextEdit("8.7"))

        classificationImagesSettingsBox.addWidget(gui.TextView("Frame Rate"))
        self.frameRateBox = classificationImagesSettingsBox.addWidget(gui.TextEdit("30"))

        classificationImagesSettingsBox.addWidget(gui.TextView("Material File"))
        self.materialBox = classificationImagesSettingsBox.addWidget(gui.TextEdit("young_caucasian_avg"))

        classificationImagesSettingsBox.addWidget(gui.TextView("Start Model File"))
        self.modelBox = classificationImagesSettingsBox.addWidget(gui.TextEdit(""))
        self.model_button = classificationImagesSettingsBox.addWidget(gui.BrowseButton('open', "Select a model file"))
        @self.model_button.mhEvent
        def onClicked(path):
            self.modelBox.setText(path)

        classificationImagesSettingsBox.addWidget(gui.TextView("End Model File"))
        self.modelBox2 = classificationImagesSettingsBox.addWidget(gui.TextEdit("None"))
        self.model_button2 = classificationImagesSettingsBox.addWidget(gui.BrowseButton('open', "Select a model file"))
        
        @self.model_button2.mhEvent
        def onClicked(path):
            self.modelBox2.setText(path)



        self.modelFeatureList = classificationImagesSettingsBox.addWidget(gui.ListView())
        classificationImagesSettingsBox.addWidget(gui.TextView("Features"))
        self.modelFeatureBox = classificationImagesSettingsBox.addWidget(gui.TextEdit(".*"))
        # recommended groups
        self.modelGroups = ["all", "nose", "head", "forehead", "eyebrow", "eyes", "mouth", "ear", "chin", "cheek"]
        self.modelGroupBox = mhapi.ui.createComboBox(self.modelGroups, self._onModelGroupChange)
        classificationImagesSettingsBox.addWidget(self.modelGroupBox)
        classificationImagesSettingsBox.addWidget(gui.TextView("Mode and SD"))
        self.modelAlphaBox = classificationImagesSettingsBox.addWidget(gui.TextEdit("0.5"))
        self.modelAlphaSDBox = classificationImagesSettingsBox.addWidget(gui.TextEdit("0.2"))
        classificationImagesSettingsBox.addWidget(gui.TextView("Concentration and SD"))
        self.modelBetaBox = classificationImagesSettingsBox.addWidget(gui.TextEdit("25.0"))
        self.modelBetaSDBox = classificationImagesSettingsBox.addWidget(gui.TextEdit("7.6667"))
        self.modelAddButton = classificationImagesSettingsBox.addWidget(gui.Button("Add"))
        self.modelRemoveButton = classificationImagesSettingsBox.addWidget(gui.Button("Remove"))
        
        classificationImagesSettingsBox.addWidget(gui.TextView("Start Expression File"))
        self.expressionBox = classificationImagesSettingsBox.addWidget(gui.TextEdit("None"))
        self.expression_button = classificationImagesSettingsBox.addWidget(gui.BrowseButton('open', "Select an expression"))
        @self.expression_button.mhEvent
        def onClicked(path):
            self.expressionBox.setText(path)

        classificationImagesSettingsBox.addWidget(gui.TextView("End Expression File"))
        self.expressionBox2 = classificationImagesSettingsBox.addWidget(gui.TextEdit(""))
        self.expression_button2 = classificationImagesSettingsBox.addWidget(gui.BrowseButton('open', "Select an expression"))
        @self.expression_button2.mhEvent
        def onClicked(path):
            self.expressionBox2.setText(path)


        self.expressionFeatureList = classificationImagesSettingsBox.addWidget(gui.ListView())

        # add the default CCNLab NSF groups
        alpha = 0.5
        alpha_sd = .2
        beta = 25.0
        beta_sd = 7 + 1/3.
        
        # between the brows
        features = "NoseWrinkler"
        self.expressionFeatureList.addItem('{0}: ({1:0.2f}, {2:0.2f})'.format(features, alpha, beta), data=dict(features=features, alpha=alpha, alpha_sd=alpha_sd, beta=beta, beta_sd=beta_sd))
        
        # the nose
        features = "Nose,Naso"
        self.expressionFeatureList.addItem('{0}: ({1:0.2f}, {2:0.2f})'.format(features, alpha, beta), data=dict(features=features, alpha=alpha, alpha_sd=alpha_sd, beta=beta, beta_sd=beta_sd))
        
        # left brow
        features = "Left.*Brow"
        self.expressionFeatureList.addItem('{0}: ({1:0.2f}, {2:0.2f})'.format(features, alpha, beta), data=dict(features=features, alpha=alpha, alpha_sd=alpha_sd, beta=beta, beta_sd=beta_sd))

        # left eyelid
        features = "Left.*Eye,Left.*Lid"
        self.expressionFeatureList.addItem('{0}: ({1:0.2f}, {2:0.2f})'.format(features, alpha, beta), data=dict(features=features, alpha=alpha, alpha_sd=alpha_sd, beta=beta, beta_sd=beta_sd))

        # right brow
        features = "Right.*Brow"
        self.expressionFeatureList.addItem('{0}: ({1:0.2f}, {2:0.2f})'.format(features, alpha, beta), data=dict(features=features, alpha=alpha, alpha_sd=alpha_sd, beta=beta, beta_sd=beta_sd))

        # right eyelid
        features = "Right.*Eye,Right.*Lid"
        self.expressionFeatureList.addItem('{0}: ({1:0.2f}, {2:0.2f})'.format(features, alpha, beta), data=dict(features=features, alpha=alpha, alpha_sd=alpha_sd, beta=beta, beta_sd=beta_sd))
        
        # chin and jaw
        features = "Chin,Jaw"
        self.expressionFeatureList.addItem('{0}: ({1:0.2f}, {2:0.2f})'.format(features, alpha, beta), data=dict(features=features, alpha=alpha, alpha_sd=alpha_sd, beta=beta, beta_sd=beta_sd))

        # left mouth and cheek
        features = "Mouth.*Left,TongueLeft,Left.*Cheek"
        self.expressionFeatureList.addItem('{0}: ({1:0.2f}, {2:0.2f})'.format(features, alpha, beta), data=dict(features=features, alpha=alpha, alpha_sd=alpha_sd, beta=beta, beta_sd=beta_sd))

        # right mouth and cheek
        features = "Mouth.*Right,TongueRight,Right.*Cheek"
        self.expressionFeatureList.addItem('{0}: ({1:0.2f}, {2:0.2f})'.format(features, alpha, beta), data=dict(features=features, alpha=alpha, alpha_sd=alpha_sd, beta=beta, beta_sd=beta_sd))

        # center mouth
        features = "Tongue,Lip"
        self.expressionFeatureList.addItem('{0}: ({1:0.2f}, {2:0.2f})'.format(features, alpha, beta), data=dict(features=features, alpha=alpha, alpha_sd=alpha_sd, beta=beta, beta_sd=beta_sd))

        classificationImagesSettingsBox.addWidget(gui.TextView("Features"))
        self.expressionFeatureBox = classificationImagesSettingsBox.addWidget(gui.TextEdit(".*"))
        # recommended groups
        self.expressionGroups = ["all", "Nose", "Eyebrow", "Eye", "Mouth", "Chin", "Cheek", "Left Eyebrow", "Left Chin", "Left Eye", "Left Mouth", "Right Eyebrow", "Right Chin", "Right Eye", "Right Mouth"]
        self.expressionGroupBox = mhapi.ui.createComboBox(self.expressionGroups, self._onExpressionGroupChange)
        classificationImagesSettingsBox.addWidget(self.expressionGroupBox)
        
        classificationImagesSettingsBox.addWidget(gui.TextView("Mode and SD"))
        self.expressionAlphaBox = classificationImagesSettingsBox.addWidget(gui.TextEdit("0.5"))
        self.expressionAlphaSDBox = classificationImagesSettingsBox.addWidget(gui.TextEdit("0.2"))
        classificationImagesSettingsBox.addWidget(gui.TextView("Concentration and SD"))
        self.expressionBetaBox = classificationImagesSettingsBox.addWidget(gui.TextEdit("25.0"))
        self.expressionBetaSDBox = classificationImagesSettingsBox.addWidget(gui.TextEdit("7.6667"))

        self.expressionAddButton = classificationImagesSettingsBox.addWidget(gui.Button("Add"))
        self.expressionRemoveButton = classificationImagesSettingsBox.addWidget(gui.Button("Remove"))

        @self.modelAddButton.mhEvent
        def onClicked(event):
            features = self.modelFeatureBox.getText()
            alpha = float(self.modelAlphaBox.getText())
            alpha_sd = float(self.modelAlphaSDBox.getText())
            beta = float(self.modelBetaBox.getText())
            beta_sd = float(self.modelBetaSDBox.getText())
            self.modelFeatureList.addItem('{0}: ({1:0.2f}, {2:0.2f})'.format(features, alpha, beta), data=dict(features=features, alpha=alpha, alpha_sd=alpha_sd, beta=beta, beta_sd=beta_sd))

        @self.modelRemoveButton.mhEvent
        def onClicked(event):
            selected_frame = self.modelFeatureList.selectedItems()
            if len(selected_frame) == 0:
                return
            selected_frame = selected_frame[0]
            new_items = [item for item in self.modelFeatureList.getItems() if item is not selected_frame]
            self.reassign(self.modelFeatureList, new_items)

        @self.expressionAddButton.mhEvent
        def onClicked(event):
            features = self.expressionFeatureBox.getText()
            alpha = float(self.expressionAlphaBox.getText())
            alpha_sd = float(self.expressionAlphaSDBox.getText())
            beta = float(self.expressionBetaBox.getText())
            beta_sd = float(self.expressionBetaSDBox.getText())
            self.expressionFeatureList.addItem('{0}: ({1:0.2f}, {2:0.2f})'.format(features, alpha, beta), data=dict(features=features, alpha=alpha, alpha_sd=alpha_sd, beta=beta, beta_sd=beta_sd))

        @self.expressionRemoveButton.mhEvent
        def onClicked(event):
            selected_frame = self.expressionFeatureList.selectedItems()
            if len(selected_frame) == 0:
                return
            selected_frame = selected_frame[0]
            new_items = [item for item in self.expressionFeatureList.getItems() if item is not selected_frame]
            self.reassign(self.expressionFeatureList, new_items)


            
            
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
            # base_model, trials, shape_parameters, pose_parameters, SD=.3, rot_X=0, rot_Y=0, material_file="young_caucasian_avg"
            shape_data,shape_parameters = self.get_data_labels(self.modelFeatureList.getItems())
            #log.message("Shape parameters "+shape_parameters)
            pose_data,pose_parameters = self.get_data_labels(self.expressionFeatureList.getItems())
            frame_rate = float(self.frameRateBox.getText())
            CI_settings = dict(base_model = self.modelBox.getText(),
                                end_model = self.modelBox2.getText(),
                                base_expression = self.expressionBox.getText(),
                                end_expression = self.expressionBox2.getText(),
                                trials = int(self.trialsBox.getText()),
                                frames = int(self.framesBox.getText()),
                                shape_parameters = shape_parameters,
                                pose_parameters=pose_parameters,
                                shape_data=shape_data,
                                pose_data=pose_data,
                                material_file = self.materialBox.getText(),
                                rot_X = float(self.camX.getText()),
                                rot_Y = float(self.camY.getText()),
                                cam_Z = float(self.camZ.getText()))
            classification_images_motion.do_op(classification_image_settings=CI_settings, 
            save_path = self.pathBox.getText(), 
            frame_rate = frame_rate, render_function = (mh2opengl.Render, settings))
            #img = mh2opengl.Render(settings)
            #img.save(path)

            
                
    def num(self, value):
        if not type(value) is str:
            return value
        if value == "":
            return ""
        if "." in value:
            return float(value)
        return int(value)
        

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
    taskview = ClassificationImagesMotionOpenGLTaskView(category)
    taskview.sortOrder = 1.3
    category.addTask(taskview)


def unload(app):
    pass
