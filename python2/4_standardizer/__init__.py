import json
from core import G
import gui
import gui3d
import mh
import PyQt4
import numpy as np
import os
import getpath
from standardize import *

class StandardizeTaskView(gui3d.TaskView):

    def __init__(self, category):
        gui3d.TaskView.__init__(self, category, 'Standardize Models')


        buttonsBox = self.addLeftWidget(gui.GroupBox('Settings'))
        buttonsBox.addWidget(gui.TextView("Options"))
        self.geoBox = buttonsBox.addWidget(gui.CheckBox("Geometries"))
        self.shapeBox = buttonsBox.addWidget(gui.CheckBox("Shapes"))
        # self.AAbox.selected
        
        self.path_out = ""
        self.path_button_out = buttonsBox.addWidget(gui.BrowseButton('dir', "Select an output directory"))
        self.out_path_box = buttonsBox.addWidget(gui.TextEdit(self.path_out))
        
        self.path_in = ""
        self.path_button_in = buttonsBox.addWidget(gui.BrowseButton('dir', "Select an input directory"))
        self.in_path_box = buttonsBox.addWidget(gui.TextEdit(self.path_in))
        
        self.path_exemplar = ""
        self.path_button_exemplar = buttonsBox.addWidget(gui.BrowseButton('open', "Select the standard model"))
        self.exemplar_path_box = buttonsBox.addWidget(gui.TextEdit(self.path_exemplar))
        
        @self.path_button_out.mhEvent
        def onClicked(path):
            self.path_out = path
            self.out_path_box.setText(self.path_out)
        
        @self.path_button_in.mhEvent
        def onClicked(path):
            self.path_in = path
            self.in_path_box.setText(self.path_in)
            
        @self.path_button_exemplar.mhEvent
        def onClicked(path):
            self.path_exemplar = path
            self.exemplar_path_box.setText(self.path_exemplar)
        buttonsBox.addWidget(gui.TextView("Features to standardize (comma+space separated regular expressions)"))
        self.standardShapeFeatures = buttonsBox.addWidget(gui.TextEdit("^head, neck, ear, proportions"))
        
        self.goButton = buttonsBox.addWidget(gui.Button('Go'))
        
        @self.goButton.mhEvent
        def onClicked(event):
            settings = {}
            settings['geometries'] = self.geoBox.selected
            settings['shapes'] = self.shapeBox.selected
            settings['standard_shapes'] = self.standardShapeFeatures.getText().split(", ")
            standard = Standardizer(settings['standard_shapes'])
            specific_model = self.exemplar_path_box.getText()
            if specific_model == "":
                specific_model = None
            standard.load_models(self.in_path_box.getText(), specific_model)
            if settings['geometries'] and settings['standard_shapes']:
                standard.standardize_all(self.out_path_box.getText())
            elif settings['geometries']:
                standard.standardize_geometries(self.out_path_box.getText())  
            elif settings['standard_shapes']:
                standard.standardize_shape(self.out_path_box.getText())  

            

    def onShow(self, event):
        gui3d.TaskView.onShow(self, event)

    def onHide(self, event):
        gui3d.TaskView.onHide(self, event)


def load(app):
    category = app.getCategory('Utilities')
    taskview = StandardizeTaskView(category)
    taskview.sortOrder = 1.3
    category.addTask(taskview)


def unload(app):
    pass