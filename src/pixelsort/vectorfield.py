import numpy as np
from PIL import Image, ImageDraw
import colorsys
import cv2 as cv

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

    def save(self, file_path, write_image: bool = False):
        """
        Saves the current vector field to a .npz file.
        The file can be loaded in with the load() function

        @param file_path: The output directory to save the file, without the extension
        @param write_image: If true, writes the HSV image representation to [fileName].png
        """
        np.savez(file_path + ".npz", 
                 vectors = self.vectors, 
                 magnitudes = self.magnitudes)
        if(write_image):
            # hsv = self.to_hsv_array()
            #img = Image.fromarray(hsv, mode='HSV').convert('RGB')
            img = self.output_arrow_image(show_image=False,hue=False)
            img.save(file_path + ".png")

    def load(self,file_path):
        """
        Loads in the specified .npz file, replacing the contents of self
        in the process.

        @param filePath: The full path of the .npz file, including the extension.
        """
        data = np.load(file_path)
        self.vectors = data["vectors"]
        self.magnitudes = data["magnitudes"]
        self.height, self.width = data["vectors"].shape[:2]

    def resize(self, new_height, new_width):
        """
        Resizes the vector field to be of the desired height and width.
        """
        uy = self.vectors[:,:,0]
        ux = self.vectors[:,:,1]
        uy2 = cv.resize(uy, (new_width,new_height), interpolation=cv.INTER_CUBIC)
        ux2 = cv.resize(ux, (new_width,new_height), interpolation=cv.INTER_CUBIC)
        m2 = cv.resize(self.magnitudes, (new_width,new_height), interpolation=cv.INTER_CUBIC)

        # TODO: see if vectors and magnitudes need be normalized/clamped

        vectors2 = np.stack((uy2,ux2), axis=-1).astype(np.float32)
        magnitudes2 = m2.astype(np.float32)
        self.vectors = vectors2
        self.magnitudes = magnitudes2
        self.height = new_height
        self.width = new_width
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


# -------- TRANSFORMATIONS -------------#


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

    def move_towards_point(self,point,falloff):
        """
        Pull all vector endpoints within the radius to (y,x)
        """
        (target_y, target_x) = point
        def towards_target(y,x,vector,mag):
            dy = target_y - y
            dx = target_x - x
            dist = np.hypot(dx,dy)
            if(dist == 0):
                return Vector(0,0), 0
            m = max(0.0, dist / falloff)
            return Vector(dy,dx), m
        self.apply_operation(towards_target)

    def move_away_from_point(self,point,falloff):
        """
        Push all vector endpoints within the radius from (y,x)
        """
        (target_y, target_x) = point
        def away(y,x,vector,mag):
            dy = target_y - y
            dx = target_x - x
            dist = np.hypot(dx,dy)
            if(dist == 0):
                return Vector(0,0), 0
            m = max(0.0, 1 - dist / falloff)
            return Vector(-dy,-dx), m
        self.apply_operation(away)

    def spiral_transform(self,center):
        phi = (1 + np.sqrt(5))/2
        b = np.log(phi) / (np.pi/2)
        target_x, target_y = center
        def spiral(y, x, vector, mag):
            dy = target_y - y
            dx = target_x - x
            theta = np.arctan2(dy,dx)
            tx = b * np.cos(theta) - np.sin(theta)
            ty = b * np.sin(theta) + np.cos(theta)
            norm = np.hypot(ty,tx)
            if(norm > 0):
                ty /= norm
                tx /= norm
            m = 1
            return Vector(ty,tx), m
        self.apply_operation(spiral)

    def chaotic_spiral_transform(self, point, radius, spiral_strength=0.01):
        (target_y, target_x) = point
        def turn(y,x,vector,mag):
            dx = x - target_x
            dy = y - target_y
            angle = np.arctan2(dy,dx)
            angle += spiral_strength*np.sqrt(dx**2 + dy**2)
            magnitude = np.exp(-((dx**2 + dy**2) / radius**2))
            return Vector(np.sin(angle),np.cos(angle)), magnitude
        self.apply_operation(turn)

    def wave_transform(self, freq, amplitude):
        """
        Make every column of vectors in the field
        follow the same sine wave tangents
        """
        def waves(y,x,vector,mag):
            slope = amplitude * freq * np.cos(freq * x)
            norm = np.hypot(1.0,slope)
            dy = slope / norm
            dx = 1.0 / norm
            m = 1
            return Vector(dy,dx), m
        self.apply_operation(waves)

    def orbit_transform(self, center=None, clockwise=False):
        if(center is None):
            target_y = self.height / 2
            target_x = self.width / 2
        else:
            target_y, target_x = center
        max_dist = np.hypot(max(target_y, self.height - target_y), max(target_x, self.width - target_x))
        def orbit(y,x,vector,mag):
            dy = target_y - y
            dx = target_x - x
            dist = np.hypot(dy,dx)
            if dist == 0:
                return Vector(0.0,0.0), 0.0
            # tangent direction to the vector to mid:
            # ccw: (-dx, +dy) cw: (+dx, - y)
            if clockwise:
                ny, nx = dx, -dy
            else:
                ny, nx = -dx, dy
            nm = dist / max_dist
            return Vector(ny,nx), nm
        self.apply_operation(orbit)

    
# -------- VISUALIZATIONS -------------#


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
        return img

    def output_arrow_image(self, show_image=True, hue=True, stride=16, line_length=16, base_width=4, tip_width=0):
        """
        Output an image with arrows placed in a sparse grid that indicate
        the magnitude and direction at that point in the field.

        @param show_image: if true, displays the image when finished rendering
        @param hue: if true, paints each arrow its relevant hue value. false=white
        @param stride: the interval in pixels between arrows
        @param line_length: the maximum length of an arrow (scaled with magnitude)
        @param base_width: the maximum base width of an arrrow
        @param tip_width: the maximum tip width of an arrow
        """
        if(hue):
            hsv = self.to_hsv_array()
        img = Image.new('RGB',(self.width,self.height))
        draw = ImageDraw.Draw(img)

        # from https://stackoverflow.com/a/24852375
        def hsv2rgb(h,s,v):
            return tuple(int(round(i * 255)) for i in colorsys.hsv_to_rgb(h/255,s/255,v/255))

        for y in range(0, self.height, stride):
            for x in range(0, self.width, stride):
                vy, vx = self.vectors[y,x]
                m = self.magnitudes[y,x]
                if m <= 0:
                    continue
                length = m * line_length
                x0, y0 = x, y
                x1 = x0 + vx * length
                y1 = y0 + vy * length

                d_norm = np.hypot(vx, vy)
                if d_norm == 0:
                    continue
                ux = vx / d_norm
                uy = vy / d_norm
                px, py = -uy, ux

                wb = base_width / 2.0
                wt = tip_width / 2.0

                base_left = (x0 + px*wb, y0 + py*wb)
                base_right = (x0 - px*wb, y0 - py*wb)
                tip_left = (x1 + px*wt, y1 + py*wt)
                tip_right = (x1 - px*wt, y1 - py*wt) # at tip_width 0 these two are the same
                poly = [base_left, base_right, tip_right, tip_left]

                if(hue):
                    color = hsv2rgb(hsv[y,x,0],hsv[y,x,1],hsv[y,x,2])
                else:
                    color = 'white'
                draw.polygon(poly,fill=color)
        img.show()
        return img

    def __repr__(self):
        return f"VectorField(width={self.width}, height={self.height})"