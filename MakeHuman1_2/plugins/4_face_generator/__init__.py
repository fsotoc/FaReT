import json
from core import G
import gui
import gui3d
import mh
import numpy as np
import os
import getpath
from . import face_generator
from glob import glob

class FaceGeneratorTaskView(gui3d.TaskView):

    def __init__(self, category):
        gui3d.TaskView.__init__(self, category, 'Generate Faces')


        buttonsBox = self.addLeftWidget(gui.GroupBox('Settings'))
        buttonsBox.addWidget(gui.TextView("Options"))
        buttonsBox.addWidget(gui.TextView("Faces to make"))
        self.faceCount = buttonsBox.addWidget(gui.TextEdit("1"))

        self.assign_skin_box = buttonsBox.addWidget(gui.CheckBox("Assign Skin"))
        self.avg_skin_box = buttonsBox.addWidget(gui.CheckBox("Assign Average Skin"))
        self.rando_gender_box = buttonsBox.addWidget(gui.CheckBox("Randomize Gender"))
        self.rando_race_box = buttonsBox.addWidget(gui.CheckBox("Randomize Race"))
        self.rando_brow_box = buttonsBox.addWidget(gui.CheckBox("Randomize Brows")) 
        self.rando_eye_box = buttonsBox.addWidget(gui.CheckBox("Randomize Eyes"))

        buttonsBox.addWidget(gui.TextView("Number of Sample Faces to use per face"))
        self.samplesUsed = buttonsBox.addWidget(gui.TextEdit("10"))

        self.path_out = ""
        self.path_button_out = buttonsBox.addWidget(gui.BrowseButton('dir', "Select an output directory"))
        self.out_path_box = buttonsBox.addWidget(gui.TextEdit(self.path_out))
        
        self.path_in = ""
        self.path_button_in = buttonsBox.addWidget(gui.BrowseButton('dir', "Select the directory of sample faces"))
        self.in_path_box = buttonsBox.addWidget(gui.TextEdit(self.path_in))
        
        self.path_exemplar = ""
        self.path_button_exemplar = buttonsBox.addWidget(gui.BrowseButton('open', "Select the average model"))
        self.exemplar_path_box = buttonsBox.addWidget(gui.TextEdit(self.path_exemplar))
        
        @self.path_button_out.mhEvent
        def onClicked(path):
            self.out_path_box.setText(path)
        
        @self.path_button_in.mhEvent
        def onClicked(path):
            self.in_path_box.setText(path)
            
        @self.path_button_exemplar.mhEvent
        def onClicked(path):
            self.exemplar_path_box.setText(path)
        
        self.goButton = buttonsBox.addWidget(gui.Button('Go'))
        
        @self.goButton.mhEvent
        def onClicked(event):
            self.path_out = self.out_path_box.getText()
            
            # where the sample faces are (comma separated)
            self.path_in = self.in_path_box.getText()
            # load the sample faces
            sample_faces = face_generator.load_faces(*self.path_in.split(","))

            # how many faces should be made?
            faceCount = int(self.faceCount.getText())
            faces_used = int(self.samplesUsed.getText())
            avg = None
            all_stuff = None
            keys = None
            rest = None
            # average model
            self.path_exemplar = self.exemplar_path_box.getText()
            if self.path_button_exemplar == "" or self.path_button_exemplar == "None":
                # generate average from "in path"
                all_stuff = np.array(face_generator.get_ordered_values(*sample_faces))
                keys = all_stuff[0]
                rest = np.array(all_stuff[1:])
                avg = np.average(rest, axis=0)

                # get the first one for writing mimic files
                self.path_exemplar = glob(os.path.join(self.path_in.split(",")[0], "*.mhm"))[0]
            else:
                # load the average
                avg_face = face_generator.read_params(self.path_exemplar)
                all_stuff = face_generator.get_ordered_values(avg_face, *sample_faces)
                keys = all_stuff[0]
                avg = all_stuff[1]
                rest = np.array(all_stuff[2:])
            
            
            
            radius, rest = face_generator.set_faces_to_radius(avg, rest)

            for i in range(faceCount):
                # make face
                faceX = face_generator.make_new_face(avg, rest)
                face_generator.write_mimic_file(self.path_exemplar, os.path.join(self.path_out,"face{0:03d}.mhm".format(i)), keys, faceX, self.assign_skin_box.selected, self.avg_skin_box.selected, self.rando_gender_box.selected, self.rando_race_box.selected, self.rando_brow_box.selected,  self.rando_eye_box.selected)


    def onShow(self, event):
        gui3d.TaskView.onShow(self, event)

    def onHide(self, event):
        gui3d.TaskView.onHide(self, event)


def load(app):
    category = app.getCategory('Utilities')
    taskview = FaceGeneratorTaskView(category)
    taskview.sortOrder = 1.3
    category.addTask(taskview)


def unload(app):
    pass