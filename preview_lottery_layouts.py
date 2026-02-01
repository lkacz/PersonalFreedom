"""
Preview of different minimalistic layout variants for the lottery reward dialog.
Focus on reducing visual clutter from outlines/borders.
"""

import sys
from PySide6 import QtWidgets, QtCore, QtGui


class BaseLayoutPreview(QtWidgets.QFrame):
    """Base preview with shared elements."""
    
    TIER_COLORS = {
        "Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3",
        "Epic": "#9c27b0", "Legendary": "#ff9800"
    }
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setMinimumSize(420, 400)
        self._variant_title = title
        
    def _create_header(self, text: str, color: str = "#9ca3af") -> QtWidgets.QLabel:
        header = QtWidgets.QLabel(text)
        header.setAlignment(QtCore.Qt.AlignCenter)
        header.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {color}; background: transparent; border: none;")
        return header
    
    def _create_stage_title(self, text: str, color: str = "#aaa") -> QtWidgets.QLabel:
        label = QtWidgets.QLabel(text)
        label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: bold; background: transparent; border: none;")
        return label
    
    def _create_result_label(self, text: str, color: str = "#888") -> QtWidgets.QLabel:
        label = QtWidgets.QLabel(text)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet(f"color: {color}; font-size: 14px; background: transparent; border: none;")
        return label
    
    def _create_continue_btn(self) -> QtWidgets.QPushButton:
        btn = QtWidgets.QPushButton("Continue")
        btn.setStyleSheet("""
            QPushButton {
                background: #4caf50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background: #66bb6a; }
        """)
        return btn
    
    def _create_tier_bar(self) -> QtWidgets.QWidget:
        """Create a simple tier probability bar."""
        bar = QtWidgets.QWidget()
        bar.setFixedHeight(35)
        bar.setStyleSheet("background: transparent; border: none;")
        
        layout = QtWidgets.QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create segments - Common 80%, Uncommon 15%, Rare 5%
        segments = [
            ("Common", 80, "#9e9e9e"),
            ("Uncommon", 15, "#4caf50"),
            ("Rare", 5, "#2196f3"),
        ]
        
        for tier, pct, color in segments:
            seg = QtWidgets.QFrame()
            seg.setStyleSheet(f"background: {color}; border: none;")
            layout.addWidget(seg, pct)
        
        return bar
    
    def _create_success_bar(self, success_pct: int = 99) -> QtWidgets.QWidget:
        """Create a success/fail probability bar."""
        bar = QtWidgets.QWidget()
        bar.setFixedHeight(35)
        bar.setStyleSheet("background: transparent; border: none;")
        
        layout = QtWidgets.QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Win zone
        win = QtWidgets.QFrame()
        win.setStyleSheet("background: #2e7d32; border: none;")
        layout.addWidget(win, success_pct)
        
        # Fail zone
        fail = QtWidgets.QFrame()
        fail.setStyleSheet("background: #c62828; border: none;")
        layout.addWidget(fail, 100 - success_pct)
        
        return bar
    
    def _create_sound_toggle(self) -> QtWidgets.QCheckBox:
        cb = QtWidgets.QCheckBox("🔊 Sound")
        cb.setStyleSheet("color: #666; font-size: 11px; background: transparent; border: none;")
        return cb


# ============================================================================
# VARIANT 1: Current Design (with prominent borders)
# ============================================================================

class Variant1_CurrentDesign(BaseLayoutPreview):
    """Current design with blue outlined frames."""
    
    def __init__(self, parent=None):
        super().__init__("Variant 1: Current (Prominent Borders)", parent)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: #1a1a2e;
                border: 2px solid #4a4a6a;
                border-radius: 12px;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 16, 20, 16)
        
        layout.addWidget(self._create_header("👁️ Eyes Routine Reward 👁️"))
        
        # Stage 1 Frame - with border
        stage1 = QtWidgets.QFrame()
        stage1.setStyleSheet("QFrame { background: #252540; border: 2px solid #444; border-radius: 8px; }")
        s1_layout = QtWidgets.QVBoxLayout(stage1)
        s1_layout.setContentsMargins(12, 8, 12, 8)
        s1_layout.addWidget(self._create_stage_title("✨ Stage 1: Rolling for Rarity..."))
        s1_layout.addWidget(self._create_tier_bar())
        s1_layout.addWidget(self._create_result_label("Common!"))
        layout.addWidget(stage1)
        
        # Stage 2 Frame - with border
        stage2 = QtWidgets.QFrame()
        stage2.setStyleSheet("QFrame { background: #252540; border: 2px solid #444; border-radius: 8px; }")
        s2_layout = QtWidgets.QVBoxLayout(stage2)
        s2_layout.setContentsMargins(12, 8, 12, 8)
        s2_layout.addWidget(self._create_stage_title("🎲 Stage 2: Will you get the Common? (99% chance)"))
        s2_layout.addWidget(self._create_success_bar())
        s2_layout.addWidget(self._create_result_label("✨ SUCCESS! ✨", "#4caf50"))
        layout.addWidget(stage2)
        
        layout.addWidget(self._create_result_label("You got Common!"))
        layout.addStretch()
        
        sound_row = QtWidgets.QHBoxLayout()
        sound_row.addStretch()
        sound_row.addWidget(self._create_sound_toggle())
        layout.addLayout(sound_row)
        
        layout.addWidget(self._create_continue_btn(), alignment=QtCore.Qt.AlignCenter)


# ============================================================================
# VARIANT 2: No Inner Borders (subtle backgrounds only)
# ============================================================================

class Variant2_NoInnerBorders(BaseLayoutPreview):
    """Removes inner stage borders, uses subtle background difference only."""
    
    def __init__(self, parent=None):
        super().__init__("Variant 2: No Inner Borders", parent)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet("""
            QFrame#outer {
                background: #1a1a2e;
                border: 2px solid #4a4a6a;
                border-radius: 12px;
            }
        """)
        self.setObjectName("outer")
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)
        
        layout.addWidget(self._create_header("👁️ Eyes Routine Reward 👁️"))
        
        # Stage 1 - subtle background, NO border
        stage1 = QtWidgets.QFrame()
        stage1.setStyleSheet("QFrame { background: #252540; border: none; border-radius: 8px; }")
        s1_layout = QtWidgets.QVBoxLayout(stage1)
        s1_layout.setContentsMargins(12, 10, 12, 10)
        s1_layout.addWidget(self._create_stage_title("✨ Stage 1: Rolling for Rarity..."))
        s1_layout.addWidget(self._create_tier_bar())
        s1_layout.addWidget(self._create_result_label("Common!"))
        layout.addWidget(stage1)
        
        # Stage 2 - subtle background, NO border
        stage2 = QtWidgets.QFrame()
        stage2.setStyleSheet("QFrame { background: #252540; border: none; border-radius: 8px; }")
        s2_layout = QtWidgets.QVBoxLayout(stage2)
        s2_layout.setContentsMargins(12, 10, 12, 10)
        s2_layout.addWidget(self._create_stage_title("🎲 Stage 2: Will you get the Common? (99% chance)"))
        s2_layout.addWidget(self._create_success_bar())
        s2_layout.addWidget(self._create_result_label("✨ SUCCESS! ✨", "#4caf50"))
        layout.addWidget(stage2)
        
        layout.addWidget(self._create_result_label("You got Common!"))
        layout.addStretch()
        
        sound_row = QtWidgets.QHBoxLayout()
        sound_row.addStretch()
        sound_row.addWidget(self._create_sound_toggle())
        layout.addLayout(sound_row)
        
        layout.addWidget(self._create_continue_btn(), alignment=QtCore.Qt.AlignCenter)


# ============================================================================
# VARIANT 3: Hairline Borders (very subtle 1px)
# ============================================================================

class Variant3_HairlineBorders(BaseLayoutPreview):
    """Ultra-thin 1px borders with low contrast."""
    
    def __init__(self, parent=None):
        super().__init__("Variant 3: Hairline Borders (1px)", parent)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet("""
            QFrame#outer {
                background: #1a1a2e;
                border: 1px solid #3a3a5a;
                border-radius: 12px;
            }
        """)
        self.setObjectName("outer")
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)
        
        layout.addWidget(self._create_header("👁️ Eyes Routine Reward 👁️"))
        
        # Stage 1 - hairline border
        stage1 = QtWidgets.QFrame()
        stage1.setStyleSheet("QFrame { background: #22223a; border: 1px solid #333348; border-radius: 6px; }")
        s1_layout = QtWidgets.QVBoxLayout(stage1)
        s1_layout.setContentsMargins(12, 10, 12, 10)
        s1_layout.addWidget(self._create_stage_title("✨ Stage 1: Rolling for Rarity..."))
        s1_layout.addWidget(self._create_tier_bar())
        s1_layout.addWidget(self._create_result_label("Common!"))
        layout.addWidget(stage1)
        
        # Stage 2 - hairline border
        stage2 = QtWidgets.QFrame()
        stage2.setStyleSheet("QFrame { background: #22223a; border: 1px solid #333348; border-radius: 6px; }")
        s2_layout = QtWidgets.QVBoxLayout(stage2)
        s2_layout.setContentsMargins(12, 10, 12, 10)
        s2_layout.addWidget(self._create_stage_title("🎲 Stage 2: Will you get the Common? (99% chance)"))
        s2_layout.addWidget(self._create_success_bar())
        s2_layout.addWidget(self._create_result_label("✨ SUCCESS! ✨", "#4caf50"))
        layout.addWidget(stage2)
        
        layout.addWidget(self._create_result_label("You got Common!"))
        layout.addStretch()
        
        sound_row = QtWidgets.QHBoxLayout()
        sound_row.addStretch()
        sound_row.addWidget(self._create_sound_toggle())
        layout.addLayout(sound_row)
        
        layout.addWidget(self._create_continue_btn(), alignment=QtCore.Qt.AlignCenter)


# ============================================================================
# VARIANT 4: Card Style (shadow instead of border)
# ============================================================================

class Variant4_CardShadow(BaseLayoutPreview):
    """Uses drop shadows instead of borders for depth."""
    
    def __init__(self, parent=None):
        super().__init__("Variant 4: Card Shadow (no borders)", parent)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet("""
            QFrame#outer {
                background: #1a1a2e;
                border: none;
                border-radius: 12px;
            }
        """)
        self.setObjectName("outer")
        
        # Apply shadow to main frame
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QtGui.QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 18, 24, 18)
        
        layout.addWidget(self._create_header("👁️ Eyes Routine Reward 👁️"))
        
        # Stage 1 - card with shadow
        stage1 = QtWidgets.QFrame()
        stage1.setStyleSheet("QFrame { background: #252540; border: none; border-radius: 8px; }")
        shadow1 = QtWidgets.QGraphicsDropShadowEffect()
        shadow1.setBlurRadius(8)
        shadow1.setColor(QtGui.QColor(0, 0, 0, 60))
        shadow1.setOffset(0, 2)
        stage1.setGraphicsEffect(shadow1)
        s1_layout = QtWidgets.QVBoxLayout(stage1)
        s1_layout.setContentsMargins(14, 12, 14, 12)
        s1_layout.addWidget(self._create_stage_title("✨ Stage 1: Rolling for Rarity..."))
        s1_layout.addWidget(self._create_tier_bar())
        s1_layout.addWidget(self._create_result_label("Common!"))
        layout.addWidget(stage1)
        
        # Stage 2 - card with shadow
        stage2 = QtWidgets.QFrame()
        stage2.setStyleSheet("QFrame { background: #252540; border: none; border-radius: 8px; }")
        shadow2 = QtWidgets.QGraphicsDropShadowEffect()
        shadow2.setBlurRadius(8)
        shadow2.setColor(QtGui.QColor(0, 0, 0, 60))
        shadow2.setOffset(0, 2)
        stage2.setGraphicsEffect(shadow2)
        s2_layout = QtWidgets.QVBoxLayout(stage2)
        s2_layout.setContentsMargins(14, 12, 14, 12)
        s2_layout.addWidget(self._create_stage_title("🎲 Stage 2: Will you get the Common? (99% chance)"))
        s2_layout.addWidget(self._create_success_bar())
        s2_layout.addWidget(self._create_result_label("✨ SUCCESS! ✨", "#4caf50"))
        layout.addWidget(stage2)
        
        layout.addWidget(self._create_result_label("You got Common!"))
        layout.addStretch()
        
        sound_row = QtWidgets.QHBoxLayout()
        sound_row.addStretch()
        sound_row.addWidget(self._create_sound_toggle())
        layout.addLayout(sound_row)
        
        layout.addWidget(self._create_continue_btn(), alignment=QtCore.Qt.AlignCenter)


# ============================================================================
# VARIANT 5: Separator Lines (horizontal dividers)
# ============================================================================

class Variant5_SeparatorLines(BaseLayoutPreview):
    """Uses horizontal separator lines instead of box borders."""
    
    def __init__(self, parent=None):
        super().__init__("Variant 5: Separator Lines", parent)
        self._setup_ui()
    
    def _create_separator(self) -> QtWidgets.QFrame:
        sep = QtWidgets.QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #3a3a5a; border: none;")
        return sep
    
    def _setup_ui(self):
        self.setStyleSheet("""
            QFrame#outer {
                background: #1a1a2e;
                border: 1px solid #3a3a5a;
                border-radius: 12px;
            }
        """)
        self.setObjectName("outer")
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(20, 16, 20, 16)
        
        layout.addWidget(self._create_header("👁️ Eyes Routine Reward 👁️"))
        layout.addWidget(self._create_separator())
        
        # Stage 1 - no frame, just content
        layout.addWidget(self._create_stage_title("✨ Stage 1: Rolling for Rarity..."))
        layout.addWidget(self._create_tier_bar())
        layout.addWidget(self._create_result_label("Common!"))
        
        layout.addSpacing(4)
        layout.addWidget(self._create_separator())
        layout.addSpacing(4)
        
        # Stage 2 - no frame, just content
        layout.addWidget(self._create_stage_title("🎲 Stage 2: Will you get the Common? (99% chance)"))
        layout.addWidget(self._create_success_bar())
        layout.addWidget(self._create_result_label("✨ SUCCESS! ✨", "#4caf50"))
        
        layout.addSpacing(4)
        layout.addWidget(self._create_separator())
        layout.addSpacing(4)
        
        layout.addWidget(self._create_result_label("You got Common!"))
        layout.addStretch()
        
        sound_row = QtWidgets.QHBoxLayout()
        sound_row.addStretch()
        sound_row.addWidget(self._create_sound_toggle())
        layout.addLayout(sound_row)
        
        layout.addWidget(self._create_continue_btn(), alignment=QtCore.Qt.AlignCenter)


# ============================================================================
# VARIANT 6: Gradient Accent Border
# ============================================================================

class Variant6_GradientAccent(BaseLayoutPreview):
    """Outer gradient accent, minimal inner styling."""
    
    def __init__(self, parent=None):
        super().__init__("Variant 6: Gradient Accent (top only)", parent)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet("""
            QFrame#outer {
                background: #1a1a2e;
                border: none;
                border-radius: 12px;
            }
        """)
        self.setObjectName("outer")
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Gradient accent bar at top
        accent = QtWidgets.QFrame()
        accent.setFixedHeight(4)
        accent.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #667eea, stop:0.5 #764ba2, stop:1 #f093fb);
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
        """)
        layout.addWidget(accent)
        
        # Content container
        content = QtWidgets.QWidget()
        content.setStyleSheet("background: transparent; border: none;")
        c_layout = QtWidgets.QVBoxLayout(content)
        c_layout.setSpacing(12)
        c_layout.setContentsMargins(20, 14, 20, 16)
        
        c_layout.addWidget(self._create_header("👁️ Eyes Routine Reward 👁️"))
        
        # Stage 1 - very subtle background
        stage1 = QtWidgets.QFrame()
        stage1.setStyleSheet("QFrame { background: rgba(255,255,255,0.03); border: none; border-radius: 6px; }")
        s1_layout = QtWidgets.QVBoxLayout(stage1)
        s1_layout.setContentsMargins(12, 10, 12, 10)
        s1_layout.addWidget(self._create_stage_title("✨ Stage 1: Rolling for Rarity..."))
        s1_layout.addWidget(self._create_tier_bar())
        s1_layout.addWidget(self._create_result_label("Common!"))
        c_layout.addWidget(stage1)
        
        # Stage 2 - very subtle background
        stage2 = QtWidgets.QFrame()
        stage2.setStyleSheet("QFrame { background: rgba(255,255,255,0.03); border: none; border-radius: 6px; }")
        s2_layout = QtWidgets.QVBoxLayout(stage2)
        s2_layout.setContentsMargins(12, 10, 12, 10)
        s2_layout.addWidget(self._create_stage_title("🎲 Stage 2: Will you get the Common? (99% chance)"))
        s2_layout.addWidget(self._create_success_bar())
        s2_layout.addWidget(self._create_result_label("✨ SUCCESS! ✨", "#4caf50"))
        c_layout.addWidget(stage2)
        
        c_layout.addWidget(self._create_result_label("You got Common!"))
        c_layout.addStretch()
        
        sound_row = QtWidgets.QHBoxLayout()
        sound_row.addStretch()
        sound_row.addWidget(self._create_sound_toggle())
        c_layout.addLayout(sound_row)
        
        c_layout.addWidget(self._create_continue_btn(), alignment=QtCore.Qt.AlignCenter)
        
        layout.addWidget(content)


# ============================================================================
# VARIANT 7: Flat Minimal (no boxes at all)
# ============================================================================

class Variant7_FlatMinimal(BaseLayoutPreview):
    """Completely flat - no boxes, just spacing and typography."""
    
    def __init__(self, parent=None):
        super().__init__("Variant 7: Flat Minimal (no boxes)", parent)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet("""
            QFrame#outer {
                background: #1e1e32;
                border: none;
                border-radius: 12px;
            }
        """)
        self.setObjectName("outer")
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(28, 22, 28, 22)
        
        layout.addWidget(self._create_header("👁️ Eyes Routine Reward 👁️"))
        
        # Stage 1 - just content, larger spacing
        layout.addWidget(self._create_stage_title("✨ Stage 1: Rolling for Rarity...", "#bbb"))
        layout.addWidget(self._create_tier_bar())
        layout.addWidget(self._create_result_label("Common!", "#fff"))
        
        layout.addSpacing(8)
        
        # Stage 2 - just content
        layout.addWidget(self._create_stage_title("🎲 Stage 2: Will you get the Common? (99% chance)", "#bbb"))
        layout.addWidget(self._create_success_bar())
        layout.addWidget(self._create_result_label("✨ SUCCESS! ✨", "#4caf50"))
        
        layout.addSpacing(8)
        
        final = QtWidgets.QLabel("You got Common!")
        final.setAlignment(QtCore.Qt.AlignCenter)
        final.setStyleSheet("color: #fff; font-size: 16px; font-weight: bold; background: transparent; border: none;")
        layout.addWidget(final)
        
        layout.addStretch()
        
        sound_row = QtWidgets.QHBoxLayout()
        sound_row.addStretch()
        sound_row.addWidget(self._create_sound_toggle())
        layout.addLayout(sound_row)
        
        layout.addWidget(self._create_continue_btn(), alignment=QtCore.Qt.AlignCenter)


# ============================================================================
# VARIANT 8: Left Accent Bars
# ============================================================================

class Variant8_LeftAccent(BaseLayoutPreview):
    """Left accent bars for stages instead of full borders."""
    
    def __init__(self, parent=None):
        super().__init__("Variant 8: Left Accent Bars", parent)
        self._setup_ui()
    
    def _create_accent_section(self, accent_color: str, content_widgets: list) -> QtWidgets.QWidget:
        """Create a section with left accent bar."""
        container = QtWidgets.QWidget()
        container.setStyleSheet("background: transparent; border: none;")
        h_layout = QtWidgets.QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(10)
        
        # Left accent bar
        accent = QtWidgets.QFrame()
        accent.setFixedWidth(3)
        accent.setStyleSheet(f"background: {accent_color}; border: none; border-radius: 1px;")
        h_layout.addWidget(accent)
        
        # Content
        content = QtWidgets.QWidget()
        content.setStyleSheet("background: transparent; border: none;")
        c_layout = QtWidgets.QVBoxLayout(content)
        c_layout.setContentsMargins(0, 4, 0, 4)
        c_layout.setSpacing(6)
        for w in content_widgets:
            c_layout.addWidget(w)
        h_layout.addWidget(content, 1)
        
        return container
    
    def _setup_ui(self):
        self.setStyleSheet("""
            QFrame#outer {
                background: #1a1a2e;
                border: 1px solid #3a3a5a;
                border-radius: 12px;
            }
        """)
        self.setObjectName("outer")
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 16, 20, 16)
        
        layout.addWidget(self._create_header("👁️ Eyes Routine Reward 👁️"))
        
        # Stage 1 with purple accent
        s1_widgets = [
            self._create_stage_title("✨ Stage 1: Rolling for Rarity..."),
            self._create_tier_bar(),
            self._create_result_label("Common!")
        ]
        layout.addWidget(self._create_accent_section("#9c27b0", s1_widgets))
        
        # Stage 2 with green accent
        s2_widgets = [
            self._create_stage_title("🎲 Stage 2: Will you get the Common? (99% chance)"),
            self._create_success_bar(),
            self._create_result_label("✨ SUCCESS! ✨", "#4caf50")
        ]
        layout.addWidget(self._create_accent_section("#4caf50", s2_widgets))
        
        layout.addWidget(self._create_result_label("You got Common!"))
        layout.addStretch()
        
        sound_row = QtWidgets.QHBoxLayout()
        sound_row.addStretch()
        sound_row.addWidget(self._create_sound_toggle())
        layout.addLayout(sound_row)
        
        layout.addWidget(self._create_continue_btn(), alignment=QtCore.Qt.AlignCenter)


# ============================================================================
# Main Preview Window
# ============================================================================

class LotteryLayoutPreviewWindow(QtWidgets.QMainWindow):
    """Main window showing all layout variants side by side."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lottery Dialog Layout Variants Preview")
        self.setMinimumSize(1800, 900)
        
        # Central widget with scroll
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: #0d0d1a; border: none; }")
        
        container = QtWidgets.QWidget()
        container.setStyleSheet("background: #0d0d1a;")
        
        # Grid layout for variants (2 rows x 4 columns)
        grid = QtWidgets.QGridLayout(container)
        grid.setSpacing(20)
        grid.setContentsMargins(20, 20, 20, 20)
        
        variants = [
            Variant1_CurrentDesign(),
            Variant2_NoInnerBorders(),
            Variant3_HairlineBorders(),
            Variant4_CardShadow(),
            Variant5_SeparatorLines(),
            Variant6_GradientAccent(),
            Variant7_FlatMinimal(),
            Variant8_LeftAccent(),
        ]
        
        for i, variant in enumerate(variants):
            row = i // 4
            col = i % 4
            
            # Wrapper with title
            wrapper = QtWidgets.QWidget()
            wrapper.setStyleSheet("background: transparent;")
            w_layout = QtWidgets.QVBoxLayout(wrapper)
            w_layout.setContentsMargins(0, 0, 0, 0)
            w_layout.setSpacing(8)
            
            title = QtWidgets.QLabel(variant._variant_title)
            title.setAlignment(QtCore.Qt.AlignCenter)
            title.setStyleSheet("color: #fff; font-size: 13px; font-weight: bold;")
            w_layout.addWidget(title)
            w_layout.addWidget(variant)
            
            grid.addWidget(wrapper, row, col)
        
        scroll.setWidget(container)
        self.setCentralWidget(scroll)


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Dark palette
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#0d0d1a"))
    palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor("#ffffff"))
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#1a1a2e"))
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor("#252540"))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor("#ffffff"))
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor("#2d2d44"))
    palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor("#ffffff"))
    app.setPalette(palette)
    
    window = LotteryLayoutPreviewWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
