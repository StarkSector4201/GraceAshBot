import os
import sys
import numpy as np
from PIL import Image, ImageDraw

# Configuration
INPUT_FILE = "umbrella_wheel.png"
OUTPUT_DIR = "Avatar"
CENTER = (512, 513)  # Approximate center of the wheel in 1024x1024
RADIUS = 415         # Radius of the interactive part
FPS = 24
DURATION = 3.5       # total seconds
TOTAL_FRAMES = int(FPS * DURATION)

# Mapping categories to landing angles (degrees to rotate image)
# Based on visual analysis:
# REWARD is bottom (~0° offset to land at bottom)
# RUN is ~4 o'clock (~300° of rotation needed to bring it to bottom?)
# Wait, let's simplify. I will define the CURRENT center angle of each slice.
# Then RotationNeeded = (DesiredLandingAngle - CurrentSliceAngle)
LANDING_POS = 180  # We want the slice to end at the bottom (180 degrees in PIL)

# Measured angles of slice centers in the original image (0° at top, clockwise)
SLICE_CENTERS = {
    "reward": 180,   # Already at bottom
    "run":     120,   # Lower right
    "tvirus":   45,   # Upper right
    "command": 315,   # Upper left
    "fact":     255,   # Left
}

def generate_frames(category):
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found. Please save the image to the root directory.")
        return
    
    img = Image.open(INPUT_FILE).convert("RGBA")
    w, h = img.size
    
    # Create mask for the wheel
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((CENTER[0]-RADIUS, CENTER[1]-RADIUS, CENTER[0]+RADIUS, CENTER[1]+RADIUS), fill=255)
    
    # Extract wheel and background
    wheel = Image.new("RGBA", (w, h), (0,0,0,0))
    wheel.paste(img, (0,0), mask=mask)
    
    bg = img.copy()
    bg.paste((0,0,0,0), (0,0), mask=mask) # Clear wheel area from BG
    
    target_slice_angle = SLICE_CENTERS.get(category, 180)
    # Total rotation: several full spins + landing offset
    # Initial speed: fast. Friction: gradual stop.
    
    # We want final_rotation % 360 == (LANDING_POS - target_slice_angle) % 360
    final_offset = (LANDING_POS - target_slice_angle) % 360
    total_rotation = 360 * 4 + final_offset # 4 full spins then land
    
    frames = []
    
    # Ease out cubic interpolation for smooth stop
    # t: current frame, b: start val, c: change in val, d: duration
    def ease_out_cubic(t, b, c, d):
        t /= d
        t -= 1
        return c * (t**3 + 1) + b

    print(f"Generating animation for {category}...")
    
    for f in range(TOTAL_FRAMES):
        angle = ease_out_cubic(f, 0, total_rotation, TOTAL_FRAMES)
        
        # Rotate wheel (negative because PIL rotates counter-clockwise, we want clockwise feel)
        rotated_wheel = wheel.rotate(-angle, resample=Image.BICUBIC, center=CENTER)
        
        # Merge
        frame = bg.copy()
        frame.alpha_composite(rotated_wheel)
        frames.append(frame.convert("RGB")) # Convert to RGB for MP4/GIF compatibility
        
    output_path = os.path.join(OUTPUT_DIR, f"umbrella_spin_{category}.mp4")
    
    try:
        import imageio
        writer = imageio.get_writer(output_path, fps=FPS, codec='libx264', quality=8)
        for frame in frames:
            writer.append_data(np.array(frame))
        writer.close()
        print(f"Successfully saved {output_path}")
    except ImportError:
        # Fallback to GIF if imageio is not present or configured for video
        output_path = os.path.join(OUTPUT_DIR, f"umbrella_spin_{category}.gif")
        frames[0].save(output_path, save_all=True, append_images=frames[1:], duration=1000/FPS, loop=0)
        print(f"Saved as GIF (imageio libx264 failed or missing): {output_path}")

if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    categories = ["command", "tvirus", "run", "reward", "fact"]
    for cat in categories:
        generate_frames(cat)
