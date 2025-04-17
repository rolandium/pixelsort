import numpy as np
from math import sin
from PIL import Image
from PIL import ImageOps
class PixelSmear:
    #initialize threshold (70, 100) and num_step = 10
    def __init__(self, img_path, out_path, mask_path=None, threshold=(70, 100), num_steps=10):
        self.img_path = img_path
        self.out_path = out_path
        self.mask_path = mask_path
        self.threshold = threshold
        self.num_steps = num_steps

        self.image = Image.open(img_path).convert("RGB")
        self.image_np = np.array(self.image)
        self.height, self.width = self.image_np.shape[:2]

        self.positions = np.full((self.num_steps, self.height, self.width, 2), fill_value=np.nan, dtype=np.float32)
        self.colors = np.zeros((self.num_steps, self.height, self.width, 3), dtype=np.float32)
        self.accum_color = np.zeros((self.height, self.width, 4), dtype=np.float32)
        self.accum_weight = np.zeros((self.height, self.width), dtype=np.float32)

    def getValue(self, pixel):
        # assuming R G B
        r, g, b = pixel
        return 0.299 * r + 0.587 * g + 0.114 * b

    #generate a mask base on the image
    def generate_mask(self):
        greyscale = np.array(ImageOps.grayscale(self.image))
        self.mask = (greyscale >= self.threshold[0]) & (greyscale <= self.threshold[1])
        if self.mask_path:
            mask_im = Image.fromarray((self.mask * 255).astype(np.uint8))
            mask_im.save(self.mask_path)
            mask_im.show()

    # given a subpixel position, apply the colour of that subpixel position to surrounding real pixels
    # accumulates weights to each pixel as time goes on
    # which will need to be normalized when outputting a real image
    def accumulate_bilinear(self, pos, color, weight=1.0):
        h, w = self.accum_color.shape[:2]
        y, x = pos
        if np.isnan(y) or np.isnan(x):
            return

        eps = 1e-6
        x = np.clip(x, 0, w - 1 - eps)
        y = np.clip(y, 0, h - 1 - eps)

        y0, x0 = int(np.floor(y)), int(np.floor(x))
        y1, x1 = min(y0 + 1, h - 1), min(x0 + 1, w - 1)
        dy, dx = y - y0, x - x0

        w00 = (1 - dx) * (1 - dy)
        w01 = dx * (1 - dy)
        w10 = (1 - dx) * dy
        w11 = dx * dy

        self.accum_color[y0, x0] += color * w00 * weight
        self.accum_color[y0, x1] += color * w01 * weight
        self.accum_color[y1, x0] += color * w10 * weight
        self.accum_color[y1, x1] += color * w11 * weight

        self.accum_weight[y0, x0] += w00 * weight
        self.accum_weight[y0, x1] += w01 * weight
        self.accum_weight[y1, x0] += w10 * weight
        self.accum_weight[y1, x1] += w11 * weight

    def warp_positions(self, mask):
        for y in range(self.height):
            for x in range(self.width):
                if self.mask[y, x]:
                    self.positions[0, y, x] = [y, x]

        for t in range(1, self.num_steps):
            print(f"warping: t={t + 1}/{self.num_steps}", end='\r', flush=True)
            for y in range(self.height):
                for x in range(self.width):
                    prev_pos = self.positions[t - 1, y, x]
                    if np.isnan(prev_pos[0]) or np.isnan(prev_pos[1]):
                        continue  # ignore pixel
                    # rate of change
                    # i.e a line defined by y = mx+b
                    # will need its derivative
                    dx = 1
                    dy = 2 * t / 5
                    new_pos = prev_pos + np.array([dy, dx])
                    self.positions[t, y, x] = new_pos

    # color smear step
    def smear_colors(self):
        for y in range(self.height):
            print(f"smearing: y={y}/{self.height}", end='\r', flush=True)
            for x in range(self.width):
                if np.any(np.isnan(self.positions[0, y, x])):
                    continue
                min_col = self.image_np[y, x]
                max_col = self.image_np[y, x]
                for t in range(1, self.num_steps):
                    pos = self.positions[t, y, x]
                    # eps = 1e-6
                    # pos_y = np.clip(pos[0], 0, height - 1 - eps)
                    # pos_x = np.clip(pos[1], 0, width - 1 - eps)
                    # y0 = int(np.floor(pos_y))
                    # x0 = int(np.floor(pos_x))
                    # pixel = image_np[y0, x0]

                    # Instead of finding the nearest floor pixel, find the pixel round it
                    h, w = self.image_np.shape[:2]
                    eps = 1e-6
                    pos_y = np.clip(pos[0], 0, self.height - 1 - eps)
                    pos_x = np.clip(pos[1], 0, self.width - 1 - eps)
                    pos_y0 = int(np.floor(pos_y))
                    pos_x0 = int(np.floor(pos_x))
                    pos_y1 = min(pos_y0 + 1, h - 1)
                    pos_x1 = min(pos_x0 + 1, w - 1)
                    pos_dy = pos_y - pos_y0
                    pos_dx = pos_x - pos_x0
                    top_pixels = (1 - pos_dx) * self.image_np[pos_y0, pos_x0] + pos_dx * self.image_np[pos_y0, pos_x1]
                    bottom_pixels = (1 - pos_dx) * self.image_np[pos_y1, pos_x0] + pos_dx * self.image_np[pos_y1, pos_x1]
                    pixel = (1 - pos_dy) * bottom_pixels + pos_dy * top_pixels
                    if (self.getValue(min_col) > self.getValue(pixel)):
                        min_col = pixel
                    if (self.getValue(max_col) < self.getValue(pixel)):
                        max_col = pixel
                # min and max colours are populated, apply gradient through all of t
                for t in range(self.num_steps):
                    # linear interpolation
                    self.colors[t, y, x] = min_col + (max_col - min_col) * (t / self.num_steps)

    # rendering step, using rgba for transparency
    def render(self):
        for t in range(self.num_steps - 1):
            for y in range(self.height):
                for x in range(self.width):
                    pos1 = self.positions[t, y, x]
                    if np.isnan(pos1[0]) or np.isnan(pos1[1]):
                        continue
                    pos2 = self.positions[t + 1, y, x]
                    rgb = self.colors[t, y, x]
                    rgba = np.array([*rgb, 1.0], dtype=np.float32)
                    length = np.linalg.norm(pos2 - pos1)
                    num_samples = max(1, int(np.ceil(length)))
                    for i in range(num_samples + 1):
                        j = i / num_samples
                        pos = pos1 * (1 - j) + pos2 * j
                        self.accumulate_bilinear(pos, rgba, weight=1.0 / (self.num_steps - 1))

        canvas = np.zeros_like(self.accum_color)
        for y in range(self.height):
            for x in range(self.width):
                if self.accum_weight[y, x] > 0:
                    canvas[y, x] = self.accum_color[y, x] / self.accum_weight[y, x]
        # todo: render inbetweens, save to local data structure
        # in the form of np.ndarray (timestep x (width height, 3 {rgb}))
        # will need to put the normalization routine in here instead.
        # final output will be the end of the output "block"

        # normalize the accumulated weights
        canvas[..., :3] = np.clip(canvas[..., :3], 0, 255)
        canvas[..., 3] = np.clip(canvas[..., 3], 0, 1) * 255
        out = canvas.astype(np.uint8)
        out_im = Image.fromarray(out, mode="RGBA")
        out_im.show()
        out_im.save(self.out_path)

    #run Pixelsmear
    def run(self):
        mask = self.generate_mask()
        self.warp_positions(mask)
        self.smear_colors()
        self.render()


if __name__ == "__main__":
    smear = PixelSmear(
        img_path="/Users/yizhoulu/Documents/GitHub/pixelsort/src/pixelsort/lenna.png",
        out_path="/Users/yizhoulu/Documents/GitHub/pixelsort/src/pixelsort/out.png",
        mask_path="/Users/yizhoulu/Documents/GitHub/pixelsort/src/pixelsort/mask.png",
        threshold=(70, 100),
        num_steps=10
    )
    smear.run()