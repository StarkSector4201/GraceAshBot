import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

# Configuration
INPUT_FILE = "umbrella_wheel.png"
OUTPUT_DIR = "Avatar"
CENTER = (512, 513)  
RADIUS = 415         
FPS = 24
DURATION = 4.0      # Slightly longer for heavy 3D feel
TOTAL_FRAMES = int(FPS * DURATION)

# 3D Tilt Parameters (Perspective)
TILT_FACTOR = 0.85   # How much to squash vertically (perspective)
EXTRUSION_DEPTH = 15 # Pixels for the 3D rim

# Mapping categories to landing angles (degrees to rotate image)
LANDING_POS = 180  # Final landing point (bottom)

SLICE_CENTERS = {
    "reward": 180,   
    "run":     120,   
    "tvirus":   45,   
    "command": 315,   
    "fact":     255,   
}

def ease_out_cubic(t, b, c, d):
    t /= d
    t -= 1
    return c * (t**3 + 1) + b

def generate_3d_frames(category):
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return
    
    img = Image.open(INPUT_FILE).convert("RGBA")
    w, h = img.size
    
    # --- 1. Isolate the Wheel ---
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((CENTER[0]-RADIUS, CENTER[1]-RADIUS, CENTER[0]+RADIUS, CENTER[1]+RADIUS), fill=255)
    
    wheel_source = Image.new("RGBA", (w, h), (0,0,0,0))
    wheel_source.paste(img, (0,0), mask=mask)
    wheel_source = wheel_source.crop((CENTER[0]-RADIUS, CENTER[1]-RADIUS, CENTER[0]+RADIUS, CENTER[1]+RADIUS))
    
    # --- 2. Prepare Background ---
    # Create a slightly blurred, darkened version of the original for atmosphere
    bg = img.copy()
    bg = ImageEnhance.Brightness(bg).enhance(0.4)
    bg = bg.filter(ImageFilter.GaussianBlur(5))
    
    # --- 3. Create a Gloss Layer (Static lighting) ---
    gloss = Image.new("RGBA", (RADIUS*2, RADIUS*2), (0,0,0,0))
    gloss_draw = ImageDraw.Draw(gloss)
    # A soft white sweep across the top left
    gloss_draw.ellipse((20, 20, RADIUS*1.2, RADIUS*1.2), fill=(255, 255, 255, 40))
    gloss = gloss.filter(ImageFilter.GaussianBlur(30))

    target_slice_angle = SLICE_CENTERS.get(category, 180)
    final_offset = (LANDING_POS - target_slice_angle) % 360
    total_rotation = (360 * 5) + final_offset
    
    frames = []
    
    print(f"🎬 Rendering Manual 3D Animation for {category}...")
    
    # Canvas size for the tilted wheel
    canvas_size = (int(RADIUS * 2.2), int(RADIUS * 2.2))
    
    for f in range(TOTAL_FRAMES):
        angle = ease_out_cubic(f, 0, total_rotation, TOTAL_FRAMES)
        
        # Rotate the wheel texture
        rot_wheel = wheel_source.rotate(-angle, resample=Image.BICUBIC)
        
        # Add gloss (static overlay)
        rot_wheel.alpha_composite(gloss)
        
        # Apply 3D Perspective Tilt (Vertical Squash)
        # We squash the height and perspective the bottom slightly wider
        tilted_h = int(rot_wheel.height * TILT_FACTOR)
        tilted_wheel = rot_wheel.resize((rot_wheel.width, tilted_h), Image.LANCZOS)
        
        # Composite layers for EXTRUSION (depth)
        # We draw the wheel several times shifted down to create a rim
        final_frame = bg.copy()
        
        # Render the 'rim' (darkened extrusion)
        rim_color = ImageEnhance.Brightness(tilted_wheel).enhance(0.3)
        render_pos = (int(CENTER[0] - RADIUS), int(CENTER[1] - (tilted_h//2)))
        
        for d in range(EXTRUSION_DEPTH, 0, -1):
            final_frame.alpha_composite(rim_color, (render_pos[0], render_pos[1] + d))
            
        # Place the interactive face
        final_frame.alpha_composite(tilted_wheel, render_pos)
        
        # Add a subtle shadow underneath
        # (This is a simplified approach)
        
        frames.append(final_frame.convert("RGB"))
        
        if f % 10 == 0:
            print(f"  > Progress: {int(f/TOTAL_FRAMES*100)}%")

    output_path = os.path.join(OUTPUT_DIR, f"umbrella_spin_{category}.mp4")
    
    try:
        import imageio
        writer = imageio.get_writer(output_path, fps=FPS, codec='libx264', quality=8)
        for frame in frames:
            writer.append_data(np.array(frame))
        writer.close()
        print(f"✅ Saved 3D animation: {output_path}")
    except Exception as e:
        print(f"⚠️ Video encoding failed: {e}. Saving as GIF fallback.")
        output_path = os.path.join(OUTPUT_DIR, f"umbrella_spin_{category}.gif")
        frames[0].save(output_path, save_all=True, append_images=frames[1:], duration=1000/FPS, loop=0)

if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    categories = ["command", "tvirus", "run", "reward", "fact"]
    for cat in categories:
        generate_3d_frames(cat)
    print("\n🎉 Manual 3D Generation Complete.")
