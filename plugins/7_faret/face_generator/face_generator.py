#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

**Authors:**           Jason Hays

"""

# common needs (without rendering)
from glob import glob
import os
import numpy as np

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


eyebrow_re_A = re.compile("eyebrows eyebrow[0-9]+ ([\-0-9a-z]+)", flags=re.MULTILINE|re.DOTALL)
# material eyebrow001 9c81ec3a-faa5-4c94-9cdb-992300ba3084 eyebrow001.mhmat
eyebrow_re_B = re.compile("material eyebrow[0-9]+ ([\-0-9a-z]+) eyebrow[0-9]+\.mhmat", flags=re.MULTILINE|re.DOTALL)

def make_brow_B(brow_A):
    _, number, code  = tuple(brow_A.split(" "))
    return "material {0} {1} {0}.mhmat".format(number, code)

eyebrows = ["eyebrows eyebrow012 1c16325c-7831-4166-831a-05c5b609c219", 
           "eyebrows eyebrow011 19e43555-4613-4457-ac6e-c30bf350d275",
           "eyebrows eyebrow010 8261cde8-7ce2-47f3-a7a2-edf459c50887",
           "eyebrows eyebrow009 55b3b52a-379e-426d-b320-562ed57202b3",
           "eyebrows eyebrow008 79ea307f-a942-40dd-bf50-bbaa41f02034",
           "eyebrows eyebrow007 f2092456-86eb-423f-a5c6-2e0b3117d664",
           "eyebrows eyebrow006 bb953a1a-db43-44db-a0ad-ed8a5d6000c9",
            "eyebrows eyebrow005 9da0aea6-fdf3-4862-baa4-0d122074179a",
            "eyebrows eyebrow004 eb028b6d-3ff8-40c7-a2ea-4d9aa808b38d",
            "eyebrows eyebrow003 4089e4e3-b842-40f4-91a4-0686118f7535",
            "eyebrows eyebrow002 a4e73c2f-3a12-47c8-b706-31a68cac6907",
            "eyebrows eyebrow001 9c81ec3a-faa5-4c94-9cdb-992300ba3084"]
eye_color_re = re.compile("material ([A-z]+) ([\-0-9a-z]+) eyes/materials/([a-z_\-\s]+)\.mhmat", flags=re.MULTILINE|re.DOTALL)
eyecolors = ["material HighPolyEyes 2c12f43b-1303-432c-b7ce-d78346baf2e6 eyes/materials/brown.mhmat",
            "material HighPolyEyes 2c12f43b-1303-432c-b7ce-d78346baf2e6 eyes/materials/blue.mhmat",
            "material HighPolyEyes 2c12f43b-1303-432c-b7ce-d78346baf2e6 eyes/materials/brownlight.mhmat",
            "material HighPolyEyes 2c12f43b-1303-432c-b7ce-d78346baf2e6 eyes/materials/deepblue.mhmat",
            "material HighPolyEyes 2c12f43b-1303-432c-b7ce-d78346baf2e6 eyes/materials/green.mhmat",
            "material HighPolyEyes 2c12f43b-1303-432c-b7ce-d78346baf2e6 eyes/materials/lightblue.mhmat"]


#eyebrows eyebrow012 1c16325c-7831-4166-831a-05c5b609c219
gender_re = re.compile("modifier macrodetails/Gender ([\-0-9.]+)", flags=re.MULTILINE|re.DOTALL)
# skin regex
afr_re = re.compile("modifier macrodetails/African ([\-0-9.]+)", flags=re.MULTILINE|re.DOTALL)
asi_re = re.compile("modifier macrodetails/Asian ([\-0-9.]+)", flags=re.MULTILINE|re.DOTALL)
cau_re = re.compile("modifier macrodetails/Caucasian ([\-0-9.]+)", flags=re.MULTILINE|re.DOTALL)

skin_re = re.compile("skinMaterial (.*?)\.mhmat", flags=re.MULTILINE|re.DOTALL)
'''skins = {1: "skinMaterial skins/young_caucasian_male/young_caucasian_male2.mhmat",
         0: "skinMaterial skins/young_caucasian_female/young_caucasian_female2.mhmat",
        -1: "skinMaterial skins/young_caucasian_avg/young_caucasian_avg.mhmat"}'''

cau = {1: "skinMaterial skins/young_caucasian_male/young_caucasian_male2.mhmat",
       0: "skinMaterial skins/young_caucasian_female/young_caucasian_female2.mhmat",
      -1: "skinMaterial skins/young_caucasian_avg/young_caucasian_avg.mhmat"}

afr = {1: "skinMaterial skins/young_african_male/young_african_male.mhmat",
       0: "skinMaterial skins/young_african_female/young_african_female.mhmat",
      -1: "skinMaterial skins/young_african_avg/young_african_avg.mhmat"}

asi = {1: "skinMaterial skins/young_asian_male/young_asian_male.mhmat",
       0: "skinMaterial skins/young_asian_female/young_asian_female.mhmat",
      -1: "skinMaterial skins/young_asian_avg/young_asian_avg.mhmat"}

skins = dict(cau=cau, afr=afr, asi=asi)

def write_mimic_file(mimic_file, out_file, keys, face_data, assign_skin=True, average_skin=False, 
                     randomize_gender=True, randomize_race=True, randomize_brow=True, randomize_eye_color=True):
    d = dict(zip(keys, list(face_data)))
    s = ""
    
    with open(mimic_file, 'r') as f:
        for line in f:
            m = re.search(modifier_pattern, line)
            if m and m.group(1) in d:
                key = m.group(1)
                if "/l-" in key:
                    d[key] = d[key.replace("/l-", "/r-")]
                    
                if key == "forehead/forehead-nubian-decr|incr":
                    d[key] = max(-.5, min(-.1, d[key]))
                elif key == "forehead/forehead-scale-vert-decr|incr":
                    d[key] = max(0, min(.5, d[key]))
                elif key == "head/head-trans-down|up":
                    d[key] = max(-1, min(0, d[key]))
                elif key == "head/head-scale-vert-decr|incr":
                    d[key] = max(-0.2, min(0.2, d[key]))
                elif key == "chin/chin-height-decr|incr":
                    d[key] = max(-1, min(0.0, d[key]))
                # left-right assymmetry, despite name of in-out, it is left-right
                elif key in ("mouth/mouth-trans-in|out", "nose/nose-trans-in|out", "head/head-trans-in|out"):
                    d[key] = 0
                elif "|" in key:
                    d[key] = max(-1, min(1, d[key]))
                else:
                    d[key] = max(0, min(1, d[key]))
                s += "modifier {} {}\n".format(key, d[key])
                #if "Gender" in m.group():
                #    print(s)
            else:
                s += line
    
    if randomize_gender:
        s = re.sub(gender_re, "modifier macrodetails/Gender "+str(np.random.random()), s)
    #modifier macrodetails/African 0.048485
    #modifier macrodetails/Asian 0.056250
    #modifier macrodetails/Caucasian 0.895265
    
    if randomize_race:
        afr_race = np.random.random()
        asi_race = np.random.random()
        cau_race = np.random.random()
        
        s = re.sub(afr_re, "modifier macrodetails/African "+str(afr_race), s)
        s = re.sub(asi_re, "modifier macrodetails/Asian "+str(asi_race), s)
        s = re.sub(cau_re, "modifier macrodetails/Caucasian "+str(cau_race), s)
    else:
        afr_race = float(re.search(afr_re, s).group(1))
        asi_race = float(re.search(asi_re, s).group(1))
        cau_race = float(re.search(cau_re, s).group(1))
        

    
    if assign_skin:
        race_key = None
        max_race = max(afr_race, asi_race, cau_race)
        if afr_race == max_race:
            race_key = "afr"
        elif asi_race == max_race:
            race_key = "asi"
        else:
            race_key = "cau"
        
        gender = np.round(float(re.search(gender_re, s).group(1)))
        if average_skin:
            skin = skins[race_key][-1]
        else:
            skin = skins[race_key][gender]
        
        s = re.sub(skin_re, skin, s)
        
    if randomize_brow:
        my_eyebrow = np.random.choice(eyebrows)
        s = re.sub(eyebrow_re_A, my_eyebrow, s)
        s = re.sub(eyebrow_re_B, make_brow_B(my_eyebrow), s)
        
    if randomize_eye_color:
        my_color = np.random.choice(eyecolors)
        s = re.sub(eye_color_re, my_color, s)
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

def make_new_face(avg_face, face_arr):
    S = .75
    norm = np.random.random(size=(face_arr.shape[0]))*2-1
    norm /= np.sum(np.abs(norm))
    faceX = np.matmul(face_arr.T+np.random.normal(0,S, size=face_arr.T.shape), norm).T + avg_face
    return faceX

def load_faces(*paths):
    full_params = []
    for path in paths:
        full_params += [read_params(f) for f in glob(os.path.join(path, "*.mhm"))]
    return full_params