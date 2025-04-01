import numpy as np
from PIL import Image, ImageOps
import cv2
import random
from vectorfield import Vector, VectorField

class ImageSmearer:
    def __init__(self, image: Image.Image):
        self.image = image.convert("RGB")
        self.array = np.array(self.image)
        self.height, self.width = self.array.shape[:2]


    def _direction_to_delta(self, direction: str):
        directions = {
            'right': (1, 0),
            'left': (-1, 0),
            'down': (0, 1),
            'up': (0, -1)
        }
        if direction not in directions:
            raise ValueError(f"Unknown direction: {direction}")
        return directions[direction]

    def _get_channel_key(self, channel: str):
        if channel == 'brightness':
            return lambda px: np.mean(px)
        elif channel == 'red':
            return lambda px: px[0]
        elif channel == 'green':
            return lambda px: px[1]
        elif channel == 'blue':
            return lambda px: px[2]
        else:
            raise ValueError(f"Invalid channel: {channel}")


    def _grayscale_mask(self, threshold):
        gray = np.array(ImageOps.grayscale(self.image))
        return (gray >= threshold[0]) & (gray <= threshold[1])

    def _channel_mask(self, channel, threshold):
        ch = self.array[:, :, channel]
        return (ch >= threshold[0]) & (ch <= threshold[1])

    def _hsv_mask(self, threshold):
        hsv = cv2.cvtColor(self.array, cv2.COLOR_RGB2HSV)
        v = hsv[:, :, 2]
        return (v >= threshold[0]) & (v <= threshold[1])

    def _edge_mask(self, threshold=(100, 255)):
        gray = cv2.cvtColor(self.array, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, threshold[0], threshold[1])
        return edges > 0



    """
    direction_smear: Smears pixels along a row using random horizontal/vertical offsets within a masked area.
    
    brightness_smear: Applies direction_smear to areas with brightness within a threshold range.
    
    red_smear: Applies direction_smear to areas where the red channel is within a threshold range.
    
    green_smear: Applies direction_smear to areas where the green channel is within a threshold range.
    
    blue_smear: Applies direction_smear to areas where the blue channel is within a threshold range.
    
    hsv_smear: Applies direction_smear to areas with specific brightness (V channel in HSV color space).
    
    edge_smear: Applies direction_smear to detected edges in the image, optionally inverting or dilating the edge mask.
    
    vector_field_smear: Smears pixels along custom directions defined by a vector field, optionally using a mask.
    """

    def direction_smear(self, mask, max_dx=30, max_dy=5):
        output = self.array.copy()
        for y in range(self.height):
            dy = random.randint(-max_dy, max_dy)
            dx = random.randint(5, max_dx)
            src_y = np.clip(y + dy, 0, self.height - 1)
            shifted_row = np.roll(self.array[src_y], dx, axis=0)
            for x in range(self.width):
                if mask[y, x]:
                    output[y, x] = shifted_row[x]
        return Image.fromarray(output)

    def brightness_smear(self, threshold=(50, 160), **kwargs):
        return self.direction_smear(self._grayscale_mask(threshold), **kwargs)

    def red_smear(self, threshold=(100, 255), **kwargs):
        return self.direction_smear(self._channel_mask(0, threshold), **kwargs)

    def green_smear(self, threshold=(100, 255), **kwargs):
        return self.direction_smear(self._channel_mask(1, threshold), **kwargs)

    def blue_smear(self, threshold=(100, 255), **kwargs):
        return self.direction_smear(self._channel_mask(2, threshold), **kwargs)

    def hsv_smear(self, threshold=(50, 160), **kwargs):
        return self.direction_smear(self._hsv_mask(threshold), **kwargs)

    def edge_smear(self, threshold=(100, 200), dilate_iter=1, invert=False, **kwargs):
        edge_raw = cv2.Canny(cv2.cvtColor(self.array, cv2.COLOR_RGB2GRAY), threshold[0], threshold[1])
        dilated = cv2.dilate(edge_raw, np.ones((3, 3), np.uint8), iterations=dilate_iter)
        mask = dilated > 0
        if invert:
            mask = ~mask
        return self.direction_smear(mask, **kwargs)

    def vector_field_smear(self, vector_field: VectorField, mask=None):
        output = self.array.copy()
        for y in range(self.height):
            for x in range(self.width):
                if mask is not None and not mask[y, x]:
                    continue
                vec = vector_field.get_vector(x, y)
                tx = int(np.clip(x + vec.x, 0, self.width - 1))
                ty = int(np.clip(y + vec.y, 0, self.height - 1))
                output[y, x] = self.array[ty, tx]
        return Image.fromarray(output)

    def pixel_smear(self, direction='right', mode='fixed', distance=15, channel='brightness', vector_field: VectorField = None):
        """
        Smear each pixel by replacing it with a pixel value from a specified direction or vector field.
        - mode: 'fixed', 'min', 'max'
        - direction: 'right', 'left', 'up', 'down' OR use a vector_field
        - distance: how far to look
        - channel: which value to compare if mode is min/max
        """
        output = self.array.copy()
        h, w = self.height, self.width
        use_vector_field = vector_field is not None
        key = self._get_channel_key(channel)

        if not use_vector_field:
            dx, dy = self._direction_to_delta(direction)

        for y in range(h):
            for x in range(w):
                pixels = []

                for i in range(1, distance + 1):
                    if use_vector_field:
                        vec = vector_field.get_vector(x, y)
                        tx = int(np.clip(x + vec.x * i, 0, w - 1))
                        ty = int(np.clip(y + vec.y * i, 0, h - 1))
                    else:
                        tx = np.clip(x + dx * i, 0, w - 1)
                        ty = np.clip(y + dy * i, 0, h - 1)

                    pixels.append(self.array[ty, tx])

                if mode == 'fixed':
                    chosen = pixels[-1]
                elif mode == 'min':
                    chosen = min(pixels, key=key)
                elif mode == 'max':
                    chosen = max(pixels, key=key)
                else:
                    raise ValueError("Invalid mode")

                output[y, x] = chosen

        return Image.fromarray(output)
