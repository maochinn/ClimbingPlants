bl_info = {
    "name": "Climbing Plants",
    "author": "maochinn",
    "version": (1, 1, 0),
    "blender": (2, 82, 0),
    "location": "",
    "description": "Implement Interative Modeling and Authoring of Climbing Plants",
    "warning": "",
    "wiki_url": "",
    "support": 'TESTING',
    "category": "Object",
}



import bpy

from . Plant_Panel import ClimbingPlantPanel
from . Plant_Operator import (PlantSeeding, PlantGrowth)
from mathutils import Vector, Euler, Quaternion

bpy.types.Scene.plant_max_scale = Vector((0.1, 0.1, 0.3))
bpy.types.Scene.plant_delta_scale = Vector((0.01, 0.01, 0.03))

classes = (ClimbingPlantPanel, PlantSeeding, PlantGrowth)

register, unregister = bpy.utils.register_classes_factory(classes)
