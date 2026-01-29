#!/usr/bin/env python3
"""
Generate industry-standard icons for Personal Liberty app.

Creates:
- app.ico - Main application icon with multiple sizes (16, 24, 32, 48, 64, 128, 256)
- tray_ready.png/ico - System tray icon (ready/idle state)
- tray_blocking.png/ico - System tray icon (active blocking state)

Design: Dynamic exercising figure doing jumping jacks
- Inspired by the training_ground_animated.svg design
- Energetic pose representing productivity and personal freedom
- 5 concentric rings with rarity color gradients
- Industry-standard antialiasing via supersampling
- Premium gradients and modern color palette
"""

from PIL import Image, ImageDraw, ImageFilter, ImageChops
import math
from pathlib import Path


# Supersampling factor for antialiasing (render at 4x, downsample)
SUPERSAMPLE = 4


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


def lerp_rgb(c1: tuple, c2: tuple, t: float) -> tuple:
    """Linearly interpolate between two RGB tuples."""
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def lighten(rgb: tuple, amount: float = 0.3) -> tuple:
    """Lighten a color by blending with white."""
    return lerp_rgb(rgb, (255, 255, 255), amount)


def darken(rgb: tuple, amount: float = 0.3) -> tuple:
    """Darken a color by blending with black."""
    return lerp_rgb(rgb, (0, 0, 0), amount)


def draw_thick_line(draw, x1, y1, x2, y2, width, color):
    """Draw a thick line with rounded ends using a series of ellipses."""
    # Draw circles at start, middle, and end for smooth thick line
    steps = max(8, int(((x2-x1)**2 + (y2-y1)**2)**0.5 / (width * 0.25)))
    for i in range(steps + 1):
        t = i / steps
        x = x1 + (x2 - x1) * t
        y = y1 + (y2 - y1) * t
        draw.ellipse([x - width/2, y - width/2, x + width/2, y + width/2], fill=color)


def create_focus_icon(size: int, blocking: bool = False, for_tray: bool = False) -> Image.Image:
    """
    Create a modern, industry-standard app icon with an exercising figure.
    
    Features:
    - 4x supersampling for smooth antialiasing
    - Gradient rings with highlight/shadow for 3D depth
    - Dynamic jumping jacks figure
    - 5 concentric rings: Legendary (orange) outside → Common (grey) inside
    """
    # Render at higher resolution for antialiasing
    render_size = size * SUPERSAMPLE
    img = Image.new('RGBA', (render_size, render_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center = render_size // 2
    
    # Exact rarity colors from the app - REVERSED ORDER (Legendary outside)
    # Each tuple: (base_color, lighter_shade, darker_shade)
    RARITY_RINGS = [
        ("#ff9800", "#ffb74d", "#e65100"),  # Legendary (orange) - outermost
        ("#9c27b0", "#ba68c8", "#6a1b9a"),  # Epic (purple)
        ("#2196f3", "#64b5f6", "#1565c0"),  # Rare (blue)
        ("#4caf50", "#81c784", "#2e7d32"),  # Uncommon (green)
        ("#9e9e9e", "#bdbdbd", "#616161"),  # Common (grey) - innermost/center
    ]
    
    # Figure colors
    figure_color = '#FFFFFF'
    figure_outline = '#333333'  # Dark outline for contrast
    headband_color = '#F44336'
    
    # No padding - circles reach to the edge
    max_radius = render_size // 2
    
    # Gap between rings for visual separation
    ring_gap = max(2, render_size // 40)
    
    # === Draw 5 concentric gradient rings with radial line patterns ===
    num_rings = len(RARITY_RINGS)
    total_gap_space = ring_gap * (num_rings - 1)
    ring_width = (max_radius - total_gap_space) / num_rings
    
    # First, draw the base solid rings with gaps
    for ring_idx, (base, light, dark) in enumerate(RARITY_RINGS):
        outer_r = max_radius - (ring_idx * (ring_width + ring_gap))
        inner_r = outer_r - ring_width
        base_rgb = hex_to_rgb(base)
        
        x1 = center - outer_r
        y1 = center - outer_r
        x2 = center + outer_r
        y2 = center + outer_r
        
        if x2 > x1 and y2 > y1:
            draw.ellipse([x1, y1, x2, y2], fill=base_rgb)
        
        # Cut out inner circle to create ring (except for innermost)
        if ring_idx < num_rings - 1 and inner_r > 0:
            # Draw transparent circle for gap
            gap_outer = inner_r
            gap_inner = inner_r - ring_gap
            if gap_inner > 0:
                draw.ellipse([center - gap_outer, center - gap_outer,
                              center + gap_outer, center + gap_outer], fill=(0, 0, 0, 0))
    
    # Redraw inner rings on top (since we cut holes)
    for ring_idx in range(1, num_rings):
        base, light, dark = RARITY_RINGS[ring_idx]
        outer_r = max_radius - (ring_idx * (ring_width + ring_gap))
        base_rgb = hex_to_rgb(base)
        
        if outer_r > 0:
            draw.ellipse([center - outer_r, center - outer_r,
                          center + outer_r, center + outer_r], fill=base_rgb)
    
    # Add radial line patterns for character
    num_rays = 24
    for ring_idx, (base, light, dark) in enumerate(RARITY_RINGS):
        outer_r = max_radius - (ring_idx * (ring_width + ring_gap))
        inner_r = outer_r - ring_width
        
        if inner_r < 0:
            inner_r = 0
        
        light_rgb = hex_to_rgb(light)
        dark_rgb = hex_to_rgb(dark)
        
        # Draw alternating light and dark radial segments
        for ray in range(num_rays):
            angle1 = (ray / num_rays) * 2 * math.pi
            angle2 = ((ray + 0.5) / num_rays) * 2 * math.pi
            
            if ray % 2 == 0:
                ray_color = (*light_rgb, 50)
            else:
                ray_color = (*dark_rgb, 35)
            
            ray_img = Image.new('RGBA', (render_size, render_size), (0, 0, 0, 0))
            ray_draw = ImageDraw.Draw(ray_img)
            
            points = [
                (center, center),
                (center + outer_r * math.cos(angle1), center + outer_r * math.sin(angle1)),
                (center + outer_r * math.cos(angle2), center + outer_r * math.sin(angle2)),
            ]
            ray_draw.polygon(points, fill=ray_color)
            
            ring_mask = Image.new('L', (render_size, render_size), 0)
            ring_mask_draw = ImageDraw.Draw(ring_mask)
            ring_mask_draw.ellipse([center - outer_r, center - outer_r, 
                                    center + outer_r, center + outer_r], fill=255)
            if inner_r > 0:
                ring_mask_draw.ellipse([center - inner_r, center - inner_r,
                                        center + inner_r, center + inner_r], fill=0)
            
            ray_img.putalpha(ImageChops.multiply(ray_img.split()[3], ring_mask))
            img = Image.alpha_composite(img, ray_img)
        
        draw = ImageDraw.Draw(img)
    
    # Add subtle edge highlights on each ring boundary
    for ring_idx in range(num_rings):
        ring_r = max_radius - (ring_idx * (ring_width + ring_gap))
        if ring_r > 5:
            # Outer edge highlight (white)
            draw.arc([center - ring_r, center - ring_r, center + ring_r, center + ring_r],
                     start=200, end=340, fill=(255, 255, 255, 50), 
                     width=max(1, render_size // 80))
            # Inner edge shadow
            draw.arc([center - ring_r, center - ring_r, center + ring_r, center + ring_r],
                     start=20, end=160, fill=(0, 0, 0, 30),
                     width=max(1, render_size // 80))
    
    # === Add highlight arc at top for gloss effect ===
    if render_size >= 64:
        highlight_img = Image.new('RGBA', (render_size, render_size), (0, 0, 0, 0))
        highlight_draw = ImageDraw.Draw(highlight_img)
        
        # Draw a white arc at the top
        arc_width = max(2, render_size // 20)
        arc_padding = arc_width + ring_gap
        highlight_draw.arc(
            [arc_padding, arc_padding, render_size - arc_padding, render_size - arc_padding],
            start=200, end=340,
            fill=(255, 255, 255, 80),
            width=arc_width
        )
        
        # Blur slightly for softness
        highlight_img = highlight_img.filter(ImageFilter.GaussianBlur(radius=render_size // 64))
        img = Image.alpha_composite(img, highlight_img)
        draw = ImageDraw.Draw(img)
    
    # === Draw the exercising figure (jumping jacks pose) ===
    fig_r, fig_g, fig_b = hex_to_rgb(figure_color)
    outline_r, outline_g, outline_b = hex_to_rgb(figure_outline)
    head_r, head_g, head_b = hex_to_rgb(headband_color)
    
    # Scale relative to render size
    scale = render_size / 100
    
    # Outline thickness
    outline_width = max(2, int(2.5 * scale))
    
    # Figure center position
    fig_cx = center
    fig_cy = center + render_size * 0.10
    
    # Calculate all figure positions first
    head_radius = max(4, int(10 * scale))
    head_y = fig_cy - int(30 * scale)
    
    torso_width = max(4, int(16 * scale))
    torso_height = max(6, int(22 * scale))
    torso_top = head_y + head_radius + int(2 * scale)
    torso_bottom = torso_top + torso_height
    
    arm_width = max(3, int(6 * scale))
    arm_length = int(24 * scale)
    shoulder_y = torso_top + int(5 * scale)
    arm_angle = math.radians(50)
    left_hand_x = fig_cx - int(arm_length * math.sin(arm_angle))
    left_hand_y = shoulder_y - int(arm_length * math.cos(arm_angle))
    right_hand_x = fig_cx + int(arm_length * math.sin(arm_angle))
    right_hand_y = shoulder_y - int(arm_length * math.cos(arm_angle))
    hand_radius = max(2, int(4 * scale))
    
    leg_width = max(3, int(7 * scale))
    leg_length = int(26 * scale)
    hip_y = torso_bottom - int(2 * scale)
    leg_angle = math.radians(25)
    left_foot_x = fig_cx - int(leg_length * math.sin(leg_angle))
    left_foot_y = hip_y + int(leg_length * math.cos(leg_angle))
    right_foot_x = fig_cx + int(leg_length * math.sin(leg_angle))
    right_foot_y = hip_y + int(leg_length * math.cos(leg_angle))
    foot_w = max(3, int(7 * scale))
    foot_h = max(2, int(4 * scale))
    
    band_height = max(2, int(4 * scale))
    band_y = head_y - int(2 * scale)
    tail_len = int(8 * scale)
    
    # === DRAW OUTLINE FIRST (slightly larger, dark color) ===
    outline_color = figure_outline
    ol = outline_width  # Outline offset
    
    # Head outline
    draw.ellipse([
        fig_cx - head_radius - ol, head_y - head_radius - ol,
        fig_cx + head_radius + ol, head_y + head_radius + ol
    ], fill=outline_color)
    
    # Torso outline
    draw.rounded_rectangle([
        fig_cx - torso_width // 2 - ol, torso_top - ol,
        fig_cx + torso_width // 2 + ol, torso_bottom + ol
    ], radius=max(2, int(4 * scale)), fill=outline_color)
    
    # Arms outline
    draw_thick_line(draw, fig_cx - int(7 * scale), shoulder_y, 
                    left_hand_x, left_hand_y, arm_width + ol * 2, outline_color)
    draw_thick_line(draw, fig_cx + int(7 * scale), shoulder_y,
                    right_hand_x, right_hand_y, arm_width + ol * 2, outline_color)
    
    # Hands outline
    draw.ellipse([
        left_hand_x - hand_radius - ol, left_hand_y - hand_radius - ol,
        left_hand_x + hand_radius + ol, left_hand_y + hand_radius + ol
    ], fill=outline_color)
    draw.ellipse([
        right_hand_x - hand_radius - ol, right_hand_y - hand_radius - ol,
        right_hand_x + hand_radius + ol, right_hand_y + hand_radius + ol
    ], fill=outline_color)
    
    # Legs outline
    draw_thick_line(draw, fig_cx - int(5 * scale), hip_y,
                    left_foot_x, left_foot_y, leg_width + ol * 2, outline_color)
    draw_thick_line(draw, fig_cx + int(5 * scale), hip_y,
                    right_foot_x, right_foot_y, leg_width + ol * 2, outline_color)
    
    # Feet outline
    draw.ellipse([
        left_foot_x - foot_w - ol, left_foot_y - foot_h - ol,
        left_foot_x + foot_w + ol, left_foot_y + foot_h + ol
    ], fill=outline_color)
    draw.ellipse([
        right_foot_x - foot_w - ol, right_foot_y - foot_h - ol,
        right_foot_x + foot_w + ol, right_foot_y + foot_h + ol
    ], fill=outline_color)
    
    # === DRAW FIGURE ON TOP (white) ===
    # Head
    draw.ellipse([
        fig_cx - head_radius, head_y - head_radius,
        fig_cx + head_radius, head_y + head_radius
    ], fill=figure_color)
    
    # Headband
    draw.rectangle([
        fig_cx - head_radius, band_y,
        fig_cx + head_radius, band_y + band_height
    ], fill=(head_r, head_g, head_b, 255))
    # Headband tail
    draw.polygon([
        (fig_cx + head_radius, band_y),
        (fig_cx + head_radius + tail_len, band_y + band_height // 2),
        (fig_cx + head_radius, band_y + band_height)
    ], fill=(head_r, head_g, head_b, 255))
    
    # Torso
    draw.rounded_rectangle([
        fig_cx - torso_width // 2, torso_top,
        fig_cx + torso_width // 2, torso_bottom
    ], radius=max(2, int(4 * scale)), fill=figure_color)
    
    # Arms
    draw_thick_line(draw, fig_cx - int(7 * scale), shoulder_y, 
                    left_hand_x, left_hand_y, arm_width, figure_color)
    draw_thick_line(draw, fig_cx + int(7 * scale), shoulder_y,
                    right_hand_x, right_hand_y, arm_width, figure_color)
    
    # Hands
    draw.ellipse([
        left_hand_x - hand_radius, left_hand_y - hand_radius,
        left_hand_x + hand_radius, left_hand_y + hand_radius
    ], fill=figure_color)
    draw.ellipse([
        right_hand_x - hand_radius, right_hand_y - hand_radius,
        right_hand_x + hand_radius, right_hand_y + hand_radius
    ], fill=figure_color)
    
    # Legs
    draw_thick_line(draw, fig_cx - int(5 * scale), hip_y,
                    left_foot_x, left_foot_y, leg_width, figure_color)
    draw_thick_line(draw, fig_cx + int(5 * scale), hip_y,
                    right_foot_x, right_foot_y, leg_width, figure_color)
    
    # Feet
    draw.ellipse([
        left_foot_x - foot_w, left_foot_y - foot_h,
        left_foot_x + foot_w, left_foot_y + foot_h
    ], fill=figure_color)
    draw.ellipse([
        right_foot_x - foot_w, right_foot_y - foot_h,
        right_foot_x + foot_w, right_foot_y + foot_h
    ], fill=figure_color)
    
    # === Add subtle drop shadow behind figure for depth ===
    # (Already have antialiasing from supersampling)
    
    # === Downsample to target size with high-quality antialiasing ===
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    
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
