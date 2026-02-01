"""
Lottery Animation System - Reusable Slot-Machine Style Roll Animation
======================================================================
Provides dramatic slider animations for any probability-based reward system.
Used by gear merging, eye protection rewards, and other lottery mechanics.
"""

import math
import random
import time
from typing import Optional, Callable
from PySide6 import QtWidgets, QtCore, QtGui


# ============================================================================
# Shared Paint Cache (avoids creating QColor/QFont/QPen in paintEvent)
# ============================================================================

class _PaintCache:
    """Global paint object cache for all lottery widgets.
    
    Creating QColor, QFont, QPen objects is expensive. This cache
    provides pre-created objects to avoid GC churn during 60 FPS animations.
    """
    _initialized = False
    
    # Tier/rarity colors
    TIER_COLORS = {}
    
    # Common colors
    COLOR_WHITE = None
    COLOR_GRAY = None
    COLOR_DARK_BG = None
    COLOR_SUCCESS = None
    COLOR_FAIL = None
    
    # Common fonts
    FONT_LABEL_SMALL = None
    FONT_LABEL_MEDIUM = None
    FONT_LABEL_BOLD = None
    FONT_PERCENT = None
    
    # Common pens
    PEN_SEPARATOR = None
    PEN_BORDER = None
    PEN_MARKER_OUTLINE = None
    PEN_BLACK_OUTLINE = None
    
    @classmethod
    def initialize(cls):
        """Initialize all cached paint objects (lazy loading, called once)."""
        if cls._initialized:
            return
        
        # Tier colors (string -> QColor)
        tier_colors = {
            "Common": "#9e9e9e",
            "Uncommon": "#4caf50",
            "Rare": "#2196f3",
            "Epic": "#9c27b0",
            "Legendary": "#ff9800"
        }
        cls.TIER_COLORS = {k: QtGui.QColor(v) for k, v in tier_colors.items()}
        
        # Common colors
        cls.COLOR_WHITE = QtGui.QColor("#ffffff")
        cls.COLOR_GRAY = QtGui.QColor("#888888")
        cls.COLOR_DARK_BG = QtGui.QColor("#1a1a2e")
        cls.COLOR_SUCCESS = QtGui.QColor("#4caf50")
        cls.COLOR_FAIL = QtGui.QColor("#f44336")
        
        # Fonts
        cls.FONT_LABEL_SMALL = QtGui.QFont("Arial", 7, QtGui.QFont.Bold)
        cls.FONT_LABEL_MEDIUM = QtGui.QFont("Arial", 9, QtGui.QFont.Bold)
        cls.FONT_LABEL_BOLD = QtGui.QFont("Arial", 10, QtGui.QFont.Bold)
        cls.FONT_PERCENT = QtGui.QFont("Arial", 8)
        
        # Pens
        cls.PEN_SEPARATOR = QtGui.QPen(cls.COLOR_DARK_BG, 2)
        cls.PEN_BORDER = QtGui.QPen(QtGui.QColor("#333333"), 2)
        cls.PEN_MARKER_OUTLINE = QtGui.QPen(cls.COLOR_WHITE, 2)
        cls.PEN_BLACK_OUTLINE = QtGui.QPen(QtGui.QColor("#000000"), 1)
        
        cls._initialized = True
    
    @classmethod
    def get_tier_color(cls, tier: str) -> QtGui.QColor:
        """Get cached QColor for a tier, with fallback."""
        cls.initialize()
        return cls.TIER_COLORS.get(tier, cls.COLOR_GRAY)


# ============================================================================
# Dialog Geometry Persistence Helpers
# ============================================================================

def _get_dialog_settings() -> QtCore.QSettings:
    """Get QSettings for dialog geometry persistence."""
    return QtCore.QSettings("PersonalFreedom", "LotteryDialogs")


def get_lottery_sound_enabled() -> bool:
    """Get whether lottery sounds are enabled."""
    settings = _get_dialog_settings()
    return settings.value("lottery_sound_enabled", True, type=bool)


def set_lottery_sound_enabled(enabled: bool) -> None:
    """Set whether lottery sounds are enabled."""
    settings = _get_dialog_settings()
    settings.setValue("lottery_sound_enabled", enabled)


# Cache the import to avoid repeated module lookups
_lottery_sounds_module = None
_lottery_sounds_import_failed = False


def _play_lottery_result_sound(won: bool) -> None:
    """Play appropriate sound for lottery result if enabled.
    
    This is a non-blocking, non-critical operation. Sound failures
    are logged but do not affect lottery functionality.
    """
    global _lottery_sounds_module, _lottery_sounds_import_failed
    
    if not get_lottery_sound_enabled():
        return
    
    # Skip if we already know the import failed
    if _lottery_sounds_import_failed:
        return
    
    try:
        # Lazy import with caching
        if _lottery_sounds_module is None:
            import lottery_sounds
            _lottery_sounds_module = lottery_sounds
        
        _lottery_sounds_module.play_lottery_result(won)
    except ImportError as e:
        _lottery_sounds_import_failed = True
        import logging
        logging.getLogger(__name__).warning(f"Lottery sounds unavailable: {e}")
    except Exception as e:
        # Log but don't crash - sound is non-critical
        import logging
        logging.getLogger(__name__).debug(f"Lottery sound playback failed: {e}")


def save_dialog_geometry(dialog: QtWidgets.QDialog, dialog_name: str) -> None:
    """Save dialog geometry to settings for persistence across restarts."""
    try:
        settings = _get_dialog_settings()
        settings.setValue(f"{dialog_name}/geometry", dialog.saveGeometry())
        settings.setValue(f"{dialog_name}/size", dialog.size())
    except Exception:
        pass  # Silently fail - geometry persistence is non-critical


def load_dialog_geometry(dialog: QtWidgets.QDialog, dialog_name: str, 
                         default_size: QtCore.QSize) -> None:
    """Load dialog geometry from settings, or use default size."""
    try:
        settings = _get_dialog_settings()
        geometry = settings.value(f"{dialog_name}/geometry")
        saved_size = settings.value(f"{dialog_name}/size")
        
        if geometry:
            dialog.restoreGeometry(geometry)
        elif saved_size:
            dialog.resize(saved_size)
        else:
            dialog.resize(default_size)
    except Exception:
        dialog.resize(default_size)


class LotterySliderWidget(QtWidgets.QWidget):
    """Custom widget that draws a probability bar with sliding marker.
    
    Visually shows a threshold line separating "WIN" and "LOSE" zones,
    with a marker that slides to the final position.
    """
    
    # Cached colors for performance (avoid creating QColor objects each frame)
    _COLOR_SUCCESS_ZONE = QtGui.QColor("#2e7d32")
    _COLOR_FAIL_ZONE = QtGui.QColor("#c62828")
    _COLOR_WHITE = QtGui.QColor("#fff")
    _COLOR_GRAY = QtGui.QColor("#888")
    _COLOR_WIN_TEXT = QtGui.QColor("#4caf50")
    _COLOR_LOSE_TEXT = QtGui.QColor("#f44336")
    _COLOR_MARKER_WIN = QtGui.QColor("#66bb6a")
    _COLOR_MARKER_LOSE = QtGui.QColor("#ef5350")
    _COLOR_MARKER_SUCCESS = QtGui.QColor("#4caf50")
    _COLOR_MARKER_FAIL = QtGui.QColor("#f44336")
    
    def __init__(self, threshold: float, parent=None):
        """
        Args:
            threshold: Success threshold as percentage (0-100).
                       Values below threshold = WIN, values at or above = LOSE.
        """
        super().__init__(parent)
        self.threshold = threshold  # Success threshold (0-100)
        self.position = 0.0  # Current marker position (0-100)
        self.result = None  # None, True (success), or False (failure)
        self.setMinimumWidth(400)
        
        # Cache fonts for performance
        self._font_threshold = QtGui.QFont("Arial", 9, QtGui.QFont.Bold)
        self._font_label = QtGui.QFont("Arial", 8)
        self._font_zone = QtGui.QFont("Arial", 10, QtGui.QFont.Bold)
        
        # Cache pens for performance
        self._pen_threshold = QtGui.QPen(self._COLOR_WHITE, 2)
        self._pen_marker_outline = QtGui.QPen(self._COLOR_WHITE, 2)
    
    def set_position(self, pos: float):
        """Set the marker position (0-100)."""
        self.position = max(0, min(100, pos))
        self.update()
    
    def set_result(self, success: bool):
        """Set the final result for visual feedback."""
        self.result = success
        self.update()
    
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        margin = 10
        bar_height = 20
        bar_y = (h - bar_height) // 2
        
        # Draw the track background
        track_rect = QtCore.QRectF(margin, bar_y, w - 2*margin, bar_height)
        
        # Success zone (green) - left side up to threshold
        threshold_x = margin + (self.threshold / 100.0) * (w - 2*margin)
        success_rect = QtCore.QRectF(margin, bar_y, threshold_x - margin, bar_height)
        painter.setBrush(self._COLOR_SUCCESS_ZONE)  # Use cached color
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRoundedRect(success_rect, 4, 4)
        
        # Failure zone (red) - right side from threshold
        fail_rect = QtCore.QRectF(threshold_x, bar_y, w - margin - threshold_x, bar_height)
        painter.setBrush(self._COLOR_FAIL_ZONE)  # Use cached color
        painter.drawRoundedRect(fail_rect, 4, 4)
        
        # Draw threshold line
        painter.setPen(self._pen_threshold)  # Use cached pen
        painter.drawLine(int(threshold_x), bar_y - 5, int(threshold_x), bar_y + bar_height + 5)
        
        # Threshold label
        painter.setFont(self._font_threshold)  # Use cached font
        painter.drawText(int(threshold_x) - 15, bar_y - 8, f"{self.threshold:.0f}%")
        
        # Draw 0% and 100% labels
        painter.setPen(self._COLOR_GRAY)  # Use cached color
        painter.setFont(self._font_label)  # Use cached font
        painter.drawText(margin, bar_y + bar_height + 15, "0%")
        painter.drawText(w - margin - 25, bar_y + bar_height + 15, "100%")
        
        # Draw "WIN" and "LOSE" zone labels
        painter.setFont(self._font_zone)  # Use cached font
        if threshold_x - margin > 40:
            painter.setPen(self._COLOR_WIN_TEXT)  # Use cached color
            win_x = margin + (threshold_x - margin) / 2 - 15
            painter.drawText(int(win_x), bar_y + bar_height // 2 + 5, "WIN")
        if w - margin - threshold_x > 40:
            painter.setPen(self._COLOR_LOSE_TEXT)  # Use cached color
            lose_x = threshold_x + (w - margin - threshold_x) / 2 - 18
            painter.drawText(int(lose_x), bar_y + bar_height // 2 + 5, "LOSE")
        
        # Draw the sliding marker
        marker_x = margin + (self.position / 100.0) * (w - 2*margin)
        marker_size = 16
        
        # Marker color based on position (use cached colors)
        if self.result is not None:
            marker_color = self._COLOR_MARKER_SUCCESS if self.result else self._COLOR_MARKER_FAIL
            glow_color = marker_color
        elif self.position < self.threshold:
            marker_color = self._COLOR_MARKER_WIN
            glow_color = None
        else:
            marker_color = self._COLOR_MARKER_LOSE
            glow_color = None
        
        # Draw glow if result shown
        if glow_color:
            for i in range(3):
                glow_size = marker_size + (3-i) * 4
                painter.setBrush(glow_color)
                painter.setOpacity(0.2)
                painter.drawEllipse(
                    QtCore.QPointF(marker_x, bar_y + bar_height // 2),
                    glow_size, glow_size
                )
            painter.setOpacity(1.0)
        
        # Draw marker (triangle pointing down)
        painter.setBrush(marker_color)
        painter.setPen(self._pen_marker_outline)  # Use cached pen
        
        # Triangle marker
        triangle = QtGui.QPolygonF([
            QtCore.QPointF(marker_x, bar_y - 2),
            QtCore.QPointF(marker_x - 8, bar_y - 14),
            QtCore.QPointF(marker_x + 8, bar_y - 14),
        ])
        painter.drawPolygon(triangle)
        
        # Marker line (need to create pen with dynamic color)
        painter.setPen(QtGui.QPen(marker_color, 3))
        painter.drawLine(int(marker_x), bar_y, int(marker_x), bar_y + bar_height)


class LotteryRollDialog(QtWidgets.QDialog):
    """Dramatic slider animation for lottery/probability roll reveal.
    
    Features:
    - Ping-pong bouncing animation (slider bounces off walls 4-6 times)
    - Quadratic friction deceleration for realistic slowdown
    - Customizable title and styling
    - Continue button for user to close when ready
    
    Usage:
        dialog = LotteryRollDialog(
            target_roll=0.35,      # The actual roll (0.0-1.0)
            success_threshold=0.50, # Win if roll < threshold
            title="🎲 Item Drop Lottery",
            parent=self
        )
        dialog.finished_signal.connect(self._on_lottery_result)
        dialog.exec()
    """
    
    finished_signal = QtCore.Signal(bool)  # Emits success/failure when done
    
    def __init__(self, target_roll: float, success_threshold: float, 
                 title: str = "🎲 Rolling...",
                 success_text: str = "✨ SUCCESS! ✨",
                 failure_text: str = "💔 FAILED 💔",
                 animation_duration: float = 10.0,
                 parent: Optional[QtWidgets.QWidget] = None):
        """
        Args:
            target_roll: The actual roll result (0.0-1.0)
            success_threshold: Win threshold (0.0-1.0). Roll < threshold = success.
            title: Dialog title text
            success_text: Text to show on success
            failure_text: Text to show on failure  
            animation_duration: How long the animation runs (seconds)
            parent: Parent widget
        """
        super().__init__(parent)
        self.target_roll = target_roll * 100  # Convert to percentage
        self.success_threshold = success_threshold * 100
        self.current_position = 50.0  # Start in the middle
        self.is_success = target_roll < success_threshold
        self.title_text = title
        self.success_text = success_text
        self.failure_text = failure_text
        
        # Animation settings
        self.tick_interval = 16  # ~60 FPS (smoother animation)
        self.elapsed_time = 0.0
        self.animation_duration = animation_duration
        
        # Style state tracking to avoid redundant setStyleSheet calls
        self._last_roll_style = None  # "success" or "fail"
        self._last_status_text = None
        
        # Generate bounce path
        self._generate_bounce_path()
        self._setup_ui()
        self._start_animation()
    
    def _generate_bounce_path(self):
        """Generate the ping-pong bounce path for the animation."""
        # Start at 50, visit walls (0/100) multiple times, end at target
        self.path_points = [50.0]
        
        # Random start direction
        going_up = random.choice([True, False])
        
        # Number of full bounces (wall-to-wall traversals)
        # 4-6 bounces creates nice suspense
        num_bounces = random.randint(4, 6)
        
        for _ in range(num_bounces):
            if going_up:
                self.path_points.append(100.0)
                self.path_points.append(0.0)
            else:
                self.path_points.append(0.0)
                self.path_points.append(100.0)
        
        # Add final target
        self.path_points.append(self.target_roll)
        
        # Pre-calculate distance segments for O(1) interpolation
        self.segments = []
        self.total_distance = 0.0
        
        for i in range(len(self.path_points) - 1):
            start = self.path_points[i]
            end = self.path_points[i+1]
            dist = abs(end - start)
            
            # Skip zero-length segments
            if dist > 0.001:
                self.segments.append({
                    "start": start,
                    "end": end,
                    "dist": dist,
                    "cum_start": self.total_distance,
                    "cum_end": self.total_distance + dist
                })
                self.total_distance += dist
    
    def _setup_ui(self):
        """Build the slider animation UI."""
        self.setWindowTitle(self.title_text)
        self.setModal(True)
        self.setMinimumSize(400, 260)
        load_dialog_geometry(self, "LotteryRollDialog", QtCore.QSize(500, 280))
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)  # Small margin for shadow
        
        # Main container
        container = QtWidgets.QWidget()
        container.setStyleSheet("""
            QWidget {
                background: #1a1a2e;
                border: none;
                border-radius: 12px;
            }
        """)
        # Apply drop shadow to container for depth without borders
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QtGui.QColor(0, 0, 0, 120))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)
        
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setSpacing(12)
        container_layout.setContentsMargins(22, 18, 22, 18)

        # Title
        title = QtWidgets.QLabel(self.title_text)
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #9ca3af;")
        container_layout.addWidget(title)
        
        # The slider track widget (custom painted)
        self.slider_widget = LotterySliderWidget(self.success_threshold)
        self.slider_widget.setFixedHeight(60)
        container_layout.addWidget(self.slider_widget)
        
        # Current roll display
        self.roll_label = QtWidgets.QLabel("0.0%")
        self.roll_label.setAlignment(QtCore.Qt.AlignCenter)
        self.roll_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #fff;
            font-family: 'Consolas', 'Monaco', monospace;
        """)
        container_layout.addWidget(self.roll_label)
        
        # Status
        self.status_label = QtWidgets.QLabel("⚡ Spinning...")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #aaa; font-size: 12px;")
        container_layout.addWidget(self.status_label)
        
        # Sound toggle
        sound_row = QtWidgets.QHBoxLayout()
        sound_row.addStretch()
        self.sound_toggle = QtWidgets.QCheckBox("🔊 Sound")
        self.sound_toggle.setChecked(get_lottery_sound_enabled())
        self.sound_toggle.setStyleSheet("color: #666; font-size: 11px;")
        self.sound_toggle.toggled.connect(set_lottery_sound_enabled)
        sound_row.addWidget(self.sound_toggle)
        container_layout.addLayout(sound_row)
        
        # Continue button (hidden until animation complete)
        self.continue_btn = QtWidgets.QPushButton("Continue")
        self.continue_btn.setStyleSheet("""
            QPushButton {
                background: #4caf50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #66bb6a;
            }
        """)
        self.continue_btn.clicked.connect(self.accept)
        self.continue_btn.hide()
        container_layout.addWidget(self.continue_btn, alignment=QtCore.Qt.AlignCenter)
        
        layout.addWidget(container)
    
    def _start_animation(self):
        """Start the damped oscillation animation."""
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(self.tick_interval)
    
    def _tick(self):
        """Update animation by traversing the pre-calculated bounce path."""
        # Update elapsed time
        self.elapsed_time += 0.016  # 16ms interval for 60 FPS
        
        # Calculate normalized progress (0.0 to 1.0)
        t = min(1.0, self.elapsed_time / self.animation_duration)
        
        # Apply easing function for realistic friction/deceleration
        # EaseOutQuart: 1 - (1-t)^4
        eased_progress = 1.0 - (1.0 - t) ** 4
        
        # Calculate current distance traveled along the path
        current_travel = eased_progress * self.total_distance
        
        # Find which segment we are in
        found_pos = self.target_roll  # Default fallback
        
        for seg in self.segments:
            if current_travel >= seg["cum_start"] and current_travel <= seg["cum_end"]:
                # Interpolate within this segment
                local_dist = current_travel - seg["cum_start"]
                local_progress = local_dist / seg["dist"]
                found_pos = seg["start"] + (seg["end"] - seg["start"]) * local_progress
                break
            elif current_travel > seg["cum_end"]:
                continue
        else:
            if current_travel >= self.total_distance:
                found_pos = self.target_roll

        self.current_position = found_pos
        
        # End condition
        if t >= 1.0:
            self.timer.stop()
            self.current_position = self.target_roll
            self.slider_widget.set_position(self.target_roll)
            self.roll_label.setText(f"{self.target_roll:.1f}%")
            self._show_final_result()
            return
            
        # Ensure bounds 0-100
        self.current_position = max(0.0, min(100.0, self.current_position))
        self.slider_widget.set_position(self.current_position)
        self.roll_label.setText(f"{self.current_position:.1f}%")
        
        # Color based on position - only update style if state changed
        new_style = "success" if self.current_position < self.success_threshold else "fail"
        if new_style != self._last_roll_style:
            self._last_roll_style = new_style
            if new_style == "success":
                self.roll_label.setStyleSheet("""
                    font-size: 28px; font-weight: bold; color: #4caf50;
                    font-family: 'Consolas', 'Monaco', monospace;
                """)
            else:
                self.roll_label.setStyleSheet("""
                    font-size: 28px; font-weight: bold; color: #f44336;
                    font-family: 'Consolas', 'Monaco', monospace;
                """)
        
        # Update status based on speed (derivative of eased_progress) - only if changed
        speed = 4 * (1.0 - t) ** 3
        if speed > 2.0:
            new_status = "⚡ Spinning..."
        elif speed > 0.8:
            new_status = "🎯 Slowing down..."
        elif speed > 0.2:
            new_status = "🎲 Almost there..."
        else:
            new_status = "✨ Settling..."
        
        if new_status != self._last_status_text:
            self._last_status_text = new_status
            self.status_label.setText(new_status)
    
    def _show_final_result(self):
        """Show the final result."""
        self.roll_label.setText(f"{self.target_roll:.1f}%")
        
        if self.is_success:
            self.roll_label.setStyleSheet("""
                font-size: 28px; font-weight: bold; color: #4caf50;
                font-family: 'Consolas', 'Monaco', monospace;
            """)
            self.status_label.setText(self.success_text)
            self.status_label.setStyleSheet("color: #4caf50; font-size: 16px; font-weight: bold;")
            self.slider_widget.set_result(True)
        else:
            self.roll_label.setStyleSheet("""
                font-size: 28px; font-weight: bold; color: #f44336;
                font-family: 'Consolas', 'Monaco', monospace;
            """)
            self.status_label.setText(self.failure_text)
            self.status_label.setStyleSheet("color: #f44336; font-size: 16px; font-weight: bold;")
            self.slider_widget.set_result(False)
        
        # Play lottery result sound
        _play_lottery_result_sound(self.is_success)
        
        # Emit signal and show continue button for user to close when ready
        self.finished_signal.emit(self.is_success)
        self.continue_btn.show()
    
    def closeEvent(self, event):
        """Clean up timer on close and save geometry."""
        save_dialog_geometry(self, "LotteryRollDialog")
        if hasattr(self, 'timer'):
            self.timer.stop()
        super().closeEvent(event)


class EyeProtectionTierSliderWidget(QtWidgets.QWidget):
    """5-zone tier slider for Eye Protection lottery.
    
    Shows the 5 rarity tiers with widths based on routine count.
    Higher routine count shifts distribution toward higher tiers.
    """
    
    TIER_COLORS = {
        "Common": "#9e9e9e",
        "Uncommon": "#4caf50", 
        "Rare": "#2196f3",
        "Epic": "#9c27b0",
        "Legendary": "#ff9800"
    }
    TIERS = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
    
    # Cached paint objects for performance (avoid creating in paintEvent)
    _CACHED_COLORS = None  # Will be initialized on first use
    _FONT_LABEL = None
    _PEN_BORDER = None
    _PEN_MARKER_OUTLINE = None
    _COLOR_WHITE = None
    
    @classmethod
    def _init_paint_cache(cls):
        """Initialize cached paint objects (lazy loading)."""
        if cls._CACHED_COLORS is None:
            cls._CACHED_COLORS = {t: QtGui.QColor(c) for t, c in cls.TIER_COLORS.items()}
            cls._FONT_LABEL = QtGui.QFont("Arial", 9, QtGui.QFont.Bold)
            cls._PEN_BORDER = QtGui.QPen(QtGui.QColor("#333"), 2)
            cls._PEN_MARKER_OUTLINE = QtGui.QPen(QtGui.QColor("#fff"), 2)
            cls._COLOR_WHITE = QtGui.QColor("#ffffff")
    
    def __init__(self, tier_weights: list, parent=None):
        """
        Args:
            tier_weights: List of 5 weights [Common, Uncommon, Rare, Epic, Legendary]
        """
        super().__init__(parent)
        self._init_paint_cache()  # Ensure cache is ready
        self.zone_widths = tier_weights  # Already percentages that sum to 100
        self.position = 0.0
        self.result_tier = None
        self.setMinimumSize(400, 60)
    
    def set_position(self, pos: float):
        """Set marker position (0-100)."""
        self.position = max(0.0, min(100.0, pos))
        self.update()
    
    def set_result(self, tier: str):
        """Set the result tier for visual feedback."""
        self.result_tier = tier
        self.update()
    
    def get_tier_at_position(self, pos: float) -> str:
        """Get tier name at a given position (0-100)."""
        total = sum(self.zone_widths)
        if total <= 0:
            return "Rare"  # Safe fallback
        cumulative = 0.0
        for tier, width in zip(self.TIERS, self.zone_widths):
            if width <= 0:
                continue
            if pos < cumulative + width:
                return tier
            cumulative += width
        return "Legendary"
    
    def get_position_for_tier(self, tier: str) -> float:
        """Get center position for a tier zone."""
        cumulative = 0.0
        for t, width in zip(self.TIERS, self.zone_widths):
            if t == tier:
                return cumulative + width / 2
            cumulative += width
        return 95.0
    
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        bar_y = 20
        bar_height = 30
        bar_width = self.width() - 20
        x_offset = 10
        
        # Draw tier zones (use cached colors)
        cumulative_x = x_offset
        for tier, width in zip(self.TIERS, self.zone_widths):
            if width <= 0:
                continue
            zone_width = (width / 100) * bar_width
            color = self._CACHED_COLORS[tier]
            
            # Highlight winning tier
            if self.result_tier and tier == self.result_tier:
                painter.setOpacity(1.0)
            else:
                painter.setOpacity(0.7 if self.result_tier else 1.0)
            
            painter.fillRect(
                int(cumulative_x), bar_y,
                int(zone_width), bar_height,
                color
            )
            
            # Zone label (only if wide enough)
            if zone_width > 30:
                painter.setOpacity(1.0)
                painter.setPen(self._COLOR_WHITE)
                painter.setFont(self._FONT_LABEL)
                painter.drawText(
                    int(cumulative_x), bar_y,
                    int(zone_width), bar_height,
                    QtCore.Qt.AlignCenter, tier[:3]
                )
            cumulative_x += zone_width
        
        painter.setOpacity(1.0)
        
        # Draw border (use cached pen)
        painter.setPen(self._PEN_BORDER)
        painter.drawRect(x_offset, bar_y, bar_width, bar_height)
        
        # Draw marker
        marker_x = x_offset + (self.position / 100) * bar_width
        current_tier = self.get_tier_at_position(self.position)
        marker_color = self._CACHED_COLORS.get(current_tier, self._COLOR_WHITE)
        
        # Glow effect for result
        if self.result_tier:
            glow_color = self._CACHED_COLORS.get(self.result_tier, self._COLOR_WHITE)
            for i in range(3):
                glow_size = 10 + (3-i) * 3
                painter.setBrush(glow_color)
                painter.setOpacity(0.3)
                painter.drawEllipse(
                    QtCore.QPointF(marker_x, bar_y + bar_height // 2),
                    glow_size, glow_size
                )
            painter.setOpacity(1.0)
        
        # Marker triangle
        painter.setBrush(marker_color)
        painter.setPen(self._PEN_MARKER_OUTLINE)
        triangle = [
            QtCore.QPointF(marker_x, bar_y - 3),
            QtCore.QPointF(marker_x - 8, bar_y - 15),
            QtCore.QPointF(marker_x + 8, bar_y - 15)
        ]
        painter.drawPolygon(triangle)
        
        # Marker line (need dynamic color pen)
        painter.setPen(QtGui.QPen(marker_color, 3))
        painter.drawLine(int(marker_x), bar_y, int(marker_x), bar_y + bar_height)


class TwoStageLotteryDialog(QtWidgets.QDialog):
    """Two-stage lottery animation for tier + item drop determination.
    
    Stage 1: Roll for tier (what rarity are you playing for?) - shows all 5 tiers
    Stage 2: Roll for item drop (did you actually win it?)
    
    This order creates more suspense - seeing the tier first
    makes the second roll more nerve-wracking!
    
    Perfect for Eye Protection rewards and similar systems.
    """
    
    finished_signal = QtCore.Signal(bool, str)  # (won_item, tier_if_won)
    
    # Tier distribution based on tier_chance (used as a scaling factor)
    # Higher tier_chance shifts weights toward legendary
    TIERS = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
    
    def __init__(self, drop_chance: float, tier_chance: float,
                 parent: Optional[QtWidgets.QWidget] = None):
        """
        Args:
            drop_chance: Chance to win an item (0.0-1.0)
            tier_chance: Scaling factor for tier distribution (0.0-1.0). Higher = more legendary chance.
        """
        super().__init__(parent)
        self.drop_chance = drop_chance
        self.tier_chance = tier_chance
        
        # Calculate tier weights based on tier_chance
        # tier_chance of 0.05 (5%) = Common-centered
        # tier_chance of 0.20 (20%) = Rare-centered
        # tier_chance of 0.50 (50%) = Epic-centered
        # tier_chance of 0.99 (99%) = Legendary-centered
        self.tier_weights = self._calculate_tier_weights(tier_chance)
        
        # Pre-roll the results
        self.drop_roll = random.random()
        self.tier_roll = random.random() * 100  # 0-100
        self.won_item = self.drop_roll < drop_chance
        self.tier = self._determine_tier(self.tier_roll)
        
        self.current_stage = 0
        self._setup_ui()
        QtCore.QTimer.singleShot(100, self._start_stage_1)
    
    def _calculate_tier_weights(self, tier_chance: float) -> list:
        """Calculate tier weights based on tier_chance factor.
        
        Returns list of 5 weights that sum to 100.
        """
        # Map tier_chance to center tier (0-4)
        # 0.05 -> tier 0 (Common), 0.99 -> tier 4 (Legendary)
        center = min(4, int(tier_chance * 5))  # 0-4
        
        # Moving window distribution: [5, 15, 60, 15, 5] centered on `center`
        # This gives 60% to the center tier, with distribution tapering off
        window = [5, 15, 60, 15, 5]
        weights = [0, 0, 0, 0, 0]
        
        for offset, pct in zip([-2, -1, 0, 1, 2], window):
            target = center + offset
            clamped = max(0, min(4, target))
            weights[clamped] += pct
        
        return weights
    
    def _determine_tier(self, roll: float) -> str:
        """Determine tier from roll (0-100) based on weights."""
        cumulative = 0.0
        for tier, weight in zip(self.TIERS, self.tier_weights):
            if roll < cumulative + weight:
                return tier
            cumulative += weight
        return "Legendary"
    
    def _setup_ui(self):
        """Build the two-stage lottery UI."""
        self.setWindowTitle("🎰 Eye Protection Lottery")
        self.setModal(True)
        self.setMinimumSize(420, 320)
        load_dialog_geometry(self, "EyeProtectionLotteryDialog", QtCore.QSize(520, 400))
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)  # Small margin for shadow
        
        # Main container
        container = QtWidgets.QWidget()
        container.setStyleSheet("""
            QWidget {
                background: #1a1a2e;
                border: none;
                border-radius: 12px;
            }
        """)
        # Apply drop shadow to container for depth without borders
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QtGui.QColor(0, 0, 0, 120))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)
        
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setSpacing(12)
        container_layout.setContentsMargins(24, 18, 24, 18)

        # Main title
        self.main_title = QtWidgets.QLabel("🎰 Eye Protection Lottery 🎰")
        self.main_title.setAlignment(QtCore.Qt.AlignCenter)
        self.main_title.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #9ca3af;"
        )
        container_layout.addWidget(self.main_title)
        
        # Stage 1: Tier Roll (what are you playing for?)
        self.stage1_frame = QtWidgets.QFrame()
        self.stage1_frame.setStyleSheet("""
            QFrame {
                background: #252540;
                border: none;
                border-radius: 8px;
            }
        """)
        # Add subtle shadow for card effect
        shadow1 = QtWidgets.QGraphicsDropShadowEffect()
        shadow1.setBlurRadius(10)
        shadow1.setColor(QtGui.QColor(0, 0, 0, 80))
        shadow1.setOffset(0, 2)
        self.stage1_frame.setGraphicsEffect(shadow1)
        self.stage1_frame.setMinimumHeight(120)  # Prevent collapse
        stage1_layout = QtWidgets.QVBoxLayout(self.stage1_frame)
        stage1_layout.setContentsMargins(14, 10, 14, 10)
        
        self.stage1_title = QtWidgets.QLabel("✨ Stage 1: Rolling for Tier...")
        self.stage1_title.setStyleSheet("color: #aaa; font-size: 12px; font-weight: bold;")
        stage1_layout.addWidget(self.stage1_title)
        
        # Use the 5-tier slider instead of binary slider
        self.stage1_slider = EyeProtectionTierSliderWidget(self.tier_weights)
        self.stage1_slider.setFixedHeight(60)
        stage1_layout.addWidget(self.stage1_slider)
        
        # Distribution legend
        dist_layout = QtWidgets.QHBoxLayout()
        tier_colors = {"Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3", 
                       "Epic": "#9c27b0", "Legendary": "#ff9800"}
        for tier, weight in zip(self.TIERS, self.tier_weights):
            if weight > 0:
                color = tier_colors.get(tier, "#888")
                label = QtWidgets.QLabel(f"<b style='color:{color};'>{tier[:3]}</b>:{weight:.0f}%")
                label.setStyleSheet("font-size: 10px; color: #aaa;")
                dist_layout.addWidget(label)
        dist_layout.addStretch()
        stage1_layout.addLayout(dist_layout)
        
        self.stage1_result = QtWidgets.QLabel("Waiting...")
        self.stage1_result.setAlignment(QtCore.Qt.AlignCenter)
        self.stage1_result.setStyleSheet("color: #888; font-size: 14px;")
        stage1_layout.addWidget(self.stage1_result)
        
        container_layout.addWidget(self.stage1_frame)
        
        # Stage 2: Item Drop (did you win it?)
        self.stage2_frame = QtWidgets.QFrame()
        self.stage2_frame.setStyleSheet("""
            QFrame {
                background: #252540;
                border: none;
                border-radius: 8px;
            }
        """)
        # Add subtle shadow for card effect
        shadow2 = QtWidgets.QGraphicsDropShadowEffect()
        shadow2.setBlurRadius(10)
        shadow2.setColor(QtGui.QColor(0, 0, 0, 80))
        shadow2.setOffset(0, 2)
        self.stage2_frame.setGraphicsEffect(shadow2)
        self.stage2_frame.setMinimumHeight(100)  # Prevent collapse
        stage2_layout = QtWidgets.QVBoxLayout(self.stage2_frame)
        stage2_layout.setContentsMargins(14, 10, 14, 10)
        
        self.stage2_title = QtWidgets.QLabel(f"🎲 Stage 2: Claim Roll ({self.drop_chance*100:.0f}% chance)")
        self.stage2_title.setStyleSheet("color: #666; font-size: 12px; font-weight: bold;")
        stage2_layout.addWidget(self.stage2_title)
        
        self.stage2_slider = LotterySliderWidget(self.drop_chance * 100)
        self.stage2_slider.setFixedHeight(50)
        self.stage2_slider.setEnabled(False)
        stage2_layout.addWidget(self.stage2_slider)
        
        self.stage2_result = QtWidgets.QLabel("(Roll tier first...)")
        self.stage2_result.setAlignment(QtCore.Qt.AlignCenter)
        self.stage2_result.setStyleSheet("color: #555; font-size: 14px;")
        stage2_layout.addWidget(self.stage2_result)
        
        container_layout.addWidget(self.stage2_frame)
        
        # Final result area
        self.final_result = QtWidgets.QLabel("")
        self.final_result.setAlignment(QtCore.Qt.AlignCenter)
        self.final_result.setMinimumHeight(40)  # Reserve space
        self.final_result.setStyleSheet("color: #fff; font-size: 16px; font-weight: bold;")
        container_layout.addWidget(self.final_result)
        
        # Stretch to absorb space changes
        container_layout.addStretch(1)
        
        # Sound toggle
        sound_row = QtWidgets.QHBoxLayout()
        sound_row.addStretch()
        self.sound_toggle = QtWidgets.QCheckBox("🔊 Sound")
        self.sound_toggle.setChecked(get_lottery_sound_enabled())
        self.sound_toggle.setStyleSheet("color: #666; font-size: 11px;")
        self.sound_toggle.toggled.connect(set_lottery_sound_enabled)
        sound_row.addWidget(self.sound_toggle)
        container_layout.addLayout(sound_row)
        
        # Continue button (hidden until animation complete)
        self.continue_btn = QtWidgets.QPushButton("Continue")
        self.continue_btn.setStyleSheet("""
            QPushButton {
                background: #4caf50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #66bb6a;
            }
        """)
        self.continue_btn.clicked.connect(self._finish)
        self.continue_btn.hide()
        container_layout.addWidget(self.continue_btn, alignment=QtCore.Qt.AlignCenter)
        
        layout.addWidget(container)
    
    def _start_stage_1(self):
        """Start the tier roll animation (Stage 1)."""
        self.current_stage = 1
        self.stage1_frame.setStyleSheet("""
            QFrame {
                background: #252540;
                border: 2px solid #6366f1;
                border-radius: 8px;
            }
        """)
        self.stage1_title.setStyleSheet("color: #a5b4fc; font-size: 12px; font-weight: bold;")
        self.stage1_title.setText("✨ Stage 1: Rolling for Tier...")
        self.stage1_result.setText("Rolling...")
        
        # Animate tier roll using the 5-tier slider
        self._animate_tier_stage(
            slider=self.stage1_slider,
            result_label=self.stage1_result,
            target_roll=self.tier_roll,
            on_complete=self._on_stage1_complete
        )
    
    def _on_stage1_complete(self):
        """Handle tier roll completion - show what tier they rolled."""
        tier_colors = {"Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3", 
                       "Epic": "#9c27b0", "Legendary": "#ff9800"}
        tier_emojis = {"Common": "⚪", "Uncommon": "💚", "Rare": "💙", 
                       "Epic": "💎", "Legendary": "⭐"}
        
        color = tier_colors.get(self.tier, "#fff")
        emoji = tier_emojis.get(self.tier, "🎁")
        
        # Store for later
        self.rolled_color = color
        
        if self.tier == "Legendary":
            self.stage1_result.setText(f"⭐ LEGENDARY! ⭐")
        elif self.tier == "Epic":
            self.stage1_result.setText(f"💎 Epic! 💎")
        else:
            self.stage1_result.setText(f"{emoji} {self.tier}!")
        
        self.stage1_result.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")
        self.stage1_slider.set_result(self.tier)
        
        # Enable and start stage 2
        self.stage2_frame.setStyleSheet("""
            QFrame {
                background: #252540;
                border: 2px solid #6366f1;
                border-radius: 8px;
            }
        """)
        self.stage2_title.setStyleSheet("color: #a5b4fc; font-size: 12px; font-weight: bold;")
        self.stage2_title.setText(f"🎲 Stage 2: Claim your {self.tier}! ({self.drop_chance*100:.0f}%)")
        self.stage2_slider.setEnabled(True)
        self.stage2_result.setText("Rolling...")
        self.stage2_result.setStyleSheet("color: #aaa; font-size: 14px;")
        
        QtCore.QTimer.singleShot(800, self._start_stage_2)
    
    def _start_stage_2(self):
        """Start the item drop lottery (Stage 2)."""
        self.current_stage = 2
        
        self._animate_stage(
            slider=self.stage2_slider,
            result_label=self.stage2_result,
            target_roll=self.drop_roll,
            threshold=self.drop_chance,
            on_complete=self._on_stage2_complete
        )
    
    def _on_stage2_complete(self, won: bool):
        """Handle item drop completion."""
        tier_colors = {"Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3", 
                       "Epic": "#9c27b0", "Legendary": "#ff9800"}
        tier_emojis = {"Common": "⚪", "Uncommon": "💚", "Rare": "💙", 
                       "Epic": "💎", "Legendary": "🏆"}
        
        color = tier_colors.get(self.tier, "#fff")
        emoji = tier_emojis.get(self.tier, "🎁")
        
        if won:
            self.stage2_result.setText("✨ SUCCESS! ✨")
            self.stage2_result.setStyleSheet("color: #4caf50; font-size: 14px; font-weight: bold;")
            self.stage2_slider.set_result(True)
            
            if self.tier == "Legendary":
                self.final_result.setText("🏆 You won a LEGENDARY item! 🏆")
                self.final_result.setStyleSheet("color: #ff9800; font-size: 18px; font-weight: bold;")
            elif self.tier == "Epic":
                self.final_result.setText("💎 You won an EPIC item! 💎")
                self.final_result.setStyleSheet("color: #9c27b0; font-size: 18px; font-weight: bold;")
            else:
                self.final_result.setText(f"{emoji} You won a {self.tier} item!")
                self.final_result.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")
        else:
            self.stage2_result.setText("💔 FAILED 💔")
            self.stage2_result.setStyleSheet("color: #f44336; font-size: 14px; font-weight: bold;")
            self.stage2_slider.set_result(False)
            
            if self.tier == "Legendary":
                self.final_result.setText("😱 The LEGENDARY slipped away! Next time! 💪")
            elif self.tier == "Epic":
                self.final_result.setText("💎 The Epic slipped away! Keep exercising! 💪")
            else:
                self.final_result.setText(f"The {self.tier} item slipped away... Keep exercising! 💪")
            self.final_result.setStyleSheet("color: #aaa; font-size: 14px;")
        
        # Play sound effect
        _play_lottery_result_sound(won)
        
        # Show continue button for user to close when ready
        self.continue_btn.show()
    
    def _animate_tier_stage(self, slider: EyeProtectionTierSliderWidget, 
                            result_label: QtWidgets.QLabel,
                            target_roll: float, on_complete: Callable):
        """Animate the 5-tier roll stage."""
        self._tier_anim_slider = slider
        self._tier_anim_result = result_label
        self._tier_anim_target = target_roll
        self._tier_anim_callback = on_complete
        
        # Generate bounce path
        path_points = [50.0]
        going_up = random.choice([True, False])
        num_bounces = random.randint(4, 6)
        
        for _ in range(num_bounces):
            if going_up:
                path_points.append(100.0)
                path_points.append(0.0)
            else:
                path_points.append(0.0)
                path_points.append(100.0)
        path_points.append(target_roll)
        
        self._tier_anim_segments = []
        self._tier_anim_total_dist = 0.0
        for i in range(len(path_points) - 1):
            start, end = path_points[i], path_points[i+1]
            dist = abs(end - start)
            if dist > 0.001:
                self._tier_anim_segments.append({
                    "start": start, "end": end, "dist": dist,
                    "cum_start": self._tier_anim_total_dist,
                    "cum_end": self._tier_anim_total_dist + dist
                })
                self._tier_anim_total_dist += dist
        
        self._tier_anim_elapsed = 0.0
        self._tier_anim_duration = 5.0  # Snappy dramatic effect
        
        # Style state tracking for performance
        self._tier_last_tier = None
        
        self._tier_anim_timer = QtCore.QTimer(self)
        self._tier_anim_timer.timeout.connect(self._tier_anim_tick)
        self._tier_anim_timer.start(16)  # 60 FPS for smoother animation
    
    def _tier_anim_tick(self):
        """Animation tick for tier stage."""
        # Cached tier colors (class constant would be better but works for this method)
        TIER_COLORS = {"Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3", 
                       "Epic": "#9c27b0", "Legendary": "#ff9800"}
        
        self._tier_anim_elapsed += 0.016  # Match 16ms timer interval
        t = min(1.0, self._tier_anim_elapsed / self._tier_anim_duration)
        eased = 1.0 - (1.0 - t) ** 4
        
        current_travel = eased * self._tier_anim_total_dist
        pos = self._tier_anim_target
        
        for seg in self._tier_anim_segments:
            if seg["cum_start"] <= current_travel <= seg["cum_end"]:
                local = (current_travel - seg["cum_start"]) / seg["dist"]
                pos = seg["start"] + (seg["end"] - seg["start"]) * local
                break
        
        pos = max(0, min(100, pos))
        self._tier_anim_slider.set_position(pos)
        
        # Update result label with current tier - only update style if tier changed
        current_tier = self._tier_anim_slider.get_tier_at_position(pos)
        if current_tier != self._tier_last_tier:
            self._tier_last_tier = current_tier
            color = TIER_COLORS.get(current_tier, "#aaa")
            self._tier_anim_result.setStyleSheet(f"color: {color}; font-size: 14px;")
        self._tier_anim_result.setText(f"🎲 {pos:.1f}% → {current_tier}")
        
        if t >= 1.0:
            self._tier_anim_timer.stop()
            self._tier_anim_slider.set_position(self._tier_anim_target)
            self._tier_anim_callback()
    
    def _animate_stage(self, slider: LotterySliderWidget, result_label: QtWidgets.QLabel,
                       target_roll: float, threshold: float, on_complete: Callable):
        """Animate a single lottery stage."""
        # Animation state
        self._anim_slider = slider
        self._anim_result = result_label
        self._anim_target = target_roll * 100
        self._anim_threshold = threshold * 100
        self._anim_callback = on_complete
        self._anim_success = target_roll < threshold
        
        # Generate bounce path
        path_points = [50.0]
        going_up = random.choice([True, False])
        num_bounces = random.randint(3, 5)
        
        for _ in range(num_bounces):
            if going_up:
                path_points.append(100.0)
                path_points.append(0.0)
            else:
                path_points.append(0.0)
                path_points.append(100.0)
        path_points.append(self._anim_target)
        
        # Calculate segments
        self._anim_segments = []
        self._anim_total_dist = 0.0
        for i in range(len(path_points) - 1):
            start, end = path_points[i], path_points[i+1]
            dist = abs(end - start)
            if dist > 0.001:
                self._anim_segments.append({
                    "start": start, "end": end, "dist": dist,
                    "cum_start": self._anim_total_dist,
                    "cum_end": self._anim_total_dist + dist
                })
                self._anim_total_dist += dist
        
        self._anim_elapsed = 0.0
        self._anim_duration = 4.0  # Snappy animation
        
        # Style state tracking for performance
        self._anim_last_zone = None
        
        self._anim_timer = QtCore.QTimer(self)
        self._anim_timer.timeout.connect(self._anim_tick)
        self._anim_timer.start(16)  # 60 FPS for smoother animation
    
    def _anim_tick(self):
        """Animation tick for current stage."""
        self._anim_elapsed += 0.016  # Match 16ms timer interval
        t = min(1.0, self._anim_elapsed / self._anim_duration)
        eased = 1.0 - (1.0 - t) ** 4
        
        current_travel = eased * self._anim_total_dist
        pos = self._anim_target
        
        for seg in self._anim_segments:
            if seg["cum_start"] <= current_travel <= seg["cum_end"]:
                local = (current_travel - seg["cum_start"]) / seg["dist"]
                pos = seg["start"] + (seg["end"] - seg["start"]) * local
                break
        
        pos = max(0, min(100, pos))
        self._anim_slider.set_position(pos)
        
        # Update result label color during animation - only if zone changed
        is_in_win_zone = pos < self._anim_threshold
        if is_in_win_zone != self._anim_last_zone:
            self._anim_last_zone = is_in_win_zone
            if is_in_win_zone:
                self._anim_result.setStyleSheet("color: #4caf50; font-size: 14px;")
            else:
                self._anim_result.setStyleSheet("color: #f44336; font-size: 14px;")
        self._anim_result.setText(f"🎲 {pos:.1f}%")
        
        if t >= 1.0:
            self._anim_timer.stop()
            self._anim_slider.set_position(self._anim_target)
            self._anim_slider.set_result(self._anim_success)
            self._anim_callback(self._anim_success)
    
    def _finish(self):
        """Emit result and close."""
        self.finished_signal.emit(self.won_item, self.tier if self.won_item else "")
        self.accept()
    
    def closeEvent(self, event):
        """Clean up timers and save geometry."""
        save_dialog_geometry(self, "EyeProtectionLotteryDialog")
        if hasattr(self, '_anim_timer'):
            self._anim_timer.stop()
        if hasattr(self, '_tier_anim_timer'):
            self._tier_anim_timer.stop()
        super().closeEvent(event)

    def get_results(self) -> tuple:
        """Get the lottery results.
        
        Returns:
            (won_item: bool, tier: str) - tier is empty string if no item won
        """
        return (self.won_item, self.tier if self.won_item else "")


class MultiTierLotterySlider(QtWidgets.QWidget):
    """Custom widget for 5-tier rarity lottery visualization.
    
    Shows colored zones for Common/Uncommon/Rare/Epic/Legendary 
    based on their probability weights.
    """
    
    # Cached paint objects for performance
    _CACHED_COLORS = None
    _FONT_LABEL = None
    _FONT_PERCENT = None
    _PEN_SEPARATOR = None
    _COLOR_WHITE = None
    _COLOR_GRAY = None
    
    @classmethod
    def _init_paint_cache(cls):
        """Initialize cached paint objects (lazy loading)."""
        if cls._CACHED_COLORS is None:
            cls._CACHED_COLORS = {
                "Common": QtGui.QColor("#9e9e9e"),
                "Uncommon": QtGui.QColor("#4caf50"),
                "Rare": QtGui.QColor("#2196f3"),
                "Epic": QtGui.QColor("#9c27b0"),
                "Legendary": QtGui.QColor("#ff9800")
            }
            cls._FONT_LABEL = QtGui.QFont("Arial", 7, QtGui.QFont.Bold)
            cls._FONT_PERCENT = QtGui.QFont("Arial", 8)
            cls._PEN_SEPARATOR = QtGui.QPen(QtGui.QColor("#1a1a2e"), 2)
            cls._COLOR_WHITE = QtGui.QColor("#fff")
            cls._COLOR_GRAY = QtGui.QColor("#888")
    
    def __init__(self, weights: dict, parent=None):
        """
        Args:
            weights: Dict mapping rarity -> weight (e.g., {"Common": 5, ...})
        """
        super().__init__(parent)
        self._init_paint_cache()  # Ensure cache is ready
        self.weights = weights
        self.total = sum(weights.values())
        self.position = 0.0
        self.result_rarity = None
        self.setMinimumWidth(400)
        
        # Rarity colors (string versions for compatibility)
        self.rarity_colors = {
            "Common": "#9e9e9e",
            "Uncommon": "#4caf50",
            "Rare": "#2196f3",
            "Epic": "#9c27b0",
            "Legendary": "#ff9800"
        }
    
    def set_position(self, pos: float):
        """Set marker position (0-100)."""
        self.position = max(0, min(100, pos))
        self.update()
    
    def set_result(self, rarity: str):
        """Set the result rarity for visual feedback."""
        self.result_rarity = rarity
        self.update()
    
    def get_rarity_at_position(self, pos: float) -> str:
        """Get which rarity zone a position falls into."""
        if self.total <= 0:
            return "Common"  # Fallback
        cumulative = 0.0
        rarity_order = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
        for rarity in rarity_order:
            weight = self.weights.get(rarity, 0)
            zone_pct = (weight / self.total) * 100
            if pos < cumulative + zone_pct:
                return rarity
            cumulative += zone_pct
        return "Legendary"  # Edge case
    
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        margin = 10
        bar_height = 30
        bar_y = (h - bar_height) // 2 + 5
        
        # Draw rarity zones
        rarity_order = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
        cumulative_pct = 0.0
        
        if self.total <= 0:
            return  # Nothing to draw
        
        for i, rarity in enumerate(rarity_order):
            weight = self.weights.get(rarity, 0)
            zone_pct = (weight / self.total) * 100
            
            start_x = margin + (cumulative_pct / 100.0) * (w - 2*margin)
            zone_width = (zone_pct / 100.0) * (w - 2*margin)
            
            # Use cached color objects
            color = self._CACHED_COLORS.get(rarity, self._COLOR_GRAY)
            painter.setBrush(color)
            painter.setPen(QtCore.Qt.NoPen)
            
            # Round corners only on first/last
            rect = QtCore.QRectF(start_x, bar_y, zone_width, bar_height)
            if i == 0:
                path = QtGui.QPainterPath()
                path.addRoundedRect(rect, 4, 4)
                painter.drawPath(path)
            elif i == len(rarity_order) - 1:
                path = QtGui.QPainterPath()
                path.addRoundedRect(rect, 4, 4)
                painter.drawPath(path)
            else:
                painter.drawRect(rect)
            
            # Draw rarity label if zone is wide enough
            if zone_width > 35:
                painter.setPen(self._COLOR_WHITE)
                painter.setFont(self._FONT_LABEL)
                label_x = start_x + zone_width/2 - 12
                painter.drawText(int(label_x), bar_y + bar_height//2 + 4, rarity[:3].upper())
            
            # Draw separator line
            if i < len(rarity_order) - 1:
                painter.setPen(self._PEN_SEPARATOR)
                sep_x = start_x + zone_width
                painter.drawLine(int(sep_x), bar_y, int(sep_x), bar_y + bar_height)
            
            cumulative_pct += zone_pct
        
        # Draw 0% and 100% labels
        painter.setPen(self._COLOR_GRAY)
        painter.setFont(self._FONT_PERCENT)
        painter.drawText(margin, bar_y + bar_height + 15, "0%")
        painter.drawText(w - margin - 25, bar_y + bar_height + 15, "100%")
        
        # Draw the sliding marker
        marker_x = margin + (self.position / 100.0) * (w - 2*margin)
        
        # Marker color based on current zone
        current_rarity = self.get_rarity_at_position(self.position)
        marker_color = self._CACHED_COLORS.get(current_rarity, self._COLOR_WHITE)
        
        # Glow effect if result
        if self.result_rarity:
            glow_color = self._CACHED_COLORS.get(self.result_rarity, self._COLOR_WHITE)
            for i in range(3):
                glow_size = 12 + (3-i) * 4
                painter.setBrush(glow_color)
                painter.setOpacity(0.3)
                painter.drawEllipse(
                    QtCore.QPointF(marker_x, bar_y + bar_height // 2),
                    glow_size, glow_size
                )
            painter.setOpacity(1.0)
        
        # Draw marker (triangle)
        painter.setBrush(marker_color)
        painter.setPen(QtGui.QPen(self._COLOR_WHITE, 2))
        
        triangle = QtGui.QPolygonF([
            QtCore.QPointF(marker_x, bar_y - 2),
            QtCore.QPointF(marker_x - 8, bar_y - 14),
            QtCore.QPointF(marker_x + 8, bar_y - 14),
        ])
        painter.drawPolygon(triangle)
        
        # Marker line
        painter.setPen(QtGui.QPen(marker_color, 3))
        painter.drawLine(int(marker_x), bar_y, int(marker_x), bar_y + bar_height)


class PriorityLotteryDialog(QtWidgets.QDialog):
    """Two-stage lottery for Priority Completion rewards.
    
    Stage 1: Win/Lose roll (chance based on logged hours: 15%-99%)
    Stage 2: Rarity roll (5-tier weighted: Common 5%, Uncommon 10%, Rare 30%, Epic 35%, Legendary 20%)
    
    Only shows Stage 2 if Stage 1 succeeds.
    """
    
    # Signal emits (won: bool, rarity: str, item: dict or None)
    finished_signal = QtCore.Signal(bool, str, object)
    
    # Rarity weights for priority rewards (inverted - high tiers more common!)
    RARITY_WEIGHTS = {
        "Common": 5,
        "Uncommon": 10,
        "Rare": 30,
        "Epic": 35,
        "Legendary": 20
    }
    
    def __init__(self, win_chance: float, priority_title: str,
                 logged_hours: float = 0, story_id: str = None,
                 parent: Optional[QtWidgets.QWidget] = None):
        """
        Args:
            win_chance: Chance to win (0.0-1.0)
            priority_title: Name of the completed priority
            logged_hours: Hours logged for display
            story_id: Story theme for item generation
            parent: Parent widget
        """
        super().__init__(parent)
        self.win_chance = win_chance
        self.priority_title = priority_title
        self.logged_hours = logged_hours
        self.story_id = story_id
        
        # Pre-roll results
        self.win_roll = random.random()
        self.won = self.win_roll < win_chance
        
        # Roll rarity (will only matter if won)
        self.rarity_roll = random.random() * 100
        self.won_rarity = self._determine_rarity(self.rarity_roll)
        self.won_item = None
        
        if self.won:
            # Generate the actual item
            try:
                from gamification import generate_item
                self.won_item = generate_item(rarity=self.won_rarity, story_id=story_id)
            except (ImportError, Exception):
                # Fallback if gamification unavailable
                self.won_item = {"name": f"{self.won_rarity} Item", "rarity": self.won_rarity, "power": 10}
        
        self.current_stage = 0
        self._setup_ui()
        QtCore.QTimer.singleShot(300, self._start_stage_1)
    
    def _determine_rarity(self, roll: float) -> str:
        """Determine rarity based on roll (0-100) and weights."""
        total = sum(self.RARITY_WEIGHTS.values())
        if total <= 0:
            return "Common"  # Fallback
        cumulative = 0.0
        for rarity in ["Common", "Uncommon", "Rare", "Epic", "Legendary"]:
            weight = self.RARITY_WEIGHTS[rarity]
            zone_pct = (weight / total) * 100
            if roll < cumulative + zone_pct:
                return rarity
            cumulative += zone_pct
        return "Legendary"
    
    def _setup_ui(self):
        """Build the two-stage lottery UI."""
        self.setWindowTitle("🎁 Lucky Gift Roll!")
        self.setModal(True)
        self.setMinimumSize(440, 340)
        load_dialog_geometry(self, "PriorityLotteryDialog", QtCore.QSize(540, 420))
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)  # Small margin for shadow
        
        # Main container
        container = QtWidgets.QWidget()
        container.setStyleSheet("""
            QWidget {
                background: #1a1a2e;
                border: none;
                border-radius: 12px;
            }
        """)
        # Apply drop shadow to container for depth without borders
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QtGui.QColor(0, 0, 0, 120))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)
        
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setSpacing(12)
        container_layout.setContentsMargins(24, 18, 24, 18)

        # Header
        header = QtWidgets.QLabel("🎁 Priority Complete! Rolling for Lucky Gift... 🎁")
        header.setAlignment(QtCore.Qt.AlignCenter)
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #9ca3af;")
        container_layout.addWidget(header)
        
        # Priority info
        info = QtWidgets.QLabel(f"✅ '{self.priority_title}'\n⏱️ {self.logged_hours:.1f}h logged")
        info.setAlignment(QtCore.Qt.AlignCenter)
        info.setStyleSheet("color: #aaa; font-size: 11px;")
        container_layout.addWidget(info)
        
        # Stage 1: Win/Lose
        self.stage1_frame = QtWidgets.QFrame()
        self.stage1_frame.setStyleSheet("""
            QFrame {
                background: #252540;
                border: none;
                border-radius: 8px;
            }
        """)
        # Add subtle shadow for card effect
        shadow1 = QtWidgets.QGraphicsDropShadowEffect()
        shadow1.setBlurRadius(10)
        shadow1.setColor(QtGui.QColor(0, 0, 0, 80))
        shadow1.setOffset(0, 2)
        self.stage1_frame.setGraphicsEffect(shadow1)
        self.stage1_frame.setMinimumHeight(100)  # Prevent collapse
        stage1_layout = QtWidgets.QVBoxLayout(self.stage1_frame)
        stage1_layout.setContentsMargins(14, 10, 14, 10)
        
        self.stage1_title = QtWidgets.QLabel(f"🎰 Stage 1: Lucky Roll ({self.win_chance*100:.0f}% chance)")
        self.stage1_title.setStyleSheet("color: #aaa; font-size: 12px; font-weight: bold;")
        # Add tooltip explaining win chance
        win_pct = self.win_chance * 100
        self.stage1_title.setToolTip(
            f"🎲 Win Chance: {win_pct:.0f}%\n"
            f"──────────────\n"
            f"Base: 15%\n"
            f"Hours logged ({self.logged_hours:.1f}h): +{min(84, int(self.logged_hours * 10))}%\n"
            f"Max: 99%\n\n"
            f"Log more hours for better odds!"
        )
        stage1_layout.addWidget(self.stage1_title)
        
        self.stage1_slider = LotterySliderWidget(self.win_chance * 100)
        self.stage1_slider.setFixedHeight(50)
        stage1_layout.addWidget(self.stage1_slider)
        
        self.stage1_result = QtWidgets.QLabel("Waiting...")
        self.stage1_result.setAlignment(QtCore.Qt.AlignCenter)
        self.stage1_result.setStyleSheet("color: #888; font-size: 14px;")
        stage1_layout.addWidget(self.stage1_result)
        
        container_layout.addWidget(self.stage1_frame)
        
        # Stage 2: Rarity (initially hidden/dimmed)
        self.stage2_frame = QtWidgets.QFrame()
        self.stage2_frame.setStyleSheet("""
            QFrame {
                background: #252540;
                border: none;
                border-radius: 8px;
            }
        """)
        # Add subtle shadow for card effect
        shadow2 = QtWidgets.QGraphicsDropShadowEffect()
        shadow2.setBlurRadius(10)
        shadow2.setColor(QtGui.QColor(0, 0, 0, 80))
        shadow2.setOffset(0, 2)
        self.stage2_frame.setGraphicsEffect(shadow2)
        self.stage2_frame.setMinimumHeight(110)  # Prevent collapse
        stage2_layout = QtWidgets.QVBoxLayout(self.stage2_frame)
        stage2_layout.setContentsMargins(14, 10, 14, 10)
        
        self.stage2_title = QtWidgets.QLabel("✨ Stage 2: Rarity Roll")
        self.stage2_title.setStyleSheet("color: #666; font-size: 12px; font-weight: bold;")
        # Add tooltip explaining rarity distribution (inverted for priorities!)
        total_weight = sum(self.RARITY_WEIGHTS.values())
        rarity_breakdown = "\n".join([
            f"{r}: {self.RARITY_WEIGHTS[r]}% ({self.RARITY_WEIGHTS[r]*100//total_weight}% actual)"
            for r in ["Legendary", "Epic", "Rare", "Uncommon", "Common"]
        ])
        self.stage2_title.setToolTip(
            f"🎲 Rarity Distribution (Priority Rewards):\n"
            f"──────────────────────\n"
            f"Legendary: {self.RARITY_WEIGHTS['Legendary']}%\n"
            f"Epic: {self.RARITY_WEIGHTS['Epic']}%\n"
            f"Rare: {self.RARITY_WEIGHTS['Rare']}%\n"
            f"Uncommon: {self.RARITY_WEIGHTS['Uncommon']}%\n"
            f"Common: {self.RARITY_WEIGHTS['Common']}%\n\n"
            f"⭐ Priority rewards favor high tiers!"
        )
        stage2_layout.addWidget(self.stage2_title)
        
        self.stage2_slider = MultiTierLotterySlider(self.RARITY_WEIGHTS)
        self.stage2_slider.setFixedHeight(60)
        self.stage2_slider.setEnabled(False)
        stage2_layout.addWidget(self.stage2_slider)
        
        self.stage2_result = QtWidgets.QLabel("(Win the lucky roll first...)")
        self.stage2_result.setAlignment(QtCore.Qt.AlignCenter)
        self.stage2_result.setStyleSheet("color: #555; font-size: 14px;")
        stage2_layout.addWidget(self.stage2_result)
        
        container_layout.addWidget(self.stage2_frame)
        
        # Final result
        self.final_result = QtWidgets.QLabel("")
        self.final_result.setAlignment(QtCore.Qt.AlignCenter)
        self.final_result.setWordWrap(True)
        self.final_result.setMinimumHeight(40)  # Reserve space for result text
        self.final_result.setStyleSheet("color: #fff; font-size: 14px;")
        container_layout.addWidget(self.final_result)
        
        # Stretch to absorb any extra space
        container_layout.addStretch(1)
        
        # Sound toggle
        sound_row = QtWidgets.QHBoxLayout()
        sound_row.addStretch()
        self.sound_toggle = QtWidgets.QCheckBox("🔊 Sound")
        self.sound_toggle.setChecked(get_lottery_sound_enabled())
        self.sound_toggle.setStyleSheet("color: #666; font-size: 11px;")
        self.sound_toggle.toggled.connect(set_lottery_sound_enabled)
        sound_row.addWidget(self.sound_toggle)
        container_layout.addLayout(sound_row)
        
        # Continue button (hidden until animation complete)
        self.continue_btn = QtWidgets.QPushButton("Continue")
        self.continue_btn.setStyleSheet("""
            QPushButton {
                background: #4caf50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #66bb6a;
            }
        """)
        self.continue_btn.clicked.connect(self._finish)
        self.continue_btn.hide()
        container_layout.addWidget(self.continue_btn, alignment=QtCore.Qt.AlignCenter)
        
        layout.addWidget(container)
    
    def _start_stage_1(self):
        """Start the win/lose roll animation."""
        self.current_stage = 1
        self.stage1_frame.setStyleSheet("""
            QFrame {
                background: #252540;
                border: 2px solid #6366f1;
                border-radius: 8px;
            }
        """)
        self.stage1_title.setStyleSheet("color: #a5b4fc; font-size: 12px; font-weight: bold;")
        self.stage1_result.setText("Rolling...")
        
        self._animate_stage(
            slider=self.stage1_slider,
            result_label=self.stage1_result,
            target_roll=self.win_roll * 100,
            on_complete=self._on_stage1_complete,
            is_rarity=False
        )
    
    def _on_stage1_complete(self):
        """Handle win/lose roll completion."""
        if self.won:
            self.stage1_result.setText("🎉 LUCKY! You won a gift!")
            self.stage1_result.setStyleSheet("color: #4caf50; font-size: 14px; font-weight: bold;")
            
            # Enable and start stage 2
            self.stage2_frame.setStyleSheet("""
                QFrame {
                    background: #252540;
                    border: 2px solid #6366f1;
                    border-radius: 8px;
                }
            """)
            self.stage2_title.setStyleSheet("color: #a5b4fc; font-size: 12px; font-weight: bold;")
            self.stage2_title.setText("✨ Stage 2: What rarity did you get?")
            self.stage2_slider.setEnabled(True)
            self.stage2_result.setText("Rolling for rarity...")
            self.stage2_result.setStyleSheet("color: #aaa; font-size: 14px;")
            
            QtCore.QTimer.singleShot(1000, self._start_stage_2)
        else:
            self.stage1_result.setText("💔 No gift this time...")
            self.stage1_result.setStyleSheet("color: #f44336; font-size: 14px; font-weight: bold;")
            
            self.stage2_result.setText("(Better luck next time!)")
            self.final_result.setText("Keep completing priorities for more chances! 💪\n+100 Coins earned anyway!")
            self.final_result.setStyleSheet("color: #aaa; font-size: 13px;")
            
            # Play lose sound
            _play_lottery_result_sound(False)
            
            # Show continue button for user to close when ready
            self.continue_btn.show()
    
    def _start_stage_2(self):
        """Start the rarity roll animation."""
        self.current_stage = 2
        
        self._animate_stage(
            slider=self.stage2_slider,
            result_label=self.stage2_result,
            target_roll=self.rarity_roll,
            on_complete=self._on_stage2_complete,
            is_rarity=True
        )
    
    def _on_stage2_complete(self):
        """Handle rarity roll completion."""
        rarity_colors = {
            "Common": "#9e9e9e",
            "Uncommon": "#4caf50",
            "Rare": "#2196f3",
            "Epic": "#9c27b0",
            "Legendary": "#ff9800"
        }
        rarity_emojis = {
            "Common": "⚪",
            "Uncommon": "💚",
            "Rare": "💙",
            "Epic": "💜",
            "Legendary": "🌟"
        }
        
        color = rarity_colors.get(self.won_rarity, "#fff")
        emoji = rarity_emojis.get(self.won_rarity, "🎁")
        
        self.stage2_result.setText(f"{emoji} {self.won_rarity.upper()}!")
        self.stage2_result.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")
        self.stage2_slider.set_result(self.won_rarity)
        
        # Show item details
        if self.won_item:
            item_name = self.won_item.get("name", "Unknown Item")
            item_slot = self.won_item.get("slot", "Item")
            item_power = self.won_item.get("power", 0)
            
            if self.won_rarity == "Legendary":
                self.final_result.setText(
                    f"🏆 LEGENDARY JACKPOT! 🏆\n"
                    f"<span style='color:{color}; font-size:15px;'>{item_name}</span>\n"
                    f"{item_slot} • +{item_power} Power\n"
                    f"+100 Coins earned!"
                )
            elif self.won_rarity == "Epic":
                self.final_result.setText(
                    f"💎 Epic find!\n"
                    f"<span style='color:{color}; font-size:14px;'>{item_name}</span>\n"
                    f"{item_slot} • +{item_power} Power\n"
                    f"+100 Coins earned!"
                )
            else:
                self.final_result.setText(
                    f"{emoji} You got:\n"
                    f"<span style='color:{color};'>{item_name}</span>\n"
                    f"{item_slot} • +{item_power} Power\n"
                    f"+100 Coins earned!"
                )
            self.final_result.setStyleSheet(f"color: {color}; font-size: 13px;")
        
        # Play win sound
        _play_lottery_result_sound(True)
        
        # Show continue button for user to close when ready
        self.continue_btn.show()
    
    def _animate_stage(self, slider, result_label, target_roll, on_complete, is_rarity=False):
        """Animate a single lottery stage."""
        self._anim_slider = slider
        self._anim_result = result_label
        self._anim_target = target_roll
        self._anim_callback = on_complete
        self._anim_is_rarity = is_rarity
        
        # Generate bounce path
        path_points = [50.0]
        going_up = random.choice([True, False])
        num_bounces = random.randint(4, 6)
        
        for _ in range(num_bounces):
            if going_up:
                path_points.append(100.0)
                path_points.append(0.0)
            else:
                path_points.append(0.0)
                path_points.append(100.0)
        path_points.append(target_roll)
        
        self._anim_segments = []
        self._anim_total_dist = 0.0
        for i in range(len(path_points) - 1):
            start, end = path_points[i], path_points[i+1]
            dist = abs(end - start)
            if dist > 0.001:
                self._anim_segments.append({
                    "start": start, "end": end, "dist": dist,
                    "cum_start": self._anim_total_dist,
                    "cum_end": self._anim_total_dist + dist
                })
                self._anim_total_dist += dist
        
        self._anim_elapsed = 0.0
        self._anim_duration = 5.0  # Snappy dramatic effect
        
        # Style state tracking for performance
        self._anim_last_rarity = None
        self._anim_last_zone = None
        
        self._anim_timer = QtCore.QTimer(self)
        self._anim_timer.timeout.connect(self._anim_tick)
        self._anim_timer.start(16)  # 60 FPS for smooth performance
    
    def _anim_tick(self):
        """Animation tick."""
        self._anim_elapsed += 0.016  # Match timer interval
        t = min(1.0, self._anim_elapsed / self._anim_duration)
        eased = 1.0 - (1.0 - t) ** 4
        
        current_travel = eased * self._anim_total_dist
        pos = self._anim_target
        
        for seg in self._anim_segments:
            if seg["cum_start"] <= current_travel <= seg["cum_end"]:
                local = (current_travel - seg["cum_start"]) / seg["dist"]
                pos = seg["start"] + (seg["end"] - seg["start"]) * local
                break
        
        pos = max(0, min(100, pos))
        self._anim_slider.set_position(pos)
        
        # Update result label - only update style if state changed
        if self._anim_is_rarity:
            rarity = self._anim_slider.get_rarity_at_position(pos)
            if rarity != self._anim_last_rarity:
                self._anim_last_rarity = rarity
                rarity_colors = {
                    "Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3",
                    "Epic": "#9c27b0", "Legendary": "#ff9800"
                }
                color = rarity_colors.get(rarity, "#aaa")
                self._anim_result.setStyleSheet(f"color: {color}; font-size: 14px;")
            self._anim_result.setText(f"🎲 {pos:.1f}% → {rarity}")
        else:
            threshold = self.win_chance * 100
            is_in_win_zone = pos < threshold
            if is_in_win_zone != self._anim_last_zone:
                self._anim_last_zone = is_in_win_zone
                if is_in_win_zone:
                    self._anim_result.setStyleSheet("color: #4caf50; font-size: 14px;")
                else:
                    self._anim_result.setStyleSheet("color: #f44336; font-size: 14px;")
            if is_in_win_zone:
                self._anim_result.setText(f"🎲 {pos:.1f}% (IN THE WIN ZONE!)")
            else:
                self._anim_result.setText(f"🎲 {pos:.1f}%")
        
        if t >= 1.0:
            self._anim_timer.stop()
            self._anim_slider.set_position(self._anim_target)
            
            if not self._anim_is_rarity:
                self._anim_slider.set_result(self.won)
            
            self._anim_callback()
    
    def _finish(self):
        """Emit result and close."""
        self.finished_signal.emit(self.won, self.won_rarity if self.won else "", self.won_item)
        self.accept()
    
    def get_results(self) -> tuple:
        """Get the lottery results.
        
        Returns:
            (won: bool, rarity: str, item: dict or None)
        """
        return (self.won, self.won_rarity if self.won else "", self.won_item)
    
    def closeEvent(self, event):
        """Clean up timers and save geometry."""
        save_dialog_geometry(self, "PriorityLotteryDialog")
        if hasattr(self, '_anim_timer'):
            self._anim_timer.stop()
        super().closeEvent(event)


class MergeTierSliderWidget(QtWidgets.QWidget):
    """Tier slider using moving window distribution centered on result rarity.
    
    Shows all 5 tiers with probability centered on the expected result,
    using a moving window that tappers off for adjacent tiers.
    """
    
    TIERS = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
    TIER_COLORS = {
        "Common": "#9e9e9e",
        "Uncommon": "#4caf50",
        "Rare": "#2196f3",
        "Epic": "#9c27b0",
        "Legendary": "#ff9800"
    }
    
    # Moving window: [5, 15, 60, 15, 5] centered on result
    BASE_WINDOW = [5, 15, 60, 15, 5]
    # Upgraded shifts distribution +1 tier higher
    UPGRADED_WINDOW = [5, 10, 25, 45, 15]
    
    # Cached paint objects for performance
    _CACHED_COLORS = None
    _FONT_LABEL = None
    _PEN_SEPARATOR = None
    _PEN_MARKER_OUTLINE = None
    _COLOR_WHITE = None
    
    @classmethod
    def _init_paint_cache(cls):
        """Initialize cached paint objects (lazy loading)."""
        if cls._CACHED_COLORS is None:
            cls._CACHED_COLORS = {t: QtGui.QColor(c) for t, c in cls.TIER_COLORS.items()}
            cls._FONT_LABEL = QtGui.QFont("Arial", 9, QtGui.QFont.Bold)
            cls._PEN_SEPARATOR = QtGui.QPen(QtGui.QColor("#1a1a2e"), 2)
            cls._PEN_MARKER_OUTLINE = QtGui.QPen(QtGui.QColor("#fff"), 2)
            cls._COLOR_WHITE = QtGui.QColor("#fff")
    
    def __init__(self, result_rarity: str = "Rare", upgraded: bool = False, parent=None):
        """
        Args:
            result_rarity: The expected result rarity (center of distribution)
            upgraded: Whether tier upgrade is enabled (shifts window higher)
        """
        super().__init__(parent)
        self._init_paint_cache()  # Ensure cache is ready
        self.result_rarity = result_rarity
        self.upgraded = upgraded
        self.position = 0.0
        self.result_tier = None
        self.setMinimumWidth(400)
        
        # Calculate tier weights using moving window
        self.tier_weights = self._calculate_tier_weights()
        self.total = sum(self.tier_weights)
    
    def _calculate_tier_weights(self) -> list:
        """Calculate weights for each tier using moving window centered on result."""
        window = self.UPGRADED_WINDOW if self.upgraded else self.BASE_WINDOW
        
        # Get result rarity index (center of window)
        try:
            center_idx = self.TIERS.index(self.result_rarity)
        except ValueError:
            center_idx = 2  # Default to Rare
        
        weights = [0, 0, 0, 0, 0]
        
        # Apply window centered on result
        for offset, pct in zip([-2, -1, 0, 1, 2], window):
            target_idx = center_idx + offset
            # Clamp to valid range
            clamped_idx = max(0, min(4, target_idx))
            weights[clamped_idx] += pct
        
        return weights
    
    def get_tier_at_position(self, pos: float) -> str:
        """Get which tier a position falls into."""
        if self.total <= 0:
            return self.result_rarity
        cumulative = 0.0
        for tier, weight in zip(self.TIERS, self.tier_weights):
            if weight <= 0:
                continue
            zone_pct = (weight / self.total) * 100
            if pos < cumulative + zone_pct:
                return tier
            cumulative += zone_pct
        return "Legendary"
    
    def get_position_for_tier(self, tier: str) -> float:
        """Get position within a tier's zone."""
        if self.total <= 0:
            return 50.0
        cumulative = 0.0
        for t, weight in zip(self.TIERS, self.tier_weights):
            if weight <= 0:
                continue
            zone_pct = (weight / self.total) * 100
            if t == tier:
                # Return middle of this zone
                return cumulative + zone_pct / 2
            cumulative += zone_pct
        return 50.0
    
    def set_position(self, pos: float):
        """Set marker position (0-100)."""
        self.position = max(0, min(100, pos))
        self.update()
    
    def set_result(self, tier: str):
        """Set the result tier for visual feedback."""
        self.result_tier = tier
        self.update()
    
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        margin = 10
        bar_height = 30
        bar_y = (h - bar_height) // 2 + 5
        
        # Draw tier zones
        cumulative_pct = 0.0
        zones_to_draw = []
        
        for tier, weight in zip(self.TIERS, self.tier_weights):
            if weight <= 0 or self.total <= 0:
                continue
            zone_pct = (weight / self.total) * 100
            zones_to_draw.append((tier, zone_pct))
        
        for i, (tier, zone_pct) in enumerate(zones_to_draw):
            color = self._CACHED_COLORS.get(tier, self._COLOR_WHITE)
            start_x = margin + (cumulative_pct / 100.0) * (w - 2*margin)
            zone_width = (zone_pct / 100.0) * (w - 2*margin)
            
            painter.setBrush(color)
            painter.setPen(QtCore.Qt.NoPen)
            
            rect = QtCore.QRectF(start_x, bar_y, zone_width, bar_height)
            if i == 0:
                path = QtGui.QPainterPath()
                path.addRoundedRect(rect, 4, 4)
                painter.drawPath(path)
            elif i == len(zones_to_draw) - 1:
                path = QtGui.QPainterPath()
                path.addRoundedRect(rect, 4, 4)
                painter.drawPath(path)
            else:
                painter.drawRect(rect)
            
            # Draw zone label
            if zone_width > 25:
                painter.setPen(self._COLOR_WHITE)
                painter.setFont(self._FONT_LABEL)
                label = tier[:4] if zone_width > 45 else tier[:3]
                label_rect = QtCore.QRectF(start_x, bar_y, zone_width, bar_height)
                painter.drawText(label_rect, QtCore.Qt.AlignCenter, label)
            
            # Separator
            if i < len(zones_to_draw) - 1:
                painter.setPen(self._PEN_SEPARATOR)
                sep_x = start_x + zone_width
                painter.drawLine(int(sep_x), bar_y, int(sep_x), bar_y + bar_height)
            
            cumulative_pct += zone_pct
        
        # Draw marker
        marker_x = margin + (self.position / 100.0) * (w - 2*margin)
        current_tier = self.get_tier_at_position(self.position)
        marker_color = self._CACHED_COLORS.get(current_tier, self._COLOR_WHITE)
        
        # Glow if result set
        if self.result_tier:
            glow_color = self._CACHED_COLORS.get(self.result_tier, self._COLOR_WHITE)
            for i in range(3):
                glow_size = 12 + (3-i) * 4
                painter.setBrush(glow_color)
                painter.setOpacity(0.3)
                painter.drawEllipse(
                    QtCore.QPointF(marker_x, bar_y + bar_height // 2),
                    glow_size, glow_size
                )
            painter.setOpacity(1.0)
        
        # Triangle marker
        painter.setBrush(marker_color)
        painter.setPen(self._PEN_MARKER_OUTLINE)
        
        triangle = QtGui.QPolygonF([
            QtCore.QPointF(marker_x, bar_y - 2),
            QtCore.QPointF(marker_x - 8, bar_y - 14),
            QtCore.QPointF(marker_x + 8, bar_y - 14),
        ])
        painter.drawPolygon(triangle)
        
        painter.setPen(QtGui.QPen(marker_color, 3))
        painter.drawLine(int(marker_x), bar_y, int(marker_x), bar_y + bar_height)


class TierJumpSliderWidget(QtWidgets.QWidget):
    """Custom widget for 4-tier jump visualization in merge.
    
    Shows colored zones for target rarities based on probability weights.
    Supports shifting the distribution via upgrade_shift parameter.
    """
    
    # Base weights: +1=50%, +2=30%, +3=15%, +4=5%
    BASE_WEIGHTS = [50, 30, 15, 5]  # Index 0=+1, 1=+2, 2=+3, 3=+4
    
    # Rarity names and colors (matching ITEM_RARITIES in gamification.py)
    RARITY_ORDER = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
    RARITY_COLORS = {
        "Common": "#9e9e9e",
        "Uncommon": "#4caf50",
        "Rare": "#2196f3",
        "Epic": "#9c27b0",
        "Legendary": "#ff9800"
    }
    
    def __init__(self, upgrade_shift: int = 0, base_rarity: str = "Common", parent=None):
        super().__init__(parent)
        self.upgrade_shift = upgrade_shift
        self.base_rarity = base_rarity
        
        # Calculate base rarity index
        try:
            self.base_idx = self.RARITY_ORDER.index(base_rarity)
        except ValueError:
            self.base_idx = 0
        
        # Apply shift to weights (moving window concept)
        # Shift 0: [50, 30, 15, 5] → +1=50%, +2=30%, +3=15%, +4=5%
        # Shift 1: [30, 35, 25, 10] → Better odds for higher tiers
        # Shift 2: [15, 30, 35, 20] → Even better
        shifted = self._get_shifted_weights(upgrade_shift)
        self.jump_weights = {1: shifted[0], 2: shifted[1], 3: shifted[2], 4: shifted[3]}
        self.total = sum(self.jump_weights.values())
        self.position = 0.0
        self.result_jump = None
        self.setMinimumWidth(400)
        
        # Calculate target rarities based on base + jump
        # Filter out jumps that exceed Legendary
        self._calculate_target_rarities()
    
    def _get_shifted_weights(self, shift: int) -> list:
        """Get shifted weights based on upgrade level.
        
        Moving window shifts probability toward higher tiers.
        """
        if shift <= 0:
            return self.BASE_WEIGHTS.copy()
        elif shift == 1:
            # Shift window: less +1, more +2/+3/+4
            return [30, 35, 25, 10]  # +1=30%, +2=35%, +3=25%, +4=10%
        elif shift >= 2:
            # Heavy shift toward top tiers
            return [15, 30, 35, 20]  # +1=15%, +2=30%, +3=35%, +4=20%
        return self.BASE_WEIGHTS.copy()
    
    def _calculate_target_rarities(self):
        """Calculate target rarities based on base rarity and jumps.
        
        Combines duplicate rarities (e.g., when multiple jumps result in Legendary).
        """
        self.target_rarities = {}  # jump -> (rarity_name, color, weight)
        self.valid_jumps = []
        self.actual_weights = {}
        
        # First, calculate raw jumps
        for jump in [1, 2, 3, 4]:
            target_idx = min(self.base_idx + jump, len(self.RARITY_ORDER) - 1)
            target_rarity = self.RARITY_ORDER[target_idx]
            target_color = self.RARITY_COLORS.get(target_rarity, "#666")
            weight = self.jump_weights.get(jump, 0)
            
            self.target_rarities[jump] = (target_rarity, target_color, weight)
        
        # Now combine duplicate rarities into single zones
        # Maps rarity -> combined weight
        self.combined_rarities = {}  # rarity -> (color, combined_weight)
        self.rarity_to_jumps = {}  # rarity -> list of jumps that result in this rarity
        
        for jump in [1, 2, 3, 4]:
            rarity, color, weight = self.target_rarities[jump]
            if rarity not in self.combined_rarities:
                self.combined_rarities[rarity] = (color, weight)
                self.rarity_to_jumps[rarity] = [jump]
            else:
                old_color, old_weight = self.combined_rarities[rarity]
                self.combined_rarities[rarity] = (old_color, old_weight + weight)
                self.rarity_to_jumps[rarity].append(jump)
        
        # Build ordered list of unique rarities for display
        self.display_rarities = []  # [(rarity, color, weight), ...]
        seen = set()
        for jump in [1, 2, 3, 4]:
            rarity = self.target_rarities[jump][0]
            if rarity not in seen:
                color, combined_weight = self.combined_rarities[rarity]
                self.display_rarities.append((rarity, color, combined_weight))
                seen.add(rarity)
        
        # Set valid jumps and weights (using original for position calculation)
        for jump in [1, 2, 3, 4]:
            self.valid_jumps.append(jump)
            self.actual_weights[jump] = self.jump_weights.get(jump, 0)
        
        # Recalculate total for valid jumps
        self.total = sum(self.actual_weights.values())
    
    def get_target_rarity_for_jump(self, jump: int) -> str:
        """Get the target rarity name for a given jump."""
        if jump in self.target_rarities:
            return self.target_rarities[jump][0]
        return "Legendary"
    
    def get_color_for_jump(self, jump: int) -> str:
        """Get the color for a given jump (based on target rarity)."""
        if jump in self.target_rarities:
            return self.target_rarities[jump][1]
        return "#ff9800"
    
    def set_position(self, pos: float):
        """Set marker position (0-100)."""
        self.position = max(0, min(100, pos))
        self.update()
    
    def set_result(self, jump: int):
        """Set the result tier jump for visual feedback."""
        self.result_jump = jump
        self.update()
    
    def get_jump_at_position(self, pos: float) -> int:
        """Get which tier jump zone a position falls into."""
        if self.total <= 0:
            return 1  # Fallback
        cumulative = 0.0
        for jump in [1, 2, 3, 4]:
            weight = self.jump_weights.get(jump, 0)
            zone_pct = (weight / self.total) * 100
            if pos < cumulative + zone_pct:
                return jump
            cumulative += zone_pct
        return 4  # Edge case
    
    def paintEvent(self, event):
        _PaintCache.initialize()  # Ensure cache is ready
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        margin = 10
        bar_height = 30
        bar_y = (h - bar_height) // 2 + 5
        
        # Draw tier zones using COMBINED rarities (no duplicate Legendary slots)
        cumulative_pct = 0.0
        
        for i, (rarity, color, weight) in enumerate(self.display_rarities):
            if self.total <= 0:
                continue
            zone_pct = (weight / self.total) * 100
            
            start_x = margin + (cumulative_pct / 100.0) * (w - 2*margin)
            zone_width = (zone_pct / 100.0) * (w - 2*margin)
            
            # Use cached tier color if available
            cached_color = _PaintCache.get_tier_color(rarity)
            painter.setBrush(cached_color)
            painter.setPen(QtCore.Qt.NoPen)
            
            rect = QtCore.QRectF(start_x, bar_y, zone_width, bar_height)
            if i == 0:
                path = QtGui.QPainterPath()
                path.addRoundedRect(rect, 4, 4)
                painter.drawPath(path)
            elif i == len(self.display_rarities) - 1:  # Last
                path = QtGui.QPainterPath()
                path.addRoundedRect(rect, 4, 4)
                painter.drawPath(path)
            else:
                painter.drawRect(rect)
            
            # Draw zone label with RARITY NAME (abbreviated)
            if zone_width > 25:
                painter.setPen(_PaintCache.COLOR_WHITE)
                painter.setFont(_PaintCache.FONT_LABEL_MEDIUM)
                # Use abbreviation for short zones
                if zone_width < 50:
                    label = rarity[:3]  # "Unc", "Rar", "Epi", "Leg"
                else:
                    label = rarity[:4]  # "Unco", "Rare", "Epic", "Lege"
                label_rect = QtCore.QRectF(start_x, bar_y, zone_width, bar_height)
                painter.drawText(label_rect, QtCore.Qt.AlignCenter, label)
            
            # Draw separator between different rarities
            if i < len(self.display_rarities) - 1:
                painter.setPen(_PaintCache.PEN_SEPARATOR)
                sep_x = start_x + zone_width
                painter.drawLine(int(sep_x), bar_y, int(sep_x), bar_y + bar_height)
            
            cumulative_pct += zone_pct
        
        # Draw marker (still uses jump positions internally)
        marker_x = margin + (self.position / 100.0) * (w - 2*margin)
        current_jump = self.get_jump_at_position(self.position)
        current_rarity = self.get_target_rarity_for_jump(current_jump)
        marker_color = _PaintCache.get_tier_color(current_rarity)
        
        # Glow if result
        if self.result_jump:
            result_rarity = self.get_target_rarity_for_jump(self.result_jump)
            glow_color = _PaintCache.get_tier_color(result_rarity)
            for i in range(3):
                glow_size = 12 + (3-i) * 4
                painter.setBrush(glow_color)
                painter.setOpacity(0.3)
                painter.drawEllipse(
                    QtCore.QPointF(marker_x, bar_y + bar_height // 2),
                    glow_size, glow_size
                )
            painter.setOpacity(1.0)
        
        # Triangle marker
        painter.setBrush(marker_color)
        painter.setPen(_PaintCache.PEN_MARKER_OUTLINE)
        
        triangle = QtGui.QPolygonF([
            QtCore.QPointF(marker_x, bar_y - 2),
            QtCore.QPointF(marker_x - 8, bar_y - 14),
            QtCore.QPointF(marker_x + 8, bar_y - 14),
        ])
        painter.drawPolygon(triangle)
        
        painter.setPen(QtGui.QPen(marker_color, 3))
        painter.drawLine(int(marker_x), bar_y, int(marker_x), bar_y + bar_height)


class MergeTwoStageLotteryDialog(QtWidgets.QDialog):
    """Two-stage lottery for Merge with tier + success animation.
    
    Stage 1: Tier roll using moving window centered on result rarity
    Stage 2: Success/Fail roll - will you get the rolled tier?
    
    Uses moving window distribution like other lottery systems.
    """
    
    finished_signal = QtCore.Signal(bool, str)  # (success, tier_name)
    
    TIERS = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
    TIER_COLORS = {
        "Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3",
        "Epic": "#9c27b0", "Legendary": "#ff9800"
    }
    
    # Moving window: [5, 15, 60, 15, 5] centered on result rarity
    BASE_WINDOW = [5, 15, 60, 15, 5]
    # Upgraded shifts distribution higher
    UPGRADED_WINDOW = [5, 10, 25, 45, 15]
    
    def __init__(self, success_roll: float, success_threshold: float,
                 tier_upgrade_enabled: bool = False,
                 base_rarity: str = "Common",
                 title: str = "",
                 parent: Optional[QtWidgets.QWidget] = None,
                 entity_perk_contributors: list = None):
        """
        Args:
            success_roll: The actual success roll (0.0-1.0). If <= 0, generates random roll.
            success_threshold: Success threshold (0.0-1.0). Roll < threshold = success.
            tier_upgrade_enabled: Whether +50 coin tier upgrade is active
            base_rarity: The RESULT rarity (center of distribution)
            title: Custom title for the dialog (empty = default "Lucky Merge")
            parent: Parent widget
            entity_perk_contributors: List of entity perks that boosted rarity/luck
        """
        super().__init__(parent)
        # Generate random roll if not provided (negative means "generate one")
        # Note: 0.0 is a valid roll (guaranteed success), so only check for negative
        self.success_roll = success_roll if success_roll >= 0 else random.random()
        self.success_threshold = success_threshold
        self.is_success = self.success_roll < success_threshold
        self.tier_upgrade_enabled = tier_upgrade_enabled
        self.result_rarity = base_rarity  # This is the CENTER of distribution
        self.custom_title = title  # Store custom title
        self._entity_perk_contributors = entity_perk_contributors or []
        
        # Calculate tier weights using moving window
        self.tier_weights = self._calculate_tier_weights()
        
        # Pre-roll tier (only matters if success)
        self.tier_roll = random.random() * 100
        self.rolled_tier = self._determine_tier(self.tier_roll)
        
        # Calculate tier jump for backwards compatibility
        try:
            result_idx = self.TIERS.index(self.result_rarity)
            rolled_idx = self.TIERS.index(self.rolled_tier)
            self.tier_jump = max(1, rolled_idx - result_idx + 1)  # +1 because base result is already +1 from input
        except ValueError:
            self.tier_jump = 1
        
        self.current_stage = 0
        self._setup_ui()
        QtCore.QTimer.singleShot(300, self._start_stage_1)
    
    def _calculate_tier_weights(self) -> list:
        """Calculate tier weights using moving window centered on result rarity."""
        window = self.UPGRADED_WINDOW if self.tier_upgrade_enabled else self.BASE_WINDOW
        
        try:
            center_idx = self.TIERS.index(self.result_rarity)
        except ValueError:
            center_idx = 2  # Default to Rare
        
        weights = [0, 0, 0, 0, 0]
        
        for offset, pct in zip([-2, -1, 0, 1, 2], window):
            target_idx = center_idx + offset
            clamped_idx = max(0, min(4, target_idx))
            weights[clamped_idx] += pct
        
        return weights
    
    def _determine_tier(self, roll: float) -> str:
        """Determine tier from roll (0-100) based on weights."""
        total = sum(self.tier_weights)
        if total <= 0:
            return self.result_rarity
        cumulative = 0.0
        for tier, weight in zip(self.TIERS, self.tier_weights):
            if weight <= 0:
                continue
            zone_pct = (weight / total) * 100
            if roll < cumulative + zone_pct:
                return tier
            cumulative += zone_pct
        return "Legendary"
    
    def _setup_ui(self):
        """Build two-stage merge lottery UI."""
        # Use custom title if provided
        if self.custom_title:
            self.setWindowTitle(self.custom_title)
        else:
            self.setWindowTitle("⚔️ Lucky Merge")
        self.setModal(True)
        self.setMinimumSize(440, 380)
        load_dialog_geometry(self, "MergeLotteryDialog", QtCore.QSize(540, 480))
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)  # Small margin for shadow
        
        container = QtWidgets.QWidget()
        container.setStyleSheet("""
            QWidget {
                background: #1a1a2e;
                border: none;
                border-radius: 12px;
            }
        """)
        # Apply drop shadow to container for depth without borders
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QtGui.QColor(0, 0, 0, 120))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)
        
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setSpacing(12)
        container_layout.setContentsMargins(24, 18, 24, 18)

        # Header - use custom title if provided
        if self.custom_title:
            header_text = self.custom_title
        elif self.tier_upgrade_enabled:
            header_text = "⚔️ Lucky Merge ⬆️ UPGRADED ⚔️"
        else:
            header_text = "⚔️ Lucky Merge ⚔️"
        header = QtWidgets.QLabel(header_text)
        header.setAlignment(QtCore.Qt.AlignCenter)
        header.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {'#ff9800' if self.tier_upgrade_enabled else '#9ca3af'};")
        container_layout.addWidget(header)
        
        # Entity Perk Bonuses section (if any)
        if self._entity_perk_contributors:
            perk_widget = self._create_entity_perk_display()
            if perk_widget:
                container_layout.addWidget(perk_widget)
        
        # Stage 1: Tier Roll
        self.stage1_frame = QtWidgets.QFrame()
        self.stage1_frame.setStyleSheet("""
            QFrame { background: #252540; border: none; border-radius: 8px; }
        """)
        # Add subtle shadow for card effect
        shadow1 = QtWidgets.QGraphicsDropShadowEffect()
        shadow1.setBlurRadius(10)
        shadow1.setColor(QtGui.QColor(0, 0, 0, 80))
        shadow1.setOffset(0, 2)
        self.stage1_frame.setGraphicsEffect(shadow1)
        self.stage1_frame.setMinimumHeight(120)  # Prevent collapse
        stage1_layout = QtWidgets.QVBoxLayout(self.stage1_frame)
        stage1_layout.setContentsMargins(14, 12, 14, 12)
        
        self.stage1_title = QtWidgets.QLabel("✨ Stage 1: Rolling for Rarity...")
        self.stage1_title.setStyleSheet("color: #aaa; font-size: 12px; font-weight: bold;")
        stage1_layout.addWidget(self.stage1_title)
        
        # Use new MergeTierSliderWidget with moving window
        self.stage1_slider = MergeTierSliderWidget(
            result_rarity=self.result_rarity,
            upgraded=self.tier_upgrade_enabled
        )
        self.stage1_slider.setFixedHeight(60)
        stage1_layout.addWidget(self.stage1_slider)
        
        # Distribution legend
        dist_widget = self._create_distribution_legend()
        stage1_layout.addWidget(dist_widget)
        
        self.stage1_result = QtWidgets.QLabel("Waiting...")
        self.stage1_result.setAlignment(QtCore.Qt.AlignCenter)
        self.stage1_result.setStyleSheet("color: #888; font-size: 14px;")
        stage1_layout.addWidget(self.stage1_result)
        
        container_layout.addWidget(self.stage1_frame)
        
        # Stage 2: Success/Fail
        self.stage2_frame = QtWidgets.QFrame()
        self.stage2_frame.setStyleSheet("""
            QFrame { background: #252540; border: none; border-radius: 8px; }
        """)
        # Add subtle shadow for card effect
        shadow2 = QtWidgets.QGraphicsDropShadowEffect()
        shadow2.setBlurRadius(10)
        shadow2.setColor(QtGui.QColor(0, 0, 0, 80))
        shadow2.setOffset(0, 2)
        self.stage2_frame.setGraphicsEffect(shadow2)
        self.stage2_frame.setMinimumHeight(100)  # Prevent collapse
        stage2_layout = QtWidgets.QVBoxLayout(self.stage2_frame)
        stage2_layout.setContentsMargins(14, 12, 14, 12)
        
        self.stage2_title = QtWidgets.QLabel(f"🎲 Stage 2: Will you get it? ({self.success_threshold*100:.0f}% chance)")
        self.stage2_title.setStyleSheet("color: #666; font-size: 12px; font-weight: bold;")
        stage2_layout.addWidget(self.stage2_title)
        
        self.stage2_slider = LotterySliderWidget(self.success_threshold * 100)
        self.stage2_slider.setFixedHeight(50)
        self.stage2_slider.setEnabled(False)
        stage2_layout.addWidget(self.stage2_slider)
        
        self.stage2_result = QtWidgets.QLabel("(Roll rarity first...)")
        self.stage2_result.setAlignment(QtCore.Qt.AlignCenter)
        self.stage2_result.setStyleSheet("color: #555; font-size: 14px;")
        stage2_layout.addWidget(self.stage2_result)
        
        container_layout.addWidget(self.stage2_frame)
        
        # Hide stage 2 if guaranteed success
        if self.success_threshold >= 1.0:
            self.stage2_frame.hide()
        
        # Final result
        self.final_result = QtWidgets.QLabel("")
        self.final_result.setAlignment(QtCore.Qt.AlignCenter)
        self.final_result.setWordWrap(True)
        self.final_result.setMinimumHeight(40)  # Reserve space for result text
        self.final_result.setStyleSheet("color: #fff; font-size: 16px;")
        container_layout.addWidget(self.final_result)
        
        # Stretch to absorb any extra space
        container_layout.addStretch(1)
        
        # Sound toggle
        sound_row = QtWidgets.QHBoxLayout()
        sound_row.addStretch()
        self.sound_toggle = QtWidgets.QCheckBox("🔊 Sound")
        self.sound_toggle.setChecked(get_lottery_sound_enabled())
        self.sound_toggle.setStyleSheet("color: #666; font-size: 11px;")
        self.sound_toggle.toggled.connect(set_lottery_sound_enabled)
        sound_row.addWidget(self.sound_toggle)
        container_layout.addLayout(sound_row)
        
        # Continue button (hidden until animation complete)
        self.continue_btn = QtWidgets.QPushButton("Continue")
        self.continue_btn.setStyleSheet("""
            QPushButton {
                background: #4caf50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #66bb6a;
            }
        """)
        self.continue_btn.clicked.connect(self._finish)
        self.continue_btn.hide()
        container_layout.addWidget(self.continue_btn, alignment=QtCore.Qt.AlignCenter)
        
        layout.addWidget(container)
    
    def _create_distribution_legend(self) -> QtWidgets.QWidget:
        """Create probability distribution legend showing chances for each tier."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(6)
        
        total = sum(self.tier_weights)
        if total <= 0:
            return widget
        
        for tier, weight in zip(self.TIERS, self.tier_weights):
            if weight <= 0:
                continue
            pct = (weight / total) * 100
            color = self.TIER_COLORS.get(tier, "#888")
            label = QtWidgets.QLabel(f"<b style='color:{color};'>{tier[:3]}</b>:{pct:.0f}%")
            label.setStyleSheet("font-size: 10px; color: #aaa;")
            layout.addWidget(label)
        
        layout.addStretch()
        
        if self.tier_upgrade_enabled:
            boost_label = QtWidgets.QLabel("⬆️")
            boost_label.setStyleSheet("font-size: 10px;")
            layout.addWidget(boost_label)
        
        return widget
    
    def _create_entity_perk_display(self) -> Optional[QtWidgets.QWidget]:
        """Create compact display of entity perks affecting this lottery."""
        if not self._entity_perk_contributors:
            return None
        
        # Calculate total bonuses
        total_rarity = sum(c.get("value", 0) for c in self._entity_perk_contributors 
                          if c.get("perk_type") == "rarity_bias")
        total_luck = sum(c.get("value", 0) for c in self._entity_perk_contributors 
                        if c.get("perk_type") == "drop_luck")
        
        if total_rarity <= 0 and total_luck <= 0:
            return None
        
        # Create frame
        frame = QtWidgets.QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: rgba(121, 134, 203, 0.15);
                border: 1px solid #7986cb;
                border-radius: 6px;
            }
        """)
        frame_layout = QtWidgets.QVBoxLayout(frame)
        frame_layout.setContentsMargins(8, 4, 8, 4)
        frame_layout.setSpacing(2)
        
        # Header with totals
        bonus_parts = []
        if total_rarity > 0:
            bonus_parts.append(f"+{total_rarity}% rarity")
        if total_luck > 0:
            bonus_parts.append(f"+{total_luck}% luck")
        
        header = QtWidgets.QLabel(f"🐾 Entity Patrons: {', '.join(bonus_parts)}")
        header.setAlignment(QtCore.Qt.AlignCenter)
        header.setStyleSheet("color: #a5b4fc; font-size: 10px; font-weight: bold;")
        frame_layout.addWidget(header)
        
        # Compact entity list (horizontal, scrollable if needed)
        entities_widget = QtWidgets.QWidget()
        entities_layout = QtWidgets.QHBoxLayout(entities_widget)
        entities_layout.setContentsMargins(0, 0, 0, 0)
        entities_layout.setSpacing(4)
        entities_layout.addStretch()
        
        # Show first 5 entities compactly
        for entity_data in self._entity_perk_contributors[:5]:
            name = entity_data.get("name", "Unknown")
            value = entity_data.get("value", 0)
            perk_type = entity_data.get("perk_type", "")
            is_exceptional = entity_data.get("is_exceptional", False)
            is_city = entity_data.get("is_city", False)
            
            icon = "🎲" if perk_type == "rarity_bias" else "🍀"
            display_name = name[:8] + ".." if len(name) > 8 else name
            
            if is_city:
                style = "color: #7fdbff; font-size: 9px;"
                prefix = "🏛️"
            elif is_exceptional:
                style = "color: #ffd700; font-size: 9px;"
                prefix = "⭐"
            else:
                style = "color: #bbb; font-size: 9px;"
                prefix = ""
            
            lbl = QtWidgets.QLabel(f"{prefix}{display_name} {icon}+{value}%")
            lbl.setStyleSheet(style)
            entities_layout.addWidget(lbl)
        
        # Show "+X more" if there are more
        if len(self._entity_perk_contributors) > 5:
            more_count = len(self._entity_perk_contributors) - 5
            more_lbl = QtWidgets.QLabel(f"+{more_count}")
            more_lbl.setStyleSheet("color: #666; font-size: 9px;")
            entities_layout.addWidget(more_lbl)
        
        entities_layout.addStretch()
        frame_layout.addWidget(entities_widget)
        
        return frame
    
    def _start_stage_1(self):
        """Start tier roll animation."""
        self.current_stage = 1
        self.stage1_frame.setStyleSheet("""
            QFrame { background: #252540; border: 2px solid #6366f1; border-radius: 8px; }
        """)
        self.stage1_title.setStyleSheet("color: #a5b4fc; font-size: 12px; font-weight: bold;")
        self.stage1_result.setText("Rolling...")
        
        self._animate_tier_stage(
            slider=self.stage1_slider,
            result_label=self.stage1_result,
            target_roll=self.tier_roll,
            on_complete=self._on_stage1_complete
        )
    
    def _on_stage1_complete(self):
        """Handle tier roll result."""
        color = self.TIER_COLORS.get(self.rolled_tier, "#aaa")
        
        if self.rolled_tier == "Legendary":
            label = f"🌟 {self.rolled_tier.upper()}!! 🌟"
        elif self.rolled_tier == "Epic":
            label = f"✨ {self.rolled_tier}! ✨"
        else:
            label = f"{self.rolled_tier}!"
        
        self.stage1_result.setText(label)
        self.stage1_result.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")
        self.stage1_slider.set_result(self.rolled_tier)
        
        # Skip stage 2 if guaranteed success (100%)
        if self.success_threshold >= 1.0:
            self.stage2_frame.hide()
            self.final_result.setText(f"You got {self.rolled_tier}!")
            self.final_result.setStyleSheet(f"color: {color}; font-size: 14px;")
            _play_lottery_result_sound(True)  # Play win sound
            self.continue_btn.show()  # Show continue button for user to close when ready
            return
        
        # Enable stage 2
        self.stage2_frame.setStyleSheet("""
            QFrame { background: #252540; border: 2px solid #6366f1; border-radius: 8px; }
        """)
        self.stage2_title.setStyleSheet("color: #a5b4fc; font-size: 12px; font-weight: bold;")
        self.stage2_title.setText(f"🎲 Stage 2: Will you get the {self.rolled_tier}? ({self.success_threshold*100:.0f}% chance)")
        self.stage2_slider.setEnabled(True)
        self.stage2_result.setText("Rolling for success...")
        self.stage2_result.setStyleSheet("color: #aaa; font-size: 14px;")
        
        QtCore.QTimer.singleShot(1000, self._start_stage_2)
    
    def _start_stage_2(self):
        """Start success/fail animation."""
        self.current_stage = 2
        
        self._animate_success_stage(
            slider=self.stage2_slider,
            result_label=self.stage2_result,
            target_roll=self.success_roll * 100,
            on_complete=self._on_stage2_complete
        )
    
    def _on_stage2_complete(self):
        """Handle success/fail result."""
        color = self.TIER_COLORS.get(self.rolled_tier, "#aaa")
        
        if self.is_success:
            self.stage2_result.setText("✨ SUCCESS! ✨")
            self.stage2_result.setStyleSheet("color: #4caf50; font-size: 14px; font-weight: bold;")
            self.stage2_slider.set_result(True)
            
            # Celebratory message
            try:
                result_idx = self.TIERS.index(self.result_rarity)
                rolled_idx = self.TIERS.index(self.rolled_tier)
                tier_diff = rolled_idx - result_idx
                
                if tier_diff >= 2:
                    self.final_result.setText(f"🎉 INCREDIBLE LUCK! You got {self.rolled_tier}! 🎉")
                elif tier_diff == 1:
                    self.final_result.setText(f"Great roll! You got {self.rolled_tier}!")
                elif tier_diff == 0:
                    self.final_result.setText(f"You got {self.rolled_tier}!")
                else:
                    self.final_result.setText(f"You got {self.rolled_tier}")
            except ValueError:
                self.final_result.setText(f"You got {self.rolled_tier}!")
            
            self.final_result.setStyleSheet(f"color: {color}; font-size: 14px;")
            _play_lottery_result_sound(True)  # Play win sound
            self.continue_btn.show()  # Show continue button for user to close when ready
        else:
            self.stage2_result.setText("💔 FAILED 💔")
            self.stage2_result.setStyleSheet("color: #f44336; font-size: 14px; font-weight: bold;")
            self.stage2_slider.set_result(False)
            
            self.final_result.setText(f"You almost had {self.rolled_tier}... All items were destroyed.")
            self.final_result.setStyleSheet("color: #f44336; font-size: 14px;")
            _play_lottery_result_sound(False)  # Play lose sound
            self.continue_btn.show()  # Show continue button for user to close when ready
    
    def _animate_tier_stage(self, slider, result_label, target_roll, on_complete):
        """Animate tier roll with bounce effect."""
        self._anim_slider = slider
        self._anim_result = result_label
        self._anim_target = target_roll
        self._anim_callback = on_complete
        
        # Generate bounce path
        path_points = [50.0]
        going_up = random.choice([True, False])
        num_bounces = random.randint(4, 6)
        
        for _ in range(num_bounces):
            if going_up:
                path_points.extend([100.0, 0.0])
            else:
                path_points.extend([0.0, 100.0])
        path_points.append(target_roll)
        
        self._anim_segments = []
        self._anim_total_dist = 0.0
        for i in range(len(path_points) - 1):
            start, end = path_points[i], path_points[i+1]
            dist = abs(end - start)
            if dist > 0.001:
                self._anim_segments.append({
                    "start": start, "end": end, "dist": dist,
                    "cum_start": self._anim_total_dist,
                    "cum_end": self._anim_total_dist + dist
                })
                self._anim_total_dist += dist
        
        self._anim_elapsed = 0.0
        self._anim_duration = 5.0
        
        # Style state tracking for performance
        self._tier_last_style = None
        
        self._tier_anim_timer = QtCore.QTimer(self)
        self._tier_anim_timer.timeout.connect(self._tier_anim_tick)
        self._tier_anim_timer.start(16)  # 60 FPS for smoother animation
    
    def _tier_anim_tick(self):
        """Tier animation tick."""
        self._anim_elapsed += 0.016  # Match 16ms timer interval
        t = min(1.0, self._anim_elapsed / self._anim_duration)
        eased = 1.0 - (1.0 - t) ** 4
        
        current_travel = eased * self._anim_total_dist
        pos = self._anim_target
        
        for seg in self._anim_segments:
            if seg["cum_start"] <= current_travel <= seg["cum_end"]:
                local = (current_travel - seg["cum_start"]) / seg["dist"]
                pos = seg["start"] + (seg["end"] - seg["start"]) * local
                break
        
        pos = max(0, min(100, pos))
        self._anim_slider.set_position(pos)
        
        # Show current tier - only update style if tier changed
        tier = self._anim_slider.get_tier_at_position(pos)
        if tier != self._tier_last_style:
            self._tier_last_style = tier
            color = self.TIER_COLORS.get(tier, "#aaa")
            self._anim_result.setStyleSheet(f"color: {color}; font-size: 14px;")
        self._anim_result.setText(f"🎲 {pos:.1f}% → {tier}")
        
        if t >= 1.0:
            self._tier_anim_timer.stop()
            self._anim_slider.set_position(self._anim_target)
            self._anim_callback()
    
    def _animate_success_stage(self, slider, result_label, target_roll, on_complete):
        """Animate success/fail roll."""
        self._success_slider = slider
        self._success_result = result_label
        self._success_target = target_roll
        self._success_callback = on_complete
        
        # Generate bounce path
        path_points = [50.0]
        going_up = random.choice([True, False])
        num_bounces = random.randint(4, 6)
        
        for _ in range(num_bounces):
            if going_up:
                path_points.extend([100.0, 0.0])
            else:
                path_points.extend([0.0, 100.0])
        path_points.append(target_roll)
        
        self._success_segments = []
        self._success_total_dist = 0.0
        for i in range(len(path_points) - 1):
            start, end = path_points[i], path_points[i+1]
            dist = abs(end - start)
            if dist > 0.001:
                self._success_segments.append({
                    "start": start, "end": end, "dist": dist,
                    "cum_start": self._success_total_dist,
                    "cum_end": self._success_total_dist + dist
                })
                self._success_total_dist += dist
        
        self._success_elapsed = 0.0
        self._success_duration = 5.0
        
        # Style state tracking for performance
        self._success_last_style = None
        
        self._success_anim_timer = QtCore.QTimer(self)
        self._success_anim_timer.timeout.connect(self._success_anim_tick)
        self._success_anim_timer.start(16)  # 60 FPS for smoother animation
    
    def _success_anim_tick(self):
        """Success animation tick."""
        self._success_elapsed += 0.016  # Match 16ms timer interval
        t = min(1.0, self._success_elapsed / self._success_duration)
        eased = 1.0 - (1.0 - t) ** 4
        
        current_travel = eased * self._success_total_dist
        pos = self._success_target
        
        for seg in self._success_segments:
            if seg["cum_start"] <= current_travel <= seg["cum_end"]:
                local = (current_travel - seg["cum_start"]) / seg["dist"]
                pos = seg["start"] + (seg["end"] - seg["start"]) * local
                break
        
        pos = max(0, min(100, pos))
        self._success_slider.set_position(pos)
        
        threshold = self.success_threshold * 100
        is_in_success_zone = pos < threshold
        
        # Only update style if zone changed
        if is_in_success_zone != self._success_last_style:
            self._success_last_style = is_in_success_zone
            if is_in_success_zone:
                self._success_result.setStyleSheet("color: #4caf50; font-size: 14px;")
            else:
                self._success_result.setStyleSheet("color: #f44336; font-size: 14px;")
        
        if is_in_success_zone:
            self._success_result.setText(f"🎲 {pos:.1f}% (SUCCESS ZONE!)")
        else:
            self._success_result.setText(f"🎲 {pos:.1f}%")
        
        if t >= 1.0:
            self._success_anim_timer.stop()
            self._success_slider.set_position(self._success_target)
            self._success_callback()
    
    def _finish(self):
        """Emit result and close."""
        self.finished_signal.emit(self.is_success, self.rolled_tier if self.is_success else "")
        self.accept()
    
    def get_results(self) -> tuple:
        """Get the results.
        
        Returns:
            (success: bool, rolled_tier: str) - rolled_tier is "" if failed
            Returns the actual tier name that was rolled, not a jump number
        """
        return (self.is_success, self.rolled_tier if self.is_success else "")
    
    def closeEvent(self, event):
        """Clean up timers and save geometry."""
        save_dialog_geometry(self, "MergeLotteryDialog")
        if hasattr(self, '_tier_anim_timer'):
            self._tier_anim_timer.stop()
        if hasattr(self, '_success_anim_timer'):
            self._success_anim_timer.stop()
        super().closeEvent(event)


class WaterTierSliderWidget(QtWidgets.QWidget):
    """5-zone tier slider for water lottery with moving window visualization.
    
    Shows the 5 rarity tiers with widths based on glass-dependent weights.
    The center tier increases with each glass (1st=Common-centered → 5th=Legendary-centered).
    """
    
    TIER_COLORS = {
        "Common": "#9e9e9e",
        "Uncommon": "#4caf50", 
        "Rare": "#2196f3",
        "Epic": "#9c27b0",
        "Legendary": "#ff9800"
    }
    TIERS = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
    
    def __init__(self, glass_number: int, parent=None):
        super().__init__(parent)
        self.glass_number = glass_number
        self.position = 0.0
        self.zone_widths = self._calculate_zone_widths()
        self.setMinimumSize(400, 60)
    
    # Moving window: [5, 15, 60, 15, 5] centered on glass tier (same as merge)
    BASE_WINDOW = [5, 15, 60, 15, 5]
    
    def _calculate_zone_widths(self) -> list:
        """Calculate zone widths based on glass number.
        
        Moving window [5, 15, 60, 15, 5] centered on glass_number-1.
        Same distribution as merge lottery for consistency.
        """
        center_tier = min(self.glass_number - 1, 4)  # 0-4
        
        # Moving window centered on center_tier
        weights = [0, 0, 0, 0, 0]  # Common, Uncommon, Rare, Epic, Legendary
        
        for offset, pct in zip([-2, -1, 0, 1, 2], self.BASE_WINDOW):
            target_tier = center_tier + offset
            clamped_tier = max(0, min(4, target_tier))
            weights[clamped_tier] += pct
        
        return weights
    
    def set_position(self, pos: float):
        """Set marker position (0-100)."""
        self.position = max(0.0, min(100.0, pos))
        self.update()
    
    def get_tier_at_position(self, pos: float) -> str:
        """Get tier name at a given position (0-100)."""
        total = sum(self.zone_widths)
        if total <= 0:
            return "Rare"  # Safe fallback
        cumulative = 0.0
        for tier, width in zip(self.TIERS, self.zone_widths):
            if width <= 0:
                continue
            if pos < cumulative + width:
                return tier
            cumulative += width
        return "Legendary"
    
    def get_position_in_tier(self, tier: str) -> float:
        """Get center position for a tier zone."""
        cumulative = 0.0
        for t, width in zip(self.TIERS, self.zone_widths):
            if t == tier:
                return cumulative + width / 2
            cumulative += width
        return 95.0
    
    def paintEvent(self, event):
        _PaintCache.initialize()  # Ensure cache is ready
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Bar dimensions
        bar_y = 20
        bar_height = 30
        bar_width = self.width() - 20
        x_offset = 10
        
        # Draw tier zones (use cached colors)
        cumulative_x = x_offset
        for tier, width in zip(self.TIERS, self.zone_widths):
            if width <= 0:
                continue
            zone_width = (width / 100) * bar_width
            color = _PaintCache.get_tier_color(tier)
            painter.fillRect(
                int(cumulative_x), bar_y,
                int(zone_width), bar_height,
                color
            )
            # Zone label (only if wide enough)
            if zone_width > 35:
                painter.setPen(_PaintCache.COLOR_WHITE)
                painter.setFont(_PaintCache.FONT_LABEL_SMALL)
                painter.drawText(
                    int(cumulative_x), bar_y,
                    int(zone_width), bar_height,
                    QtCore.Qt.AlignCenter, tier[:3]
                )
            cumulative_x += zone_width
        
        # Draw border
        painter.setPen(_PaintCache.PEN_BORDER)
        painter.drawRect(x_offset, bar_y, bar_width, bar_height)
        
        # Draw marker
        marker_x = x_offset + (self.position / 100) * bar_width
        current_tier = self.get_tier_at_position(self.position)
        marker_color = _PaintCache.get_tier_color(current_tier)
        
        # Marker triangle
        painter.setBrush(marker_color)
        painter.setPen(_PaintCache.PEN_BLACK_OUTLINE)
        triangle = [
            QtCore.QPointF(marker_x, bar_y - 5),
            QtCore.QPointF(marker_x - 6, bar_y - 15),
            QtCore.QPointF(marker_x + 6, bar_y - 15)
        ]
        painter.drawPolygon(triangle)
        
        # Marker line
        painter.setPen(QtGui.QPen(marker_color, 3))
        painter.drawLine(int(marker_x), bar_y, int(marker_x), bar_y + bar_height)


class WaterWinSliderWidget(QtWidgets.QWidget):
    """Win/Lose slider for water lottery with progressive win chance.
    
    Shows Win zone (green) and Lose zone (red) based on current win chance.
    Win chance starts at 1% and increases +1% per accumulated roll.
    """
    
    def __init__(self, win_chance: float, parent=None):
        super().__init__(parent)
        self.win_chance = win_chance  # 0.0-1.0
        self.position = 0.0
        self.result_won = None  # For visual feedback
        self.setMinimumSize(400, 60)
    
    def set_position(self, pos: float):
        """Set marker position (0-100)."""
        self.position = max(0.0, min(100.0, pos))
        self.update()
    
    def set_result(self, won: bool):
        """Set the result for visual feedback."""
        self.result_won = won
        self.update()
    
    def paintEvent(self, event):
        _PaintCache.initialize()  # Ensure cache is ready
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        bar_y = 20
        bar_height = 30
        bar_width = self.width() - 20
        x_offset = 10
        
        win_pct = self.win_chance * 100
        lose_pct = 100 - win_pct
        
        # Win zone (green, left side)
        win_width = (win_pct / 100) * bar_width
        win_color = _PaintCache.COLOR_SUCCESS
        painter.fillRect(x_offset, bar_y, int(win_width), bar_height, win_color)
        
        # Lose zone (red, right side)
        lose_width = (lose_pct / 100) * bar_width
        lose_color = _PaintCache.COLOR_FAIL
        painter.fillRect(int(x_offset + win_width), bar_y, int(lose_width), bar_height, lose_color)
        
        # Labels
        painter.setPen(_PaintCache.COLOR_WHITE)
        painter.setFont(_PaintCache.FONT_LABEL_MEDIUM)
        if win_width > 30:
            painter.drawText(x_offset, bar_y, int(win_width), bar_height,
                           QtCore.Qt.AlignCenter, f"WIN {win_pct:.0f}%")
        if lose_width > 40:
            painter.drawText(int(x_offset + win_width), bar_y, int(lose_width), bar_height,
                           QtCore.Qt.AlignCenter, f"LOSE {lose_pct:.0f}%")
        
        # Border
        painter.setPen(_PaintCache.PEN_BORDER)
        painter.drawRect(x_offset, bar_y, bar_width, bar_height)
        
        # Marker
        marker_x = x_offset + (self.position / 100) * bar_width
        in_win_zone = self.position < win_pct
        marker_color = _PaintCache.COLOR_SUCCESS if in_win_zone else _PaintCache.COLOR_FAIL
        
        # Marker triangle
        painter.setBrush(marker_color)
        painter.setPen(_PaintCache.PEN_BLACK_OUTLINE)
        triangle = [
            QtCore.QPointF(marker_x, bar_y - 5),
            QtCore.QPointF(marker_x - 6, bar_y - 15),
            QtCore.QPointF(marker_x + 6, bar_y - 15)
        ]
        painter.drawPolygon(triangle)
        
        # Marker line
        painter.setPen(QtGui.QPen(marker_color, 3))
        painter.drawLine(int(marker_x), bar_y, int(marker_x), bar_y + bar_height)


class WaterLotteryDialog(QtWidgets.QDialog):
    """Two-stage lottery for Water/Hydration tracking.
    
    Stage 1: Tier Roll (rarity based on glass number - moving window)
        Uses [5, 15, 60, 15, 5] distribution centered on glass tier:
        - Glass 1: Common-centered, 99% success rate
        - Glass 2: Uncommon-centered, 80% success rate
        - Glass 3: Rare-centered, 60% success rate
        - Glass 4: Epic-centered, 40% success rate
        - Glass 5: Legendary-centered, 20% success rate
    
    Stage 2: Win/Lose Roll (decreasing success rate)
        - Glass 1: 99% success rate
        - Glass 2: 80% success rate
        - Glass 3: 60% success rate
        - Glass 4: 40% success rate
        - Glass 5: 20% success rate
    
    Order: Roll tier FIRST (what you're playing for), then roll win/lose.
    
    Same moving window distribution as merge lottery for consistency.
    """
    
    # Signal emits (won: bool, rarity: str, item: dict or None, new_attempts: int)
    finished_signal = QtCore.Signal(bool, str, object, int)
    
    def __init__(self, glass_number: int, lottery_attempts: int,
                 story_id: str = None, parent: Optional[QtWidgets.QWidget] = None):
        """
        Args:
            glass_number: Which glass this is today (1-5)
            lottery_attempts: Not used anymore (kept for backwards compatibility)
            story_id: Story theme for item generation
            parent: Parent widget
        """
        super().__init__(parent)
        self.glass_number = glass_number
        self.lottery_attempts = lottery_attempts
        self.story_id = story_id
        
        # Success rate decreases with each glass: 99%, 80%, 60%, 40%, 20%
        success_rates = [0.99, 0.80, 0.60, 0.40, 0.20]
        self.success_rate = success_rates[min(glass_number - 1, len(success_rates) - 1)]
        
        # Pre-roll tier result
        self.tier_roll = random.random() * 100
        self.rolled_tier = self._determine_tier(self.tier_roll)
        
        # Pre-roll win/lose result  
        self.win_roll = random.random()
        self.won = self.win_roll < self.success_rate
        
        # Generate item if won
        self.won_item = None
        if self.won:
            try:
                from gamification import generate_item
                self.won_item = generate_item(rarity=self.rolled_tier, story_id=story_id)
            except (ImportError, Exception):
                # Fallback if gamification unavailable
                self.won_item = {"name": f"{self.rolled_tier} Item", "rarity": self.rolled_tier, "power": 10}
        
        # No longer using attempt counter - kept for compatibility
        self.new_attempts = 0
        
        self.current_stage = 0
        self._setup_ui()
        QtCore.QTimer.singleShot(300, self._start_stage_1)
    
    # Moving window: [5, 15, 60, 15, 5] centered on glass tier (same as merge)
    BASE_WINDOW = [5, 15, 60, 15, 5]
    TIERS = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
    
    def _determine_tier(self, roll: float) -> str:
        """Determine tier from roll (0-100) based on glass number.
        
        Uses moving window [5, 15, 60, 15, 5] centered on glass tier,
        same distribution as merge lottery for consistency.
        """
        center_tier = min(self.glass_number - 1, 4)
        
        # Moving window centered on center_tier
        weights = [0, 0, 0, 0, 0]
        
        for offset, pct in zip([-2, -1, 0, 1, 2], self.BASE_WINDOW):
            target_tier = center_tier + offset
            clamped_tier = max(0, min(4, target_tier))
            weights[clamped_tier] += pct
        
        cumulative = 0.0
        for tier, weight in zip(self.TIERS, weights):
            if roll < cumulative + weight:
                return tier
            cumulative += weight
        return "Legendary"
    
    def _setup_ui(self):
        """Build the two-stage water lottery UI."""
        self.setWindowTitle("💧 Water Lottery!")
        self.setModal(True)
        self.setMinimumSize(440, 360)
        load_dialog_geometry(self, "WaterLotteryDialog", QtCore.QSize(540, 440))
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)  # Small margin for shadow
        
        # Main container
        container = QtWidgets.QWidget()
        container.setStyleSheet("""
            QWidget {
                background: #1a1a2e;
                border: none;
                border-radius: 12px;
            }
        """)
        # Apply drop shadow to container for depth without borders
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QtGui.QColor(0, 0, 0, 120))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)
        
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setSpacing(12)
        container_layout.setContentsMargins(24, 18, 24, 18)
        
        # Header
        header = QtWidgets.QLabel(f"💧 Glass #{self.glass_number} Lottery")
        header.setFont(QtGui.QFont("Arial", 16, QtGui.QFont.Bold))
        header.setAlignment(QtCore.Qt.AlignCenter)
        container_layout.addWidget(header)
        
        # Success rate info
        success_info = QtWidgets.QLabel(f"🎲 Success rate: {self.success_rate*100:.0f}%")
        success_info.setFont(QtGui.QFont("Arial", 10))
        success_info.setAlignment(QtCore.Qt.AlignCenter)
        success_info.setStyleSheet("color: #888;")
        # Add tooltip explaining success rate calculation
        success_info.setToolTip(
            f"💧 Water Lottery Success Rate\n"
            f"──────────────────\n"
            f"Glass #{self.glass_number}: {self.success_rate*100:.0f}%\n\n"
            f"Higher glasses = better odds!\n"
            f"Glass 1: ~50% | Glass 8: ~85%"
        )
        container_layout.addWidget(success_info)
        
        # Stage 1: Tier Roll
        self.stage1_frame = QtWidgets.QFrame()
        self.stage1_frame.setStyleSheet("""
            QFrame { background: #252540; border: none; border-radius: 8px; }
        """)
        # Add subtle shadow for card effect
        shadow1 = QtWidgets.QGraphicsDropShadowEffect()
        shadow1.setBlurRadius(10)
        shadow1.setColor(QtGui.QColor(0, 0, 0, 80))
        shadow1.setOffset(0, 2)
        self.stage1_frame.setGraphicsEffect(shadow1)
        self.stage1_frame.setMinimumHeight(100)  # Prevent collapse
        stage1_layout = QtWidgets.QVBoxLayout(self.stage1_frame)
        stage1_layout.setContentsMargins(14, 10, 14, 10)
        
        self.stage1_title = QtWidgets.QLabel(f"✨ Stage 1: What Tier? (Glass #{self.glass_number})")
        self.stage1_title.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        # Add tooltip explaining tier distribution
        center_tier = min(self.glass_number - 1, 4)
        tier_names = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
        self.stage1_title.setToolTip(
            f"🎲 Tier Distribution for Glass #{self.glass_number}\n"
            f"──────────────────────\n"
            f"Center tier: {tier_names[center_tier]}\n"
            f"Distribution: [5%, 15%, 60%, 15%, 5%]\n"
            f"centered on {tier_names[center_tier]}\n\n"
            f"Drink more glasses for higher tiers!"
        )
        stage1_layout.addWidget(self.stage1_title)
        
        self.tier_slider = WaterTierSliderWidget(self.glass_number)
        stage1_layout.addWidget(self.tier_slider)
        
        self.stage1_result = QtWidgets.QLabel("Rolling...")
        self.stage1_result.setFont(QtGui.QFont("Arial", 10))
        stage1_layout.addWidget(self.stage1_result)
        
        container_layout.addWidget(self.stage1_frame)
        
        # Stage 2: Win/Lose Roll (initially dimmed)
        self.stage2_frame = QtWidgets.QFrame()
        self.stage2_frame.setStyleSheet("""
            QFrame { background: #252540; border: none; border-radius: 8px; }
        """)
        # Add subtle shadow for card effect
        shadow2 = QtWidgets.QGraphicsDropShadowEffect()
        shadow2.setBlurRadius(10)
        shadow2.setColor(QtGui.QColor(0, 0, 0, 80))
        shadow2.setOffset(0, 2)
        self.stage2_frame.setGraphicsEffect(shadow2)
        self.stage2_frame.setMinimumHeight(100)  # Prevent collapse
        self.stage2_frame.setEnabled(False)
        stage2_layout = QtWidgets.QVBoxLayout(self.stage2_frame)
        stage2_layout.setContentsMargins(14, 10, 14, 10)
        
        self.stage2_title = QtWidgets.QLabel(f"🎲 Stage 2: Win or Lose? ({self.success_rate*100:.0f}% chance)")
        self.stage2_title.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        stage2_layout.addWidget(self.stage2_title)
        
        self.win_slider = WaterWinSliderWidget(self.success_rate)
        stage2_layout.addWidget(self.win_slider)
        
        self.stage2_result = QtWidgets.QLabel("Waiting...")
        self.stage2_result.setFont(QtGui.QFont("Arial", 10))
        stage2_layout.addWidget(self.stage2_result)
        
        container_layout.addWidget(self.stage2_frame)
        
        # Final result area
        self.final_result = QtWidgets.QLabel("")
        self.final_result.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
        self.final_result.setAlignment(QtCore.Qt.AlignCenter)
        self.final_result.setMinimumHeight(40)  # Reserve space
        self.final_result.hide()
        container_layout.addWidget(self.final_result)
        
        # Stretch to absorb space changes
        container_layout.addStretch(1)
        
        # Sound toggle
        sound_row = QtWidgets.QHBoxLayout()
        sound_row.addStretch()
        self.sound_toggle = QtWidgets.QCheckBox("🔊 Sound")
        self.sound_toggle.setChecked(get_lottery_sound_enabled())
        self.sound_toggle.setStyleSheet("color: #666; font-size: 11px;")
        self.sound_toggle.toggled.connect(set_lottery_sound_enabled)
        sound_row.addWidget(self.sound_toggle)
        container_layout.addLayout(sound_row)
        
        # Continue button (hidden until animation complete)
        self.continue_btn = QtWidgets.QPushButton("Continue")
        self.continue_btn.setStyleSheet("""
            QPushButton {
                background: #4caf50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #66bb6a;
            }
        """)
        self.continue_btn.clicked.connect(self._finish)
        self.continue_btn.hide()
        container_layout.addWidget(self.continue_btn, alignment=QtCore.Qt.AlignCenter)
        
        layout.addWidget(container)
    
    def _start_stage_1(self):
        """Start tier roll animation using bounce path (same as merge dialog)."""
        self.current_stage = 1
        # Highlight active stage with brighter background
        self.stage1_frame.setStyleSheet("QFrame { background: #303050; border: none; border-radius: 8px; }")
        
        # Generate bounce path (same as merge dialog)
        self._stage1_path_points = [50.0]
        going_up = random.choice([True, False])
        num_bounces = random.randint(4, 6)
        
        for _ in range(num_bounces):
            if going_up:
                self._stage1_path_points.extend([100.0, 0.0])
            else:
                self._stage1_path_points.extend([0.0, 100.0])
        self._stage1_path_points.append(self.tier_roll)
        
        # Pre-compute segments for smoother animation
        self._stage1_segments = []
        self._stage1_total_dist = 0.0
        for i in range(len(self._stage1_path_points) - 1):
            start, end = self._stage1_path_points[i], self._stage1_path_points[i+1]
            dist = abs(end - start)
            if dist > 0.001:
                self._stage1_segments.append({
                    "start": start, "end": end, "dist": dist,
                    "cum_start": self._stage1_total_dist,
                    "cum_end": self._stage1_total_dist + dist
                })
                self._stage1_total_dist += dist
        
        self._stage1_elapsed = 0.0
        self._stage1_duration = 5.0
        
        # Style state tracking for performance
        self._stage1_last_tier = None
        
        self._stage1_timer = QtCore.QTimer(self)
        self._stage1_timer.timeout.connect(self._animate_stage1_tick)
        self._stage1_timer.start(16)  # 60 FPS for smooth performance
    
    def _animate_stage1_tick(self):
        """Tier roll animation tick."""
        # Cached tier colors for performance
        TIER_COLORS = {
            "Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3",
            "Epic": "#9c27b0", "Legendary": "#ff9800"
        }
        
        self._stage1_elapsed += 0.016  # Match timer interval
        t = min(1.0, self._stage1_elapsed / self._stage1_duration)
        eased = 1.0 - (1.0 - t) ** 4  # EaseOutQuart
        
        current_travel = eased * self._stage1_total_dist
        pos = self.tier_roll
        
        for seg in self._stage1_segments:
            if seg["cum_start"] <= current_travel <= seg["cum_end"]:
                local = (current_travel - seg["cum_start"]) / seg["dist"]
                pos = seg["start"] + (seg["end"] - seg["start"]) * local
                break
        
        pos = max(0, min(100, pos))
        self.tier_slider.set_position(pos)
        
        # Show current tier during animation - only update style if tier changed
        tier = self.tier_slider.get_tier_at_position(pos)
        if tier != self._stage1_last_tier:
            self._stage1_last_tier = tier
            color = TIER_COLORS.get(tier, "#fff")
            self.stage1_result.setStyleSheet(f"color: {color}; font-size: 14px;")
        self.stage1_result.setText(f"🎲 {pos:.1f}% → {tier}")
        
        if t >= 1.0:
            self._stage1_timer.stop()
            self.tier_slider.set_position(self.tier_roll)
            self._finish_stage_1()
    
    def _finish_stage_1(self):
        """Finish tier roll, show result and start stage 2."""
        tier_colors = {
            "Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3",
            "Epic": "#9c27b0", "Legendary": "#ff9800"
        }
        color = tier_colors.get(self.rolled_tier, "#fff")
        self.stage1_result.setText(f"<b style='color:{color};'>🎯 {self.rolled_tier.upper()}!</b>")
        self.stage1_result.setTextFormat(QtCore.Qt.RichText)
        
        # Mark stage1 as complete with success background
        self.stage1_frame.setStyleSheet("QFrame { background: #2a3a2a; border: none; border-radius: 8px; }")
        
        # Update stage 2 title
        self.stage2_title.setText(f"🎲 Stage 2: Claim your {self.rolled_tier}! ({self.success_rate*100:.0f}% chance)")
        
        # Enable and start stage 2
        QtCore.QTimer.singleShot(800, self._start_stage_2)
    
    def _start_stage_2(self):
        """Start win/lose roll animation using bounce path (same as merge dialog)."""
        self.current_stage = 2
        self.stage2_frame.setEnabled(True)
        # Highlight active stage with brighter background
        self.stage2_frame.setStyleSheet("QFrame { background: #303050; border: none; border-radius: 8px; }")
        
        # Generate bounce path (same as merge dialog)
        self._stage2_path_points = [50.0]
        going_up = random.choice([True, False])
        num_bounces = random.randint(4, 6)
        
        for _ in range(num_bounces):
            if going_up:
                self._stage2_path_points.extend([100.0, 0.0])
            else:
                self._stage2_path_points.extend([0.0, 100.0])
        # Convert 0-1 roll to 0-100 for slider position
        self._stage2_path_points.append(self.win_roll * 100)
        
        # Pre-compute segments for smoother animation
        self._stage2_segments = []
        self._stage2_total_dist = 0.0
        for i in range(len(self._stage2_path_points) - 1):
            start, end = self._stage2_path_points[i], self._stage2_path_points[i+1]
            dist = abs(end - start)
            if dist > 0.001:
                self._stage2_segments.append({
                    "start": start, "end": end, "dist": dist,
                    "cum_start": self._stage2_total_dist,
                    "cum_end": self._stage2_total_dist + dist
                })
                self._stage2_total_dist += dist
        
        self._stage2_elapsed = 0.0
        self._stage2_duration = 5.0
        
        # Style state tracking for performance
        self._stage2_last_zone = None
        
        self._stage2_timer = QtCore.QTimer(self)
        self._stage2_timer.timeout.connect(self._animate_stage2_tick)
        self._stage2_timer.start(16)  # 60 FPS for smooth performance
    
    def _animate_stage2_tick(self):
        """Win/lose animation tick."""
        self._stage2_elapsed += 0.016  # Match timer interval
        t = min(1.0, self._stage2_elapsed / self._stage2_duration)
        eased = 1.0 - (1.0 - t) ** 4  # EaseOutQuart
        
        current_travel = eased * self._stage2_total_dist
        pos = self.win_roll * 100  # Convert to 0-100 for display
        
        for seg in self._stage2_segments:
            if seg["cum_start"] <= current_travel <= seg["cum_end"]:
                local = (current_travel - seg["cum_start"]) / seg["dist"]
                pos = seg["start"] + (seg["end"] - seg["start"]) * local
                break
        
        pos = max(0, min(100, pos))
        self.win_slider.set_position(pos)
        
        # Show win/lose status during animation - only update style if zone changed
        success_pct = self.success_rate * 100
        is_in_win_zone = pos < success_pct
        if is_in_win_zone != self._stage2_last_zone:
            self._stage2_last_zone = is_in_win_zone
            if is_in_win_zone:
                self.stage2_result.setStyleSheet("color: #4caf50; font-size: 14px;")
            else:
                self.stage2_result.setStyleSheet("color: #f44336; font-size: 14px;")
        
        if is_in_win_zone:
            self.stage2_result.setText(f"🎲 {pos:.1f}% (WIN ZONE!)")
        else:
            self.stage2_result.setText(f"🎲 {pos:.1f}%")
        
        if t >= 1.0:
            self._stage2_timer.stop()
            self.win_slider.set_position(self.win_roll * 100)
            self._finish_stage_2()
    
    def _finish_stage_2(self):
        """Finish win/lose roll, show final result."""
        success_pct = self.success_rate * 100
        win_roll_pct = self.win_roll * 100
        
        if self.won:
            self.stage2_result.setText(f"<b style='color:#4caf50;'>✅ WIN! ({win_roll_pct:.1f}% < {success_pct:.0f}%)</b>")
            # Mark stage2 as success with green-tinted background
            self.stage2_frame.setStyleSheet("QFrame { background: #2a3a2a; border: none; border-radius: 8px; }")
            
            tier_colors = {
                "Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3",
                "Epic": "#9c27b0", "Legendary": "#ff9800"
            }
            color = tier_colors.get(self.rolled_tier, "#fff")
            
            if self.won_item:
                item_name = self.won_item.get("name", "Unknown Item")
                self.final_result.setText(f"<span style='color:{color};'>🎉 YOU WON: [{self.rolled_tier}] {item_name}!</span>")
            else:
                self.final_result.setText(f"<span style='color:{color};'>🎉 YOU WON: {self.rolled_tier}!</span>")
            
            self.final_result.setTextFormat(QtCore.Qt.RichText)
            self.final_result.setStyleSheet(f"color: {color};")
        else:
            self.stage2_result.setText(f"<b style='color:#f44336;'>❌ LOSE ({win_roll_pct:.1f}% ≥ {success_pct:.0f}%)</b>")
            # Mark stage2 as failed with red-tinted background
            self.stage2_frame.setStyleSheet("QFrame { background: #3a2a2a; border: none; border-radius: 8px; }")
            
            # Show decreasing success rate message
            if self.glass_number < 5:
                next_glass_rates = [99, 80, 60, 40, 20]
                next_rate = next_glass_rates[self.glass_number]  # Next glass rate
                self.final_result.setText(f"💔 Not this time... Next glass: {next_rate}% success rate!")
            else:
                self.final_result.setText(f"💔 Not this time... Try again tomorrow!")
            self.final_result.setStyleSheet("color: #f44336;")
        
        self.stage2_result.setTextFormat(QtCore.Qt.RichText)
        self.final_result.show()
        
        # Play lottery result sound
        _play_lottery_result_sound(self.won)
        
        # Show continue button for user to close when ready
        self.continue_btn.show()
    
    def _finish(self):
        """Emit result and close."""
        self.finished_signal.emit(self.won, self.rolled_tier, self.won_item, self.new_attempts)
        self.accept()
    
    def get_results(self) -> tuple:
        """Get the results.
        
        Returns:
            (won: bool, tier: str, item: dict or None, new_attempts: int)
        """
        return (self.won, self.rolled_tier, self.won_item, self.new_attempts)
    
    def closeEvent(self, event):
        """Clean up timers and save geometry."""
        # Stop timers first to prevent any callbacks during cleanup
        if hasattr(self, '_stage1_timer') and self._stage1_timer:
            self._stage1_timer.stop()
        if hasattr(self, '_stage2_timer') and self._stage2_timer:
            self._stage2_timer.stop()
        save_dialog_geometry(self, "WaterLotteryDialog")
        super().closeEvent(event)


class FocusTimerTierSliderWidget(QtWidgets.QWidget):
    """5-zone tier slider for Focus Timer rewards showing rarity distribution.
    
    Based on session length, shows the probability zones for each tier.
    """
    
    TIER_COLORS = {
        "Common": "#9e9e9e",
        "Uncommon": "#4caf50", 
        "Rare": "#2196f3",
        "Epic": "#9c27b0",
        "Legendary": "#ff9800"
    }
    TIERS = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
    
    def __init__(self, session_minutes: int, streak_days: int = 0, parent=None):
        super().__init__(parent)
        self.session_minutes = session_minutes
        self.streak_days = streak_days
        self.zone_widths = self._calculate_zone_widths()
        self.position = 50.0
        self.result_tier = None
        self.setMinimumSize(400, 70)
    
    def _calculate_zone_widths(self) -> list:
        """Calculate zone widths based on session duration (matches gamification.py)."""
        # Session length to center tier mapping
        # <30min: -1 (base weights), 30min: 0, 1hr: 1, 2hr: 2, 3hr: 3, 4hr+: 4
        session_hours = self.session_minutes / 60.0
        
        if self.session_minutes < 30:
            center_tier = -1  # No bonus
        elif session_hours < 1:
            center_tier = 0  # Common-centered
        elif session_hours < 2:
            center_tier = 1  # Uncommon-centered
        elif session_hours < 3:
            center_tier = 2  # Rare-centered
        elif session_hours < 4:
            center_tier = 3  # Epic-centered
        else:
            center_tier = 4  # Legendary-centered
        
        # Streak bonus (each 7 days adds +1 tier)
        streak_bonus = self.streak_days // 7
        effective_center = center_tier + streak_bonus
        
        if center_tier >= 0:
            # Moving window: [5%, 15%, 60%, 15%, 5%] centered on tier (same as merge/water)
            window = [5, 15, 60, 15, 5]
            weights = [0, 0, 0, 0, 0]
            
            for offset, pct in zip([-2, -1, 0, 1, 2], window):
                target_tier = effective_center + offset
                clamped_tier = max(0, min(4, target_tier))
                weights[clamped_tier] += pct
            
            return weights
        else:
            # Base distribution (<30min)
            return [50, 30, 15, 4, 1]  # Common-heavy
    
    def set_position(self, pos: float):
        """Set marker position (0-100)."""
        self.position = max(0.0, min(100.0, pos))
        self.update()
    
    def set_result(self, tier: str):
        """Set the result tier for visual feedback."""
        self.result_tier = tier
        self.update()
    
    def get_tier_at_position(self, pos: float) -> str:
        """Get tier name at a given position (0-100)."""
        total = sum(self.zone_widths)
        if total <= 0:
            return "Common"  # Safe fallback for focus timer
        cumulative = 0.0
        for tier, width in zip(self.TIERS, self.zone_widths):
            if width <= 0:
                continue
            if pos < cumulative + width:
                return tier
            cumulative += width
        return "Legendary"
    
    def get_position_for_tier(self, tier: str) -> float:
        """Get a random position within the tier zone."""
        cumulative = 0.0
        for t, width in zip(self.TIERS, self.zone_widths):
            if t == tier:
                # Return center of the zone
                return cumulative + width / 2
            cumulative += width
        return 95.0
    
    def paintEvent(self, event):
        _PaintCache.initialize()  # Ensure cache is ready
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        bar_y = 20
        bar_height = 35
        bar_width = w - 20
        x_offset = 10
        
        # Draw tier zones (use cached colors)
        cumulative_x = x_offset
        for tier, width in zip(self.TIERS, self.zone_widths):
            if width <= 0:
                continue
            zone_width = (width / 100) * bar_width
            color = _PaintCache.get_tier_color(tier)
            
            # Highlight winning tier
            if self.result_tier and tier == self.result_tier:
                painter.setOpacity(1.0)
            else:
                painter.setOpacity(0.7 if self.result_tier else 1.0)
            
            painter.fillRect(
                int(cumulative_x), bar_y,
                int(zone_width), bar_height,
                color
            )
            
            # Zone label with tier name and percentage
            if zone_width > 45:
                painter.setOpacity(1.0)
                painter.setPen(_PaintCache.COLOR_WHITE)
                painter.setFont(_PaintCache.FONT_LABEL_MEDIUM)
                label = f"{tier[:3]}:{width:.0f}%"
                painter.drawText(
                    int(cumulative_x), bar_y,
                    int(zone_width), bar_height,
                    QtCore.Qt.AlignCenter, label
                )
            elif zone_width > 30:
                painter.setOpacity(1.0)
                painter.setPen(_PaintCache.COLOR_WHITE)
                painter.setFont(_PaintCache.FONT_LABEL_MEDIUM)
                label = f"{tier[:3]}"
                painter.drawText(
                    int(cumulative_x), bar_y,
                    int(zone_width), bar_height,
                    QtCore.Qt.AlignCenter, label
                )
            cumulative_x += zone_width
        
        painter.setOpacity(1.0)
        
        # Draw border
        painter.setPen(_PaintCache.PEN_BORDER)
        painter.drawRect(x_offset, bar_y, bar_width, bar_height)
        
        # Draw marker
        marker_x = x_offset + (self.position / 100) * bar_width
        current_tier = self.get_tier_at_position(self.position)
        marker_color = _PaintCache.get_tier_color(current_tier)
        
        # Glow effect for result
        if self.result_tier:
            glow_color = _PaintCache.get_tier_color(self.result_tier)
            for i in range(3):
                glow_size = 10 + (3-i) * 3
                painter.setBrush(glow_color)
                painter.setOpacity(0.3)
                painter.drawEllipse(
                    QtCore.QPointF(marker_x, bar_y + bar_height // 2),
                    glow_size, glow_size
                )
            painter.setOpacity(1.0)
        
        # Marker triangle
        painter.setBrush(marker_color)
        painter.setPen(_PaintCache.PEN_MARKER_OUTLINE)
        triangle = [
            QtCore.QPointF(marker_x, bar_y - 3),
            QtCore.QPointF(marker_x - 8, bar_y - 15),
            QtCore.QPointF(marker_x + 8, bar_y - 15)
        ]
        painter.drawPolygon(triangle)
        
        # Marker line
        painter.setPen(QtGui.QPen(marker_color, 3))
        painter.drawLine(int(marker_x), bar_y, int(marker_x), bar_y + bar_height)


class FocusTimerLotteryDialog(QtWidgets.QDialog):
    """Lottery animation for Focus Timer rewards - 100% guaranteed item drop.
    
    Shows exciting tier roll animation for session rewards.
    The item is always awarded, this just shows WHAT tier they get.
    """
    
    finished_signal = QtCore.Signal(str, dict)  # (tier, item)
    
    def __init__(self, session_minutes: int, streak_days: int, 
                 item: dict, parent=None):
        """
        Args:
            session_minutes: Session duration in minutes
            streak_days: Current streak for bonus calculation
            item: Pre-generated item to reveal
        """
        super().__init__(parent)
        self.session_minutes = session_minutes
        self.streak_days = streak_days
        self.item = item
        self.rolled_tier = item.get("rarity", "Common")
        
        # Calculate target position in the slider
        self._setup_ui()
        
        # Calculate roll position based on tier
        self.tier_roll = self._calculate_roll_for_tier(self.rolled_tier)
        
        QtCore.QTimer.singleShot(300, self._start_animation)
    
    def _calculate_roll_for_tier(self, tier: str) -> float:
        """Calculate roll position for the given tier."""
        return self.tier_slider.get_position_for_tier(tier)
    
    def _setup_ui(self):
        """Build the lottery UI."""
        session_hours = self.session_minutes / 60.0
        if session_hours >= 1:
            title = f"🎁 {self.session_minutes // 60}hr Session Reward!"
        else:
            title = f"🎁 {self.session_minutes}min Session Reward!"
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(450, 380)
        load_dialog_geometry(self, "FocusTimerLotteryDialog", QtCore.QSize(520, 420))
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)  # Small margin for shadow
        
        container = QtWidgets.QWidget()
        container.setStyleSheet("""
            QWidget {
                background: #1a1a2e;
                border: none;
                border-radius: 12px;
            }
        """)
        # Apply drop shadow to container for depth without borders
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QtGui.QColor(0, 0, 0, 120))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)
        
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setSpacing(12)
        container_layout.setContentsMargins(24, 18, 24, 18)

        # Header
        header = QtWidgets.QLabel("🎁 Session Reward! 🎁")
        header.setAlignment(QtCore.Qt.AlignCenter)
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #9ca3af;")
        container_layout.addWidget(header)
        
        # Session info
        streak_text = f" • 🔥 {self.streak_days} day streak" if self.streak_days > 0 else ""
        info = QtWidgets.QLabel(f"⏱️ {self.session_minutes} min session{streak_text}")
        info.setAlignment(QtCore.Qt.AlignCenter)
        info.setStyleSheet("color: #aaa; font-size: 12px;")
        container_layout.addWidget(info)
        
        # Tier lottery frame
        lottery_frame = QtWidgets.QFrame()
        lottery_frame.setStyleSheet("""
            QFrame { background: #252540; border: none; border-radius: 8px; }
        """)
        # Add subtle shadow for card effect
        lottery_shadow = QtWidgets.QGraphicsDropShadowEffect()
        lottery_shadow.setBlurRadius(10)
        lottery_shadow.setColor(QtGui.QColor(0, 0, 0, 80))
        lottery_shadow.setOffset(0, 2)
        lottery_frame.setGraphicsEffect(lottery_shadow)
        
        lottery_layout = QtWidgets.QVBoxLayout(lottery_frame)
        lottery_layout.setContentsMargins(14, 12, 14, 12)
        
        lottery_title = QtWidgets.QLabel("✨ Rolling for Item Tier...")
        lottery_title.setStyleSheet("color: #ff9800; font-size: 14px; font-weight: bold;")
        lottery_layout.addWidget(lottery_title)
        
        # Tier slider
        self.tier_slider = FocusTimerTierSliderWidget(self.session_minutes, self.streak_days)
        self.tier_slider.setFixedHeight(70)
        lottery_layout.addWidget(self.tier_slider)
        
        # Result label (percentages shown in bar zones)
        self.lottery_result = QtWidgets.QLabel("🎲 Rolling...")
        self.lottery_result.setAlignment(QtCore.Qt.AlignCenter)
        self.lottery_result.setStyleSheet("color: #aaa; font-size: 14px;")
        lottery_layout.addWidget(self.lottery_result)
        
        container_layout.addWidget(lottery_frame)
        
        # Item reveal area (hidden until animation complete)
        self.item_frame = QtWidgets.QFrame()
        self.item_frame.setStyleSheet("""
            QFrame { background: #252540; border: none; border-radius: 8px; }
        """)
        self.item_frame.setMinimumHeight(60)  # Reserve space
        self.item_frame.hide()
        item_layout = QtWidgets.QVBoxLayout(self.item_frame)
        item_layout.setContentsMargins(14, 12, 14, 12)
        
        self.item_label = QtWidgets.QLabel("")
        self.item_label.setAlignment(QtCore.Qt.AlignCenter)
        self.item_label.setWordWrap(True)
        self.item_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        item_layout.addWidget(self.item_label)
        
        container_layout.addWidget(self.item_frame)
        
        # Stretch to absorb space changes
        container_layout.addStretch(1)
        
        # Sound toggle
        sound_row = QtWidgets.QHBoxLayout()
        sound_row.addStretch()
        self.sound_toggle = QtWidgets.QCheckBox("🔊 Sound")
        self.sound_toggle.setChecked(get_lottery_sound_enabled())
        self.sound_toggle.setStyleSheet("color: #666; font-size: 11px;")
        self.sound_toggle.toggled.connect(set_lottery_sound_enabled)
        sound_row.addWidget(self.sound_toggle)
        container_layout.addLayout(sound_row)
        
        # Continue button (hidden until animation complete)
        self.continue_btn = QtWidgets.QPushButton("Continue")
        self.continue_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 10px 30px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.continue_btn.clicked.connect(self._finish)
        self.continue_btn.hide()
        container_layout.addWidget(self.continue_btn, alignment=QtCore.Qt.AlignCenter)
        
        layout.addWidget(container)
    
    def _start_animation(self):
        """Start tier roll animation using bounce path (same as merge dialog)."""
        # Generate bounce path (same as merge dialog)
        self._path_points = [50.0]
        going_up = random.choice([True, False])
        num_bounces = random.randint(4, 6)
        
        for _ in range(num_bounces):
            if going_up:
                self._path_points.extend([100.0, 0.0])
            else:
                self._path_points.extend([0.0, 100.0])
        self._path_points.append(self.tier_roll)
        
        # Pre-compute segments for smoother animation
        self._segments = []
        self._total_dist = 0.0
        for i in range(len(self._path_points) - 1):
            start, end = self._path_points[i], self._path_points[i+1]
            dist = abs(end - start)
            if dist > 0.001:
                self._segments.append({
                    "start": start, "end": end, "dist": dist,
                    "cum_start": self._total_dist,
                    "cum_end": self._total_dist + dist
                })
                self._total_dist += dist
        
        self._anim_elapsed = 0.0
        self._anim_duration = 4.0
        
        # Style state tracking for performance
        self._anim_last_tier = None
        
        self._anim_timer = QtCore.QTimer(self)
        self._anim_timer.timeout.connect(self._animate_step)
        self._anim_timer.start(16)  # 60 FPS for smooth performance
    
    def _animate_step(self):
        """Animation frame using bounce path."""
        # Cached tier colors for performance
        TIER_COLORS = {
            "Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3",
            "Epic": "#9c27b0", "Legendary": "#ff9800"
        }
        
        self._anim_elapsed += 0.016  # Match timer interval
        t = min(1.0, self._anim_elapsed / self._anim_duration)
        eased = 1.0 - (1.0 - t) ** 4  # EaseOutQuart
        
        current_travel = eased * self._total_dist
        pos = self.tier_roll
        
        for seg in self._segments:
            if seg["cum_start"] <= current_travel <= seg["cum_end"]:
                local = (current_travel - seg["cum_start"]) / seg["dist"]
                pos = seg["start"] + (seg["end"] - seg["start"]) * local
                break
        
        pos = max(0, min(100, pos))
        self.tier_slider.set_position(pos)
        
        # Update rolling text - only update style if tier changed
        current_tier = self.tier_slider.get_tier_at_position(pos)
        if current_tier != self._anim_last_tier:
            self._anim_last_tier = current_tier
            color = TIER_COLORS.get(current_tier, "#fff")
            self.lottery_result.setStyleSheet(f"color: {color}; font-size: 14px;")
        self.lottery_result.setText(f"🎲 {pos:.1f}% → {current_tier}")
        
        if t >= 1.0:
            self._anim_timer.stop()
            self.tier_slider.set_position(self.tier_roll)
            self._show_result()
    
    def _show_result(self):
        """Show the won item."""
        tier = self.rolled_tier
        tier_colors = {
            "Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3",
            "Epic": "#9c27b0", "Legendary": "#ff9800"
        }
        color = tier_colors.get(tier, "#fff")
        
        # Update slider with result
        self.tier_slider.set_result(tier)
        
        # Show tier result
        self.lottery_result.setText(f"<b style='color:{color};'>🎯 {tier.upper()}!</b>")
        self.lottery_result.setTextFormat(QtCore.Qt.RichText)
        
        # Reveal item
        self.item_frame.show()
        self.item_frame.setStyleSheet(f"QFrame {{ background: #252540; border: 2px solid {color}; border-radius: 8px; }}")
        
        item_name = self.item.get("name", "Unknown Item")
        slot = self.item.get("slot", "unknown")
        power = self.item.get("power", 0)
        
        # Check for lucky options
        lucky_opts = self.item.get("lucky_options", {})
        lucky_text = ""
        if lucky_opts:
            opts = []
            if lucky_opts.get("xp_bonus"):
                opts.append(f"+{lucky_opts['xp_bonus']}% XP")
            if lucky_opts.get("coin_discount"):
                opts.append(f"+{lucky_opts['coin_discount']}% Coin Discount")
            if lucky_opts.get("merge_luck"):
                opts.append(f"+{lucky_opts['merge_luck']}% Merge Luck")
            if opts:
                lucky_text = f"<br><span style='color:#ffd700;'>⭐ {', '.join(opts)}</span>"
        
        self.item_label.setText(
            f"<span style='color:{color};'>[{tier}] {item_name}</span><br>"
            f"<span style='color:#888;'>📍 {slot.title()} • ⚔️ +{power} Power</span>"
            f"{lucky_text}"
        )
        self.item_label.setTextFormat(QtCore.Qt.RichText)
        
        # Play win sound (FocusTimer always wins an item)
        _play_lottery_result_sound(True)
        
        # Show continue button for user to close when ready
        self.continue_btn.show()
    
    def _finish(self):
        """Emit result and close."""
        self.finished_signal.emit(self.rolled_tier, self.item)
        self.accept()
    
    def get_results(self) -> tuple:
        """Get the results."""
        return (self.rolled_tier, self.item)
    
    def closeEvent(self, event):
        """Clean up timers and save geometry."""
        save_dialog_geometry(self, "FocusTimerLotteryDialog")
        if hasattr(self, '_anim_timer'):
            self._anim_timer.stop()
        super().closeEvent(event)


class ActivityLotteryDialog(QtWidgets.QDialog):
    """Single-stage rarity lottery for physical activity rewards.
    
    Shows dramatic animation revealing the rarity tier based on effective minutes.
    Uses moving window [5, 15, 60, 15, 5] distribution centered on effective minutes tier.
    """
    
    finished_signal = QtCore.Signal(str, object)  # (rarity, item)
    
    TIERS = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
    TIER_COLORS = {
        "Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3",
        "Epic": "#9c27b0", "Legendary": "#ff9800"
    }
    BASE_WINDOW = [5, 15, 60, 15, 5]
    
    def __init__(self, effective_minutes: float, pre_rolled_rarity: str,
                 story_id: str = None, parent: Optional[QtWidgets.QWidget] = None):
        """
        Args:
            effective_minutes: Calculated effective minutes for display
            pre_rolled_rarity: The rarity that was already determined (from gamification.py)
            story_id: Story theme for display
            parent: Parent widget
        """
        super().__init__(parent)
        self.effective_minutes = effective_minutes
        self.rolled_tier = pre_rolled_rarity
        self.story_id = story_id
        self.item = None  # Item will be generated after showing animation
        
        # Calculate tier distribution for display
        self.tier_weights = self._calculate_tier_weights()
        
        # Pre-roll the position (0-100) for animation target
        self.tier_roll = self._get_position_for_tier(self.rolled_tier)
        
        self._setup_ui()
        QtCore.QTimer.singleShot(300, self._start_animation)
    
    def _calculate_tier_weights(self) -> list:
        """Calculate tier weights based on effective minutes."""
        # Determine center tier (same logic as gamification.py)
        if self.effective_minutes >= 100:
            center_tier = 4  # Legendary-centered (75%)
        elif self.effective_minutes >= 70:
            center_tier = 3  # Epic-centered
        elif self.effective_minutes >= 40:
            center_tier = 2  # Rare-centered
        elif self.effective_minutes >= 20:
            center_tier = 1  # Uncommon-centered
        else:  # 8-19 min
            center_tier = 0  # Common-centered
        
        weights = [0, 0, 0, 0, 0]
        
        for offset, pct in zip([-2, -1, 0, 1, 2], self.BASE_WINDOW):
            target_tier = center_tier + offset
            clamped_tier = max(0, min(4, target_tier))
            weights[clamped_tier] += pct
        
        return weights
    
    def _get_position_for_tier(self, tier: str) -> float:
        """Get a random position within the zone for the given tier."""
        import random
        
        cumulative = 0.0
        for t, weight in zip(self.TIERS, self.tier_weights):
            zone_size = weight
            if t == tier:
                # Random position within this zone
                return cumulative + random.random() * zone_size
            cumulative += zone_size
        return 50.0  # Fallback
    
    def _setup_ui(self):
        """Build the activity lottery UI."""
        self.setWindowTitle("🏃 Activity Reward!")
        self.setModal(True)
        self.setMinimumSize(440, 280)
        load_dialog_geometry(self, "ActivityLotteryDialog", QtCore.QSize(500, 320))
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)  # Small margin for shadow
        
        # Main container
        container = QtWidgets.QWidget()
        container.setStyleSheet("""
            QWidget {
                background: #1a1a2e;
                border: none;
                border-radius: 12px;
            }
        """)
        # Apply drop shadow to container for depth without borders
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QtGui.QColor(0, 0, 0, 120))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)
        
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setSpacing(12)
        container_layout.setContentsMargins(24, 18, 24, 18)
        
        # Header
        header = QtWidgets.QLabel(f"🏃 Activity Reward - {self.effective_minutes:.0f} eff. min")
        header.setFont(QtGui.QFont("Arial", 16, QtGui.QFont.Bold))
        header.setAlignment(QtCore.Qt.AlignCenter)
        container_layout.addWidget(header)
        
        # Tier lottery frame
        lottery_frame = QtWidgets.QFrame()
        lottery_frame.setStyleSheet("""
            QFrame { background: #252540; border: none; border-radius: 8px; }
        """)
        # Add subtle shadow for card effect
        lottery_shadow = QtWidgets.QGraphicsDropShadowEffect()
        lottery_shadow.setBlurRadius(10)
        lottery_shadow.setColor(QtGui.QColor(0, 0, 0, 80))
        lottery_shadow.setOffset(0, 2)
        lottery_frame.setGraphicsEffect(lottery_shadow)
        
        lottery_layout = QtWidgets.QVBoxLayout(lottery_frame)
        lottery_layout.setContentsMargins(14, 12, 14, 12)
        
        # Tier slider widget
        self.tier_slider = ActivityTierSliderWidget(self.tier_weights)
        self.tier_slider.setMinimumHeight(60)
        lottery_layout.addWidget(self.tier_slider)
        
        # Result label
        self.result_label = QtWidgets.QLabel("Rolling...")
        self.result_label.setAlignment(QtCore.Qt.AlignCenter)
        self.result_label.setStyleSheet("font-size: 14px; color: #888;")
        lottery_layout.addWidget(self.result_label)
        
        container_layout.addWidget(lottery_frame)
        
        # Final result (hidden initially)
        self.final_result = QtWidgets.QLabel("")
        self.final_result.setAlignment(QtCore.Qt.AlignCenter)
        self.final_result.setStyleSheet("font-size: 16px; font-weight: bold; color: #4caf50;")
        self.final_result.setMinimumHeight(40)  # Reserve space
        self.final_result.hide()
        container_layout.addWidget(self.final_result)
        
        # Stretch to absorb space changes
        container_layout.addStretch(1)
        
        # Sound toggle
        sound_row = QtWidgets.QHBoxLayout()
        sound_row.addStretch()
        self.sound_toggle = QtWidgets.QCheckBox("🔊 Sound")
        self.sound_toggle.setChecked(get_lottery_sound_enabled())
        self.sound_toggle.setStyleSheet("color: #666; font-size: 11px;")
        self.sound_toggle.toggled.connect(set_lottery_sound_enabled)
        sound_row.addWidget(self.sound_toggle)
        container_layout.addLayout(sound_row)
        
        # Continue button (hidden until animation complete)
        self.continue_btn = QtWidgets.QPushButton("Continue")
        self.continue_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 10px 30px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.continue_btn.clicked.connect(self._finish)
        self.continue_btn.hide()
        container_layout.addWidget(self.continue_btn, alignment=QtCore.Qt.AlignCenter)
        
        layout.addWidget(container)
    
    def _start_animation(self):
        """Start the tier roll animation using bounce path."""
        # Build bounce path (same logic as other lottery dialogs)
        self._path_points = [50.0]  # Start at center
        
        # 5 full bar sweeps with decreasing amplitude
        for bounce in range(5):
            amplitude = 1.0 - (bounce * 0.18)
            self._path_points.append(100 * amplitude)
            self._path_points.append(0)
        
        # Final approach to target
        self._path_points.append(self.tier_roll)
        
        # Calculate segment distances
        self._segments = []
        self._total_dist = 0.0
        
        for i in range(len(self._path_points) - 1):
            start, end = self._path_points[i], self._path_points[i+1]
            dist = abs(end - start)
            if dist > 0.001:
                self._segments.append({
                    "start": start, "end": end, "dist": dist,
                    "cum_start": self._total_dist,
                    "cum_end": self._total_dist + dist
                })
                self._total_dist += dist
        
        self._elapsed = 0.0
        self._duration = 4.0
        
        # Style state tracking for performance
        self._last_tier = None
        
        self._anim_timer = QtCore.QTimer(self)
        self._anim_timer.timeout.connect(self._anim_tick)
        self._anim_timer.start(16)  # 60 FPS for smooth performance
    
    def _anim_tick(self):
        """Animation tick."""
        # Cached tier colors for performance
        TIER_COLORS = {
            "Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3",
            "Epic": "#9c27b0", "Legendary": "#ff9800"
        }
        
        self._elapsed += 0.016  # Match timer interval
        t = min(1.0, self._elapsed / self._duration)
        eased = 1.0 - (1.0 - t) ** 4  # EaseOutQuart
        
        current_travel = eased * self._total_dist
        pos = self.tier_roll
        
        for seg in self._segments:
            if seg["cum_start"] <= current_travel <= seg["cum_end"]:
                local = (current_travel - seg["cum_start"]) / seg["dist"]
                pos = seg["start"] + (seg["end"] - seg["start"]) * local
                break
        
        pos = max(0, min(100, pos))
        self.tier_slider.set_position(pos)
        
        # Show current tier during animation - only update style if tier changed
        tier = self.tier_slider.get_tier_at_position(pos)
        if tier != self._last_tier:
            self._last_tier = tier
            color = TIER_COLORS.get(tier, "#fff")
            self.result_label.setStyleSheet(f"color: {color}; font-size: 14px;")
        self.result_label.setText(f"🎲 {pos:.1f}% → {tier}")
        
        if t >= 1.0:
            self._anim_timer.stop()
            self.tier_slider.set_position(self.tier_roll)
            self._finish_animation()
    
    def _finish_animation(self):
        """Show final result."""
        color = self.TIER_COLORS.get(self.rolled_tier, "#aaa")
        
        # Set result on slider to trigger glow effect
        self.tier_slider.set_result(self.rolled_tier)
        
        self.result_label.setText(f"✨ Rolled: {self.rolled_tier}!")
        self.result_label.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
        
        # Generate item
        try:
            from gamification import generate_item
            self.item = generate_item(rarity=self.rolled_tier, story_id=self.story_id)
        except (ImportError, Exception):
            self.item = {"name": f"{self.rolled_tier} Item", "rarity": self.rolled_tier, "power": 10}
        
        # Show item name
        item_name = self.item.get("name", "Unknown Item")
        self.final_result.setText(f"🎁 {item_name}")
        self.final_result.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
        self.final_result.show()
        
        # Play win sound (activity always awards an item)
        _play_lottery_result_sound(True)
        
        # Show continue button for user to close when ready
        self.continue_btn.show()
    
    def _finish(self):
        """Emit result and close."""
        self.finished_signal.emit(self.rolled_tier, self.item)
        self.accept()
    
    def get_results(self) -> tuple:
        """Get the results."""
        return (self.rolled_tier, self.item)
    
    def closeEvent(self, event):
        """Clean up timers and save geometry."""
        save_dialog_geometry(self, "ActivityLotteryDialog")
        if hasattr(self, '_anim_timer'):
            self._anim_timer.stop()
        super().closeEvent(event)


class ActivityTierSliderWidget(QtWidgets.QWidget):
    """5-zone tier slider for activity lottery with dynamic weights."""
    
    TIER_COLORS = {
        "Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3",
        "Epic": "#9c27b0", "Legendary": "#ff9800"
    }
    TIERS = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
    
    def __init__(self, tier_weights: list, parent=None):
        super().__init__(parent)
        self.tier_weights = tier_weights  # [Common%, Uncommon%, Rare%, Epic%, Legendary%]
        self.position = 0.0
        self.result_tier = None  # For glow effect after result
        self.setMinimumSize(400, 60)
    
    def set_position(self, pos: float):
        """Set marker position (0-100)."""
        self.position = max(0.0, min(100.0, pos))
        self.update()
    
    def set_result(self, tier: str):
        """Set the result tier for visual feedback with glow effect."""
        self.result_tier = tier
        self.update()
    
    def get_tier_at_position(self, pos: float) -> str:
        """Get the tier at a given position."""
        cumulative = 0.0
        for tier, weight in zip(self.TIERS, self.tier_weights):
            if pos < cumulative + weight:
                return tier
            cumulative += weight
        return "Legendary"
    
    def get_position_for_tier(self, tier: str) -> float:
        """Get the center position for a tier zone."""
        cumulative = 0.0
        for t, weight in zip(self.TIERS, self.tier_weights):
            if t == tier:
                return cumulative + weight / 2
            cumulative += weight
        return 95.0
    
    def paintEvent(self, event):
        _PaintCache.initialize()  # Ensure cache is ready
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Bar dimensions
        bar_y = 20
        bar_height = 35
        bar_width = self.width() - 20
        x_offset = 10
        
        # Draw tier zones (use cached colors)
        cumulative_x = x_offset
        for tier, weight in zip(self.TIERS, self.tier_weights):
            if weight <= 0:
                continue
            zone_width = (weight / 100) * bar_width
            color = _PaintCache.get_tier_color(tier)
            
            # Highlight winning tier, dim others
            if self.result_tier and tier == self.result_tier:
                painter.setOpacity(1.0)
            else:
                painter.setOpacity(0.7 if self.result_tier else 1.0)
            
            painter.fillRect(
                int(cumulative_x), bar_y,
                int(zone_width), bar_height,
                color
            )
            
            # Zone label with tier name and percentage (matches FocusTimerTierSliderWidget)
            if zone_width > 45:
                painter.setOpacity(1.0)
                painter.setPen(_PaintCache.COLOR_WHITE)
                painter.setFont(_PaintCache.FONT_LABEL_MEDIUM)
                label = f"{tier[:3]}:{weight:.0f}%"
                painter.drawText(
                    int(cumulative_x), bar_y,
                    int(zone_width), bar_height,
                    QtCore.Qt.AlignCenter, label
                )
            elif zone_width > 30:
                painter.setOpacity(1.0)
                painter.setPen(_PaintCache.COLOR_WHITE)
                painter.setFont(_PaintCache.FONT_LABEL_MEDIUM)
                painter.drawText(
                    int(cumulative_x), bar_y,
                    int(zone_width), bar_height,
                    QtCore.Qt.AlignCenter,
                    tier[:3]  # First 3 letters
                )
            cumulative_x += zone_width
        
        painter.setOpacity(1.0)
        
        # Draw border
        painter.setPen(_PaintCache.PEN_BORDER)
        painter.drawRect(x_offset, bar_y, bar_width, bar_height)
        
        # Marker
        marker_x = x_offset + (self.position / 100) * bar_width
        current_tier = self.get_tier_at_position(self.position)
        marker_color = _PaintCache.get_tier_color(current_tier)
        
        # Glow effect for result
        if self.result_tier:
            glow_color = _PaintCache.get_tier_color(self.result_tier)
            for i in range(3):
                glow_size = 10 + (3-i) * 3
                painter.setBrush(glow_color)
                painter.setOpacity(0.3)
                painter.drawEllipse(
                    QtCore.QPointF(marker_x, bar_y + bar_height // 2),
                    glow_size, glow_size
                )
            painter.setOpacity(1.0)
        
        # Marker triangle
        painter.setBrush(marker_color)
        painter.setPen(_PaintCache.PEN_MARKER_OUTLINE)
        triangle = [
            QtCore.QPointF(marker_x, bar_y - 3),
            QtCore.QPointF(marker_x - 8, bar_y - 15),
            QtCore.QPointF(marker_x + 8, bar_y - 15)
        ]
        painter.drawPolygon(triangle)
        
        # Marker line
        painter.setPen(QtGui.QPen(marker_color, 3))
        painter.drawLine(int(marker_x), bar_y, int(marker_x), bar_y + bar_height)


class WeightLotteryDialog(QtWidgets.QDialog):
    """Single-stage rarity lottery for weight tracking rewards.
    
    Shows dramatic animation revealing the rarity tier for a pre-generated item.
    Uses moving window [5, 15, 60, 15, 5] distribution based on weight progress tier.
    Matches FocusTimerLotteryDialog's polished visual design.
    """
    
    finished_signal = QtCore.Signal(str, object)  # (rarity, item)
    
    TIERS = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
    TIER_COLORS = {
        "Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3",
        "Epic": "#9c27b0", "Legendary": "#ff9800"
    }
    BASE_WINDOW = [5, 15, 60, 15, 5]
    
    def __init__(self, item: dict, reward_source: str = "Weight Tracking",
                 extra_items: list = None, parent: Optional[QtWidgets.QWidget] = None):
        """
        Args:
            item: The primary item that was already generated (with 'rarity' key)
            reward_source: Display string for the reward source (e.g., "Daily Weigh-In")
            extra_items: Additional items to show after animation (won't be animated)
            parent: Parent widget
        """
        super().__init__(parent)
        self.item = item
        self.reward_source = reward_source
        self.extra_items = extra_items or []
        self.rolled_tier = item.get("rarity", "Common")
        
        # Calculate tier weights based on rarity tier (higher tier = better weights shown)
        self.tier_weights = self._calculate_tier_weights()
        
        self._setup_ui()
        
        # Calculate target position using the slider's method
        self.tier_roll = self.tier_slider.get_position_for_tier(self.rolled_tier)
        
        QtCore.QTimer.singleShot(300, self._start_animation)
    
    def _calculate_tier_weights(self) -> list:
        """Calculate tier weights based on the rolled rarity."""
        # Center the window on the rolled tier
        tier_index = self.TIERS.index(self.rolled_tier) if self.rolled_tier in self.TIERS else 0
        
        weights = [0, 0, 0, 0, 0]
        
        for offset, pct in zip([-2, -1, 0, 1, 2], self.BASE_WINDOW):
            target_tier = tier_index + offset
            clamped_tier = max(0, min(4, target_tier))
            weights[clamped_tier] += pct
        
        return weights
    
    def _setup_ui(self):
        """Build the weight lottery UI with polished styling (matches FocusTimerLotteryDialog)."""
        self.setWindowTitle("⚖️ Weight Reward!")
        self.setModal(True)
        self.setMinimumSize(450, 380)
        load_dialog_geometry(self, "WeightLotteryDialog", QtCore.QSize(520, 420))
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)  # Small margin for shadow
        
        # Main container with border
        container = QtWidgets.QWidget()
        container.setStyleSheet("""
            QWidget {
                background: #1a1a2e;
                border: none;
                border-radius: 12px;
            }
        """)
        # Apply drop shadow to container for depth without borders
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QtGui.QColor(0, 0, 0, 120))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)
        
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setSpacing(12)
        container_layout.setContentsMargins(24, 18, 24, 18)
        
        # Header
        header = QtWidgets.QLabel("⚖️ Weight Reward! ⚖️")
        header.setAlignment(QtCore.Qt.AlignCenter)
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #9ca3af;")
        container_layout.addWidget(header)
        
        # Reward source info
        info = QtWidgets.QLabel(f"🏆 {self.reward_source}")
        info.setAlignment(QtCore.Qt.AlignCenter)
        info.setStyleSheet("color: #aaa; font-size: 12px;")
        container_layout.addWidget(info)
        
        # Tier lottery frame
        lottery_frame = QtWidgets.QFrame()
        lottery_frame.setStyleSheet("""
            QFrame { background: #252540; border: none; border-radius: 8px; }
        """)
        # Add subtle shadow for card effect
        lottery_shadow = QtWidgets.QGraphicsDropShadowEffect()
        lottery_shadow.setBlurRadius(10)
        lottery_shadow.setColor(QtGui.QColor(0, 0, 0, 80))
        lottery_shadow.setOffset(0, 2)
        lottery_frame.setGraphicsEffect(lottery_shadow)
        
        lottery_layout = QtWidgets.QVBoxLayout(lottery_frame)
        lottery_layout.setContentsMargins(14, 12, 14, 12)
        
        lottery_title = QtWidgets.QLabel("✨ Rolling for Item Tier...")
        lottery_title.setStyleSheet("color: #ff9800; font-size: 14px; font-weight: bold;")
        lottery_layout.addWidget(lottery_title)
        
        # Tier slider
        self.tier_slider = ActivityTierSliderWidget(self.tier_weights)
        self.tier_slider.setFixedHeight(70)
        lottery_layout.addWidget(self.tier_slider)
        
        # Result label
        self.lottery_result = QtWidgets.QLabel("🎲 Rolling...")
        self.lottery_result.setAlignment(QtCore.Qt.AlignCenter)
        self.lottery_result.setStyleSheet("color: #aaa; font-size: 14px;")
        lottery_layout.addWidget(self.lottery_result)
        
        container_layout.addWidget(lottery_frame)
        
        # Item reveal area (hidden until animation complete)
        self.item_frame = QtWidgets.QFrame()
        self.item_frame.setStyleSheet("""
            QFrame { background: #252540; border: none; border-radius: 8px; }
        """)
        self.item_frame.hide()
        item_layout = QtWidgets.QVBoxLayout(self.item_frame)
        item_layout.setContentsMargins(14, 12, 14, 12)
        
        self.item_label = QtWidgets.QLabel("")
        self.item_label.setAlignment(QtCore.Qt.AlignCenter)
        self.item_label.setWordWrap(True)
        self.item_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        item_layout.addWidget(self.item_label)
        
        # Extra items label
        self.extra_label = QtWidgets.QLabel("")
        self.extra_label.setAlignment(QtCore.Qt.AlignCenter)
        self.extra_label.setStyleSheet("font-size: 12px; color: #888;")
        self.extra_label.hide()
        item_layout.addWidget(self.extra_label)
        
        container_layout.addWidget(self.item_frame)
        
        # Stretch to absorb space changes
        container_layout.addStretch(1)
        
        # Sound toggle
        sound_row = QtWidgets.QHBoxLayout()
        sound_row.addStretch()
        self.sound_toggle = QtWidgets.QCheckBox("🔊 Sound")
        self.sound_toggle.setChecked(get_lottery_sound_enabled())
        self.sound_toggle.setStyleSheet("color: #666; font-size: 11px;")
        self.sound_toggle.toggled.connect(set_lottery_sound_enabled)
        sound_row.addWidget(self.sound_toggle)
        container_layout.addLayout(sound_row)
        
        # Continue button (hidden until animation complete)
        self.continue_btn = QtWidgets.QPushButton("Continue")
        self.continue_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 10px 30px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.continue_btn.clicked.connect(self._finish)
        self.continue_btn.hide()
        container_layout.addWidget(self.continue_btn, alignment=QtCore.Qt.AlignCenter)
        
        layout.addWidget(container)
    
    def _start_animation(self):
        """Start tier roll animation using bounce path (same as FocusTimerLotteryDialog)."""
        # Generate bounce path with randomized direction (matches FocusTimerLotteryDialog)
        self._path_points = [50.0]
        going_up = random.choice([True, False])
        num_bounces = random.randint(4, 6)
        
        for _ in range(num_bounces):
            if going_up:
                self._path_points.extend([100.0, 0.0])
            else:
                self._path_points.extend([0.0, 100.0])
        self._path_points.append(self.tier_roll)
        
        # Pre-compute segments for smoother animation
        self._segments = []
        self._total_dist = 0.0
        for i in range(len(self._path_points) - 1):
            start, end = self._path_points[i], self._path_points[i+1]
            dist = abs(end - start)
            if dist > 0.001:
                self._segments.append({
                    "start": start, "end": end, "dist": dist,
                    "cum_start": self._total_dist,
                    "cum_end": self._total_dist + dist
                })
                self._total_dist += dist
        
        self._anim_elapsed = 0.0
        self._anim_duration = 4.0
        
        # Style state tracking for performance
        self._anim_last_tier = None
        
        self._anim_timer = QtCore.QTimer(self)
        self._anim_timer.timeout.connect(self._animate_step)
        self._anim_timer.start(16)  # 60 FPS
    
    def _animate_step(self):
        """Animation frame using bounce path."""
        self._anim_elapsed += 0.016  # Match timer interval
        t = min(1.0, self._anim_elapsed / self._anim_duration)
        eased = 1.0 - (1.0 - t) ** 4  # EaseOutQuart
        
        current_travel = eased * self._total_dist
        pos = self.tier_roll
        
        for seg in self._segments:
            if seg["cum_start"] <= current_travel <= seg["cum_end"]:
                local = (current_travel - seg["cum_start"]) / seg["dist"]
                pos = seg["start"] + (seg["end"] - seg["start"]) * local
                break
        
        pos = max(0, min(100, pos))
        self.tier_slider.set_position(pos)
        
        # Update rolling text - only update style if tier changed
        current_tier = self.tier_slider.get_tier_at_position(pos)
        if current_tier != self._anim_last_tier:
            self._anim_last_tier = current_tier
            color = self.TIER_COLORS.get(current_tier, "#fff")
            self.lottery_result.setStyleSheet(f"color: {color}; font-size: 14px;")
        self.lottery_result.setText(f"🎲 {pos:.1f}% → {current_tier}")
        
        if t >= 1.0:
            self._anim_timer.stop()
            self.tier_slider.set_position(self.tier_roll)
            self._show_result()
    
    def _show_result(self):
        """Show the won item with polished reveal."""
        tier = self.rolled_tier
        color = self.TIER_COLORS.get(tier, "#fff")
        
        # Update slider with result (triggers glow effect)
        self.tier_slider.set_result(tier)
        
        # Show tier result
        self.lottery_result.setText(f"<b style='color:{color};'>🎯 {tier.upper()}!</b>")
        self.lottery_result.setTextFormat(QtCore.Qt.RichText)
        
        # Reveal item frame
        self.item_frame.show()
        self.item_frame.setStyleSheet(f"QFrame {{ background: #252540; border: 2px solid {color}; border-radius: 8px; }}")
        
        item_name = self.item.get("name", "Unknown Item")
        slot = self.item.get("slot", "unknown")
        power = self.item.get("power", 0)
        
        # Check for lucky options
        lucky_opts = self.item.get("lucky_options", {})
        lucky_text = ""
        if lucky_opts:
            opts = []
            if lucky_opts.get("xp_bonus"):
                opts.append(f"+{lucky_opts['xp_bonus']}% XP")
            if lucky_opts.get("coin_discount"):
                opts.append(f"+{lucky_opts['coin_discount']}% Coin Discount")
            if lucky_opts.get("merge_luck"):
                opts.append(f"+{lucky_opts['merge_luck']}% Merge Luck")
            if opts:
                lucky_text = f"<br><span style='color:#ffd700;'>⭐ {', '.join(opts)}</span>"
        
        self.item_label.setText(
            f"<span style='color:{color};'>[{tier}] {item_name}</span><br>"
            f"<span style='color:#888;'>📍 {slot.title()} • ⚔️ +{power} Power</span>"
            f"{lucky_text}"
        )
        self.item_label.setTextFormat(QtCore.Qt.RichText)
        
        # Show extra items if any
        if self.extra_items:
            extra_count = len(self.extra_items)
            self.extra_label.setText(f"✨ +{extra_count} more item{'s' if extra_count > 1 else ''}!")
            self.extra_label.show()
        
        # Play win sound
        _play_lottery_result_sound(True)
        
        # Show continue button
        self.continue_btn.show()
    
    def _finish(self):
        """Emit result and close."""
        self.finished_signal.emit(self.rolled_tier, self.item)
        self.accept()
    
    def get_results(self) -> tuple:
        """Get the results."""
        return (self.rolled_tier, self.item)
    
    def closeEvent(self, event):
        """Clean up timers and save geometry."""
        save_dialog_geometry(self, "WeightLotteryDialog")
        if hasattr(self, '_anim_timer'):
            self._anim_timer.stop()
        super().closeEvent(event)


class SleepLotteryDialog(QtWidgets.QDialog):
    """Single-stage rarity lottery for sleep tracking rewards.
    
    Shows dramatic animation revealing the rarity tier for a pre-generated item.
    Matches FocusTimerLotteryDialog's polished visual design with sleep-themed styling.
    """
    
    finished_signal = QtCore.Signal(str, object)  # (rarity, item)
    
    TIERS = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
    TIER_COLORS = {
        "Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3",
        "Epic": "#9c27b0", "Legendary": "#ff9800"
    }
    BASE_WINDOW = [5, 15, 60, 15, 5]
    
    def __init__(self, item: dict, reward_source: str = "Sleep Tracking",
                 extra_items: list = None, parent: Optional[QtWidgets.QWidget] = None):
        """
        Args:
            item: The primary item that was already generated (with 'rarity' key)
            reward_source: Display string for the reward source (e.g., "Sleep Logged")
            extra_items: Additional items to show after animation (won't be animated)
            parent: Parent widget
        """
        super().__init__(parent)
        self.item = item
        self.reward_source = reward_source
        self.extra_items = extra_items or []
        self.rolled_tier = item.get("rarity", "Common")
        
        # Calculate tier weights based on rarity tier (higher tier = better weights shown)
        self.tier_weights = self._calculate_tier_weights()
        
        self._setup_ui()
        
        # Calculate target position using the slider's method
        self.tier_roll = self.tier_slider.get_position_for_tier(self.rolled_tier)
        
        QtCore.QTimer.singleShot(300, self._start_animation)
    
    def _calculate_tier_weights(self) -> list:
        """Calculate tier weights based on the rolled rarity."""
        # Center the window on the rolled tier
        tier_index = self.TIERS.index(self.rolled_tier) if self.rolled_tier in self.TIERS else 0
        
        weights = [0, 0, 0, 0, 0]
        
        for offset, pct in zip([-2, -1, 0, 1, 2], self.BASE_WINDOW):
            target_tier = tier_index + offset
            clamped_tier = max(0, min(4, target_tier))
            weights[clamped_tier] += pct
        
        return weights
    
    def _setup_ui(self):
        """Build the sleep lottery UI with polished styling (matches FocusTimerLotteryDialog)."""
        self.setWindowTitle("🌙 Sleep Reward!")
        self.setModal(True)
        self.setMinimumSize(450, 380)
        load_dialog_geometry(self, "SleepLotteryDialog", QtCore.QSize(520, 420))
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)  # Small margin for shadow
        
        # Main container (sleep-themed indigo)
        container = QtWidgets.QWidget()
        container.setStyleSheet("""
            QWidget {
                background: #1a1a2e;
                border: none;
                border-radius: 12px;
            }
        """)
        # Apply drop shadow to container for depth without borders
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QtGui.QColor(0, 0, 0, 120))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)
        
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setSpacing(12)
        container_layout.setContentsMargins(24, 18, 24, 18)
        
        # Header
        header = QtWidgets.QLabel("🌙 Sleep Reward! 🌙")
        header.setAlignment(QtCore.Qt.AlignCenter)
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #9ca3af;")
        container_layout.addWidget(header)
        
        # Reward source info
        info = QtWidgets.QLabel(f"💤 {self.reward_source}")
        info.setAlignment(QtCore.Qt.AlignCenter)
        info.setStyleSheet("color: #aaa; font-size: 12px;")
        container_layout.addWidget(info)
        
        # Tier lottery frame (sleep-themed indigo)
        lottery_frame = QtWidgets.QFrame()
        lottery_frame.setStyleSheet("""
            QFrame { background: #252540; border: none; border-radius: 8px; }
        """)
        # Add subtle shadow for card effect
        lottery_shadow = QtWidgets.QGraphicsDropShadowEffect()
        lottery_shadow.setBlurRadius(10)
        lottery_shadow.setColor(QtGui.QColor(0, 0, 0, 80))
        lottery_shadow.setOffset(0, 2)
        lottery_frame.setGraphicsEffect(lottery_shadow)
        
        lottery_layout = QtWidgets.QVBoxLayout(lottery_frame)
        lottery_layout.setContentsMargins(14, 12, 14, 12)
        
        lottery_title = QtWidgets.QLabel("✨ Rolling for Item Tier...")
        lottery_title.setStyleSheet("color: #7986cb; font-size: 14px; font-weight: bold;")
        lottery_layout.addWidget(lottery_title)
        
        # Tier slider
        self.tier_slider = ActivityTierSliderWidget(self.tier_weights)
        self.tier_slider.setFixedHeight(70)
        lottery_layout.addWidget(self.tier_slider)
        
        # Result label
        self.lottery_result = QtWidgets.QLabel("🎲 Rolling...")
        self.lottery_result.setAlignment(QtCore.Qt.AlignCenter)
        self.lottery_result.setStyleSheet("color: #aaa; font-size: 14px;")
        lottery_layout.addWidget(self.lottery_result)
        
        container_layout.addWidget(lottery_frame)
        
        # Item reveal area (hidden until animation complete)
        self.item_frame = QtWidgets.QFrame()
        self.item_frame.setStyleSheet("""
            QFrame { background: #252540; border: none; border-radius: 8px; }
        """)
        self.item_frame.setMinimumHeight(60)  # Reserve space
        self.item_frame.hide()
        item_layout = QtWidgets.QVBoxLayout(self.item_frame)
        item_layout.setContentsMargins(14, 12, 14, 12)
        
        self.item_label = QtWidgets.QLabel("")
        self.item_label.setAlignment(QtCore.Qt.AlignCenter)
        self.item_label.setWordWrap(True)
        self.item_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        item_layout.addWidget(self.item_label)
        
        # Extra items label
        self.extra_label = QtWidgets.QLabel("")
        self.extra_label.setAlignment(QtCore.Qt.AlignCenter)
        self.extra_label.setStyleSheet("font-size: 12px; color: #888;")
        self.extra_label.hide()
        item_layout.addWidget(self.extra_label)
        
        container_layout.addWidget(self.item_frame)
        
        # Stretch to absorb space changes
        container_layout.addStretch(1)
        
        # Sound toggle
        sound_row = QtWidgets.QHBoxLayout()
        sound_row.addStretch()
        self.sound_toggle = QtWidgets.QCheckBox("🔊 Sound")
        self.sound_toggle.setChecked(get_lottery_sound_enabled())
        self.sound_toggle.setStyleSheet("color: #666; font-size: 11px;")
        self.sound_toggle.toggled.connect(set_lottery_sound_enabled)
        sound_row.addWidget(self.sound_toggle)
        container_layout.addLayout(sound_row)
        
        # Continue button (hidden until animation complete, sleep-themed indigo)
        self.continue_btn = QtWidgets.QPushButton("Continue")
        self.continue_btn.setStyleSheet("""
            QPushButton {
                background-color: #5c6bc0;
                color: white;
                border: none;
                padding: 10px 30px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7986cb;
            }
        """)
        self.continue_btn.clicked.connect(self._finish)
        self.continue_btn.hide()
        container_layout.addWidget(self.continue_btn, alignment=QtCore.Qt.AlignCenter)
        
        layout.addWidget(container)
    
    def _start_animation(self):
        """Start tier roll animation using bounce path (same as FocusTimerLotteryDialog)."""
        # Generate bounce path with randomized direction
        self._path_points = [50.0]
        going_up = random.choice([True, False])
        num_bounces = random.randint(4, 6)
        
        for _ in range(num_bounces):
            if going_up:
                self._path_points.extend([100.0, 0.0])
            else:
                self._path_points.extend([0.0, 100.0])
        self._path_points.append(self.tier_roll)
        
        # Pre-compute segments for smoother animation
        self._segments = []
        self._total_dist = 0.0
        for i in range(len(self._path_points) - 1):
            start, end = self._path_points[i], self._path_points[i+1]
            dist = abs(end - start)
            if dist > 0.001:
                self._segments.append({
                    "start": start, "end": end, "dist": dist,
                    "cum_start": self._total_dist,
                    "cum_end": self._total_dist + dist
                })
                self._total_dist += dist
        
        self._anim_elapsed = 0.0
        self._anim_duration = 4.0
        
        # Style state tracking for performance
        self._anim_last_tier = None
        
        self._anim_timer = QtCore.QTimer(self)
        self._anim_timer.timeout.connect(self._animate_step)
        self._anim_timer.start(16)  # 60 FPS
    
    def _animate_step(self):
        """Animation frame using bounce path."""
        self._anim_elapsed += 0.016  # Match timer interval
        t = min(1.0, self._anim_elapsed / self._anim_duration)
        eased = 1.0 - (1.0 - t) ** 4  # EaseOutQuart
        
        current_travel = eased * self._total_dist
        pos = self.tier_roll
        
        for seg in self._segments:
            if seg["cum_start"] <= current_travel <= seg["cum_end"]:
                local = (current_travel - seg["cum_start"]) / seg["dist"]
                pos = seg["start"] + (seg["end"] - seg["start"]) * local
                break
        
        pos = max(0, min(100, pos))
        self.tier_slider.set_position(pos)
        
        # Update rolling text - only update style if tier changed
        current_tier = self.tier_slider.get_tier_at_position(pos)
        if current_tier != self._anim_last_tier:
            self._anim_last_tier = current_tier
            color = self.TIER_COLORS.get(current_tier, "#fff")
            self.lottery_result.setStyleSheet(f"color: {color}; font-size: 14px;")
        self.lottery_result.setText(f"🎲 {pos:.1f}% → {current_tier}")
        
        if t >= 1.0:
            self._anim_timer.stop()
            self.tier_slider.set_position(self.tier_roll)
            self._show_result()
    
    def _show_result(self):
        """Show the won item with polished reveal."""
        tier = self.rolled_tier
        color = self.TIER_COLORS.get(tier, "#fff")
        
        # Update slider with result (triggers glow effect)
        self.tier_slider.set_result(tier)
        
        # Show tier result
        self.lottery_result.setText(f"<b style='color:{color};'>🎯 {tier.upper()}!</b>")
        self.lottery_result.setTextFormat(QtCore.Qt.RichText)
        
        # Reveal item frame
        self.item_frame.show()
        self.item_frame.setStyleSheet(f"QFrame {{ background: #252540; border: 2px solid {color}; border-radius: 8px; }}")
        
        item_name = self.item.get("name", "Unknown Item")
        slot = self.item.get("slot", "unknown")
        power = self.item.get("power", 0)
        
        # Check for lucky options
        lucky_opts = self.item.get("lucky_options", {})
        lucky_text = ""
        if lucky_opts:
            opts = []
            if lucky_opts.get("xp_bonus"):
                opts.append(f"+{lucky_opts['xp_bonus']}% XP")
            if lucky_opts.get("coin_discount"):
                opts.append(f"+{lucky_opts['coin_discount']}% Coin Discount")
            if lucky_opts.get("merge_luck"):
                opts.append(f"+{lucky_opts['merge_luck']}% Merge Luck")
            if opts:
                lucky_text = f"<br><span style='color:#ffd700;'>⭐ {', '.join(opts)}</span>"
        
        self.item_label.setText(
            f"<span style='color:{color};'>[{tier}] {item_name}</span><br>"
            f"<span style='color:#888;'>📍 {slot.title()} • ⚔️ +{power} Power</span>"
            f"{lucky_text}"
        )
        self.item_label.setTextFormat(QtCore.Qt.RichText)
        
        # Show extra items if any
        if self.extra_items:
            extra_count = len(self.extra_items)
            self.extra_label.setText(f"✨ +{extra_count} more item{'s' if extra_count > 1 else ''}!")
            self.extra_label.show()
        
        # Play win sound
        _play_lottery_result_sound(True)
        
        # Show continue button
        self.continue_btn.show()
    
    def _finish(self):
        """Emit result and close."""
        self.finished_signal.emit(self.rolled_tier, self.item)
        self.accept()
    
    def get_results(self) -> tuple:
        """Get the results."""
        return (self.rolled_tier, self.item)
    
    def closeEvent(self, event):
        """Clean up timers and save geometry."""
        save_dialog_geometry(self, "SleepLotteryDialog")
        if hasattr(self, '_anim_timer'):
            self._anim_timer.stop()
        super().closeEvent(event)


# Backwards compatibility aliases
MergeSliderWidget = LotterySliderWidget
MergeRollAnimationDialog = LotteryRollDialog
