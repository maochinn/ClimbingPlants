import bpy
from mathutils import Vector, Matrix, Quaternion, geometry

from .Plant_Type import (
    createParticleProperty)


def createPlantParticle(context, name, location, plant_type, sa_strength, pr_strength, parent = None):
    bpy.ops.mesh.primitive_uv_sphere_add(location=location)
    particle = context.active_object

    # seed.scale = bpy.types.Scene.plant_delta_scale
    default = bpy.types.Scene.plant_delta_size
    # particle.dimensions = default
    bpy.ops.transform.resize(value=default*0.5)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.transform.translate(value=(0,0,default.z*0.5))
    bpy.ops.object.mode_set(mode='OBJECT')
    particle.name = name

    # set parent
    if(parent != None):
        bpy.ops.object.select_all(action='DESELECT')
        particle.select_set(True)
        context.view_layer.objects.active = parent
        bpy.ops.object.parent_set()

    createParticleProperty(
        context, 
        particle, 
        sa_strength, 
        pr_strength,
        plant_type)

    return particle

def getParticleMainAxis(particle):
    return particle.rotation_euler.to_quaternion() @ Vector((0,0,1))

def setParticleDimension(particle, dimension):
    scale = (
        (dimension[0] / particle.dimensions[0]),
        (dimension[1] / particle.dimensions[1]),
        (dimension[2] / particle.dimensions[2]))

    bpy.ops.object.select_all(action='DESELECT')
    particle.select_set(True)
    bpy.ops.transform.resize(value=scale)

def getParticleGlobalLocation(context, particle):
    # particle_global_location = particle.location
    # parent = particle.parent
    # while(parent):
    #     particle_global_location = parent.matrix_world @ particle.matrix_parent_inverse @ particle_global_location
    #     particle = particle.parent
    #     parent = particle.parent
    parent = particle.parent
    particle_global_location = particle.location
    if (parent):
        bpy.ops.object.select_all(action='DESELECT')
        particle.select_set(True)
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        particle_global_location = particle.location
        context.view_layer.objects.active = parent
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
        setParticleDimension(particle, particle['Size'])

    return particle_global_location