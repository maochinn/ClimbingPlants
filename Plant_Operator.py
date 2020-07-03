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
from math import sin, cos, pi

import numpy as np
from scipy.linalg import polar
from numpy.linalg import inv, det

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
        particle = createPlantParticle(context, "Seed",  self.location, (1, 0, 0, 0), 'SEED', self.sa_strength, self.pr_strength)

        current = context.scene.frame_current

        particle.keyframe_insert(data_path='position', frame = current)
        particle.keyframe_insert(data_path='velocity', frame = current)
        particle.keyframe_insert(data_path='orientation', frame = current)
        particle.keyframe_insert(data_path='angular_velocity', frame = current)

        particle.keyframe_insert(data_path='location', frame = current)
        particle.keyframe_insert(data_path='rotation_quaternion', frame = current)

        return {'FINISHED'}

class PlantDynamics(Operator):
    bl_idname = "plant.dynamics"
    bl_label = "plant dynamic"
    bl_description = "plant particle simulation, modify location"
    bl_options = {'REGISTER', 'UNDO'}

    #
    STIFFNESS = 1.0
    RIGID = 1.0
    EPSILON = 0.001

    # rest position and orientation
    x0 = {};    q0 = {}
    # target position and orientation in a frame
    xt = {};    qt = {}
    # predict position and orientation in a frame
    xp = {};    qp = {}

    # delta time
    dt = 0
    # 
    context = bpy.context

    def predict(self, particle):
        EPSILON = self.EPSILON
        dt = self.dt
        g = self.context.scene.gravity

        xi = particle.position.copy()
        vi = particle.velocity.copy()
        qi = particle.rotation_quaternion
        wi = particle.angular_velocity

        self.x0[particle] = particle.rest_position.copy()
        self.q0[particle] = particle.rest_orientation.copy()

        self.xt[particle] = []
        self.qt[particle] = []

        if self.context.scene.use_gravity:
            self.xp[particle] = xi + vi*dt + 0.5*g*dt*dt
        else:
            self.xp[particle] = xi + vi*dt
                
        Wi = wi.length
        if Wi < EPSILON:
            self.qp[particle] = qi.copy()
        else:
            self.qp[particle] = Quaternion(wi/Wi * sin(0.5*Wi*dt), cos(0.5*Wi*dt)) @ qi
        
        # constraint
        if self.context.scene.frame_current <= particle.animation_data.action.frame_range[1]:
            self.xp[particle] = xi.copy()
            # self.qp[particle] = qi.copy()

        if self.xp[particle].z < 0.0:
            self.xp[particle].z = 0.0

        if (particle['Childs']):
            for child in particle['Childs']:
                self.predict(child)

    def computeTarget(self, particle):
        
        def massCenter(x, m):
            c = Vector((0, 0, 0))
            M = 0.0
            for i in range(len(x)):
                c = c + m[i] * x[i]
                M = M + m[i]
            return c/M

        RIGID = self.RIGID
        STIFFNESS = self.STIFFNESS

        group = [particle['Parent']] if particle['Parent'] else []
        group += [particle]
        group += [child for child in particle['Childs']]


        x0 = [self.x0[particle] for particle in group]
        q0 = [self.q0[particle] for particle in group]
        xp = [self.xp[particle] for particle in group]
        # qp = [self.qp[particle] for particle in group]
        m = [1.3334 * pi * particle.scale[0]*particle.scale[1]*particle.scale[2] for particle in group]
        
        # find opitmal transformation
        x0_c = massCenter(x0, m)
        xp_c = massCenter(xp, m)
        A = np.matrix(np.zeros((3, 3)))
        c_ = np.matrix(x0_c).T
        c = np.matrix(xp_c).T
        
        for i in range(len(xp)):
            xi_ = np.matrix(x0[i]).T
            xi = np.matrix(xp[i]).T
            
            aa = group[i].scale[0] * group[i].scale[0]
            bb = group[i].scale[1] * group[i].scale[1]
            cc = group[i].scale[2] * group[i].scale[2]
            
            R = np.matrix(q0[i].to_matrix())
            # R = np.matrix(Matrix.Identity(3))

            Ai = 0.2 * m[i] * np.matrix([[aa, 0, 0],[0, bb, 0],[0, 0, cc]]) * R

            A += Ai + m[i]*xi*xi_.T - m[i]*c*c_.T
            
        R, S = polar(A)
        Rg = Matrix((RIGID*R + (1.0 - RIGID)*A).tolist())

        g = [Rg @ (x0_i - x0_c) + xp_c for x0_i in x0]
                

        weight = 1.0
        for i, ob in enumerate(group):
            xt = xp[i] + STIFFNESS*(g[i] - xp[i])
            # qt = q0[i] @ Rg.to_quaternion()
            
            self.xt[ob] += [(xt, weight)]
            # self.qt[ob] += [(qt, weight)]

        qt = self.q0[particle] @ Rg.to_quaternion()
        self.qt[particle] += [(qt, weight)]

        if (particle['Childs']):
            for child in particle['Childs']:
                self.computeTarget(child)
        

    def computeGoal(self, particle):

        def weightSumPosition(list):
            X = Vector((0, 0, 0))
            W = 0.0
            for x, w in list:
                X = X + w*x
                W = W + w
            return X/W

        def weightSumOrientation(list):
            Q = Vector((0, 0, 0))
            W = 0.0
            for q, w in list:
                Q = Q + w*q.to_exponential_map()
                W = W + w
            return Quaternion(Q/W)

        xg = weightSumPosition(self.xt[particle])
        qg = weightSumOrientation(self.qt[particle])

        self.xt[particle] = []
        self.qt[particle] = []

        self.xp[particle] = xg
        self.qp[particle] = qg

        # constraint
        if self.context.scene.frame_current <= particle.animation_data.action.frame_range[1]:
            self.xp[particle] = particle.position.copy()
            # self.qp[particle] = particle.orientation.copy()
            
        if self.xp[particle].z < 0.0:
            self.xp[particle].z = 0.0

        if (particle['Childs']):
            for child in particle['Childs']:
                self.computeGoal(child)




    # def computePredictPosition(self, particle):

    #     def massCenter(x, m):
    #         c = Vector((0, 0, 0))
    #         M = 0.0
    #         for i in range(len(x)):
    #             c = c + m[i] * x[i]
    #             M = M + m[i]
    #         return c/M
        
    #     cluster = [particle['Parent']] if particle['Parent'] else []
    #     cluster += [particle]
    #     cluster += [child for child in particle['Childs']]

    #     for P in cluster:
    #         if P not in self.xt:
    #             self.xt[P] = []
    #             self.qt[P] = []


    #     x = [P.position.copy() for P in cluster]
    #     v = [P.velocity.copy() for P in cluster]
    #     q = [P.orientation.copy() for P in cluster]
    #     w = [P.angular_velocity.copy() for P in cluster]
    #     m = [1.3334 * pi * P.scale[0]*P.scale[1]*P.scale[2] for P in cluster]

    #     x0 = [P.rest_position.copy() for P in cluster]
    #     q0 = [P.rest_orientation.copy() for P in cluster]
    #     x0_cm = massCenter(x0, m)   # need m0?

    #     # predict 
    #     xp = []
    #     qp = []

    #     for i in range(len(cluster)):
    #         if self.context.scene.frame_current > cluster[i].animation_data.action.frame_range[1]:
    #             a = Vector((0, 0, 0))
    #             if (self.context.scene.use_gravity):
    #                 a += self.context.scene.gravity

    #             xp += [x[i] + v[i]*self.dt + 0.5*a*self.dt*self.dt]
    #             w_i = w[i].length
    #             if w_i < self.EPSILON:
    #                 qp += [q[i]]
    #             else:
    #                 qp += [Quaternion(w[i]/w_i * sin(0.5*w_i*self.dt), cos(0.5*w_i*self.dt)) @ q[i]]
    #         else:
    #             xp += [x[i]]
    #             qp += [q[i]]


    #     # find opitmal transformation
    #     xp_cm = massCenter(xp, m)
    #     A = np.matrix(np.zeros((3, 3)))
    #     c_ = np.matrix(x0_cm).T
    #     c = np.matrix(xp_cm).T
        
    #     for i in range(len(x)):
    #         xi_ = np.matrix(x0[i]).T
    #         xi = np.matrix(xp[i]).T
            
    #         aa = cluster[i].scale[0] * cluster[i].scale[0]
    #         bb = cluster[i].scale[1] * cluster[i].scale[1]
    #         cc = cluster[i].scale[2] * cluster[i].scale[2]
            
    #         R = np.matrix(q[i].to_matrix())
            
    #         Ai = 0.2 * m[i] * np.matrix([[aa, 0, 0],[0, bb, 0],[0, 0, cc]]) * R

    #         A += Ai + m[i]*xi*xi_.T - m[i]*c*c_.T
            
    #     R, S = polar(A)
    #     R = Matrix(R.tolist())
    #     # mat = Matrix((RIGID*R + (1.0 - RIGID)*A).tolist())

    #     g = [R @ (x0_i - x0_cm) + xp_cm for x0_i in x0]
    #     for i in range(len(g)):
    #         xp[i] += self.STIFFNESS*(g[i] - xp[i])
    #         qp[i] = R.to_quaternion() @ q0[i]

    #     for i, P in enumerate(cluster):
    #         if self.context.scene.frame_current > P.animation_data.action.frame_range[1]:
    #             self.xt[P] += [xp[i]]
    #             self.qt[P] += [qp[i]]

    #     if (particle['Childs']):
    #         for child in particle['Childs']:
    #             # child.location = particle.location + particle.rotation_quaternion @ Vector((0, 0, 2*c))
    #             self.computePredictPosition(child)


    # def computeGoalPosition(self, particle):

    #     def averagePostions(positions):
    #         def sumPositions(l,n):
    #             if n == 0:
    #                 return l[n]
    #             return l[n] + sumPositions(l,n-1)
        
    #         return sumPositions(positions, len(positions)-1) / len(positions)

    #     def averageOrientation(orientations):
    #         # refer: https://docs.blender.org/api/current/mathutils.html
    #         def sumQuaternions(l,n):
    #             if n == 0:
    #                 return l[n].to_exponential_map()
    #             return l[n].to_exponential_map() + sumQuaternions(l,n-1)
            
    #         exp_avg = sumQuaternions(orientations, len(orientations)-1) / len(orientations)
    #         return Quaternion(exp_avg)


    #     if self.context.scene.frame_current > particle.animation_data.action.frame_range[1]:
    #         goal_position = averagePostions(self.xt[particle])
    #         goal_orientation = averageOrientation(self.qt[particle])
            
    #         # ob.velocity = (xp - ob.location)/h + h*bpy.context.scene.gravity
    #         particle.velocity = (goal_position - particle.position)/self.dt
    #         particle.position = goal_position
    #         r = goal_orientation @ particle.orientation.inverted()
    #         r = -r if r.w < 0 else r
    #         axis, angle = r.to_axis_angle()
            
    #         if abs(angle) > self.EPSILON: 
    #             particle.angular_velocity = axis*angle / self.dt
    #             particle.orientation = goal_orientation

    #         if particle.position.z < 0.0:
    #             particle.velocity = (0.0, 0.0, 0.0)
    #             particle.position.z = 0.0

    #     if (particle['Childs']):
    #         for child in particle['Childs']:
    #             self.computeGoalPosition(child)
            


    # def updateAnchor(self, context, particle):
    #     # find all obstacle to attract particle
    #     obstacles = [obj for obj in context.scene.objects if ParticleType[1]['name'] in obj.keys() and obj[ParticleType[1]['name']] == 'OBSTACLE']
    #     particle[ParticleAnchor[1]['name']] = closestAnchor(getParticleCenter(particle), obstacles)

    #     if (particle['Childs']):
    #         for child in particle['Childs']:
    #             child.location = particle.location + particle.rotation_quaternion @ Vector((0, 0, 2*c))
    #             self.grow(context, child, delta_t)


    def updateAnimation(self, particle):
        EPSILON = self.EPSILON
        dt = self.dt
        current = self.context.scene.frame_current

        if current > particle.animation_data.action.frame_range[1]:
            xg = self.xp[particle]
            qg = self.qp[particle]
            
            particle.velocity = (xg - particle.position)/dt
            particle.position = xg
            r = qg @ particle.orientation.inverted()
            r = -r if r.w < 0 else r
            axis, angle = r.to_axis_angle()
            
            if abs(angle) > EPSILON:
                particle.angular_velocity = axis*angle / dt
                particle.orientation = qg

            if particle.position.z < 0.0:
                particle.velocity = Vector((0.0, 0.0, 0.0))
                particle.position.z = 0.0
            
            # particle dynamic update
            particle.keyframe_insert(data_path='position', frame = current)
            particle.keyframe_insert(data_path='velocity', frame = current)
            particle.keyframe_insert(data_path='orientation', frame = current)
            particle.keyframe_insert(data_path='angular_velocity', frame = current)

            # particle location and rotation
            particle.location = particle.position - particle.orientation @ Vector((0, 0, particle.scale[2]))
            particle.rotation_quaternion = particle.orientation

            particle.keyframe_insert(data_path='location', frame = current)
            particle.keyframe_insert(data_path='rotation_quaternion', frame = current)

        if (particle['Childs']):
            for child in particle['Childs']:
                self.updateAnimation(child)
        



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

        self.x0 = {}; self.q0 = {}
        self.xp = {}; self.qp = {}
        self.xt = {}; self.qt = {}
        
        self.dt = context.scene.frame_step / context.scene.render.fps
        self.context = context

        context.scene.frame_current += context.scene.frame_step

        self.predict(seed)
        # shape matching
        for i in range(4):
            self.computeTarget(seed)
            self.computeGoal(seed)

        # self.computePredictPosition(seed)
        
        # self.computeGoalPosition(seed)

        # self.updateAnchor(context, seed)

        self.updateAnimation(seed)

        context.view_layer.objects.active = seed
        # seed.select_set(True)
        # bpy.ops.object.select_grouped(extend=True, type='CHILDREN_RECURSIVE')

        # bpy.ops.anim.keyframe_insert_menu(type='Scaling')
        return {'FINISHED'}

class PlantGrowth(Operator):
    bl_idname = "plant.growth"
    bl_label = "plant growing"
    bl_description = "plant particle grow and branch"
    bl_options = {'REGISTER', 'UNDO'}

    dt = 0
    context = bpy.context

    def grow(self, particle):
        a, b, c = particle.scale

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

        particle.select_set(True)
        particle.scale = (a, b, c)

        # Surface Adaption
        tau = particle['SA']
        v_s = Vector(particle['Anchor']) - getParticleCenter(particle)
        v_f = getParticleMainAxis(particle)
        v_s.normalize(); v_f.normalize(); 
        a_a = v_s.cross(v_f)
        alpha_a = (v_s @ v_f) * tau * self.dt

        # Phototropism
        eta = particle['PR']
        lights = [obj for obj in self.context.scene.objects if 'Type' in obj.keys() and obj['Type'] == 'LIGHT']
        if(lights):
            v_l = lights[0].location - getParticleCenter(particle)
            radial = v_l.length
            occlusion = lights[0].data.energy/(radial*radial) # not the correct way
            v_l.normalize()
            a_p = v_l.cross(v_f)
            # alpha_p = (1 - occlusion) * eta * delta_t
            alpha_p = -eta * self.dt

        rotation = Quaternion(a_a[:], alpha_a) @ Quaternion(a_p[:], alpha_p)
        particle.rotation_quaternion = particle.rotation_quaternion @ rotation

        particle_global_location = particle.matrix_world.to_translation()
        particle_global_orienation = particle.matrix_world.to_quaternion()

        if (particle['Childs']):
            for child in particle['Childs']:
                child.location = particle.location + particle.rotation_quaternion @ Vector((0, 0, 2*c))
                child.rotation_quaternion = rotation @ child.rotation_quaternion
                self.grow(child)
        elif(c >= max_c):        # grow branch particle
            rand = random.random()
            rand = 1 - rand
            if (rand > bpy.types.Scene.plant_branch_probablity):
                # create child particle(branch)
                branch_location = particle.location + particle.rotation_quaternion @ Vector((0, 0, 2*c))
                createPlantParticle(
                    self.context, "branch", 
                    branch_location, 
                    particle_global_orienation, 
                    'BRANCH', 
                    particle['SA'],
                    particle['PR'], particle)

    def updateAnimation(self, particle):

        # particle location and rotation
        particle.keyframe_insert(data_path='location', frame = self.context.scene.frame_current)
        particle.keyframe_insert(data_path='rotation_quaternion', frame = self.context.scene.frame_current)
        particle.keyframe_insert(data_path='scale', frame = self.context.scene.frame_current)

        # particle position and orientation
        particle.position = particle.location + particle.rotation_quaternion @ Vector((0, 0, particle.scale[2]))
        particle.orientation = particle.rotation_quaternion

        particle.rest_position = particle.position
        particle.rest_orientation = particle.orientation

        particle.keyframe_insert(data_path='position', frame = self.context.scene.frame_current)
        particle.keyframe_insert(data_path='orientation', frame = self.context.scene.frame_current)
        particle.keyframe_insert(data_path='rest_position', frame = self.context.scene.frame_current)
        particle.keyframe_insert(data_path='rest_orientation', frame = self.context.scene.frame_current)

        if (particle['Childs']):
            for child in particle['Childs']:
                self.updateAnimation(child)


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

        self.context = context
        self.dt = context.scene.frame_step/context.scene.render.fps

        context.scene.frame_current += context.scene.frame_step

        self.grow(seed)

        self.updateAnimation(seed)

        context.view_layer.objects.active = seed
        # seed.select_set(True)
        # bpy.ops.object.select_grouped(extend=True, type='CHILDREN_RECURSIVE')

        # bpy.ops.anim.keyframe_insert_menu(type='Scaling')
        # bpy.ops.anim.keyframe_insert_menu(type='Rotation')
        return {'FINISHED'}

        

        
