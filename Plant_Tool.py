import bpy
from mathutils import Vector, Matrix, Quaternion, geometry

from .Plant_Type import (
    ParticleType,
    createParticleProperty)

# 
# local:        Vector(X, Y, Z) location in world space
# orientation:  Euler(X, Y, Z)  radians for 3 axis in world space
def createPlantParticle(context, name, location, orientation, plant_type, sa_strength, pr_strength, parent = None):
    bpy.ops.mesh.primitive_uv_sphere_add(location=location)
    particle = context.active_object

    # seed.scale = bpy.types.Scene.plant_delta_scale
    default = bpy.types.Scene.plant_delta_size
    # particle.dimensions = default
    bpy.ops.transform.resize(value=default*0.5)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.transform.translate(value=(0,0,default.z*0.5))
    bpy.ops.object.mode_set(mode='OBJECT')

    particle.rotation_mode = 'QUATERNION'
    # context.active_object.rotation_euler = orientation
    particle.rotation_quaternion = orientation
    particle.name = name

    # find all obstacle to attract particle
    obstacles = [obj for obj in context.scene.objects if 'Type' in obj.keys() and obj['Type'] == 'OBSTACLE']

    createParticleProperty(
        context,
        particle, 
        sa_strength, 
        pr_strength,
        plant_type,
        closestAnchor(getParticleCenter(particle), obstacles),
        parent)
    
    particle.position = Vector((0, 0, default.z*0.5))
    particle.velocity = Vector((0, 0, 0))
    
    particle.orientation = particle.rotation_quaternion
    particle.angular_velocity = (0, 0, 0)

    particle.rest_position = particle.position
    particle.rest_orientation = particle.orientation

    return particle

def getParticleMainAxis(particle):
    # return particle.rotation_euler.to_quaternion() @ Vector((0,0,1))
    return particle.matrix_world.to_quaternion() @ Vector((0, 0, 1))

# return particle mass of center in world space
def getParticleCenter(particle):
    return particle.matrix_world.to_translation() + particle.scale[2] * getParticleMainAxis(particle)

def setParticleDimension(particle, dimension):
    scale = (
        (dimension[0] / particle.dimensions[0]),
        (dimension[1] / particle.dimensions[1]),
        (dimension[2] / particle.dimensions[2]))

    bpy.ops.object.select_all(action='DESELECT')
    particle.select_set(True)
    bpy.ops.transform.resize(value=scale, orient_type="LOCAL")

# return closest anchor point in obstacles, if null , return v  
def closestAnchor(v, obstacles):
    distances = {}
    for ob in obstacles:
        result, location, normal, index = ob.closest_point_on_mesh(ob.matrix_world.inverted() @ v)
        p = ob.matrix_world @ location
        distances[(p - v).length] = p
    if(distances):
        return distances[min(distances)]
    else:
        return v