#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FaReT — Face Research Toolkit as a single MakeHuman plugin package.

Install by copying or symlinking this directory into MakeHuman's plugins/
(or user plugins). Do not copy anything into MakeHuman's shared/.
"""

from . import average_model
from . import difference_model
from . import face_generator
from . import interpolate_render
from . import socket_psychopy
from . import standardizer
from . import classification_images
from . import classification_images_motion

# Registration order matches former alphabetical top-level plugin load order
# (4_average … 4_standardizer, then 5_/6_ classification plugins).
# saving_obj has no MH load()/UI; it remains an importable helper subpackage.
_FEATURES = (
    average_model,
    difference_model,
    face_generator,
    interpolate_render,
    socket_psychopy,
    standardizer,
    classification_images,
    classification_images_motion,
)


def load(app):
    for feature in _FEATURES:
        feature.load(app)


def unload(app):
    for feature in reversed(_FEATURES):
        feature.unload(app)
