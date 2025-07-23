#!/usr/bin/env python3
"""
Cross-platform icon generator for BOQ Processor
Creates icons for Windows (.ico), macOS (.icns), and Linux (.png)
"""

import os
import sys
from pathlib import Path
import platform

def create_boq_icon(size=512):
    """Create a BOQ-themed icon"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("❌ PIL (Pillow) not found. Installing...")
        os.system(f"{sys.executable} -m pip install Pillow")
        from PIL import Image, ImageDraw, ImageFont
    
    # Create image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Colors - professional blue and green theme
    bg_color = (41, 128, 185)      # Professional blue
    accent_color = (46, 204, 113)   # Success green
    text_color = (255, 255, 255)   # White text
    
    # Draw background circle
    margin = size // 16
    draw.ellipse([margin, margin, size-margin, size-margin], 
                fill=bg_color, outline=accent_color, width=size//32)
    
    # Try to use a font (fallback to default if not available)
    try:
        # Try different font paths for different OS
        font_paths = [
            "/System/Library/Fonts/Arial.ttf",  # macOS
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
            "C:/Windows/Fonts/arial.ttf",  # Windows
            "/usr/share/fonts/TTF/arial.ttf",  # Some Linux
        ]
        
        font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, size//8)
                break
        
        if font is None:
            font = ImageFont.load_default()
            
    except:
        font = ImageFont.load_default()
    
    # Draw "BOQ" text
    text = "BOQ"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    text_x = (size - text_width) // 2
    text_y = (size - text_height) // 2 - size // 16
    
    # Draw text with shadow effect
    shadow_offset = size // 64
    draw.text((text_x + shadow_offset, text_y + shadow_offset), text, 
              font=font, fill=(0, 0, 0, 128))  # Shadow
    draw.text((text_x, text_y), text, font=font, fill=text_color)
    
    # Draw small "Processor" text below
    small_text = "PROCESSOR"
    try:
        small_font = ImageFont.truetype(font_paths[0] if font_paths else "", size//20)
    except:
        small_font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), small_text, font=small_font)
    small_text_width = bbox[2] - bbox[0]
    small_text_x = (size - small_text_width) // 2
    small_text_y = text_y + text_height + size // 32
    
    draw.text((small_text_x, small_text_y), small_text, 
              font=small_font, fill=accent_color)
    
    # Draw decorative elements (spreadsheet grid)
    grid_size = size // 16
    grid_start_x = size // 4
    grid_start_y = size - size // 3
    grid_color = (255, 255, 255, 100)
    
    # Draw mini spreadsheet grid
    for i in range(3):
        for j in range(4):
            x = grid_start_x + j * grid_size // 2
            y = grid_start_y + i * grid_size // 3
            draw.rectangle([x, y, x + grid_size//3, y + grid_size//4], 
                         outline=grid_color, width=1)
    
    return img

def create_windows_ico(base_image, output_path):
    """Create Windows .ico file with multiple sizes"""
    from PIL import Image
    
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    
    for size in sizes:
        resized = base_image.resize((size, size), Image.Resampling.LANCZOS)
        images.append(resized)
    
    # Save as ICO
    images[0].save(output_path, format='ICO', sizes=[(img.width, img.height) for img in images])
    print(f"✅ Created Windows icon: {output_path}")

def create_macos_icns(base_image, output_path):
    """Create macOS .icns file"""
    from PIL import Image
    import shutil
    
    try:
        # For macOS icns, we need the iconutil command or use a library
        # First, create PNG files at various sizes
        sizes = [16, 32, 128, 256, 512, 1024]
        temp_dir = Path("temp_iconset")
        temp_dir.mkdir(exist_ok=True)
        
        for size in sizes:
            resized = base_image.resize((size, size), Image.Resampling.LANCZOS)
            if size <= 32:
                resized.save(temp_dir / f"icon_{size}x{size}.png")
                # Also create @2x versions for retina
                resized_2x = base_image.resize((size*2, size*2), Image.Resampling.LANCZOS)
                resized_2x.save(temp_dir / f"icon_{size}x{size}@2x.png")
            else:
                resized.save(temp_dir / f"icon_{size}x{size}.png")
        
        # Try to create ICNS using iconutil (macOS only)
        if platform.system() == "Darwin":
            iconset_dir = temp_dir.with_suffix('.iconset')
            iconset_dir.mkdir(exist_ok=True)
            
            # Move files to iconset structure
            for png_file in temp_dir.glob("*.png"):
                new_name = png_file.name.replace("icon_", "icon_").replace(".png", ".png")
                (iconset_dir / new_name).write_bytes(png_file.read_bytes())
            
            # Create ICNS
            os.system(f"iconutil -c icns {iconset_dir} -o {output_path}")
            
            # Cleanup
            shutil.rmtree(temp_dir)
            shutil.rmtree(iconset_dir)
        else:
            # Fallback: save largest PNG as "icns" (some tools accept this)
            largest = base_image.resize((1024, 1024), Image.Resampling.LANCZOS)
            largest.save(output_path.with_suffix('.png'))
            print(f"⚠️  Created PNG instead of ICNS (iconutil not available): {output_path.with_suffix('.png')}")
            return
            
        print(f"✅ Created macOS icon: {output_path}")
        
    except Exception as e:
        print(f"⚠️  Could not create ICNS, creating PNG instead: {e}")
        # Fallback to PNG
        png_path = output_path.with_suffix('.png')
        base_image.save(png_path)
        print(f"✅ Created PNG fallback: {png_path}")

def create_linux_png(base_image, output_path):
    """Create Linux PNG icon"""
    from PIL import Image
    
    # Create multiple sizes for Linux
    sizes = [48, 64, 128, 256, 512]
    
    for size in sizes:
        resized = base_image.resize((size, size), Image.Resampling.LANCZOS)
        size_path = output_path.parent / f"icon_{size}.png"
        resized.save(size_path)
        print(f"✅ Created Linux icon: {size_path}")
    
    # Also save the main icon
    base_image.save(output_path)
    print(f"✅ Created main Linux icon: {output_path}")

def main():
    """Generate icons for all platforms"""
    print("🎨 Generating BOQ Processor icons for all platforms...")
    print("")
    
    # Create base icon
    print("🖼️  Creating base icon design...")
    base_icon = create_boq_icon(512)
    
    # Create platform-specific icons
    current_dir = Path(__file__).parent
    
    # Windows ICO
    print("\n🪟 Creating Windows icon...")
    ico_path = current_dir / "icon.ico"
    create_windows_ico(base_icon, ico_path)
    
    # macOS ICNS  
    print("\n🍎 Creating macOS icon...")
    icns_path = current_dir / "icon.icns"
    create_macos_icns(base_icon, icns_path)
    
    # Linux PNG
    print("\n🐧 Creating Linux icons...")
    png_path = current_dir / "icon.png"
    create_linux_png(base_icon, png_path)
    
    print(f"\n🎉 Icon generation complete!")
    print(f"📁 Icons created in: {current_dir}")
    print(f"   - Windows: icon.ico")
    print(f"   - macOS: icon.icns (or icon.png if iconutil unavailable)")
    print(f"   - Linux: icon.png + multiple sizes")
    print("")
    print("These icons will be automatically used by packaging tools.")

if __name__ == "__main__":
    main()