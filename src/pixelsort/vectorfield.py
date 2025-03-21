import numpy as np
from PIL import Image
class Vector:
    def __init__(self,x=0.0,y=0.0):
        self.x = x
        self.y = y

    @property
    def magnitude(self):
        """Calculate and return the magnitude of the vector"""
        return np.sqrt(self.x ** 2 + self.y ** 2)

    @property 
    def direction(self):
        """Calculate and return the direction (angle in radians) of the vector"""
        return np.arctan2(self.y,self.x); 

    def to_hsv(self,max_magnitude=1.0):
        angle_deg = np.degrees(self.direction) % 360
        hue = angle_deg / 360
        value = np.clip(self.magnitude / max_magnitude, 0, 1)
        saturation = 1.0
        return (hue,saturation,value)
    
    def __add__(self,other):
        if(isinstance(other, Vector)):
            return Vector(self.x + other.x, self.y + other.y)
        return ValueError("Trying to add a vector to a non-vector")
    
    def __mul__(self,scalar):
        return Vector(self.x * scalar, self.y * scalar)
    
    def __repr__(self):
        return f"Vector(x={self.x}, y={self.y})"
    
class VectorField:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.field = np.array([[Vector(0,0) for _ in range(width)] for _ in range(height)])
        print(self.field.shape)
    
    def get_vector(self,x,y):
        return self.field[y,x]
    
    def set_vector(self,x,y,vector):
        self.field = vector
    
    def get_max_magnitiude(self):
        max_mag = 0.0
        for y in range(self.height):
            for x in range(self.width):
                mag = self.field[y,x].magnitude
                if(mag > max_mag):
                    max_mag = mag
        return max_mag

    def apply_operation(self,func):
        for y in range(self.height):
            for x in range(self.width):
                self.field[y,x] = func(x,y,self.field[y,x])

    def reset(self):
        self.field.fill(0)

    def line_transform(self,x1,y1,x2,y2,strength,falloff):
        """
        Given a line with the starting point (x1,y1) and ending point (x2,y2),
        transforms the vector field's vectors in some proximity to the line
        to point towards the same direction the line is going, with a magnitude 
        according to strength and falloff.

        :param (x1,y1): the starting point of the line
        :param (x2,y2): the ending point of the line
        :param strength: the amount of influence applied to vectors on the line
        :param falloff: the maximum distance where the line still influences the field.
        """
        # line direction and length
        dx = x2 - x1
        dy = y2 - y1
        line_length = np.sqrt(dx**2 + dy**2)
        if(line_length == 0):
            return
        # unit vector in the direction of the line
        ux = dx/line_length
        uy = dy/line_length
        def operation(x,y,vector):
            px = x - x1
            py = y - y1
            distance = abs(dx * py - dy * px) / line_length
            weight = strength * max(0,1 - (distance/falloff))
            new_x = vector.x + ux * weight
            new_y = vector.y + ux * weight
            return Vector(new_x,new_y)
        self.apply_operation(operation)
        pass

    def move_towards_point(self,target_x,target_y):
        """Pull all vector endpoints on (x,y)"""
        def towards_target(x,y,vector):
            dx = target_x - x
            dy = target_y - y
            magnitiude = 1 #np.sqrt(dx**2+dy**2)
            if(magnitiude == 0):
                return Vector(0,0)
            return Vector(dx/magnitiude,dy/magnitiude)
        self.apply_operation(towards_target)

    def to_hsv_array(self,max_magnitude=1.0):
        hsv_array = np.zeros((self.height,self.width, 3), dtype=np.uint8)
        for y in range(self.height):
            for x in range(self.width):
                h,s,v = self.field[y,x].to_hsv(max_magnitude)
                hsv_array[y,x,0] = int(h*255)
                hsv_array[y,x,1] = int(s*255)
                hsv_array[y,x,2] = int(v*255)
        return hsv_array

    def output_hsv_image(self):
        max_magnitude = self.get_max_magnitiude()
        hsv_array = self.to_hsv_array(max_magnitude)
        print(hsv_array.shape)
        img = Image.fromarray(hsv_array,mode='HSV')
        print(f'img height:{img.height}, img width:{img.width}')
        img.show()

    def __repr__(self):
        return f"VectorField(width={self.width}, height={self.height})"