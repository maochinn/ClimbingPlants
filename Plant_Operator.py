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
    PhototropismResponseStrength,
    ParticleAnchor,
    ParticleSize,
    ParticleType)
from .Plant_Tool import (
    createPlantParticle,
    setParticleDimension,
    getParticleMainAxis,
    getParticleCenter,
    closestAnchor)



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
        createPlantParticle(context, "Seed",  self.location, (0, 0, 0), 'SEED', self.sa_strength, self.pr_strength)
        return {'FINISHED'}

class PlantDynamics(Operator):
    bl_idname = "plant.dynamics"
    bl_label = "plant dynamic"
    bl_description = "plant particle simulation, modify location"
    bl_options = {'REGISTER', 'UNDO'}

    def predict(self, context, particle, delta_t):
        x = particle.matrix_world.to_translation()
        v = particle.velocity



        a = Vector((0, 0, 0))
        if (context.scene.use_gravity):
            a += context.scene.gravity

        x_p = x + v*delta_t + 0.5*(a*delta_t*delta_t)

        # TODO
        x = x_p

        if (particle.children):
            for child in particle.children:
                self.predict(context, child, delta_t)

    def updateAnchor(self, context, particle):
        # find all obstacle to attract particle
        obstacles = [obj for obj in context.scene.objects if ParticleType[1]['name'] in obj.keys() and obj[ParticleType[1]['name']] == 'OBSTACLE']
        particle[ParticleAnchor[1]['name']] = closestAnchor(getParticleCenter(particle), obstacles)

        if (particle.children):
            for child in particle.children:
                self.updateAnchor(context, child)





    @classmethod
    def poll(cls, context):
        
        if (context.active_object and ParticleType[1]['name'] in context.active_object.keys()):
            if (context.active_object[ParticleType[1]['name']] == 'SEED'):
                return True

        return False
            
    def invoke(self, context, event):
        # wm = context.window_manager

        # return wm.invoke_props_dialog(self)
        return self.execute(context)
        
    def execute(self, context):
        seed = context.active_object

        self.predict(context, seed, context.scene.frame_step / context.scene.render.fps)
        
        self.updateAnchor(context, seed)

        context.view_layer.objects.active = seed
        seed.select_set(True)
        bpy.ops.object.select_grouped(extend=True, type='CHILDREN_RECURSIVE')

        bpy.ops.anim.keyframe_insert_menu(type='Scaling')
        return {'FINISHED'}

class PlantGrowth(Operator):
    bl_idname = "plant.growth"
    bl_label = "plant growing"
    bl_description = "plant particle grow and branch"
    bl_options = {'REGISTER', 'UNDO'}

    # seeds = []

    def grow(self, context, particle, delta_t):
        a, b, c = particle[ParticleSize[1]['name']]

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

        particle[ParticleSize[1]['name']] = (a, b, c)
        # particle.dimensions = (a, b, c)
        # scale = (
        #     (a / particle.dimensions[0]),
        #     (b / particle.dimensions[1]),
        #     (c / particle.dimensions[2]))

        # bpy.ops.object.select_all(action='DESELECT')
        # particle.select_set(True)
        # bpy.ops.transform.resize(value=scale)
        setParticleDimension(particle, particle[ParticleSize[1]['name']])
        # bpy.ops.anim.keyframe_insert_menu(type='Scaling')


        if (particle.children):
            for child in particle.children:
                self.grow(context, child, delta_t)
        else:
            # Surface Adaption
            tau = particle[SurfaceAdaptionStrength[1]['name']]
            v_s = Vector(particle[ParticleAnchor[1]['name']]) - getParticleCenter(particle)
            v_f = getParticleMainAxis(particle)
            v_s.normalize(); v_f.normalize(); 
            a_a = v_s.cross(v_f)
            alpha_a = (v_s @ v_f) * tau * delta_t

            # Phototropism
            eta = particle[PhototropismResponseStrength[1]['name']]
            lights = [obj for obj in context.scene.objects if ParticleType[1]['name'] in obj.keys() and obj[ParticleType[1]['name']] == 'LIGHT']
            if(lights):
                v_l = lights[0].location - getParticleCenter(particle)
                radial = v_l.length
                oclusion = lights[0].data.energy/(radial*radial) # not the correct way
                v_l.normalize()
                a_p = v_l.cross(v_f)
                alpha_p = (1 - oclusion) * eta * delta_t

            # particle.rotation_quaternion = particle.rotation_quaternion @ Quaternion(a_a[:], alpha_a) @ Quaternion(a_p[:], alpha_p)
            particle.rotation_euler = (particle.rotation_euler.to_quaternion() @ Quaternion(a_a[:], alpha_a) @ Quaternion(a_p[:], alpha_p)).to_euler()
            # bpy.ops.object.select_all(action='DESELECT')
            # particle.select_set(True)
            # temp = (Quaternion(a_a[:], 1.0) @ Quaternion(a_p[:], alpha_p)).to_matrix()
            # bpy.ops.transform.rotate(orient_matrix=temp)
            # grow branch particle
            if (c >= max_c):
                rand = random.random()
                rand = 1 - rand
                if (rand > bpy.types.Scene.plant_branch_probablity):
                    # create child particle(branch)
                    particle_global_location = particle.matrix_world.to_translation()
                    particle_global_orienation = particle.matrix_world.to_euler()
                    branch_location = particle_global_location + c*getParticleMainAxis(particle)
                    createPlantParticle(
                        context, "branch", 
                        branch_location, 
                        particle_global_orienation, 
                        'BRANCH', 
                        particle[SurfaceAdaptionStrength[1]['name']],
                        particle[PhototropismResponseStrength[1]['name']], particle)
                    # bpy.ops.anim.keyframe_insert_menu(type='Scaling')

    @classmethod
    def poll(cls, context):
        
        if (context.active_object and ParticleType[1]['name'] in context.active_object.keys()):
            if (context.active_object[ParticleType[1]['name']] == 'SEED'):
                return True

        return False
            
    def invoke(self, context, event):
        # wm = context.window_manager

        # return wm.invoke_props_dialog(self)
        return self.execute(context)
        
    def execute(self, context):
        seed = context.active_object

        context.scene.frame_current += context.scene.frame_step
        self.grow(context, seed, context.scene.frame_step)

        context.view_layer.objects.active = seed
        seed.select_set(True)
        bpy.ops.object.select_grouped(extend=True, type='CHILDREN_RECURSIVE')

        bpy.ops.anim.keyframe_insert_menu(type='Scaling')
        bpy.ops.anim.keyframe_insert_menu(type='Rotation')
        return {'FINISHED'}

        

        
