#!/usr/bin/env python3
"""
Generate high-quality icons using Qt rendering (same as timer icons).
"""

from PySide6 import QtGui, QtCore, QtWidgets
import sys
from pathlib import Path

# Initialize application
if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)
else:
    app = QtWidgets.QApplication.instance()


def create_person_icon(size: int, blocking: bool = False) -> QtGui.QPixmap:
    """Create high-quality icon with person figure using Qt rendering."""
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtCore.Qt.transparent)
    
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
    
    center_x = size // 2
    center_y = size // 2
    
    # Rarity rings (reversed - Legendary outside) - LINEAR gradients top to bottom
    rings = [
        ("#ff9800", "#ffb74d", "#e65100"),  # Legendary (orange)
        ("#9c27b0", "#ba68c8", "#6a1b9a"),  # Epic (purple)
        ("#2196f3", "#64b5f6", "#1565c0"),  # Rare (blue)
        ("#4caf50", "#81c784", "#2e7d32"),  # Uncommon (green)
        ("#9e9e9e", "#bdbdbd", "#616161"),  # Common (grey)
    ]
    
    # Draw rings with LINEAR gradients (top to bottom)
    max_radius = size // 2 - 2
    ring_width = max_radius // len(rings)
    
    for ring_idx, (base, light, dark) in enumerate(rings):
        outer_r = max_radius - (ring_idx * ring_width)
        inner_r = outer_r - ring_width
        
        # Create linear gradient (top to bottom)
        gradient = QtGui.QLinearGradient(center_x, center_y - outer_r, 
                                         center_x, center_y + outer_r)
        gradient.setColorAt(0, QtGui.QColor(light))
        gradient.setColorAt(0.5, QtGui.QColor(base))
        gradient.setColorAt(1, QtGui.QColor(dark))
        
        painter.setBrush(gradient)
        painter.setPen(QtCore.Qt.NoPen)
        
        # Draw outer circle
        painter.drawEllipse(center_x - outer_r, center_y - outer_r, 
                          outer_r * 2, outer_r * 2)
        
        # Cut out inner circle (except for innermost)
        if inner_r > 0:
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_DestinationOut)
            painter.setBrush(QtGui.QColor(0, 0, 0, 255))
            painter.drawEllipse(center_x - inner_r, center_y - inner_r,
                              inner_r * 2, inner_r * 2)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
    
    # Draw person figure
    scale = size / 128.0
    
    # Figure colors - simple white
    figure_color = QtGui.QColor("#FFFFFF")
    
    fig_cx = center_x
    fig_cy = center_y + int(size * 0.08)
    
    # Head
    head_radius = max(8, int(13 * scale))
    head_y = fig_cy - int(38 * scale)
    
    painter.setPen(QtCore.Qt.NoPen)
    painter.setBrush(figure_color)
    painter.drawEllipse(fig_cx - head_radius, head_y - head_radius,
                       head_radius * 2, head_radius * 2)
    
    # Torso
    torso_width = max(8, int(20 * scale))
    torso_height = max(10, int(28 * scale))
    torso_top = head_y + head_radius + int(3 * scale)
    torso_bottom = torso_top + torso_height
    
    painter.setPen(QtCore.Qt.NoPen)
    painter.setBrush(figure_color)
    painter.drawRoundedRect(fig_cx - torso_width // 2, torso_top,
                           torso_width, torso_height,
                           max(3, int(5 * scale)), max(3, int(5 * scale)))
    
    # Arms (raised for jumping jack)
    arm_width = max(5, int(8 * scale))
    arm_length = int(30 * scale)
    shoulder_y = torso_top + int(6 * scale)
    
    import math
    arm_angle = math.radians(50)
    
    # Left arm
    left_hand_x = fig_cx - int(arm_length * math.sin(arm_angle))
    left_hand_y = shoulder_y - int(arm_length * math.cos(arm_angle))
    
    pen = QtGui.QPen(figure_color, arm_width)
    pen.setCapStyle(QtCore.Qt.RoundCap)
    painter.setPen(pen)
    painter.drawLine(fig_cx - int(9 * scale), shoulder_y, left_hand_x, left_hand_y)
    
    # Right arm
    right_hand_x = fig_cx + int(arm_length * math.sin(arm_angle))
    right_hand_y = shoulder_y - int(arm_length * math.cos(arm_angle))
    
    pen = QtGui.QPen(figure_color, arm_width)
    pen.setCapStyle(QtCore.Qt.RoundCap)
    painter.setPen(pen)
    painter.drawLine(fig_cx + int(9 * scale), shoulder_y, right_hand_x, right_hand_y)
    
    # Legs (spread for jumping jack)
    leg_width = max(5, int(9 * scale))
    leg_length = int(32 * scale)
    hip_y = torso_bottom - int(3 * scale)
    
    leg_angle = math.radians(25)
    
    # Left leg
    left_foot_x = fig_cx - int(leg_length * math.sin(leg_angle))
    left_foot_y = hip_y + int(leg_length * math.cos(leg_angle))
    
    pen = QtGui.QPen(figure_color, leg_width)
    pen.setCapStyle(QtCore.Qt.RoundCap)
    painter.setPen(pen)
    painter.drawLine(fig_cx - int(5 * scale), hip_y, left_foot_x, left_foot_y)
    
    # Right leg
    right_foot_x = fig_cx + int(leg_length * math.sin(leg_angle))
    right_foot_y = hip_y + int(leg_length * math.cos(leg_angle))
    
    pen = QtGui.QPen(figure_color, leg_width)
    pen.setCapStyle(QtCore.Qt.RoundCap)
    painter.setPen(pen)
    painter.drawLine(fig_cx + int(5 * scale), hip_y, right_foot_x, right_foot_y)
    
    painter.end()
    return pixmap


def main():
    output_dir = Path("icons")
    output_dir.mkdir(exist_ok=True)
    
    print("Generating high-quality Qt-rendered icons...")
    
    # Generate ready icon (green - idle state)
    ready_pixmap = create_person_icon(128, blocking=False)
    ready_pixmap.save(str(output_dir / "tray_ready.png"))
    print(f"  ✓ {output_dir / 'tray_ready.png'}")
    
    # Generate blocking icon (blue - active state)
    blocking_pixmap = create_person_icon(128, blocking=True)
    blocking_pixmap.save(str(output_dir / "tray_blocking.png"))
    print(f"  ✓ {output_dir / 'tray_blocking.png'}")

    # Generate ICO files by resizing the high-quality 128px PNGs
    print("\n  Generating ICO files by resizing 128px PNGs...")
    try:
        from PIL import Image
        
        # Load the 128px ready icon
        ready_img = Image.open(str(output_dir / "tray_ready.png"))
        
        # Generate app.ico with multiple sizes (resized from 128px)
        app_sizes = [16, 24, 32, 48, 64, 128]
        app_images = [ready_img.resize((s, s), Image.Resampling.LANCZOS) for s in app_sizes]
        
        ico_path = output_dir / "app.ico"
        app_images[0].save(
            str(ico_path),
            format='ICO',
            sizes=[(s, s) for s in app_sizes],
            append_images=app_images[1:]
        )
        print(f"  ✓ {ico_path} (sizes: {app_sizes})")
        
        # Generate tray ICO files
        for name in ["tray_ready", "tray_blocking"]:
            png_path = output_dir / f"{name}.png"
            img = Image.open(str(png_path))
            ico_path = output_dir / f"{name}.ico"
            tray_sizes = [16, 24, 32, 48, 64, 128]
            tray_images = [img.resize((s, s), Image.Resampling.LANCZOS) for s in tray_sizes]
            tray_images[0].save(
                str(ico_path),
                format='ICO',
                sizes=[(s, s) for s in tray_sizes],
                append_images=tray_images[1:]
            )
            print(f"  ✓ {ico_path}")

    except ImportError:
        print("  ⚠ PIL not available, skipping ICO generation")
    
    print("\nDone! Icons generated with Qt rendering (same quality as timer icons)")


if __name__ == "__main__":
    main()
