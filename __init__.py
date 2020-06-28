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
from . Plant_Operator import (PlantSeeding, PlantDynamics, PlantGrowth)
from mathutils import Vector, Euler, Quaternion

# size is dimension
bpy.types.Scene.plant_max_size = Vector((0.2, 0.2, 0.6))
bpy.types.Scene.plant_delta_size = Vector((0.01, 0.01, 0.05))
bpy.types.Scene.plant_branch_probablity = 0.0002


# particle center position
bpy.types.Object.position = bpy.props.FloatVectorProperty(subtype='TRANSLATION')
# particle rest center position
bpy.types.Object.rest_position = bpy.props.FloatVectorProperty(subtype='TRANSLATION')
# particle orientation
bpy.types.Object.orientation = bpy.props.FloatVectorProperty(subtype='QUATERNION', size=4)
# particle rest orientation
bpy.types.Object.rest_orientation = bpy.props.FloatVectorProperty(subtype='QUATERNION', size=4)
# particle velocity
bpy.types.Object.velocity = bpy.props.FloatVectorProperty(subtype='VELOCITY')
# particle anguler velocity
bpy.types.Object.angular_velocity = bpy.props.FloatVectorProperty(subtype='DIRECTION')


classes = (ClimbingPlantPanel, PlantSeeding, PlantDynamics, PlantGrowth)

register, unregister = bpy.utils.register_classes_factory(classes)

