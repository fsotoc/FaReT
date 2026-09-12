# common needs
import os
import json
import numpy as np
from . import mh2opengl
import bvh, getpath, gui3d, mh, mhmain, animation
import wavefront
from export import ExportConfig

from core import G
from collections import OrderedDict
# straight from MakeHuman's scripting plugin
# changed iteritems for python 3
def updateModelingParameters(dictOfParameterNameAndValue):
    human = gui3d.app.selectedHuman
    for key, value in iter(dictOfParameterNameAndValue.items()):
        modifier = human.getModifier(key)
        modifier.setValue(value)
    human.applyAllTargets()
    mh.redraw()

def merge_dictionaries(d1, d2):
    for key in d1:
        if not key in d2:
            d2[key] = d1[key]
    return d2

def load_pose_modifiers(filename):
    modifiers, _ = get_blank_pose()
    if filename is None or filename == "None":
        
        return modifiers
    with open(filename, 'r') as f:
        # need to keep all keys available from neutral expression for interpolation
        return merge_dictionaries(modifiers, json.load(f, object_pairs_hook=OrderedDict)['unit_poses'])
    return None

def get_blank_pose(skip_blank_pose=False):
    human = gui3d.app.selectedHuman
    base_bvh = bvh.load(getpath.getSysDataPath('poseunits/face-poseunits.bvh'), allowTranslation="none")
    base_anim = base_bvh.createAnimationTrack(human.getBaseSkeleton(), name="Expression-Face-PoseUnits")

    poseunit_json = json.load(open(getpath.getSysDataPath('poseunits/face-poseunits.json'),'rb'), object_pairs_hook=OrderedDict)
    # the names of the changeable facial expression features
    poseunit_names = poseunit_json['framemapping']
    modifiers = dict(zip(poseunit_names, len(poseunit_names)*[0.0]))
    base_poseunit = animation.PoseUnit(base_anim.name, base_anim.data[:base_anim.nBones*len(poseunit_names)], poseunit_names)
    if skip_blank_pose:
        return modifiers, None
    return modifiers, base_poseunit

def set_pose(pose_modifiers):
    human = gui3d.app.selectedHuman
    modifiers, base_poseunit = get_blank_pose()

    for key in pose_modifiers:
        modifiers[key] = pose_modifiers[key]
    # see which values are different so only those are updated
    posenames = []
    posevalues = []
    for pname, pval in modifiers.items():
        posenames.append(pname)
        posevalues.append(pval)
    if len(posenames) > 0:
        panim = base_poseunit.getBlendedPose(posenames, posevalues)
        panim.disableBaking = False

        human.addAnimation(panim)
        human.setActiveAnimation(panim.name)
        human.refreshPose()
        

def get_shape_params():
    human = gui3d.app.selectedHuman
    
    param_dict = {}
    for key in human.modifierNames:
        param_dict[key] = human.getModifier(key).getValue()
    return param_dict

def get_params(change_key):
    if change_key == 'expression':
        return load_pose_modifiers("None")
    elif change_key == 'model':
        return get_shape_params()
    elif change_key == "rot_X":
        gui3d.app.modelCamera.getRotation()[0]
    elif change_key == "rot_Y":
        gui3d.app.modelCamera.getRotation()[1]
    else:
        return 0.0

def save_model(path, name):
    human = gui3d.app.selectedHuman
    filename = os.path.join(path,name + ".mhm")
    human.save(filename,name)
    
def render(out_path, settings, image_count=0):
    if not 'scene' in settings:
        settings['scene'] = G.app.scene
    img = mh2opengl.Render(settings)
    img_path = os.path.join(out_path, "render_{0}.png".format(image_count))
    img.save(img_path)
    return img_path


class ObjExportConfig(ExportConfig):
    def __init__(self):
        ExportConfig.__init__(self)
        self.useRelPaths = True
        self.useNormals = False
        self.hiddenGeom = False


_OBJ_EXPORT_SCALES = {
    "decimeter": 1.0,
    "meter": 0.1,
    "inch": 1.0 / 0.254,
    "centimeter": 10.0,
}

_OBJ_EXPORT_SCALE_ALIASES = {
    "dm": "decimeter",
    "decimeters": "decimeter",
    "m": "meter",
    "meters": "meter",
    "metre": "meter",
    "metres": "meter",
    "in": "inch",
    "inches": "inch",
    "cm": "centimeter",
    "centimeters": "centimeter",
    "centimetres": "centimeter",
}


def _normalize_obj_scale_unit(scale_unit):
    if scale_unit is None:
        return "decimeter"

    unit_name = str(scale_unit).strip().lower()
    unit_name = _OBJ_EXPORT_SCALE_ALIASES.get(unit_name, unit_name)
    if unit_name not in _OBJ_EXPORT_SCALES:
        valid_units = ", ".join(sorted(_OBJ_EXPORT_SCALES.keys()))
        raise ValueError("Unsupported OBJ scale unit '{0}'. Expected one of: {1}".format(scale_unit, valid_units))
    return unit_name


def export_obj(filepath, scale_unit="decimeter", use_normals=False, hidden_geom=False, feet_on_ground=True):
    human = gui3d.app.selectedHuman
    unit_name = _normalize_obj_scale_unit(scale_unit)

    filepath = os.path.abspath(filepath)
    root, ext = os.path.splitext(filepath)
    if ext.lower() != ".obj":
        filepath = root + ".obj"

    out_dir = os.path.dirname(filepath)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir)

    cfg = ObjExportConfig()
    cfg.setHuman(human)
    cfg.scale = _OBJ_EXPORT_SCALES[unit_name]
    cfg.unit = unit_name
    cfg.useNormals = bool(use_normals)
    cfg.hiddenGeom = bool(hidden_geom)
    cfg.feetOnGround = bool(feet_on_ground)

    cfg.setupTexFolder(filepath)
    objects = human.getObjects(excludeZeroFaceObjs=not cfg.hiddenGeom)
    meshes = [obj.mesh for obj in objects]

    if cfg.hiddenGeom:
        meshes = [mesh.clone(filterMaskedVerts=False) for mesh in meshes]
        for mesh in meshes:
            face_mask = np.ones(mesh.face_mask.shape, dtype=bool)
            mesh.changeFaceMask(face_mask)
            mesh.calcNormals()
            mesh.updateIndexBuffer()

    wavefront.writeObjFile(filepath, meshes, True, cfg, filterMaskedFaces=not cfg.hiddenGeom)
    return filepath

isNumberType = None
Number = None
try:
    from numbers import Number
except:
    import operator
    isNumberType = operator.isNumberType

def add(a, change):
    # just numbers
    if (isNumberType is not None and isNumberType(a)) or (Number is not None and isinstance(a, Number)):
        return a + change
    
    summed = {}
    for key in a:
        summed[key] = a[key] + change[key]
    return summed

def difference(b, a, bPercent):
    # get the difference between the values
    # if the values are dictionaries, make sure to assign values of 0 when the keys do not exist
    if (isNumberType is not None and isNumberType(a)) or (Number is not None and isinstance(a, Number)):
        return b-a

    diff = {}
    for key in b:
        if not key in a:
            a[key] = 0
    for key in a:
        if not key in b:
            b[key] = 0
        
        diff[key] = (b[key] - a[key])*(bPercent/100.)
    return diff
