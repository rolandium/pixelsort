import numpy as np
from PIL import Image
import cv2

class Vector:
    def __init__(self,y=0.0,x=0.0):
        self.y = y
        self.x = x

    @property
    def magnitude(self):
        """
        Calculate and return the magnitude of the vector
        The vector field uses its own per-pixel magnitude values so this is unused.
        """
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
    def __init__(self, height,width):
        self.height = height
        self.width = width
        self.vectors = np.zeros((height,width,2),dtype=np.float32)
        self.magnitudes = np.zeros((height,width),dtype=np.float32)
    
    def get_vector(self,y,x) -> Vector:
        uy, ux = self.vectors[y,x]
        return Vector(uy,ux)
    
    def set_vector(self,y,x,vector: Vector):
        norm = np.hypot(vector.y,vector.x)
        if(norm > 0):
            self.vectors[y,x] = (vector.y/norm, vector.x/norm)
        else:
            self.vectors[y,x] = (0.0,0.0)
    
    def get_magnitude(self,y,x) -> float:
        return self.magnitudes[y,x]
    
    def set_magnitude(self,y,x,magnitude: float):
        self.magnitudes[y,x] = np.clip(magnitude, 0.0, 1.0)

    def reset(self):
        self.vectors.fill(0.0)
        self.magnitudes.fill(0.0)

    def save(self, path, fileName, writeImage: bool = False):
        """
        Saves the current vector field to a .npz file.
        The file can be loaded in with the load() function

        @param path: The output directory to save the file, ending with a slash
        @param fileName: The name of the output file, without any extension
        @param writeImage: If true, writes the HSV image representation to [fileName].png
        """
        np.savez(path + fileName + ".npz", 
                 vectors = self.vectors, 
                 magnitudes = self.magnitudes)
        if(writeImage):
            hsv = self.to_hsv_array()
            img = Image.fromarray(hsv, mode='HSV').convert('RGB')
            img.save(path + fileName + ".png")

    def load(self,filePath):
        """
        Loads in the specified .npz file, replacing the contents of self
        in the process.

        @param filePath: The full path of the .npz file, including the extension.
        """
        data = np.load(filePath)
        self.vectors = data["vectors"]
        self.magnitudes = data["magnitudes"]
        self.height, self.width = data["vectors"].shape[:2]

    def resize(self, height,width):
        """
        Resizes the vector field to be of the desired height and width.
        """
        # TODO: complete this function 
        pass

    def apply_operation(self,func):
        """
        Applies func(y,x,vector,magnitude) -> (new vector, new magnitude)
        to every pixel
        """
        for y in range(self.height):
            for x in range(self.width):
                uy, ux = self.vectors[y,x]
                mag = self.magnitudes[y,x]
                new_vector, new_mag = func(y,x,Vector(uy, ux),mag)
                norm = np.hypot(new_vector.y, new_vector.x)
                if norm > 0:
                    self.vectors[y,x] = (new_vector.y/norm,new_vector.x/norm)
                else:
                    self.vectors[y,x] = (0.0,0.0)
                self.magnitudes[y,x] = np.clip(new_mag, 0.0, 1.0)

    

    def line_transform(self,p1,p2,strength,falloff,decay_type="gaussian"):
        """
        Given a line with the starting point (y1,x1) and ending point (y2,x2),
        transforms the vector field's vectors in some proximity to the line
        to point towards the same direction the line is going, with a magnitude 
        according to strength and falloff.

        :param (y1,x1), p1: 
        the starting point of the line
        :param (y2,x2), p2: 
        the ending point of the line
        :param strength: 
        the amount of influence applied to vectors close to the line
        :param falloff: 
        the maximum distance where the line still influences the field.
        :param  "linear", "gaussian", "exponential" decay_type: 
        the type of decay function to use for falloff
        """
        (y1, x1) = p1
        (y2, x2) = p2
        # line direction and length
        dx = x2 - x1
        dy = y2 - y1
        line_length = np.hypot(dy,dx)
        if(line_length == 0):
            return
        # unit vector in the direction of the line
        ux = dx/line_length
        uy = dy/line_length
        def operation(y,x,vector,mag):
            px = x - x1
            py = y - y1
            distance = abs(dx * py - dy * px) / line_length
            if(decay_type == "linear"):
                weight = strength * max(0,1 - (distance/falloff))
            if(decay_type == "exponential"):
                weight = strength * np.exp(-(distance/falloff))
            if(decay_type == "gaussian"):
                weight = strength * np.exp(- (distance**2)/(2*falloff**2))
            
            nx = vector.x * mag + ux * weight
            ny = vector.y * mag + uy * weight
            ng = mag * (1-weight) + weight
            return Vector(ny,nx), ng
        self.apply_operation(operation)

    def move_towards_point(self,point,radius):
        """
        Pull all vector endpoints within the radius to (y,x)
        """
        (target_y, target_x) = point
        def towards_target(y,x,vector,mag):
            dy = target_y - y
            dx = target_x - x
            dist = np.hypot(dx,dy)
            if(dist > radius):
                return vector, mag
            
            return Vector(dy,dx), dist / radius
        self.apply_operation(towards_target)

    def spiral_transform(self, point, radius, spiral_strength=0.01):
        (target_y, target_x) = point
        def turn(y,x,vector,mag):
            dx = x - target_x
            dy = y - target_y
            angle = np.arctan2(dy,dx)
            angle += spiral_strength*np.sqrt(dx**2 + dy**2)
            magnitude = np.exp(-((dx**2 + dy**2) / radius**2))
            return Vector(np.sin(angle),np.cos(angle)), magnitude
        self.apply_operation(turn)

    def wave_transform(self, freq_y, freq_x):
        def waves(y,x,vector,mag):
            dy = np.sin(freq_y * y)
            dx = np.cos(freq_x * x)
            m = 1
            return Vector(dy,dx), m
        self.apply_operation(waves)

    def to_hsv_array(self,max_magnitude=1.0):
        hsv = np.zeros((self.height,self.width, 3), dtype=np.uint8)
        for y in range(self.height):
            for x in range(self.width):
                uy, ux = self.vectors[y,x]
                h = (np.degrees(np.arctan2(uy,ux)) % 360) / 360
                s = 1.0
                v = self.magnitudes[y,x]
                hsv[y,x] = (int(h*255), int(s*255), int(v*255))
        return hsv

    def output_hsv_image(self):
        """
        Output an image where the hue and value of a given pixel indicates
        that pixel's direction and magnitude, respectively.
        """
        hsv = self.to_hsv_array()
        img = Image.fromarray(hsv, mode='HSV').convert('RGB')
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