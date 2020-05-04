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
from mathutils import Vector, Matrix, Quaternion, geometry

from .Plant_Type import (
    SurfaceAdaptionStrength,
    PhototropismResponseStrength)
from .Plant_Tool import (
    createPlantParticle,
    setParticleDimension,
    getParticleMainAxis,
    getParticleGlobalLocation)



class PlantSeeding(Operator):
    bl_idname = "plant.seeding"
    bl_label = "dynamic plant seeding"
    bl_description = "seed plant root"
    bl_options = {'REGISTER', 'UNDO'}
    
    sa_strength :SurfaceAdaptionStrength
    pr_strength :PhototropismResponseStrength
    # depth       :plant_depth
    # plant_type  :plant_type
    location    :FloatVectorProperty(name="Location", default=(0, 0, 0))

    @classmethod
    def poll(cls, context):
        return True
            
    def invoke(self, context, event):
        wm = context.window_manager

        return wm.invoke_props_dialog(self)

    def execute(self, context):
        createPlantParticle(context, "Seed",  self.location, 'SEED', self.sa_strength, self.pr_strength)
        return {'FINISHED'}


class PlantGrowth(Operator):
    bl_idname = "plant.growth"
    bl_label = "plant growing"
    bl_description = "plant growing"
    bl_options = {'REGISTER', 'UNDO'}

    # seeds = []

    def grow(self, context, particle):
        
        a, b, c = particle['Size']

        max_a, max_b, max_c = bpy.types.Scene.plant_max_size
        delta_a, delta_b, delta_c = bpy.types.Scene.plant_delta_size
        
        a += delta_a
        b += delta_b
        c += delta_c

        if (a > max_a):
            a = max_a
        if (b > max_b):
            b = max_b
        if (c > max_c):
            c = max_c

        particle['Size'] = (a, b, c)
        # particle.dimensions = (a, b, c)
        # scale = (
        #     (a / particle.dimensions[0]),
        #     (b / particle.dimensions[1]),
        #     (c / particle.dimensions[2]))

        # bpy.ops.object.select_all(action='DESELECT')
        # particle.select_set(True)
        # bpy.ops.transform.resize(value=scale)
        setParticleDimension(particle, particle['Size'])
        # bpy.ops.anim.keyframe_insert_menu(type='Scaling')


        if (particle.children):
            for child in particle.children:
                self.grow(context, child)
        elif (c >= max_c/2):
            rand = random.random()
            rand = 1 - rand
            if (rand > bpy.types.Scene.plant_branch_probablity):
                particle_global_location = getParticleGlobalLocation(context, particle)
                branch_location = particle_global_location + c*getParticleMainAxis(particle)
                createPlantParticle(
                    context, "branch", branch_location, 'BRANCH', particle["SA"], particle["PR"], particle)
                # bpy.ops.anim.keyframe_insert_menu(type='Scaling')

    @classmethod
    def poll(cls, context):
        
        if (context.active_object and 'Type' in context.active_object.keys()):
            if (context.active_object['Type'] == 'SEED'):
                return True

        return False
            
    def invoke(self, context, event):
        # wm = context.window_manager

        # return wm.invoke_props_dialog(self)
        return self.execute(context)
        
    def execute(self, context):
        seed = context.active_object

        context.scene.frame_current += 1
        self.grow(context, seed)

        context.view_layer.objects.active = seed
        seed.select_set(True)
        bpy.ops.object.select_grouped(extend=True, type='CHILDREN_RECURSIVE')

        bpy.ops.anim.keyframe_insert_menu(type='Scaling')


        return {'FINISHED'}

        

        
