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

import re
modifier_pattern = re.compile("modifier\s([^\s]+)\s([^\s]+)")
def read_params(filename):
    modifiers = {}
    with open(filename, 'r') as f:
        for line in f:
            m = re.search(modifier_pattern, line)
            if m:
                modifiers[m.group(1)] = float(m.group(2))
    return modifiers


face_modifier_regex = re.compile("nose|head|eye|mouth|chin|cheek|ear|Gender")

def get_ordered_values(*faces):
    # nose,^head,forehead,eyebrow,eyes,mouth,ear,chin,cheek, neck?
    face_list = []
    key_list = []
    
    for face in faces:
        for key in face:
            if re.search(face_modifier_regex,key):
                key_list.append(key)
            
    key_list = np.unique(key_list)
    face_list.append(key_list)
    for face in faces:
        f = []
        for key in key_list:
            if key in face:
                f.append(face[key])
            else:
                f.append(0)
        face_list.append(f)
    
    return face_list

gender_re = re.compile("modifier macrodetails/Gender ([\-0-9.]+)", flags=re.MULTILINE|re.DOTALL)
skin_re = re.compile("skinMaterial (.*?)\.mhmat", flags=re.MULTILINE|re.DOTALL)
skins = {1: "skinMaterial skins/young_caucasian_male/young_caucasian_male2.mhmat",
0: "skinMaterial skins/young_caucasian_female/young_caucasian_female2.mhmat",
-1: "skinMaterial skins/young_caucasian_avg/young_caucasian_avg.mhmat"}

def write_mimic_file(mimic_file, out_file, keys, face_data, assign_skin=True, average_skin=False, randomize_gender=True):
    d = dict(zip(keys, list(face_data)))
    s = ""
    
    with open(mimic_file, 'r') as f:
        for line in f:
            m = re.search(modifier_pattern, line)
            if m and m.group(1) in d:
                
                s += "modifier {} {}\n".format(m.group(1), d[m.group(1)])
                #if "Gender" in m.group():
                #    print(s)
            else:
                s += line
    
    if randomize_gender:
        s = re.sub(gender_re, "modifier macrodetails/Gender "+str(np.random.random()), s)
    if assign_skin:
        gender = np.round(float(re.search(gender_re, s).group(1)))
        if average_skin:
            skin = skins[-1]
        else:
            skin = skins[gender]
        
        s = re.sub(skin_re, skin, s)
    with open(out_file, 'w') as f:
        f.write(s)

def set_faces_to_radius(avg, faces):
    # function taken from our PEMGUIN package
    d1 = None
    for faceA in faces:
        d = dist(avg, faceA)
        if d1 is None or d1 > d:
            d1 = d
    for i,faceA in enumerate(faces):
        faces[i] = avg+(faceA-avg)/dist(avg, faceA) * d1
    
    return d1, faces


def dist(A,B):
    # function taken from our PEMGUIN package
    return np.sqrt(np.sum((A-B)**2))

def angle(A,B):
    # function taken from our PEMGUIN package
    # get the angle from the arccos of cosine similarity
    Al = np.linalg.norm(A)
    Bl = np.linalg.norm(B)
    
    sim = np.dot(A,B)/(Al*Bl)
    # account for numerical precision problems,
    # maintain [-1, 1] bounds:
    if abs(sim) > 1:
        sim = np.sign(sim)
    return np.arccos(sim)/np.pi*180

def get_face_from_angle(avg, radius, faceA, faceB, desired_angle):
    # function taken from our PEMGUIN package

    # desired_angle: uses angles (0,180) noninclusive
    # faceA and faceB NEED to already be on the circle.
    #if dist(faceA, avg) != dist(avg, faceB):
    #    raise Exception("The faces must be equidistant from the average.")
    direction = faceB-faceA
    if desired_angle < 0:
        # switching face A and B (while keeping the starting point) 
        #  and flipping the sign of desired_angle to +
        #  gives the same effect as a negative angle.
        desired_angle *= -1
        direction *= -1
    
    if desired_angle == 180:
        return avg + (avg-faceA)

    if desired_angle > 180:
        direction *= -1
        desired_angle = abs(desired_angle-360)
    faceC = faceA + direction

    # make the face on the edge
    faceC = avg + (faceC-avg)/dist(faceC,avg) * radius

    # brute force the rotation by using vectors that are definitely on the circle
    # and by using properties of the circle:
    # C must be on the radius, and it must be vaguely in the direction specified by A and B.
    # (A and B must not be on exactly opposite sides of average)
    ang = angle(faceA-avg,faceC-avg)
    prev = [ang]
    while ang != desired_angle:#abs(ang-desired_angle)>0.0000000000001:
        # move it towards or away from faceA based on the ratio 
        #  of the desired angle and the last angle
        faceC = faceA + (faceC-faceA)*(desired_angle/ang)
        # set it at the radius
        faceC = avg + (faceC-avg)/dist(faceC,avg) * radius
        # measure the new angle
        ang = angle(faceA-avg,faceC-avg)
        #print(ang)
        if ang in prev:
            #print("Stopped Due to limited floating point precision.")
            break
        prev.append(ang)
    return faceC


def make_new_face(avg, radius, face_arr, iterations=10):
    faces_idx = np.random.choice(np.arange(len(face_arr)), size=iterations+1, replace=False)
    faces = np.array(face_arr)[faces_idx]
    faceB = faces[0]
    faces = faces[1:]
    
    for i in range(iterations):
        faceA = faces[i]
        # stray away from the exact face/antiface of faceA
        x = np.random.normal(90,30) * np.random.choice([-1,1])
        faceB = get_face_from_angle(avg, radius, faceA, faceB, x)
    return faceB

def load_faces(*paths):
    full_params = []
    for path in paths:
        full_params += [read_params(f) for f in glob(os.path.join(path, "*.mhm"))]
    return full_params