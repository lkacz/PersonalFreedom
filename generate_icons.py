#!/usr/bin/env python3
"""
Generate industry-standard icons for Personal Liberty app.

Creates:
- app.ico - Main application icon with multiple sizes (16, 24, 32, 48, 64, 128, 256)
- tray_ready.png/ico - System tray icon (ready/idle state)
- tray_blocking.png/ico - System tray icon (active blocking state)

Design: Modern shield icon with "liberty torch" or "focused mind" motif
- Clean, bold silhouette that reads well at all sizes
- Premium gradients and lighting effects
- Distinctive enough to be recognized instantly
"""

from PIL import Image, ImageDraw, ImageFilter
import math
from pathlib import Path


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: tuple) -> str:
    """Convert RGB tuple to hex string."""
    return '#{:02x}{:02x}{:02x}'.format(*rgb[:3])


def lerp_color(color1: str, color2: str, t: float) -> str:
    """Linearly interpolate between two colors."""
    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return rgb_to_hex((r, g, b))


def create_focus_icon(size: int, blocking: bool = False, for_tray: bool = False) -> Image.Image:
    """
    Create a modern, distinctive app icon.
    
    Design: Shield shape with an upward-pointing stylized "flame" or "focus beam"
    representing liberation, focus, and protection from distractions.
    
    The design uses:
    - Bold shield silhouette (protection/blocking)
    - Central upward element (growth/freedom/focus)
    - Modern gradient with rim lighting
    - Clean geometry that scales well
    """
    # Create RGBA image
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center = size // 2
    
    # Color palettes - STRONG gradient for premium look
    if blocking:
        # Active blocking - Electric blue/cyan with strong gradient
        bg_gradient_top = '#38BDF8'     # Bright sky blue (lighter top)
        bg_gradient_bottom = '#0C4A6E'  # Very deep navy (darker bottom)
        inner_glow = '#38BDF8'          # Bright cyan
        symbol_color = '#FFFFFF'         # Pure white
        symbol_glow = '#7DD3FC'          # Light cyan
        rim_light = '#BAE6FD'            # Very light blue
    else:
        # Ready/idle - Emerald green with strong gradient
        bg_gradient_top = '#34D399'      # Bright emerald (lighter top)
        bg_gradient_bottom = '#064E3B'   # Very deep green (darker bottom)
        inner_glow = '#34D399'           # Bright green
        symbol_color = '#FFFFFF'          # Pure white
        symbol_glow = '#6EE7B7'           # Light green
        rim_light = '#A7F3D0'             # Very light green
    
    padding = max(1, size // 16)
    
    # Shield dimensions
    shield_width = size - padding * 2
    shield_height = size - padding * 2
    shield_top = padding
    shield_left = padding
    
    # === Draw Shield Shape ===
    # Modern rounded shield: rectangle top, pointed bottom
    
    # Create shield path points
    corner_radius = max(2, size // 8)
    point_y = shield_top + shield_height  # Bottom point
    shoulder_y = shield_top + shield_height * 0.55  # Where sides start curving to point
    
    # Build shield as a polygon with curves simulated
    shield_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    shield_draw = ImageDraw.Draw(shield_img)
    
    # Draw gradient background for shield - use eased curve for more dramatic effect
    steps = max(24, size // 2)  # More steps for smoother gradient
    for i in range(steps):
        t = i / steps
        # Apply ease-in curve for more dramatic gradient (darker bottom emphasis)
        t_curved = t * t * (3 - 2 * t)  # Smoothstep for nicer transition
        y1 = shield_top + shield_height * t
        y2 = shield_top + shield_height * (t + 1/steps)
        color = lerp_color(bg_gradient_top, bg_gradient_bottom, t_curved)
        
        # Calculate width at this y level (shield narrows toward bottom)
        if y1 < shoulder_y:
            # Upper rectangular portion
            width_factor = 1.0
        else:
            # Lower triangular portion
            progress = (y1 - shoulder_y) / (point_y - shoulder_y)
            width_factor = 1.0 - progress * 0.95  # Narrows to a point
        
        half_width = (shield_width / 2) * width_factor
        x_left = center - half_width
        x_right = center + half_width
        
        shield_draw.rectangle([x_left, y1, x_right, y2], fill=color)
    
    # Create proper shield mask with rounded top corners and pointed bottom
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    
    # Draw shield shape as polygon
    # Top left corner arc, top edge, top right corner arc, right edge, point, left edge
    points = []
    
    # Top-left rounded corner
    for angle in range(180, 271, 10):
        x = shield_left + corner_radius + corner_radius * math.cos(math.radians(angle))
        y = shield_top + corner_radius + corner_radius * math.sin(math.radians(angle))
        points.append((x, y))
    
    # Top-right rounded corner
    for angle in range(270, 361, 10):
        x = shield_left + shield_width - corner_radius + corner_radius * math.cos(math.radians(angle))
        y = shield_top + corner_radius + corner_radius * math.sin(math.radians(angle))
        points.append((x, y))
    
    # Right edge down to shoulder
    points.append((shield_left + shield_width, shoulder_y))
    
    # Right edge curves to bottom point
    points.append((center, point_y))
    
    # Left edge from point up to shoulder
    points.append((shield_left, shoulder_y))
    
    # Close back to start
    points.append((shield_left, shield_top + corner_radius))
    
    mask_draw.polygon(points, fill=255)
    
    # Apply mask to shield
    shield_img.putalpha(mask)
    img = Image.alpha_composite(img, shield_img)
    draw = ImageDraw.Draw(img)
    
    # === Add rim lighting (edge highlight) ===
    if size >= 32:
        rim_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        rim_draw = ImageDraw.Draw(rim_img)
        rim_r, rim_g, rim_b = hex_to_rgb(rim_light)
        
        # Draw slightly smaller shield outline for rim light effect
        rim_draw.polygon(points, outline=(rim_r, rim_g, rim_b, 100), width=max(1, size // 32))
        
        # Only keep top portion of rim (light from above)
        for y in range(size // 2, size):
            for x in range(size):
                pixel = rim_img.getpixel((x, y))
                if pixel[3] > 0:
                    # Fade out rim light toward bottom
                    fade = 1.0 - (y - size // 2) / (size // 2)
                    rim_img.putpixel((x, y), (pixel[0], pixel[1], pixel[2], int(pixel[3] * fade)))
        
        img = Image.alpha_composite(img, rim_img)
        draw = ImageDraw.Draw(img)
    
    # === Draw central symbol: Stylized Sword (RPG gamification) ===
    # A bold upward-pointing sword that extends ABOVE the shield for dramatic effect
    
    symbol_center_y = center + size * 0.08  # Lower center to make room for blade extending up
    sword_height = shield_height * 0.85  # Much larger sword
    sword_width = shield_width * 0.38   # Wider sword
    
    sym_r, sym_g, sym_b = hex_to_rgb(symbol_color)
    glow_r, glow_g, glow_b = hex_to_rgb(symbol_glow)
    
    # Sword dimensions - larger and more prominent
    blade_width = sword_width * 0.25
    blade_length = sword_height * 0.60
    guard_width = sword_width * 1.1
    guard_height = sword_height * 0.07
    grip_width = sword_width * 0.20
    grip_length = sword_height * 0.20
    pommel_radius = sword_width * 0.14
    
    # Position blade to extend ABOVE the shield
    blade_top = padding - size * 0.12  # Extends above shield!
    guard_y = symbol_center_y + sword_height * 0.05
    grip_bottom = guard_y + grip_length
    
    # Glow behind sword - extends above shield for dramatic effect
    if size >= 32:
        glow_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_img)
        
        # Draw larger, softer sword shape for glow - extends above!
        glow_scale = 1.6
        glow_blade_w = blade_width * glow_scale
        glow_blade_points = [
            (center, blade_top - size * 0.04),  # Tip extends further
            (center + glow_blade_w * 1.2, guard_y),
            (center - glow_blade_w * 1.2, guard_y),
        ]
        glow_draw.polygon(glow_blade_points, fill=(glow_r, glow_g, glow_b, 70))
        
        glow_img = glow_img.filter(ImageFilter.GaussianBlur(radius=max(3, size // 16)))
        # Don't mask the glow - let it extend above shield
        img = Image.alpha_composite(img, glow_img)
        draw = ImageDraw.Draw(img)
    
    # === Draw the sword ===
    # Sword is drawn AFTER shield so it appears on top and can extend beyond
    
    # 1. Blade - pointed triangle (extends above shield)
    blade_points = [
        (center, blade_top),  # Tip point - extends above shield!
        (center + blade_width, guard_y - guard_height * 0.5),  # Right edge
        (center - blade_width, guard_y - guard_height * 0.5),  # Left edge
    ]
    draw.polygon(blade_points, fill=symbol_color)
    
    # 2. Blade edge highlights for metallic look
    if size >= 32:
        # Left edge highlight
        edge_highlight = [(center - blade_width * 0.7, guard_y - guard_height),
                          (center - blade_width * 0.15, blade_top + (guard_y - blade_top) * 0.1)]
        draw.line(edge_highlight, fill=(255, 255, 255, 180), width=max(1, size // 48))
        
        # Right edge (darker for contrast)
        edge_shadow = [(center + blade_width * 0.5, guard_y - guard_height),
                       (center + blade_width * 0.1, blade_top + (guard_y - blade_top) * 0.15)]
        inner_r, inner_g, inner_b = hex_to_rgb(inner_glow)
        draw.line(edge_shadow, fill=(inner_r, inner_g, inner_b, 100), width=max(1, size // 64))
    
    # 3. Blade center line (fuller) for detail on larger icons
    if size >= 48:
        fuller_width = max(1, blade_width * 0.25)
        inner_r, inner_g, inner_b = hex_to_rgb(inner_glow)
        # Draw a thin line down the blade center
        draw.line(
            [(center, blade_top + (guard_y - blade_top) * 0.12), 
             (center, guard_y - guard_height * 1.5)],
            fill=(inner_r, inner_g, inner_b, 60),
            width=max(1, int(fuller_width))
        )
    
    # 4. Cross-guard (horizontal bar) - slightly curved ends
    guard_points = [
        (center - guard_width * 0.5, guard_y - guard_height * 0.5),
        (center + guard_width * 0.5, guard_y - guard_height * 0.5),
        (center + guard_width * 0.5, guard_y + guard_height * 0.5),
        (center - guard_width * 0.5, guard_y + guard_height * 0.5),
    ]
    draw.polygon(guard_points, fill=symbol_color)
    
    # Guard end caps (small circles for style)
    if size >= 24:
        cap_size = max(2, guard_height * 1.0)
        # Left cap
        draw.ellipse([
            center - guard_width * 0.5 - cap_size * 0.5, guard_y - cap_size * 0.5,
            center - guard_width * 0.5 + cap_size * 0.5, guard_y + cap_size * 0.5
        ], fill=symbol_color)
        # Right cap
        draw.ellipse([
            center + guard_width * 0.5 - cap_size * 0.5, guard_y - cap_size * 0.5,
            center + guard_width * 0.5 + cap_size * 0.5, guard_y + cap_size * 0.5
        ], fill=symbol_color)
    
    # 5. Grip/Handle
    grip_points = [
        (center - grip_width, guard_y + guard_height * 0.3),
        (center + grip_width, guard_y + guard_height * 0.3),
        (center + grip_width, grip_bottom),
        (center - grip_width, grip_bottom),
    ]
    draw.polygon(grip_points, fill=symbol_color)
    
    # Grip wrap lines for detail on larger icons
    if size >= 64:
        wrap_color = hex_to_rgb(symbol_glow)
        num_wraps = 3
        for i in range(num_wraps):
            wrap_y = guard_y + guard_height * 0.5 + (grip_length - guard_height * 0.2) * (i + 0.5) / num_wraps
            draw.line(
                [(center - grip_width * 0.8, wrap_y), (center + grip_width * 0.8, wrap_y)],
                fill=(wrap_color[0], wrap_color[1], wrap_color[2], 50),
                width=max(1, size // 64)
            )
    
    # 6. Pommel (bottom sphere)
    pommel_y = grip_bottom + pommel_radius * 0.5
    draw.ellipse([
        center - pommel_radius, pommel_y - pommel_radius,
        center + pommel_radius, pommel_y + pommel_radius
    ], fill=symbol_color)
    
    # === Add subtle drop shadow for depth ===
    if size >= 48 and not for_tray:
        # Create shadow version
        final_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        
        shadow_offset = max(1, size // 48)
        shadow_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_img)
        shadow_draw.polygon(points, fill=(0, 0, 0, 30))
        shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=max(1, size // 32)))
        
        # Offset shadow
        shadow_offset_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        shadow_offset_img.paste(shadow_img, (shadow_offset, shadow_offset))
        
        final_img = Image.alpha_composite(final_img, shadow_offset_img)
        final_img = Image.alpha_composite(final_img, img)
        img = final_img
    
    return img


def create_app_icon() -> list:
    """Create main app icon with all required sizes."""
    # Standard Windows ICO sizes
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = []
    
    for size in sizes:
        # Use ready (green) state for main app icon for a calming appearance
        # Or use blue which is more neutral and professional
        img = create_focus_icon(size, blocking=True, for_tray=(size <= 32))
        images.append(img)
    
    return images


def create_tray_icons():
    """Create system tray icons for ready and blocking states."""
    size = 64  # Good size for tray icons
    
    ready_icon = create_focus_icon(size, blocking=False, for_tray=True)
    blocking_icon = create_focus_icon(size, blocking=True, for_tray=True)
    
    return ready_icon, blocking_icon


def save_icons(output_dir: Path):
    """Generate and save all icons."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating Personal Liberty icons...")
    print(f"Output directory: {output_dir}")
    print()
    
    # Generate main app icon
    print("Creating app.ico (main application icon)...")
    app_images = create_app_icon()
    
    # Save as ICO with multiple sizes
    ico_path = output_dir / "app.ico"
    # Use the largest image as base, append smaller ones
    app_images[0].save(
        ico_path,
        format='ICO',
        sizes=[(img.size[0], img.size[1]) for img in app_images],
        append_images=app_images[1:]
    )
    print(f"  ✓ Saved: {ico_path}")
    print(f"    Sizes: {', '.join(f'{img.size[0]}x{img.size[1]}' for img in app_images)}")
    
    # Generate tray icons
    print()
    print("Creating system tray icons...")
    ready_icon, blocking_icon = create_tray_icons()
    
    # Save as PNG (for pystray compatibility)
    ready_png = output_dir / "tray_ready.png"
    blocking_png = output_dir / "tray_blocking.png"
    ready_icon.save(ready_png, format='PNG')
    blocking_icon.save(blocking_png, format='PNG')
    print(f"  ✓ Saved: {ready_png}")
    print(f"  ✓ Saved: {blocking_png}")
    
    # Also save as ICO for Windows compatibility
    ready_ico = output_dir / "tray_ready.ico"
    blocking_ico = output_dir / "tray_blocking.ico"
    
    # Create multiple sizes for tray ICO
    tray_sizes = [16, 24, 32, 48, 64]
    ready_images = [create_focus_icon(s, blocking=False, for_tray=True) for s in tray_sizes]
    blocking_images = [create_focus_icon(s, blocking=True, for_tray=True) for s in tray_sizes]
    
    ready_images[0].save(
        ready_ico, format='ICO',
        sizes=[(s, s) for s in tray_sizes],
        append_images=ready_images[1:]
    )
    blocking_images[0].save(
        blocking_ico, format='ICO',
        sizes=[(s, s) for s in tray_sizes],
        append_images=blocking_images[1:]
    )
    print(f"  ✓ Saved: {ready_ico}")
    print(f"  ✓ Saved: {blocking_ico}")
    
    print()
    print("=" * 50)
    print("Icon generation complete!")
    print()
    print("Files created:")
    print(f"  • app.ico          - Main app icon (Windows Explorer, taskbar)")
    print(f"  • tray_ready.png   - Tray icon (idle/ready state)")
    print(f"  • tray_ready.ico   - Tray icon ICO format")
    print(f"  • tray_blocking.png- Tray icon (active blocking state)")
    print(f"  • tray_blocking.ico- Tray icon ICO format")


if __name__ == "__main__":
    # Output to icons folder
    script_dir = Path(__file__).parent
    icons_dir = script_dir / "icons"
    save_icons(icons_dir)
