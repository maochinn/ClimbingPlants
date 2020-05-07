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

# size is dimension
bpy.types.Scene.plant_max_size = Vector((0.2, 0.2, 0.6))
bpy.types.Scene.plant_delta_size = Vector((0.01, 0.01, 0.05))
bpy.types.Scene.plant_branch_probablity = 0.0002

#
bpy.types.Object.velocity = bpy.props.FloatVectorProperty()

classes = (ClimbingPlantPanel, PlantSeeding, PlantGrowth)

register, unregister = bpy.utils.register_classes_factory(classes)

