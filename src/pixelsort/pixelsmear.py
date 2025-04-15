import numpy as np
from PIL import Image
from PIL import ImageOps

THRESHOLD = (70,100)

IMG_PATH = r"C:\Users\roland\Desktop\cmpt461\pixelsort\src\pixelsort\mountains.png"
MASK_PATH = r"C:\Users\roland\Desktop\cmpt461\pixelsort\results\mask.png"
OUT_PATH = r"C:\Users\roland\Desktop\cmpt461\pixelsort\results\out.png"

def getValue(pixel):
    # assuming R G B
    r, g, b = pixel
    return 0.299 * r + 0.587 * g + 0.114 * b

# given a subpixel position, apply the colour of that subpixel position to surrounding real pixels
# accumulates weights to each pixel as time goes on
# which will need to be normalized when outputting a real image
def accumulate_bilinear(accum_color, accum_weight,pos,color,weight=1.0):
    h, w = accum_color.shape[:2]
    y, x = pos
    if np.isnan(y) or np.isnan(x):
        return
    
    eps = 1e-6
    x = np.clip(x, 0, w - 1 - eps)
    y = np.clip(y, 0, h - 1 - eps)

    y0 = int(np.floor(y))
    x0 = int(np.floor(x))

    y1 = min(y0+1,h-1)
    x1 = min(x0+1,w-1)

    dy = y - y0
    dx = x - x0

    w00 = (1 - dx) * (1 - dy)
    w01 = dx * (1 - dy)
    w10 = (1 - dx) * dy
    w11 = dx * dy

    accum_color[y0,x0] += color * w00 * weight
    accum_color[y0,x1] += color * w01 * weight
    accum_color[y1,x0] += color * w10 * weight
    accum_color[y1,x1] += color * w11 * weight

    accum_weight[y0,x0] += w00 * weight
    accum_weight[y0,x1] += w01 * weight
    accum_weight[y1,x0] += w10 * weight
    accum_weight[y1,x1] += w11 * weight
    
def main():
    image = Image.open(IMG_PATH).convert("RGB")
    image_np = np.array(image)
    height, width = image_np.shape[:2]
    num_steps = 10

    # a NaN position indicates pixel to ignore
    positions = np.full((num_steps,height,width,2),fill_value=np.nan,dtype=np.float32)
    colors = np.zeros((num_steps,height,width,3), dtype=np.float32)
    
    # mask for pixel line starting positions
    greyscale = np.array(ImageOps.grayscale(image))
    mask = (greyscale >= THRESHOLD[0]) & (greyscale <= THRESHOLD[1])
    mask_im = Image.fromarray((mask*255).astype(np.uint8))
    mask_im.save(MASK_PATH)
    mask_im.show()

    # set initial vals only the pixels inside the threshold
    for y in range(height):
        for x in range(width):
            if mask[y,x]:
                positions[0,y,x] = [y,x]

    # warping step
    for t in range(1, num_steps):
        print(f"warping: t={t+1}/{num_steps}", end='\r', flush=True)
        for y in range(height):
            for x in range(width):
                prev_pos = positions[t-1,y,x]
                if np.isnan(prev_pos[0]) or np.isnan(prev_pos[1]):
                    continue # ignore pixel
                dx = t
                dy = -t
                new_pos = prev_pos + np.array([dy,dx])
                positions[t,y,x] = new_pos

    # color smear step
    for y in range(height):
        print(f"smearing: y={y}/{height}", end='\r', flush=True)
        for x in range(width):
            if np.any(np.isnan(positions[0,y,x])):
                continue
            min_col = image_np[y,x]
            max_col = image_np[y,x]
            for t in range(1, num_steps):
                pos = positions[t,y,x]
                eps = 1e-6
                pos_y = np.clip(pos[0], 0, height - 1 - eps)
                pos_x = np.clip(pos[1], 0, width  - 1 - eps)
                y0 = int(np.floor(pos_y))
                x0 = int(np.floor(pos_x))
                pixel = image_np[y0, x0]
                if(getValue(min_col) > getValue(pixel)):
                    min_col = pixel
                if(getValue(max_col) < getValue(pixel)):
                    max_col = pixel
            # min and max colours are populated, apply gradient through all of t
            for t in range(num_steps):
                # linear interpolation
                colors[t,y,x] = min_col + (max_col-min_col) * (t/num_steps)
                


    # rendering step, using rgba for transparency
    accum_color = np.zeros((height,width,4), dtype=np.float32)
    accum_weight = np.zeros((height,width), dtype=np.float32)
    for t in range(num_steps - 1):
        print(f"rendering: t={t+1}/{num_steps}", end='\r', flush=True)
        for y in range(height):
            for x in range(width):
                pos1 = positions[t,y,x]
                if np.isnan(pos1[0]) or np.isnan(pos1[1]):
                    continue
                pos2 = positions[t+1,y,x]
                
                rgb = colors[t,y,x]
                rgba = np.array([rgb[0],rgb[1],rgb[2],255], dtype=np.float32)      

                line_length = np.linalg.norm(pos2-pos1)
                num_samples = max(1, int(np.ceil(line_length)))
                for i in range(num_samples + 1):
                    j = i / num_samples
                    pos = pos1 * (1 - j) + pos2 * j
                    accumulate_bilinear(accum_color,accum_weight, pos, rgba, weight=1.0/(num_steps-1))

    # normalize the accumulated weights
    canvas = np.zeros_like(accum_color)
    for y in range(height):
        for x in range(width):
            if accum_weight[y,x] > 0:
                canvas[y,x] = accum_color[y,x] / accum_weight[y,x]

    out = np.clip(canvas,0,255).astype(np.uint8)
    out_im = Image.fromarray(out,mode="RGBA")
    out_im.show()
    out_im.save(OUT_PATH)

    pass

if __name__ == "__main__":
    main()