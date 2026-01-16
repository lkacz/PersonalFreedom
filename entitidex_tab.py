"""
Entitidex Tab - Collection viewer for entity companions.

Shows all entities in the current story theme with:
- Full details for collected entities
- Silhouettes for uncollected entities (mysterious appearance)
"""

import os
import math
from pathlib import Path
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtSvg import QSvgRenderer

# Try to import QWebEngineView for animated SVG support
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEngineSettings
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False
    print("Warning: QWebEngineView not available - SVG animations disabled")

# Import entitidex components
from entitidex import (
    get_entities_for_story,
    Entity,
    EntitidexProgress,
)


# Rarity colors
RARITY_COLORS = {
    "common": "#9E9E9E",
    "uncommon": "#4CAF50",
    "rare": "#2196F3",
    "epic": "#9C27B0",
    "legendary": "#FF9800",
}

# Rarity background colors (matching preview_entities.py)
RARITY_BG = {
    "common": "#2D2D2D",
    "uncommon": "#1B3D1B",
    "rare": "#1B2D3D",
    "epic": "#2D1B3D",
    "legendary": "#3D2D1B",
}

# Path to entity SVGs
ENTITY_ICONS_PATH = Path(__file__).parent / "icons" / "entities"
EXCEPTIONAL_ICONS_PATH = ENTITY_ICONS_PATH / "exceptional"

# =============================================================================
# EXCEPTIONAL/SHINY ENTITY COLORS
# Predefined contrasting colors for each entity when it's exceptional
# Format: {entity_id: (R, G, B)} - complementary/contrasting to original
# =============================================================================
EXCEPTIONAL_ENTITY_COLORS = {
    # WARRIOR THEME - Fire/Red creatures get cool blue/teal versions
    "warrior_001": (0, 200, 200),      # Hatchling Drake: Red → Cyan/Teal
    "warrior_002": (100, 50, 150),     # Training Dummy: Brown → Purple
    "warrior_003": (255, 100, 200),    # Battle Falcon: Brown → Pink
    "warrior_004": (50, 200, 100),     # War Horse: Brown → Emerald Green
    "warrior_005": (0, 180, 255),      # Dragon Whelp Ember: Orange → Sky Blue
    "warrior_006": (200, 100, 255),    # Battle Standard: Red → Violet
    "warrior_007": (0, 255, 150),      # Battle Dragon Crimson: Red → Jade Green
    "warrior_008": (255, 200, 50),     # Dire Wolf Fenris: Gray → Golden Yellow
    "warrior_009": (255, 50, 50),      # Old War Ant: Black → Crimson Red
    
    # SCHOLAR THEME - Books/Paper get vibrant magical colors
    "scholar_001": (255, 150, 200),    # Library Mouse: White → Pink
    "scholar_002": (200, 50, 255),     # Study Owl: Brown → Purple
    "scholar_003": (50, 255, 200),     # Reading Candle: Orange → Turquoise
    "scholar_004": (150, 100, 255),    # Library Cat: Orange → Lavender
    "scholar_005": (255, 50, 100),     # Living Bookmark: Gold → Ruby Red
    "scholar_006": (50, 255, 100),     # Sentient Tome: Brown → Lime Green
    "scholar_007": (255, 100, 0),      # Ancient Star Map: Blue → Orange
    "scholar_008": (0, 200, 255),      # Archive Phoenix: Red/Orange → Cyan
    "scholar_009": (255, 215, 0),      # Blank Parchment: Yellow → Gold Shimmer
    
    # WANDERER THEME - Travel gear gets mystical colors
    "wanderer_001": (50, 255, 50),     # Lucky Coin: Copper → Green
    "wanderer_002": (255, 50, 150),    # Brass Compass: Gold → Magenta
    "wanderer_003": (100, 200, 255),   # Journey Journal: Brown → Sky Blue
    "wanderer_004": (255, 255, 100),   # Road Dog: Brown → Bright Yellow
    "wanderer_005": (200, 50, 255),    # Self-Drawing Map: Parchment → Purple
    "wanderer_006": (50, 255, 200),    # Wanderer's Carriage: Brown → Aqua
    "wanderer_007": (255, 100, 50),    # Timeworn Backpack: Brown → Sunset Orange
    "wanderer_008": (255, 50, 255),    # Sky Balloon: Rainbow → Magenta
    "wanderer_009": (0, 255, 200),     # Hobo Rat: Gray → Mint Green
    
    # UNDERDOG THEME - Office items get neon/cyber colors
    "underdog_001": (0, 255, 255),     # Office Rat: Gray → Cyan
    "underdog_002": (255, 100, 255),   # Lucky Sticky Note: Yellow → Magenta
    "underdog_003": (255, 200, 50),    # Vending Machine Coin: Silver → Gold
    "underdog_004": (100, 255, 100),   # Window Pigeon: Gray → Neon Green
    "underdog_005": (255, 50, 150),    # Desk Succulent: Green → Pink
    "underdog_006": (50, 200, 255),    # Coffee Maker: Black → Electric Blue
    "underdog_007": (255, 150, 50),    # Corner Office Chair: Black → Orange
    "underdog_008": (150, 255, 200),   # AGI Assistant: Blue → Mint
    "underdog_009": (255, 100, 100),   # Break Room Fridge: Beige → Salmon Pink
    
    # SCIENTIST THEME - Lab equipment gets bioluminescent colors
    "scientist_001": (200, 50, 255),   # Cracked Test Tube: Clear → Purple
    "scientist_002": (0, 255, 150),    # Old Bunsen Burner: Blue Flame → Green Flame
    "scientist_003": (255, 150, 50),   # Lucky Petri Dish: Clear → Amber
    "scientist_004": (255, 200, 255),  # Wise Lab Rat: Gray → Light Pink
    "scientist_005": (50, 255, 255),   # Vintage Microscope: Brass → Cyan
    "scientist_006": (255, 50, 200),   # Bubbling Flask: Multi → Hot Pink
    "scientist_007": (255, 200, 0),    # Tesla Coil: Purple → Gold Electric
    "scientist_008": (100, 255, 200),  # Golden DNA Helix: Gold → Aquamarine
    "scientist_009": (200, 150, 255),  # White Mouse: White → Lavender
}


def _resolve_entity_svg_path(entity: Entity, is_exceptional: bool = False) -> Optional[str]:
    """
    Resolve the SVG path for an entity using multiple strategies.
    
    SVG files are named: {id}_{name_snake_case}.svg
    e.g., warrior_003_battle_falcon_swift.svg
    
    Exceptional variants are in icons/entities/exceptional/ with _exceptional suffix.
    e.g., warrior_003_battle_falcon_swift_exceptional.svg
    
    Args:
        entity: The Entity to find SVG for
        is_exceptional: If True, look for exceptional variant first
    
    Returns:
        Path to SVG file or None if not found
    """
    name_snake = entity.name.lower().replace(" ", "_").replace("-", "_").replace("'", "")
    
    # If exceptional, try to find the exceptional variant first
    if is_exceptional and EXCEPTIONAL_ICONS_PATH.exists():
        # Strategy 1: Try filename pattern {id}_{name_snake_case}_exceptional.svg
        exceptional_path = EXCEPTIONAL_ICONS_PATH / f"{entity.id}_{name_snake}_exceptional.svg"
        if exceptional_path.exists():
            return str(exceptional_path)
        
        # Strategy 2: Search for file starting with entity id in exceptional folder
        for svg_file in EXCEPTIONAL_ICONS_PATH.glob(f"{entity.id}*_exceptional.svg"):
            return str(svg_file)
    
    # Fall back to regular SVG resolution
    # Strategy 1: Try entity's icon_path if provided
    if entity.icon_path and os.path.exists(entity.icon_path):
        return entity.icon_path
    
    # Strategy 2: Try filename pattern {id}_{name_snake_case}.svg
    pattern_path = ENTITY_ICONS_PATH / f"{entity.id}_{name_snake}.svg"
    if pattern_path.exists():
        return str(pattern_path)
    
    # Strategy 3: Search for file starting with entity id
    if ENTITY_ICONS_PATH.exists():
        for svg_file in ENTITY_ICONS_PATH.glob(f"{entity.id}*.svg"):
            return str(svg_file)
    
    # Strategy 4: Fall back to simple {id}.svg (legacy support)
    simple_path = ENTITY_ICONS_PATH / f"{entity.id}.svg"
    if simple_path.exists():
        return str(simple_path)
    
    return None


class SilhouetteSvgWidget(QtWidgets.QWidget):
    """
    Custom widget that displays an SVG as a silhouette (black shape).
    Used for uncollected entities to show mysterious appearance.
    Size: 128x128 to match preview cards.
    """
    
    def __init__(self, svg_path: str, parent=None):
        super().__init__(parent)
        self.svg_path = svg_path
        self.renderer = QSvgRenderer(svg_path)
        self.setFixedSize(128, 128)
        
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Create a pixmap from the SVG
        pixmap = QtGui.QPixmap(self.size())
        pixmap.fill(QtCore.Qt.transparent)
        
        svg_painter = QtGui.QPainter(pixmap)
        self.renderer.render(svg_painter)
        svg_painter.end()
        
        # Convert to image and make silhouette
        image = pixmap.toImage()
        
        # Create silhouette by making all non-transparent pixels dark
        for x in range(image.width()):
            for y in range(image.height()):
                pixel = image.pixelColor(x, y)
                if pixel.alpha() > 0:
                    # Make it a dark silhouette with slight transparency
                    image.setPixelColor(x, y, QtGui.QColor(30, 30, 40, min(pixel.alpha(), 200)))
        
        # Draw the silhouette
        painter.drawImage(0, 0, image)
        painter.end()


class AnimatedSvgWidget(QtWidgets.QWidget):
    """
    Widget that displays SVG with full animation support using QWebEngineView.
    Used for exceptional entities to show their embedded SMIL animations
    (e.g., wagging tails, electricity effects, rotating elements).
    
    Falls back to QSvgWidget if WebEngine is not available.
    """
    
    def __init__(self, svg_path: str, parent=None):
        super().__init__(parent)
        self.svg_path = svg_path
        self.setFixedSize(128, 128)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        if HAS_WEBENGINE:
            # Use WebEngine for full SVG animation support
            self.web_view = QWebEngineView()
            self.web_view.setFixedSize(128, 128)
            
            # Configure for transparent background
            self.web_view.page().setBackgroundColor(QtCore.Qt.transparent)
            self.web_view.setAttribute(QtCore.Qt.WA_TranslucentBackground)
            
            # Disable scrollbars and interactions
            settings = self.web_view.settings()
            settings.setAttribute(QWebEngineSettings.ShowScrollBars, False)
            settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)  # For CSS animations
            
            # Load SVG with transparent background HTML wrapper
            self._load_svg()
            
            layout.addWidget(self.web_view)
        else:
            # Fallback to static QSvgWidget
            self.svg_widget = QSvgWidget(svg_path)
            self.svg_widget.setFixedSize(128, 128)
            self.svg_widget.setStyleSheet("background: transparent;")
            layout.addWidget(self.svg_widget)
    
    def _load_svg(self):
        """Load the SVG file into WebEngine with proper styling."""
        # Read SVG content
        try:
            with open(self.svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
        except Exception as e:
            print(f"Error loading SVG {self.svg_path}: {e}")
            svg_content = '<svg></svg>'
        
        # Wrap SVG in HTML with transparent background and scaled display
        # SVGs are 64x64 viewBox, scale to 128x128 display
        html = f'''<!DOCTYPE html>
<html>
<head>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html, body {{ 
        width: 128px; 
        height: 128px; 
        overflow: hidden;
        background: transparent;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    svg {{
        width: 128px;
        height: 128px;
        display: block;
    }}
</style>
</head>
<body>
{svg_content}
</body>
</html>'''
        
        # Load with file:// base URL to allow relative references
        base_url = QtCore.QUrl.fromLocalFile(str(Path(self.svg_path).parent) + '/')
        self.web_view.setHtml(html, base_url)


class EntityCard(QtWidgets.QFrame):
    """
    Card widget for displaying a single entity.
    Shows full details if collected, silhouette if not.
    Uses the same layout as preview_entities.py (180x220 with 128x128 SVG).
    
    Exceptional entities get special animated effects:
    - Pulsing border glow
    - Floating sparkle decorations
    - Shimmer sweep effect
    - Icon breathing/pulse effect
    - Rotating halo particles
    """
    
    clicked = QtCore.Signal(object, bool)  # Emits (Entity, is_exceptional) when clicked
    
    def __init__(self, entity: Entity, is_collected: bool, is_encountered: bool = False, 
                 is_exceptional: bool = False, exceptional_colors: dict = None, parent=None):
        super().__init__(parent)
        self.entity = entity
        self.is_collected = is_collected
        self.is_encountered = is_encountered
        self.is_exceptional = is_exceptional
        self.exceptional_colors = exceptional_colors or {}
        
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Raised)
        self.setLineWidth(2)  # Match preview_entities.py
        self.setCursor(QtCore.Qt.PointingHandCursor)
        
        # Animation for exceptional cards
        self._glow_animation = None
        self._glow_value = 0.0
        self._sparkle_labels = []  # For sparkle decorations
        self._shimmer_widget = None  # Shimmer sweep overlay
        self._halo_particles = []  # Rotating particles around icon
        self._icon_widget = None  # Store reference for animation
        self._icon_scale_animation = None
        
        self._build_ui()
        
        # Start animations for exceptional entities
        if self.is_exceptional and self.is_collected:
            self._start_glow_animation()
            self._start_icon_breathing()
            self._create_shimmer_overlay()
        
    def _start_glow_animation(self):
        """Start the pulsing glow animation for exceptional entities."""
        self._glow_animation = QtCore.QPropertyAnimation(self, b"glow_value")
        self._glow_animation.setDuration(2000)  # 2 second pulse
        self._glow_animation.setStartValue(0.0)
        self._glow_animation.setEndValue(1.0)
        self._glow_animation.setLoopCount(-1)  # Infinite loop
        self._glow_animation.setEasingCurve(QtCore.QEasingCurve.InOutSine)
        self._glow_animation.start()
        
    def _start_icon_breathing(self):
        """Create a subtle opacity pulse animation for the icon (breathing effect).
        
        Note: Skipped when using AnimatedSvgWidget since the SVG already has
        native SMIL animations (e.g., wagging tails, electricity effects).
        """
        if not self._icon_widget:
            return
        
        # Skip breathing effect for AnimatedSvgWidget - it has native SVG animations
        if HAS_WEBENGINE and isinstance(self._icon_widget, AnimatedSvgWidget):
            return
            
        # Use graphics effect for scale simulation via opacity pulse
        self._icon_effect = QtWidgets.QGraphicsOpacityEffect(self._icon_widget)
        self._icon_widget.setGraphicsEffect(self._icon_effect)
        
        self._icon_opacity_anim = QtCore.QPropertyAnimation(self._icon_effect, b"opacity")
        self._icon_opacity_anim.setDuration(1500)
        self._icon_opacity_anim.setStartValue(0.85)
        self._icon_opacity_anim.setEndValue(1.0)
        self._icon_opacity_anim.setLoopCount(-1)
        self._icon_opacity_anim.setEasingCurve(QtCore.QEasingCurve.InOutSine)
        # Ping-pong by using keyframes
        self._icon_opacity_anim.setKeyValueAt(0.5, 1.0)
        self._icon_opacity_anim.setKeyValueAt(1.0, 0.85)
        self._icon_opacity_anim.start()
        
    def _create_shimmer_overlay(self):
        """Create a shimmer sweep effect that moves across the card."""
        # Create a transparent overlay widget for the shimmer
        self._shimmer_widget = QtWidgets.QWidget(self)
        self._shimmer_widget.setFixedSize(180, 220)
        self._shimmer_widget.move(0, 0)
        self._shimmer_widget.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self._shimmer_widget.setStyleSheet("background: transparent;")
        self._shimmer_widget.lower()  # Behind sparkles but above background
        
        # Store shimmer position for animation
        self._shimmer_pos = -60  # Start off-screen left
        
        # Timer for shimmer animation
        self._shimmer_timer = QtCore.QTimer(self)
        self._shimmer_timer.timeout.connect(self._update_shimmer)
        self._shimmer_timer.start(50)  # 20 FPS for smooth animation
        
    def _update_shimmer(self):
        """Update shimmer sweep position."""
        if not self._shimmer_widget:
            return
            
        self._shimmer_pos += 3  # Speed of shimmer sweep
        if self._shimmer_pos > 240:  # Past card width + buffer
            self._shimmer_pos = -60  # Reset to start
            
        # Get shiny color for shimmer
        shiny_color = EXCEPTIONAL_ENTITY_COLORS.get(self.entity.id, (255, 215, 0))
        r, g, b = shiny_color
        
        # Create gradient shimmer effect at current position
        pos_pct = max(0, min(100, int((self._shimmer_pos / 180) * 100)))
        
        self._shimmer_widget.setStyleSheet(f"""
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0.5,
                stop: {max(0, pos_pct - 15) / 100:.2f} transparent,
                stop: {pos_pct / 100:.2f} rgba({r}, {g}, {b}, 40),
                stop: {min(100, pos_pct + 15) / 100:.2f} transparent
            );
        """)
    
    def _get_glow_value(self):
        return self._glow_value
    
    def _set_glow_value(self, value):
        self._glow_value = value
        self._update_exceptional_style()
    
    glow_value = QtCore.Property(float, _get_glow_value, _set_glow_value)
    
    def _update_exceptional_style(self):
        """Update the stylesheet for animated border shimmer effect."""
        if not self.is_exceptional:
            return
        
        # Use rarity background
        rarity = self.entity.rarity.lower()
        bg_base = RARITY_BG.get(rarity, "#2D2D2D")
        gradient_start = "#0D0D0D"
        gradient_end = bg_base
        
        # Get predefined shiny color for this entity
        shiny_color = EXCEPTIONAL_ENTITY_COLORS.get(self.entity.id, (255, 215, 0))  # Default gold
        
        # Create color shimmer effect for border
        r_base, g_base, b_base = shiny_color
        
        # Pulse between the base color and a brighter version
        brightness_factor = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(self._glow_value * math.pi * 2))
        
        r = min(255, int(r_base + (255 - r_base) * (1 - brightness_factor) * 0.5))
        g = min(255, int(g_base + (255 - g_base) * (1 - brightness_factor) * 0.5))
        b = min(255, int(b_base + (255 - b_base) * (1 - brightness_factor) * 0.5))
        
        border_color = f"#{r:02X}{g:02X}{b:02X}"
        
        # Fixed border width (no bouncing)
        self.setStyleSheet(f"""
            EntityCard {{
                background: qradialgradient(
                    cx: 0.5, cy: 0.5, radius: 0.8,
                    fx: 0.5, fy: 0.5,
                    stop: 0 {gradient_start},
                    stop: 1 {gradient_end}
                );
                border: 3px solid {border_color};
                border-radius: 12px;
            }}
        """)
        
        # Animate sparkle positions around the card
        self._update_sparkle_positions()
    
    def _update_sparkle_positions(self):
        """Animate sparkle decorations floating around the card with varying sizes."""
        if not self._sparkle_labels:
            return
        
        # Get shiny color for sparkle tint
        shiny_color = EXCEPTIONAL_ENTITY_COLORS.get(self.entity.id, (255, 215, 0))
        r, g, b = shiny_color
        
        # Sparkle positions orbit around the card
        positions = [
            (10, 10), (160, 10),   # Top corners
            (5, 100), (165, 100),  # Sides
            (40, 200), (130, 200), # Bottom
        ]
        
        for i, sparkle in enumerate(self._sparkle_labels):
            # Oscillate position and opacity with different phases
            phase = (self._glow_value * math.pi * 2) + (i * math.pi / 3)
            
            base_x, base_y = positions[i % len(positions)]
            # Larger orbit movement
            offset_x = math.sin(phase) * 8
            offset_y = math.cos(phase) * 8
            
            sparkle.move(int(base_x + offset_x), int(base_y + offset_y))
            
            # Vary font size for twinkling effect (10-16px)
            size = int(10 + 6 * (0.5 + 0.5 * math.sin(phase * 1.5)))
            
            # Pulse opacity (0.4 - 1.0)
            opacity = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(phase))
            sparkle.setStyleSheet(f"""
                color: rgb({r},{g},{b}); 
                background: transparent; 
                font-size: {size}px;
            """)
        
        # Update halo particles if they exist
        self._update_halo_particles()
    
    def _update_halo_particles(self):
        """Update rotating halo particles around the icon."""
        if not self._halo_particles:
            return
            
        shiny_color = EXCEPTIONAL_ENTITY_COLORS.get(self.entity.id, (255, 215, 0))
        r, g, b = shiny_color
        
        # Icon center position (90, 74 for 128x128 icon centered in 180 width card)
        center_x, center_y = 90, 74
        radius = 70  # Orbit radius around icon
        
        for i, particle in enumerate(self._halo_particles):
            # Each particle has different phase offset for smooth rotation
            angle = (self._glow_value * math.pi * 2) + (i * math.pi * 2 / len(self._halo_particles))
            
            x = center_x + radius * math.cos(angle) - 6  # -6 to center the particle
            y = center_y + radius * math.sin(angle) - 6
            
            particle.move(int(x), int(y))
            
            # Pulse opacity based on position (brighter at top)
            opacity_factor = 0.5 + 0.5 * math.sin(angle + math.pi / 2)
            particle.setStyleSheet(f"""
                color: rgba({r},{g},{b},{int(150 + 105 * opacity_factor)}); 
                background: transparent; 
                font-size: 10px;
            """)
    
    def _add_sparkle_decorations(self):
        """Add floating sparkle decorations around the card for exceptional entities."""
        shiny_color = EXCEPTIONAL_ENTITY_COLORS.get(self.entity.id, (255, 215, 0))
        r, g, b = shiny_color
        
        # Create sparkle emoji labels positioned absolutely on card
        sparkle_chars = ["✦", "✧", "★", "✦", "✧", "★"]
        positions = [
            (10, 10), (160, 10),   # Top corners
            (5, 100), (165, 100),  # Sides
            (40, 200), (130, 200), # Bottom
        ]
        
        for i, (x, y) in enumerate(positions):
            sparkle = QtWidgets.QLabel(sparkle_chars[i], self)
            sparkle.setStyleSheet(f"color: rgb({r},{g},{b}); background: transparent; font-size: 12px;")
            sparkle.setFixedSize(20, 20)  # Slightly larger for size animation
            sparkle.move(x, y)
            sparkle.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
            sparkle.show()
            self._sparkle_labels.append(sparkle)
        
        # Add rotating halo particles around the icon
        self._add_halo_particles()
    
    def _add_halo_particles(self):
        """Add rotating particle effect around the entity icon."""
        shiny_color = EXCEPTIONAL_ENTITY_COLORS.get(self.entity.id, (255, 215, 0))
        r, g, b = shiny_color
        
        # Create 8 small particles that will orbit the icon
        particle_chars = ["•", "◦", "·", "•", "◦", "·", "•", "◦"]
        
        for i, char in enumerate(particle_chars):
            particle = QtWidgets.QLabel(char, self)
            particle.setStyleSheet(f"color: rgb({r},{g},{b}); background: transparent; font-size: 10px;")
            particle.setFixedSize(12, 12)
            particle.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
            particle.show()
            self._halo_particles.append(particle)
        
    def _build_ui(self):
        rarity = self.entity.rarity.lower()
        rarity_color = RARITY_COLORS.get(rarity, "#9E9E9E")
        bg_base = RARITY_BG.get(rarity, "#2D2D2D")
        gradient_start = "#0D0D0D"  # Very dark center
        gradient_end = bg_base  # Rarity-tinted outer
        
        # Exceptional entities get golden outline with rarity background
        if self.is_exceptional and self.is_collected:
            # Get predefined shiny color for border
            shiny_color = EXCEPTIONAL_ENTITY_COLORS.get(self.entity.id, (255, 215, 0))
            shiny_hex = f"#{shiny_color[0]:02X}{shiny_color[1]:02X}{shiny_color[2]:02X}"
            self.setStyleSheet(f"""
                EntityCard {{
                    background: qradialgradient(
                        cx: 0.5, cy: 0.5, radius: 0.8,
                        fx: 0.5, fy: 0.5,
                        stop: 0 {gradient_start},
                        stop: 1 {gradient_end}
                    );
                    border: 3px solid {shiny_hex};
                    border-radius: 12px;
                }}
            """)
        elif self.is_collected:
            # Card styling based on collection status - gradient background with rarity border
            self.setStyleSheet(f"""
                EntityCard {{
                    background: qradialgradient(
                        cx: 0.5, cy: 0.5, radius: 0.8,
                        fx: 0.5, fy: 0.5,
                        stop: 0 {gradient_start},
                        stop: 1 {gradient_end}
                    );
                    border: 3px solid {rarity_color};
                    border-radius: 12px;
                }}
                EntityCard:hover {{
                    border: 3px solid #FFD700;
                    background: qradialgradient(
                        cx: 0.5, cy: 0.5, radius: 0.8,
                        fx: 0.5, fy: 0.5,
                        stop: 0 #151515,
                        stop: 1 {gradient_end}
                    );
                }}
            """)
        else:
            # Darker, mysterious look for uncollected
            gradient_start = "#080808"
            gradient_end = "#1A1A1A"
            # Give exceptional uncollected slots a subtle golden border hint
            if self.is_exceptional:
                border_color = "#3A3A20"  # Dim gold hint
            else:
                border_color = "#2A2A2A"
            self.setStyleSheet(f"""
                EntityCard {{
                    background: qradialgradient(
                        cx: 0.5, cy: 0.5, radius: 0.8,
                        fx: 0.5, fy: 0.5,
                        stop: 0 {gradient_start},
                        stop: 1 {gradient_end}
                    );
                    border: 3px solid {border_color};
                    border-radius: 12px;
                }}
                EntityCard:hover {{
                    border: 3px solid {"#5A5A30" if self.is_exceptional else "#444444"};
                    background: qradialgradient(
                        cx: 0.5, cy: 0.5, radius: 0.8,
                        fx: 0.5, fy: 0.5,
                        stop: 0 #101010,
                        stop: 1 #222222
                    );
                }}
            """)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Entity icon - resolve SVG path properly
        # Use exceptional SVG if entity is collected and exceptional
        use_exceptional = self.is_collected and self.is_exceptional
        svg_path = _resolve_entity_svg_path(self.entity, is_exceptional=use_exceptional)
        
        # Center the SVG (matching preview_entities.py layout)
        svg_container = QtWidgets.QWidget()
        svg_layout = QtWidgets.QHBoxLayout(svg_container)
        svg_layout.addStretch()
        svg_layout.setContentsMargins(0, 0, 0, 0)
        
        if svg_path and os.path.exists(svg_path):
            if self.is_collected:
                if HAS_WEBENGINE:
                    # Use AnimatedSvgWidget for all collected entities (supports SMIL animations)
                    # This enables wagging tails, electricity effects, rotating elements, etc.
                    icon_widget = AnimatedSvgWidget(svg_path)
                else:
                    # Fallback to QSvgWidget if WebEngine not available
                    icon_widget = QSvgWidget(svg_path)
                    icon_widget.setFixedSize(128, 128)
                    icon_widget.setStyleSheet("background: transparent;")
                # Store reference for animation
                self._icon_widget = icon_widget
            else:
                # Silhouette for uncollected - also 128x128
                icon_widget = SilhouetteSvgWidget(svg_path)
                icon_widget.setFixedSize(128, 128)
        else:
            # Placeholder if no SVG
            icon_widget = QtWidgets.QLabel("❓")
            icon_widget.setAlignment(QtCore.Qt.AlignCenter)
            icon_widget.setFixedSize(128, 128)
            icon_widget.setStyleSheet("font-size: 64px; color: #333333;")
        
        svg_layout.addWidget(icon_widget)
        svg_layout.addStretch()
        layout.addWidget(svg_container)
        
        # Entity name - matching preview_entities.py style
        # For exceptional entities, show the playful exceptional_name if available
        if self.is_collected:
            if self.is_exceptional and self.entity.exceptional_name:
                name_text = self.entity.exceptional_name
            else:
                name_text = self.entity.name
            name_color = rarity_color
        elif self.is_encountered:
            name_text = "???"
            name_color = "#555555"
        else:
            name_text = "???"
            name_color = "#333333"
        
        # Add star prefix for exceptional slot
        if self.is_exceptional and not self.is_collected:
            name_text = f"⭐ {name_text}"
            name_color = "#4A4A2A"  # Dim gold hint
        
        name_label = QtWidgets.QLabel(name_text)
        name_label.setAlignment(QtCore.Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setFont(QtGui.QFont("Segoe UI", 8, QtGui.QFont.Bold))
        name_label.setStyleSheet(f"color: {name_color}; background: transparent;")
        name_label.setMinimumHeight(32)  # Reserve space for two lines
        layout.addWidget(name_label, 0, QtCore.Qt.AlignCenter)
        
        # Power display - matching preview_entities.py style
        if self.is_collected:
            power_text = f"⚔️ Power: {self.entity.power}"
            power_color = "#FFFFFF"
        else:
            power_text = "⚔️ ???"
            power_color = "#333333"
        
        power_label = QtWidgets.QLabel(power_text)
        power_label.setAlignment(QtCore.Qt.AlignCenter)
        power_label.setFont(QtGui.QFont("Segoe UI", 10))
        power_label.setStyleSheet(f"color: {power_color}; background: transparent;")
        layout.addWidget(power_label)
        
        # Rarity badge - styled like preview_entities.py
        if self.is_collected:
            # Add star icon for exceptional entities
            if self.is_exceptional:
                rarity_text = f"⭐ {rarity.upper()}"
            else:
                rarity_text = rarity.upper()
            rarity_label_color = rarity_color
        else:
            # Show star hint for exceptional slot
            if self.is_exceptional:
                rarity_text = "⭐ ???"
                rarity_label_color = "#4A4A2A"  # Dim gold hint
            else:
                rarity_text = "???"
                rarity_label_color = "#333333"
        
        rarity_label = QtWidgets.QLabel(rarity_text)
        rarity_label.setAlignment(QtCore.Qt.AlignCenter)
        rarity_label.setFont(QtGui.QFont("Segoe UI", 9, QtGui.QFont.Bold))
        rarity_label.setStyleSheet(f"color: {rarity_label_color}; background: transparent;")
        layout.addWidget(rarity_label)
        
        # Card size: 180 wide, 235 tall (extra height for two-line names)
        self.setFixedSize(180, 235)
        
        # Add sparkle decorations for exceptional entities (after setFixedSize so they can be positioned)
        if self.is_collected and self.is_exceptional:
            self._add_sparkle_decorations()
    
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit(self.entity, self.is_exceptional)
        super().mousePressEvent(event)


# Theme info for tabs (matching preview_entities.py)
THEME_INFO = {
    "warrior": ("🗡️ Warrior", "#C62828"),
    "scholar": ("📚 Scholar", "#6A1B9A"),
    "underdog": ("💪 Underdog", "#E65100"),
    "scientist": ("🔬 Scientist", "#1565C0"),
    "wanderer": ("🗺️ Wanderer", "#2E7D32"),
}


class EntitidexTab(QtWidgets.QWidget):
    """
    Main Entitidex tab showing the entity collection.
    Uses tabbed interface with one tab per story theme (matching preview_entities.py).
    """
    
    def __init__(self, blocker, parent=None):
        super().__init__(parent)
        self.blocker = blocker
        self.current_story = "warrior"
        self.progress = EntitidexProgress()
        self.theme_tabs = {}  # Store references to theme tab widgets
        
        # Load progress from blocker if available
        self._load_progress()
        
        self._build_ui()
    
    def _load_progress(self):
        """Load entitidex progress from blocker config."""
        try:
            if hasattr(self.blocker, 'adhd_buster'):
                entitidex_data = self.blocker.adhd_buster.get("entitidex", {})
                if entitidex_data:
                    # Support both old "collected" and new "collected_entity_ids" keys
                    collected = set(entitidex_data.get("collected_entity_ids", 
                                    entitidex_data.get("collected", [])))
                    encounters = entitidex_data.get("encounters", {})
                    exceptional = entitidex_data.get("exceptional_entities", {})
                    self.progress.collected_entity_ids = collected
                    self.progress.encounters = encounters
                    self.progress.exceptional_entities = exceptional
        except Exception as e:
            print(f"Error loading entitidex progress: {e}")
    
    def _save_progress(self):
        """Save entitidex progress to blocker config."""
        try:
            if hasattr(self.blocker, 'adhd_buster'):
                self.blocker.adhd_buster["entitidex"] = {
                    "collected_entity_ids": list(self.progress.collected_entity_ids),
                    "encounters": self.progress.encounters,
                    "exceptional_entities": self.progress.exceptional_entities,
                }
                self.blocker.save_config()
        except Exception as e:
            print(f"Error saving entitidex progress: {e}")
    
    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header_layout = QtWidgets.QHBoxLayout()
        
        title = QtWidgets.QLabel("📖 Entitidex")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #FFD700;
            }
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Overall progress label
        self.total_progress_label = QtWidgets.QLabel()
        self.total_progress_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        header_layout.addWidget(self.total_progress_label)
        
        layout.addLayout(header_layout)
        
        # Tab widget for themes (matching preview_entities.py style)
        self.theme_tab_widget = QtWidgets.QTabWidget()
        self.theme_tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444444;
                background-color: #1A1A1A;
            }
            QTabBar::tab {
                background-color: #2D2D2D;
                color: #FFFFFF;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background-color: #444444;
            }
            QTabBar::tab:hover {
                background-color: #3A3A3A;
            }
        """)
        
        # Create a tab for each theme
        for theme_key, (theme_name, theme_color) in THEME_INFO.items():
            tab_widget = self._create_theme_tab(theme_key)
            self.theme_tab_widget.addTab(tab_widget, theme_name)
            self.theme_tabs[theme_key] = tab_widget
        
        layout.addWidget(self.theme_tab_widget)
        
        # Detail panel (shown when entity is clicked)
        self.detail_panel = QtWidgets.QFrame()
        self.detail_panel.setStyleSheet("""
            QFrame {
                background: #1E1E1E;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        self.detail_panel.setVisible(False)
        
        detail_layout = QtWidgets.QVBoxLayout(self.detail_panel)
        
        self.detail_name = QtWidgets.QLabel()
        self.detail_name.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.detail_name.setAlignment(QtCore.Qt.AlignCenter)
        detail_layout.addWidget(self.detail_name)
        
        self.detail_lore = QtWidgets.QLabel()
        self.detail_lore.setWordWrap(True)
        self.detail_lore.setStyleSheet("color: #CCCCCC; font-size: 12px; padding: 10px;")
        self.detail_lore.setAlignment(QtCore.Qt.AlignCenter)
        detail_layout.addWidget(self.detail_lore)
        
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #444;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background: #555;
            }
        """)
        close_btn.clicked.connect(lambda: self.detail_panel.setVisible(False))
        detail_layout.addWidget(close_btn, 0, QtCore.Qt.AlignCenter)
        
        layout.addWidget(self.detail_panel)
        
        # Load initial data
        self._refresh_all_tabs()
    
    def _create_theme_tab(self, theme_key: str) -> QtWidgets.QWidget:
        """Create a tab widget for a specific theme."""
        tab_container = QtWidgets.QWidget()
        tab_layout = QtWidgets.QVBoxLayout(tab_container)
        tab_layout.setSpacing(10)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        
        # Progress bar for this theme
        progress_frame = QtWidgets.QFrame()
        progress_frame.setStyleSheet("""
            QFrame {
                background: #1E1E1E;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        progress_layout = QtWidgets.QVBoxLayout(progress_frame)
        
        progress_label = QtWidgets.QLabel(f"Collection Progress - {theme_key.capitalize()}")
        progress_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        progress_label.setObjectName(f"progress_label_{theme_key}")
        progress_layout.addWidget(progress_label)
        
        progress_bar = QtWidgets.QProgressBar()
        progress_bar.setMaximum(100)
        progress_bar.setTextVisible(True)
        progress_bar.setObjectName(f"progress_bar_{theme_key}")
        progress_bar.setStyleSheet("""
            QProgressBar {
                background: #333333;
                border-radius: 5px;
                text-align: center;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:1 #8BC34A);
                border-radius: 5px;
            }
        """)
        progress_layout.addWidget(progress_bar)
        
        stats_label = QtWidgets.QLabel()
        stats_label.setAlignment(QtCore.Qt.AlignCenter)
        stats_label.setStyleSheet("color: #888888; font-size: 11px;")
        stats_label.setObjectName(f"stats_label_{theme_key}")
        progress_layout.addWidget(stats_label)
        
        tab_layout.addWidget(progress_frame)
        
        # Scroll area for entity cards
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #1E1E1E;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #444444;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        cards_container = QtWidgets.QWidget()
        cards_container.setObjectName(f"cards_container_{theme_key}")
        cards_layout = QtWidgets.QGridLayout(cards_container)
        cards_layout.setSpacing(16)
        cards_layout.setContentsMargins(16, 16, 16, 16)
        
        scroll.setWidget(cards_container)
        tab_layout.addWidget(scroll)
        
        return tab_container
    
    def _create_entity_pair_widget(self, entity: Entity) -> QtWidgets.QWidget:
        """Create a widget containing both normal and exceptional cards for an entity."""
        pair_widget = QtWidgets.QWidget()
        pair_layout = QtWidgets.QHBoxLayout(pair_widget)
        pair_layout.setContentsMargins(0, 0, 0, 0)
        pair_layout.setSpacing(8)
        
        # Normal card
        is_collected_normal = self.progress.is_collected(entity.id) and not self.progress.is_exceptional(entity.id)
        # If user has exceptional, they also have normal (exceptional is upgrade)
        if self.progress.is_collected(entity.id):
            is_collected_normal = True
        is_encountered = self.progress.is_encountered(entity.id)
        
        normal_card = EntityCard(
            entity, is_collected_normal, is_encountered,
            is_exceptional=False,
            exceptional_colors={}
        )
        normal_card.clicked.connect(self._on_entity_clicked)
        pair_layout.addWidget(normal_card)
        
        # Exceptional card
        is_collected_exceptional = self.progress.is_exceptional(entity.id)
        exceptional_colors = self.progress.get_exceptional_colors(entity.id)
        
        exceptional_card = EntityCard(
            entity, is_collected_exceptional, is_encountered,
            is_exceptional=True,
            exceptional_colors=exceptional_colors
        )
        exceptional_card.clicked.connect(self._on_entity_clicked)
        pair_layout.addWidget(exceptional_card)
        
        return pair_widget

    def _refresh_theme_tab(self, theme_key: str):
        """Refresh a single theme tab."""
        if theme_key not in self.theme_tabs:
            return
            
        tab_widget = self.theme_tabs[theme_key]
        
        # Find the cards container and clear it
        cards_container = tab_widget.findChild(QtWidgets.QWidget, f"cards_container_{theme_key}")
        if not cards_container:
            return
            
        cards_layout = cards_container.layout()
        
        # Clear existing cards
        while cards_layout.count():
            child = cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Get entities for this theme
        entities = get_entities_for_story(theme_key)
        entities_sorted = sorted(entities, key=lambda e: e.power)
        
        # Calculate progress - count normal and exceptional separately
        collected_normal = 0
        collected_exceptional = 0
        encountered_count = 0
        
        for entity in entities_sorted:
            if self.progress.is_collected(entity.id):
                collected_normal += 1
                if self.progress.is_exceptional(entity.id):
                    collected_exceptional += 1
            elif self.progress.is_encountered(entity.id):
                encountered_count += 1
        
        total_entities = len(entities_sorted)
        total_slots = total_entities * 2  # Normal + Exceptional for each
        total_collected = collected_normal + collected_exceptional
        progress_percent = int((total_collected / total_slots) * 100) if total_slots > 0 else 0
        
        # Update progress display for this tab
        progress_bar = tab_widget.findChild(QtWidgets.QProgressBar, f"progress_bar_{theme_key}")
        if progress_bar:
            progress_bar.setValue(progress_percent)
            progress_bar.setFormat(f"{total_collected}/{total_slots} ({progress_percent}%)")
        
        stats_label = tab_widget.findChild(QtWidgets.QLabel, f"stats_label_{theme_key}")
        if stats_label:
            stats_label.setText(
                f"✅ Normal: {collected_normal}/{total_entities}  |  "
                f"⭐ Exceptional: {collected_exceptional}/{total_entities}  |  "
                f"👁️ Encountered: {encountered_count}"
            )
        
        # Create paired cards - Layout: Each entity gets [Normal | Exceptional] pair
        # Sort by rarity for proper grouping
        rarity_order = {"common": 0, "uncommon": 1, "rare": 2, "epic": 3, "legendary": 4}
        entities_by_rarity = sorted(entities_sorted, key=lambda e: rarity_order.get(e.rarity.lower(), 0))
        
        # Separate legendary from others
        legendary = [e for e in entities_by_rarity if e.rarity.lower() == "legendary"]
        others = [e for e in entities_by_rarity if e.rarity.lower() != "legendary"]
        
        # Layout grid with paired cards (each pair is wider, so 2 pairs per row)
        # Row 0: Legendary pair centered
        # Row 1-2: Epic pairs
        # Row 3-4: Rare pairs  
        # Row 5-6: Uncommon pairs
        # Row 7-8: Common pairs
        
        current_row = 0
        
        # Add legendary at top center
        for entity in legendary:
            pair_widget = self._create_entity_pair_widget(entity)
            cards_layout.addWidget(pair_widget, current_row, 0, 1, 1, QtCore.Qt.AlignCenter)
            current_row += 1
        
        # Sort remaining by rarity (highest first for display)
        epic = [e for e in others if e.rarity.lower() == "epic"]
        rare = [e for e in others if e.rarity.lower() == "rare"]
        uncommon = [e for e in others if e.rarity.lower() == "uncommon"]
        common = [e for e in others if e.rarity.lower() == "common"]
        
        # Add each rarity group - one entity pair per row, centered
        for rarity_group in [epic, rare, uncommon, common]:
            for entity in rarity_group:
                pair_widget = self._create_entity_pair_widget(entity)
                cards_layout.addWidget(pair_widget, current_row, 0, 1, 1, QtCore.Qt.AlignCenter)
                current_row += 1
    
    def _refresh_all_tabs(self):
        """Refresh all theme tabs and update total progress."""
        total_normal = 0
        total_exceptional = 0
        total_entities = 0
        
        for theme_key in THEME_INFO.keys():
            self._refresh_theme_tab(theme_key)
            
            # Count for total progress
            entities = get_entities_for_story(theme_key)
            total_entities += len(entities)
            for entity in entities:
                if self.progress.is_collected(entity.id):
                    total_normal += 1
                    if self.progress.is_exceptional(entity.id):
                        total_exceptional += 1
        
        # Update total progress label (both normal and exceptional)
        total_slots = total_entities * 2  # Normal + Exceptional for each
        total_collected = total_normal + total_exceptional
        total_percent = int((total_collected / total_slots) * 100) if total_slots > 0 else 0
        self.total_progress_label.setText(
            f"Total: {total_collected}/{total_slots} ({total_percent}%) | "
            f"Normal: {total_normal} | ⭐ Exceptional: {total_exceptional}"
        )
    
    def _on_story_changed(self, story: str):
        """Legacy method - kept for compatibility."""
        self.current_story = story
        # Find and select the corresponding tab
        theme_keys = list(THEME_INFO.keys())
        if story in theme_keys:
            self.theme_tab_widget.setCurrentIndex(theme_keys.index(story))
    
    def _on_entity_clicked(self, entity: Entity, is_exceptional: bool = False):
        """Handle entity card click - show details if collected."""
        # Check if this specific variant is collected
        is_normal_collected = self.progress.is_collected(entity.id)
        is_exceptional_collected = self.progress.is_exceptional(entity.id)
        
        # Determine which variant was clicked and if it's collected
        if is_exceptional:
            is_this_collected = is_exceptional_collected
            variant_text = "⭐ Exceptional "
        else:
            is_this_collected = is_normal_collected
            variant_text = ""
        
        if is_this_collected:
            rarity_color = RARITY_COLORS.get(entity.rarity.lower(), "#9E9E9E")
            # Use shiny color for exceptional
            if is_exceptional:
                shiny_color = EXCEPTIONAL_ENTITY_COLORS.get(entity.id, (255, 215, 0))
                rarity_color = f"#{shiny_color[0]:02X}{shiny_color[1]:02X}{shiny_color[2]:02X}"
            # Use exceptional_name for exceptional entities if available
            display_name = entity.exceptional_name if is_exceptional and entity.exceptional_name else entity.name
            self.detail_name.setText(f"{variant_text}{display_name}")
            self.detail_name.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {rarity_color};")
            if is_exceptional:
                self.detail_lore.setText(f"⭐ EXCEPTIONAL VARIANT ⭐\n\n{entity.lore}\n\n✨ This rare variant has unique coloring and special animations!")
            else:
                self.detail_lore.setText(entity.lore)
            self.detail_panel.setVisible(True)
        else:
            # Show hint for uncollected
            if is_exceptional:
                self.detail_name.setText("⭐ ??? Exceptional Unknown")
                self.detail_name.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFD700;")
                if is_normal_collected:
                    self.detail_lore.setText(f"You have the normal {entity.name}, but not the exceptional variant!\n\n✨ Exceptional entities are rare special versions with unique colors and animations.\n\nKeep completing focus sessions for a chance to find this exceptional variant!")
                else:
                    self.detail_lore.setText("This exceptional entity awaits discovery.\n\n✨ Exceptional entities are rare special versions with unique colors.\n\nComplete focus sessions to encounter entities - some may be exceptional!")
            else:
                self.detail_name.setText("??? Unknown Entity")
                self.detail_name.setStyleSheet("font-size: 18px; font-weight: bold; color: #666666;")
                if self.progress.is_encountered(entity.id):
                    self.detail_lore.setText("You've seen this entity before, but haven't bonded yet.\nComplete focus sessions to encounter it again!")
                else:
                    self.detail_lore.setText("This entity awaits discovery.\nComplete focus sessions to encounter new companions!")
            self.detail_panel.setVisible(True)
    
    def add_collected_entity(self, entity_id: str):
        """Mark an entity as collected and refresh display."""
        self.progress.collected_entity_ids.add(entity_id)
        self._save_progress()
        self._refresh_all_tabs()
    
    def add_encountered_entity(self, entity_id: str):
        """Mark an entity as encountered and refresh display."""
        self.progress.record_encounter(entity_id)
        self._save_progress()
        self._refresh_all_tabs()
    
    def refresh(self):
        """Public method to refresh the display."""
        self._load_progress()
        self._refresh_all_tabs()
