import random
import bpy

from bpy.types import Operator
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

surface_adaption_strength = FloatProperty(
    name="Surface Adaption",
    description="Surface Adaption Strength",
    default =0.0,
    soft_min=0.0,soft_max=1.0,
    # options={'HIDDEN'},
)
phototropism_response_strength = FloatProperty(
    name="Phototropism Response",
    description="Phototropism Response Strength",
    soft_min=0.0,soft_max=1.0,
    # options={'HIDDEN'},
)
plant_depth = IntProperty(
    name="Plant depth",
    description="plant particle depth",
    soft_min=0, soft_max=999
)
plant_type = EnumProperty(
    name="Plant Type",
    description="only for climbing plant object type",
    items=(
        ('SEED', "seed", "plant seed"),
        ('PLANT', "plant", "plant particle")),
    default='SEED',
    options={'HIDDEN'},
)
Plant_object = PointerProperty(
    type=bpy.types.ID,
    name="Plant object",
    description="climbing plant object",

)

#####
# object bpy.types.Object
#####
def createParticleProperty(
    context, particle, sa_strength, pr_strength, depth, plant_type, childs=[], parent=[]):
    context.view_layer.objects.active = particle
    if parent == None:
        parent = particle
     # refer: bpy.ops.wm.properties_add(data_path="object")
    from rna_prop_ui import rna_idprop_ui_create

    data_path = "object"
    item = eval("context.%s" % data_path)

    rna_idprop_ui_create(
        item, "Surface_Adaption",
        default     =sa_strength,
        description =surface_adaption_strength[1]['description'],
        soft_min    =surface_adaption_strength[1]['soft_min'],
        soft_max    =surface_adaption_strength[1]['soft_max'], )
    rna_idprop_ui_create(
        item, "Phototropism_Response",
        default     =pr_strength,
        description =phototropism_response_strength[1]['description'],
        soft_min    =phototropism_response_strength[1]['soft_min'],
        soft_max    =phototropism_response_strength[1]['soft_max'], )
    rna_idprop_ui_create(
        item, "Plant_Depth",
        default     =depth,
        description =plant_depth[1]['description'],
        soft_min    =plant_depth[1]['soft_min'],
        soft_max    =plant_depth[1]['soft_max'], )
    rna_idprop_ui_create(
        item, "Plant_Type",
        default     =plant_type)
    rna_idprop_ui_create(
        item, "childs",
        default     =[])
    rna_idprop_ui_create(
        item, "parent",
        default     =[parent])



class PlantSeeding(Operator):
    bl_idname = "plant.seeding"
    bl_label = "dynamic plant seeding"
    bl_description = "seed plant root"
    bl_options = {'REGISTER', 'UNDO'}

    
    sa_strength :surface_adaption_strength
    pr_strength :phototropism_response_strength
    depth       :plant_depth
    plant_type  :plant_type
    location    :FloatVectorProperty(name="Location", default=(0, 0, 0))

    @classmethod
    def poll(cls, context):
        return True
            
    def invoke(self, context, event):
        wm = context.window_manager

        return wm.invoke_props_dialog(self)

    def execute(self, context):
        bpy.ops.mesh.primitive_uv_sphere_add(location=self.location)
        seed = context.active_object
        # seed.scale = bpy.types.Scene.plant_delta_scale
        default = bpy.types.Scene.plant_delta_scale
        bpy.ops.transform.resize(value=default)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.transform.translate(value=(0,0,default.z))
        bpy.ops.object.mode_set(mode='OBJECT')
        seed.name = "Seed"

        createParticleProperty(
            context, 
            seed, 
            self.sa_strength, 
            self.pr_strength,
            self.depth,
            self.plant_type)
        return {'FINISHED'}

def grow(particle):
    a, b, c = particle.scale

    max_a, max_b, max_c = bpy.types.Scene.plant_max_scale
    delta_a, delta_b, delta_c = bpy.types.Scene.plant_delta_scale
    
    a += delta_a
    b += delta_b
    c += delta_c

    if (a > max_a):
        a = max_a
    if (b > max_b):
        b = max_b
    if (c > max_c):
        c = max_c

    particle.scale = (a, b, c)

    bpy.ops.anim.keyframe_insert_menu(type='Scaling')

    if (particle['childs'] == [] and c >= max_c):
        rand = random.random()
        rand = 1 - rand
        if (rand > bpy.types):



class PlantGrowth(Operator):
    bl_idname = "plant.growth"
    bl_label = "plant growing"
    bl_description = "plant growing"
    bl_options = {'REGISTER', 'UNDO'}

    # seeds = []

    @classmethod
    def poll(cls, context):
        
        if (context.active_object and 'Plant_Type' in context.active_object.keys()):
            if (context.active_object['Plant_Type'] == 'SEED'):
                return True

        return False
            
    def invoke(self, context, event):
        # wm = context.window_manager

        # return wm.invoke_props_dialog(self)
        return self.execute(context)
        
    def execute(self, context):
        seed = context.active_object

        context.scene.frame_current += 1
        grow(seed)

        return {'FINISHED'}

        

        
