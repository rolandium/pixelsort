import numpy as np
import scipy.ndimage as nd
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
        if(self.magnitude == 0):
            value = 0
        else:
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

    def warp_image(self,image,initial_strength,decay,stop_threshold):
        """
        Given an image, transform the given image accordingly?
        """
        image_out = np.array(image)
        height, width = image_out.shape[:2]
        strength = initial_strength
        while(strength >= stop_threshold):
            image_current = np.zeros_like(image_out)
            for y in range(height):
                for x in range(width):
                    vector = self.get_vector(x,y)
                    dx = (x - strength * vector.x)
                    dy = (y - strength * vector.y)
                    # if y == int(height/2): print(f'x:{x} y:{y} dx: {dx}, dy:{dy}')
                    # resulting coords in the current image
                    # should be (x,y) + displacement
                    # need to clamp the ending coords
                    # for now just discard them
                    if(0 <= dy < height and 0 <= dx < width):
                        image_current[y,x] = image_out[int(dy),int(dx)]
                        pass
            image_out = image_current
            strength *= decay
        return image_out
            

    def line_transform(self,p1,p2,strength,falloff,decay_type="gaussian"):
        """
        Given a line with the starting point (x1,y1) and ending point (x2,y2),
        transforms the vector field's vectors in some proximity to the line
        to point towards the same direction the line is going, with a magnitude 
        according to strength and falloff.

        :param (x1,y1), p1: 
        the starting point of the line
        :param (x2,y2), p2: 
        the ending point of the line
        :param strength: 
        the amount of influence applied to vectors close to the line
        :param falloff: 
        the maximum distance where the line still influences the field.
        :param  "linear", "gaussian", "exponential" decay_type: 
        the type of decay function to use for falloff
        """
        (x1, y1) = p1
        (x2, y2) = p2
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
            if(decay_type == "exponential"):
                weight = strength * np.exp(-(distance/falloff))
            if(decay_type == "gaussian"):
                weight = strength * np.exp(- (distance**2)/(2*falloff**2))
            if(decay_type == "linear"):
                weight = strength * max(0,1 - (distance/falloff))
            new_x = vector.x + ux * weight
            new_y = vector.y + uy * weight
            return Vector(new_x,new_y)
        self.apply_operation(operation)

    # formula from https://stackoverflow.com/a/4091430
    def _cubic_bezier(t,p0,p1,p2,p3):
        p0 = np.array(p0)
        p1 = np.array(p1)
        p2 = np.array(p2)
        p3 = np.array(p3)
        return (1-t)**3 * p0 + 3*t*(1-t)**2*p1 + 3*t**2*(1-t)*p2 + t**3*p3

    def _cubic_bezier_derivative(t,p0,p1,p2,p3):
        p0 = np.array(p0)
        p1 = np.array(p1)
        p2 = np.array(p2)
        p3 = np.array(p3)
        return -3*(1-t)**2*p0 + 3*(1-t)**2*p1 - 6*t*(1-t)*p1 - 3*t**2*p2 + 6*t*(1-t)*p2 + 3*t**2*p3

    def spline_transform(self,p0,p1,p2,p3,num_samples,strength,falloff,decay_type="gaussian"):
        """
        Given a cubic bezier spline with the control points p0-p3, transform close vectors
        in the field according to their distance to the spline, along with the strength parameter
        and the falloff parameter.

        :param (x,y), pX: 
        control point of the cubic bezier spline
        :param num_samples: 
        the number of sampled points for the spline
        :param strength: 
        the amount of influence applied to vectors close to the line
        :param falloff:
        the maximum distance of the line's influence
        :param  "linear", "gaussian", "exponential" decay_type: 
        the type of decay function to use for falloff
        """
        def cubic_bezier(t,p0,p1,p2,p3):
            p0 = np.array(p0)
            p1 = np.array(p1)
            p2 = np.array(p2)
            p3 = np.array(p3)
            return (1-t)**3 * p0 + 3*t*(1-t)**2*p1 + 3*t**2*(1-t)*p2 + t**3*p3
        def cubic_bezier_derivative(t,p0,p1,p2,p3):
            p0 = np.array(p0)
            p1 = np.array(p1)
            p2 = np.array(p2)
            p3 = np.array(p3)
            return -3*(1-t)**2*p0 + 3*(1-t)**2*p1 - 6*t*(1-t)*p1 - 3*t**2*p2 + 6*t*(1-t)*p2 + 3*t**2*p3
        t_values = np.linspace(0,1,num_samples)
        samples = [cubic_bezier(t,p0,p1,p2,p3) for t in t_values]
        tangents = [cubic_bezier_derivative(t,p0,p1,p2,p3) for t in t_values]
        def operation(x,y,vector):
            point = np.array([x,y])
            distances = [np.linalg.norm(point - sample) for sample in samples]
            min_index = np.argmin(distances)
            distance = distances[min_index]
            if(decay_type == "exponential"):
                weight = strength * np.exp(-(distance/falloff))
            if(decay_type == "gaussian"):
                weight = strength * np.exp(- (distance**2)/(2*falloff**2))
            if(decay_type == "linear"):
                weight = strength * max(0,1 - (distance/falloff))
            tangent = tangents[min_index]
            new_x = vector.x + tangent[0] * weight
            new_y = vector.y + tangent[1] * weight
            return Vector(new_x,new_y)
        self.apply_operation(operation)

    def move_towards_point(self,point):
        """
        Pull all vector endpoints to (x,y)
        """
        (target_x, target_y) = point
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
        """
        Output an image where the hue and value of a given pixel indicates
        that pixel's direction and magnitude, respectively.
        """
        max_magnitude = self.get_max_magnitiude()
        hsv_array = self.to_hsv_array(max_magnitude)
        print(hsv_array.shape)
        img = Image.fromarray(hsv_array,mode='HSV')
        print(f'img height:{img.height}, img width:{img.width}')
        img.show()

    def output_arrow_image(self):
        """
        Output an image with arrows placed in a sparse grid that indicate
        the average magnitude and direction at that point in the field.
        """
        # TODO: implement this
        pass

    def __repr__(self):
        return f"VectorField(width={self.width}, height={self.height})"