import bpy
from mathutils import Vector, Matrix, Quaternion, geometry
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    PointerProperty,
    IntProperty,
    StringProperty,
)

SurfaceAdaptionStrength = FloatProperty(
    name="SA",
    description="Surface Adaption Strength",
    default =0.0,
    soft_min=0.0,soft_max=1.0,
    # options={'HIDDEN'},
)
PhototropismResponseStrength = FloatProperty(
    name="PR",
    description="Phototropism Response Strength",
    soft_min=0.0,soft_max=1.0,
    # options={'HIDDEN'},
)
ParticleSize = FloatVectorProperty(
    name="Size", 
    description="Plant particle size",
    default=(0, 0, 0)
)
ParticleAnchor = FloatVectorProperty(
    name="Anchor", 
    description="Anchor point of particle",
    default=(0, 0, 0)
)

# plant_depth = IntProperty(
#     name="Plant depth",
#     description="plant particle depth",
#     soft_min=0, soft_max=999
# )
ParticleType = EnumProperty(
    name="Type",
    description="only for climbing plant object type",
    items=(
        ('SEED', "seed", "plant seed"),
        ('BRANCH', "branch", "branch particle"),
        ('OBSTACLE', "obstacle", "obstacle object"),
        ('LIGHT', "light", "light object")),
    default='SEED',
    options={'HIDDEN'},
)
# Plant_object = PointerProperty(
#     type=bpy.types.ID,
#     name="Plant object",
#     description="climbing plant object",
# )


#####
# object bpy.types.Object
#####
def createParticleProperty(
    context, particle, sa_strength, pr_strength, plant_type, anchor, parent=None):
    context.view_layer.objects.active = particle
     # refer: bpy.ops.wm.properties_add(data_path="object")
    from rna_prop_ui import rna_idprop_ui_create

    data_path = "object"
    item = eval("context.%s" % data_path)

    rna_idprop_ui_create(
        item, "SA",
        default     =sa_strength,
        description =SurfaceAdaptionStrength[1]['description'],
        soft_min    =SurfaceAdaptionStrength[1]['soft_min'],
        soft_max    =SurfaceAdaptionStrength[1]['soft_max'], )
    rna_idprop_ui_create(
        item, "PR",
        default     =pr_strength,
        description =PhototropismResponseStrength[1]['description'],
        soft_min    =PhototropismResponseStrength[1]['soft_min'],
        soft_max    =PhototropismResponseStrength[1]['soft_max'], )
    # rna_idprop_ui_create(
    #     item, "Size",
    #     default     =particle.dimensions,
    #     description =ParticleSize[1]['description'])
    # rna_idprop_ui_create(
    #     item, "Depth",
    #     default     =depth,
    #     description =plant_depth[1]['description'],
    #     soft_min    =plant_depth[1]['soft_min'],
    #     soft_max    =plant_depth[1]['soft_max'], )
    rna_idprop_ui_create(
        item, "Type",
        default     =plant_type)
    rna_idprop_ui_create(
        item, "Anchor",
        default     =anchor,
        description =ParticleAnchor[1]['description'])
    rna_idprop_ui_create(
        item, "Childs",
        default     =[])
    rna_idprop_ui_create(
        item, "Parent",
        default     =[])

    if(parent):
        particle['Parent'] = parent
        if(parent['Childs']):
            parent['Childs'] += [particle]
        else:
            parent['Childs'] = [particle]
            