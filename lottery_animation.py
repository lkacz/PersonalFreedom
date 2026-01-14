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
# Dialog Geometry Persistence Helpers
# ============================================================================

def _get_dialog_settings() -> QtCore.QSettings:
    """Get QSettings for dialog geometry persistence."""
    return QtCore.QSettings("PersonalFreedom", "LotteryDialogs")


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
        painter.setBrush(QtGui.QColor("#2e7d32"))  # Dark green
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRoundedRect(success_rect, 4, 4)
        
        # Failure zone (red) - right side from threshold
        fail_rect = QtCore.QRectF(threshold_x, bar_y, w - margin - threshold_x, bar_height)
        painter.setBrush(QtGui.QColor("#c62828"))  # Dark red
        painter.drawRoundedRect(fail_rect, 4, 4)
        
        # Draw threshold line
        painter.setPen(QtGui.QPen(QtGui.QColor("#fff"), 2))
        painter.drawLine(int(threshold_x), bar_y - 5, int(threshold_x), bar_y + bar_height + 5)
        
        # Threshold label
        painter.setFont(QtGui.QFont("Arial", 9, QtGui.QFont.Bold))
        painter.drawText(int(threshold_x) - 15, bar_y - 8, f"{self.threshold:.0f}%")
        
        # Draw 0% and 100% labels
        painter.setPen(QtGui.QColor("#888"))
        painter.setFont(QtGui.QFont("Arial", 8))
        painter.drawText(margin, bar_y + bar_height + 15, "0%")
        painter.drawText(w - margin - 25, bar_y + bar_height + 15, "100%")
        
        # Draw "WIN" and "LOSE" zone labels
        painter.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        if threshold_x - margin > 40:
            painter.setPen(QtGui.QColor("#4caf50"))
            win_x = margin + (threshold_x - margin) / 2 - 15
            painter.drawText(int(win_x), bar_y + bar_height // 2 + 5, "WIN")
        if w - margin - threshold_x > 40:
            painter.setPen(QtGui.QColor("#f44336"))
            lose_x = threshold_x + (w - margin - threshold_x) / 2 - 18
            painter.drawText(int(lose_x), bar_y + bar_height // 2 + 5, "LOSE")
        
        # Draw the sliding marker
        marker_x = margin + (self.position / 100.0) * (w - 2*margin)
        marker_size = 16
        
        # Marker color based on position
        if self.result is not None:
            marker_color = "#4caf50" if self.result else "#f44336"
            glow_color = "#4caf50" if self.result else "#f44336"
        elif self.position < self.threshold:
            marker_color = "#66bb6a"
            glow_color = None
        else:
            marker_color = "#ef5350"
            glow_color = None
        
        # Draw glow if result shown
        if glow_color:
            for i in range(3):
                glow_size = marker_size + (3-i) * 4
                painter.setBrush(QtGui.QColor(glow_color))
                painter.setOpacity(0.2)
                painter.drawEllipse(
                    QtCore.QPointF(marker_x, bar_y + bar_height // 2),
                    glow_size, glow_size
                )
            painter.setOpacity(1.0)
        
        # Draw marker (triangle pointing down)
        painter.setBrush(QtGui.QColor(marker_color))
        painter.setPen(QtGui.QPen(QtGui.QColor("#fff"), 2))
        
        # Triangle marker
        triangle = QtGui.QPolygonF([
            QtCore.QPointF(marker_x, bar_y - 2),
            QtCore.QPointF(marker_x - 8, bar_y - 14),
            QtCore.QPointF(marker_x + 8, bar_y - 14),
        ])
        painter.drawPolygon(triangle)
        
        # Marker line
        painter.setPen(QtGui.QPen(QtGui.QColor(marker_color), 3))
        painter.drawLine(int(marker_x), bar_y, int(marker_x), bar_y + bar_height)


class LotteryRollDialog(QtWidgets.QDialog):
    """Dramatic slider animation for lottery/probability roll reveal.
    
    Features:
    - Ping-pong bouncing animation (slider bounces off walls 4-6 times)
    - Quadratic friction deceleration for realistic slowdown
    - Customizable title and styling
    - Auto-closes after showing result
    
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
        self.tick_interval = 16  # ~60 FPS
        self.elapsed_time = 0.0
        self.animation_duration = animation_duration
        
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
        self.setMinimumSize(400, 160)
        load_dialog_geometry(self, "LotteryRollDialog", QtCore.QSize(500, 200))
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main container
        container = QtWidgets.QWidget()
        container.setStyleSheet("""
            QWidget {
                background: #1a1a2e;
                border: 3px solid #ffd700;
                border-radius: 12px;
            }
        """)
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setSpacing(12)
        container_layout.setContentsMargins(20, 16, 20, 16)
        
        # Title
        title = QtWidgets.QLabel(self.title_text)
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffd700;")
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
        
        layout.addWidget(container)
    
    def _start_animation(self):
        """Start the damped oscillation animation."""
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(self.tick_interval)
    
    def _tick(self):
        """Update animation by traversing the pre-calculated bounce path."""
        # Update elapsed time
        self.elapsed_time += self.tick_interval / 1000.0  # seconds
        
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
        
        # Color based on position
        if self.current_position < self.success_threshold:
            self.roll_label.setStyleSheet("""
                font-size: 28px; font-weight: bold; color: #4caf50;
                font-family: 'Consolas', 'Monaco', monospace;
            """)
        else:
            self.roll_label.setStyleSheet("""
                font-size: 28px; font-weight: bold; color: #f44336;
                font-family: 'Consolas', 'Monaco', monospace;
            """)
        
        # Update status based on speed (derivative of eased_progress)
        speed = 4 * (1.0 - t) ** 3
        if speed > 2.0:
            self.status_label.setText("⚡ Spinning...")
        elif speed > 0.8:
            self.status_label.setText("🎯 Slowing down...")
        elif speed > 0.2:
            self.status_label.setText("🎲 Almost there...")
        else:
            self.status_label.setText("✨ Settling...")
    
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
        
        # Emit signal and auto-close
        self.finished_signal.emit(self.is_success)
        QtCore.QTimer.singleShot(1200, self.accept)
    
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
    
    def __init__(self, tier_weights: list, parent=None):
        """
        Args:
            tier_weights: List of 5 weights [Common, Uncommon, Rare, Epic, Legendary]
        """
        super().__init__(parent)
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
        
        # Draw tier zones
        cumulative_x = x_offset
        for tier, width in zip(self.TIERS, self.zone_widths):
            if width <= 0:
                continue
            zone_width = (width / 100) * bar_width
            color = QtGui.QColor(self.TIER_COLORS[tier])
            
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
                painter.setPen(QtGui.QColor("#ffffff"))
                painter.setFont(QtGui.QFont("Arial", 9, QtGui.QFont.Bold))
                painter.drawText(
                    int(cumulative_x), bar_y,
                    int(zone_width), bar_height,
                    QtCore.Qt.AlignCenter, tier[:3]
                )
            cumulative_x += zone_width
        
        painter.setOpacity(1.0)
        
        # Draw border
        painter.setPen(QtGui.QPen(QtGui.QColor("#333"), 2))
        painter.drawRect(x_offset, bar_y, bar_width, bar_height)
        
        # Draw marker
        marker_x = x_offset + (self.position / 100) * bar_width
        current_tier = self.get_tier_at_position(self.position)
        marker_color = self.TIER_COLORS.get(current_tier, "#fff")
        
        # Glow effect for result
        if self.result_tier:
            glow_color = self.TIER_COLORS.get(self.result_tier, "#fff")
            for i in range(3):
                glow_size = 10 + (3-i) * 3
                painter.setBrush(QtGui.QColor(glow_color))
                painter.setOpacity(0.3)
                painter.drawEllipse(
                    QtCore.QPointF(marker_x, bar_y + bar_height // 2),
                    glow_size, glow_size
                )
            painter.setOpacity(1.0)
        
        # Marker triangle
        painter.setBrush(QtGui.QColor(marker_color))
        painter.setPen(QtGui.QPen(QtGui.QColor("#fff"), 2))
        triangle = [
            QtCore.QPointF(marker_x, bar_y - 3),
            QtCore.QPointF(marker_x - 8, bar_y - 15),
            QtCore.QPointF(marker_x + 8, bar_y - 15)
        ]
        painter.drawPolygon(triangle)
        
        # Marker line
        painter.setPen(QtGui.QPen(QtGui.QColor(marker_color), 3))
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
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main container
        container = QtWidgets.QWidget()
        container.setStyleSheet("""
            QWidget {
                background: #1a1a2e;
                border: 3px solid #ffd700;
                border-radius: 12px;
            }
        """)
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setSpacing(12)
        container_layout.setContentsMargins(24, 16, 24, 16)
        
        # Main title
        self.main_title = QtWidgets.QLabel("🎰 Eye Protection Lottery 🎰")
        self.main_title.setAlignment(QtCore.Qt.AlignCenter)
        self.main_title.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #ffd700;"
        )
        container_layout.addWidget(self.main_title)
        
        # Stage 1: Tier Roll (what are you playing for?)
        self.stage1_frame = QtWidgets.QFrame()
        self.stage1_frame.setStyleSheet("""
            QFrame {
                background: #252540;
                border: 2px solid #444;
                border-radius: 8px;
            }
        """)
        stage1_layout = QtWidgets.QVBoxLayout(self.stage1_frame)
        stage1_layout.setContentsMargins(12, 8, 12, 8)
        
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
                border: 2px solid #333;
                border-radius: 8px;
            }
        """)
        stage2_layout = QtWidgets.QVBoxLayout(self.stage2_frame)
        stage2_layout.setContentsMargins(12, 8, 12, 8)
        
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
        self.final_result.setStyleSheet("color: #fff; font-size: 16px; font-weight: bold;")
        container_layout.addWidget(self.final_result)
        
        layout.addWidget(container)
    
    def _start_stage_1(self):
        """Start the tier roll animation (Stage 1)."""
        self.current_stage = 1
        self.stage1_frame.setStyleSheet("""
            QFrame {
                background: #252540;
                border: 2px solid #ffd700;
                border-radius: 8px;
            }
        """)
        self.stage1_title.setStyleSheet("color: #ffd700; font-size: 12px; font-weight: bold;")
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
                border: 2px solid #ffd700;
                border-radius: 8px;
            }
        """)
        self.stage2_title.setStyleSheet("color: #ffd700; font-size: 12px; font-weight: bold;")
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
        
        # Auto close after delay
        QtCore.QTimer.singleShot(2500, self._finish)
    
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
        self._tier_anim_duration = 9.0  # Longer for dramatic effect
        
        self._tier_anim_timer = QtCore.QTimer(self)
        self._tier_anim_timer.timeout.connect(self._tier_anim_tick)
        self._tier_anim_timer.start(16)
    
    def _tier_anim_tick(self):
        """Animation tick for tier stage."""
        tier_colors = {"Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3", 
                       "Epic": "#9c27b0", "Legendary": "#ff9800"}
        
        self._tier_anim_elapsed += 0.016
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
        
        # Update result label with current tier
        current_tier = self._tier_anim_slider.get_tier_at_position(pos)
        color = tier_colors.get(current_tier, "#aaa")
        self._tier_anim_result.setText(f"🎲 {pos:.1f}% → {current_tier}")
        self._tier_anim_result.setStyleSheet(f"color: {color}; font-size: 14px;")
        
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
        self._anim_duration = 8.0  # Doubled for more dramatic effect
        
        self._anim_timer = QtCore.QTimer(self)
        self._anim_timer.timeout.connect(self._anim_tick)
        self._anim_timer.start(16)
    
    def _anim_tick(self):
        """Animation tick for current stage."""
        self._anim_elapsed += 0.016
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
        
        # Update result label color during animation
        if pos < self._anim_threshold:
            self._anim_result.setStyleSheet("color: #4caf50; font-size: 14px;")
            self._anim_result.setText(f"🎲 {pos:.1f}%")
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
    
    def __init__(self, weights: dict, parent=None):
        """
        Args:
            weights: Dict mapping rarity -> weight (e.g., {"Common": 5, ...})
        """
        super().__init__(parent)
        self.weights = weights
        self.total = sum(weights.values())
        self.position = 0.0
        self.result_rarity = None
        self.setMinimumWidth(400)
        
        # Rarity colors
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
            
            color = self.rarity_colors.get(rarity, "#666")
            painter.setBrush(QtGui.QColor(color))
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
                painter.setPen(QtGui.QColor("#fff"))
                painter.setFont(QtGui.QFont("Arial", 7, QtGui.QFont.Bold))
                label_x = start_x + zone_width/2 - 12
                painter.drawText(int(label_x), bar_y + bar_height//2 + 4, rarity[:3].upper())
            
            # Draw separator line
            if i < len(rarity_order) - 1:
                painter.setPen(QtGui.QPen(QtGui.QColor("#1a1a2e"), 2))
                sep_x = start_x + zone_width
                painter.drawLine(int(sep_x), bar_y, int(sep_x), bar_y + bar_height)
            
            cumulative_pct += zone_pct
        
        # Draw 0% and 100% labels
        painter.setPen(QtGui.QColor("#888"))
        painter.setFont(QtGui.QFont("Arial", 8))
        painter.drawText(margin, bar_y + bar_height + 15, "0%")
        painter.drawText(w - margin - 25, bar_y + bar_height + 15, "100%")
        
        # Draw the sliding marker
        marker_x = margin + (self.position / 100.0) * (w - 2*margin)
        
        # Marker color based on current zone
        current_rarity = self.get_rarity_at_position(self.position)
        marker_color = self.rarity_colors.get(current_rarity, "#fff")
        
        # Glow effect if result
        if self.result_rarity:
            glow_color = self.rarity_colors.get(self.result_rarity, "#fff")
            for i in range(3):
                glow_size = 12 + (3-i) * 4
                painter.setBrush(QtGui.QColor(glow_color))
                painter.setOpacity(0.3)
                painter.drawEllipse(
                    QtCore.QPointF(marker_x, bar_y + bar_height // 2),
                    glow_size, glow_size
                )
            painter.setOpacity(1.0)
        
        # Draw marker (triangle)
        painter.setBrush(QtGui.QColor(marker_color))
        painter.setPen(QtGui.QPen(QtGui.QColor("#fff"), 2))
        
        triangle = QtGui.QPolygonF([
            QtCore.QPointF(marker_x, bar_y - 2),
            QtCore.QPointF(marker_x - 8, bar_y - 14),
            QtCore.QPointF(marker_x + 8, bar_y - 14),
        ])
        painter.drawPolygon(triangle)
        
        # Marker line
        painter.setPen(QtGui.QPen(QtGui.QColor(marker_color), 3))
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
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main container
        container = QtWidgets.QWidget()
        container.setStyleSheet("""
            QWidget {
                background: #1a1a2e;
                border: 3px solid #ffd700;
                border-radius: 12px;
            }
        """)
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setSpacing(12)
        container_layout.setContentsMargins(24, 16, 24, 16)
        
        # Header
        header = QtWidgets.QLabel("🎁 Priority Complete! Rolling for Lucky Gift... 🎁")
        header.setAlignment(QtCore.Qt.AlignCenter)
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffd700;")
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
                border: 2px solid #444;
                border-radius: 8px;
            }
        """)
        stage1_layout = QtWidgets.QVBoxLayout(self.stage1_frame)
        stage1_layout.setContentsMargins(12, 8, 12, 8)
        
        self.stage1_title = QtWidgets.QLabel(f"🎰 Stage 1: Lucky Roll ({self.win_chance*100:.0f}% chance)")
        self.stage1_title.setStyleSheet("color: #aaa; font-size: 12px; font-weight: bold;")
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
                border: 2px solid #333;
                border-radius: 8px;
            }
        """)
        stage2_layout = QtWidgets.QVBoxLayout(self.stage2_frame)
        stage2_layout.setContentsMargins(12, 8, 12, 8)
        
        self.stage2_title = QtWidgets.QLabel("✨ Stage 2: Rarity Roll")
        self.stage2_title.setStyleSheet("color: #666; font-size: 12px; font-weight: bold;")
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
        self.final_result.setStyleSheet("color: #fff; font-size: 14px;")
        container_layout.addWidget(self.final_result)
        
        layout.addWidget(container)
    
    def _start_stage_1(self):
        """Start the win/lose roll animation."""
        self.current_stage = 1
        self.stage1_frame.setStyleSheet("""
            QFrame {
                background: #252540;
                border: 2px solid #ffd700;
                border-radius: 8px;
            }
        """)
        self.stage1_title.setStyleSheet("color: #ffd700; font-size: 12px; font-weight: bold;")
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
                    border: 2px solid #ffd700;
                    border-radius: 8px;
                }
            """)
            self.stage2_title.setStyleSheet("color: #ffd700; font-size: 12px; font-weight: bold;")
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
            
            # Auto close
            QtCore.QTimer.singleShot(2500, self._finish)
    
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
        
        # Auto close
        QtCore.QTimer.singleShot(3000, self._finish)
    
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
        self._anim_duration = 9.0  # 2x slower for dramatic effect
        
        self._anim_timer = QtCore.QTimer(self)
        self._anim_timer.timeout.connect(self._anim_tick)
        self._anim_timer.start(16)
    
    def _anim_tick(self):
        """Animation tick."""
        self._anim_elapsed += 0.016
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
        
        # Update result label
        if self._anim_is_rarity:
            rarity = self._anim_slider.get_rarity_at_position(pos)
            rarity_colors = {
                "Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3",
                "Epic": "#9c27b0", "Legendary": "#ff9800"
            }
            color = rarity_colors.get(rarity, "#aaa")
            self._anim_result.setText(f"🎲 {pos:.1f}% → {rarity}")
            self._anim_result.setStyleSheet(f"color: {color}; font-size: 14px;")
        else:
            threshold = self.win_chance * 100
            if pos < threshold:
                self._anim_result.setStyleSheet("color: #4caf50; font-size: 14px;")
                self._anim_result.setText(f"🎲 {pos:.1f}% (IN THE WIN ZONE!)")
            else:
                self._anim_result.setStyleSheet("color: #f44336; font-size: 14px;")
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
    
    def __init__(self, result_rarity: str = "Rare", upgraded: bool = False, parent=None):
        """
        Args:
            result_rarity: The expected result rarity (center of distribution)
            upgraded: Whether tier upgrade is enabled (shifts window higher)
        """
        super().__init__(parent)
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
            color = self.TIER_COLORS.get(tier, "#666")
            start_x = margin + (cumulative_pct / 100.0) * (w - 2*margin)
            zone_width = (zone_pct / 100.0) * (w - 2*margin)
            
            painter.setBrush(QtGui.QColor(color))
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
                painter.setPen(QtGui.QColor("#fff"))
                painter.setFont(QtGui.QFont("Arial", 9, QtGui.QFont.Bold))
                label = tier[:4] if zone_width > 45 else tier[:3]
                label_rect = QtCore.QRectF(start_x, bar_y, zone_width, bar_height)
                painter.drawText(label_rect, QtCore.Qt.AlignCenter, label)
            
            # Separator
            if i < len(zones_to_draw) - 1:
                painter.setPen(QtGui.QPen(QtGui.QColor("#1a1a2e"), 2))
                sep_x = start_x + zone_width
                painter.drawLine(int(sep_x), bar_y, int(sep_x), bar_y + bar_height)
            
            cumulative_pct += zone_pct
        
        # Draw marker
        marker_x = margin + (self.position / 100.0) * (w - 2*margin)
        current_tier = self.get_tier_at_position(self.position)
        marker_color = self.TIER_COLORS.get(current_tier, "#aaa")
        
        # Glow if result set
        if self.result_tier:
            glow_color = self.TIER_COLORS.get(self.result_tier, "#aaa")
            for i in range(3):
                glow_size = 12 + (3-i) * 4
                painter.setBrush(QtGui.QColor(glow_color))
                painter.setOpacity(0.3)
                painter.drawEllipse(
                    QtCore.QPointF(marker_x, bar_y + bar_height // 2),
                    glow_size, glow_size
                )
            painter.setOpacity(1.0)
        
        # Triangle marker
        painter.setBrush(QtGui.QColor(marker_color))
        painter.setPen(QtGui.QPen(QtGui.QColor("#fff"), 2))
        
        triangle = QtGui.QPolygonF([
            QtCore.QPointF(marker_x, bar_y - 2),
            QtCore.QPointF(marker_x - 8, bar_y - 14),
            QtCore.QPointF(marker_x + 8, bar_y - 14),
        ])
        painter.drawPolygon(triangle)
        
        painter.setPen(QtGui.QPen(QtGui.QColor(marker_color), 3))
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
            
            painter.setBrush(QtGui.QColor(color))
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
                painter.setPen(QtGui.QColor("#fff"))
                painter.setFont(QtGui.QFont("Arial", 9, QtGui.QFont.Bold))
                # Use abbreviation for short zones
                if zone_width < 50:
                    label = rarity[:3]  # "Unc", "Rar", "Epi", "Leg"
                else:
                    label = rarity[:4]  # "Unco", "Rare", "Epic", "Lege"
                label_rect = QtCore.QRectF(start_x, bar_y, zone_width, bar_height)
                painter.drawText(label_rect, QtCore.Qt.AlignCenter, label)
            
            # Draw separator between different rarities
            if i < len(self.display_rarities) - 1:
                painter.setPen(QtGui.QPen(QtGui.QColor("#1a1a2e"), 2))
                sep_x = start_x + zone_width
                painter.drawLine(int(sep_x), bar_y, int(sep_x), bar_y + bar_height)
            
            cumulative_pct += zone_pct
        
        # Draw marker (still uses jump positions internally)
        marker_x = margin + (self.position / 100.0) * (w - 2*margin)
        current_jump = self.get_jump_at_position(self.position)
        marker_color = self.get_color_for_jump(current_jump)
        
        # Glow if result
        if self.result_jump:
            glow_color = self.get_color_for_jump(self.result_jump)
            for i in range(3):
                glow_size = 12 + (3-i) * 4
                painter.setBrush(QtGui.QColor(glow_color))
                painter.setOpacity(0.3)
                painter.drawEllipse(
                    QtCore.QPointF(marker_x, bar_y + bar_height // 2),
                    glow_size, glow_size
                )
            painter.setOpacity(1.0)
        
        # Triangle marker
        painter.setBrush(QtGui.QColor(marker_color))
        painter.setPen(QtGui.QPen(QtGui.QColor("#fff"), 2))
        
        triangle = QtGui.QPolygonF([
            QtCore.QPointF(marker_x, bar_y - 2),
            QtCore.QPointF(marker_x - 8, bar_y - 14),
            QtCore.QPointF(marker_x + 8, bar_y - 14),
        ])
        painter.drawPolygon(triangle)
        
        painter.setPen(QtGui.QPen(QtGui.QColor(marker_color), 3))
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
                 parent: Optional[QtWidgets.QWidget] = None):
        """
        Args:
            success_roll: The actual success roll (0.0-1.0)
            success_threshold: Success threshold (0.0-1.0). Roll < threshold = success.
            tier_upgrade_enabled: Whether +50 coin tier upgrade is active
            base_rarity: The RESULT rarity (center of distribution)
            parent: Parent widget
        """
        super().__init__(parent)
        self.success_roll = success_roll
        self.success_threshold = success_threshold
        self.is_success = success_roll < success_threshold
        self.tier_upgrade_enabled = tier_upgrade_enabled
        self.result_rarity = base_rarity  # This is the CENTER of distribution
        
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
        self.setWindowTitle("⚔️ Lucky Merge")
        self.setModal(True)
        self.setMinimumSize(440, 380)
        load_dialog_geometry(self, "MergeLotteryDialog", QtCore.QSize(540, 480))
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        container = QtWidgets.QWidget()
        container.setStyleSheet("""
            QWidget {
                background: #1a1a2e;
                border: 3px solid #ffd700;
                border-radius: 12px;
            }
        """)
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setSpacing(10)
        container_layout.setContentsMargins(24, 16, 24, 16)
        
        # Header
        header_text = "⚔️ Lucky Merge ⚔️"
        if self.tier_upgrade_enabled:
            header_text = "⚔️ Lucky Merge ⬆️ UPGRADED ⚔️"
        header = QtWidgets.QLabel(header_text)
        header.setAlignment(QtCore.Qt.AlignCenter)
        header.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {'#ff9800' if self.tier_upgrade_enabled else '#ffd700'};")
        container_layout.addWidget(header)
        
        # Stage 1: Tier Roll
        self.stage1_frame = QtWidgets.QFrame()
        self.stage1_frame.setStyleSheet("""
            QFrame { background: #252540; border: 2px solid #444; border-radius: 8px; }
        """)
        stage1_layout = QtWidgets.QVBoxLayout(self.stage1_frame)
        stage1_layout.setContentsMargins(12, 8, 12, 8)
        
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
            QFrame { background: #252540; border: 2px solid #333; border-radius: 8px; }
        """)
        stage2_layout = QtWidgets.QVBoxLayout(self.stage2_frame)
        stage2_layout.setContentsMargins(12, 8, 12, 8)
        
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
        
        # Final result
        self.final_result = QtWidgets.QLabel("")
        self.final_result.setAlignment(QtCore.Qt.AlignCenter)
        self.final_result.setWordWrap(True)
        self.final_result.setStyleSheet("color: #fff; font-size: 16px;")
        container_layout.addWidget(self.final_result)
        
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
    
    def _start_stage_1(self):
        """Start tier roll animation."""
        self.current_stage = 1
        self.stage1_frame.setStyleSheet("""
            QFrame { background: #252540; border: 2px solid #ffd700; border-radius: 8px; }
        """)
        self.stage1_title.setStyleSheet("color: #ffd700; font-size: 12px; font-weight: bold;")
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
        
        # Enable stage 2
        self.stage2_frame.setStyleSheet("""
            QFrame { background: #252540; border: 2px solid #ffd700; border-radius: 8px; }
        """)
        self.stage2_title.setStyleSheet("color: #ffd700; font-size: 12px; font-weight: bold;")
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
            QtCore.QTimer.singleShot(2500, self._finish)
        else:
            self.stage2_result.setText("💔 FAILED 💔")
            self.stage2_result.setStyleSheet("color: #f44336; font-size: 14px; font-weight: bold;")
            self.stage2_slider.set_result(False)
            
            self.final_result.setText(f"You almost had {self.rolled_tier}... All items were destroyed.")
            self.final_result.setStyleSheet("color: #f44336; font-size: 14px;")
            QtCore.QTimer.singleShot(2000, self._finish)
    
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
        self._anim_duration = 9.0
        
        self._tier_anim_timer = QtCore.QTimer(self)
        self._tier_anim_timer.timeout.connect(self._tier_anim_tick)
        self._tier_anim_timer.start(16)
    
    def _tier_anim_tick(self):
        """Tier animation tick."""
        self._anim_elapsed += 0.016
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
        
        # Show current tier
        tier = self._anim_slider.get_tier_at_position(pos)
        color = self.TIER_COLORS.get(tier, "#aaa")
        self._anim_result.setText(f"🎲 {pos:.1f}% → {tier}")
        self._anim_result.setStyleSheet(f"color: {color}; font-size: 14px;")
        
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
        self._success_duration = 9.0
        
        self._success_anim_timer = QtCore.QTimer(self)
        self._success_anim_timer.timeout.connect(self._success_anim_tick)
        self._success_anim_timer.start(16)
    
    def _success_anim_tick(self):
        """Success animation tick."""
        self._success_elapsed += 0.016
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
        if pos < threshold:
            self._success_result.setStyleSheet("color: #4caf50; font-size: 14px;")
            self._success_result.setText(f"🎲 {pos:.1f}% (SUCCESS ZONE!)")
        else:
            self._success_result.setStyleSheet("color: #f44336; font-size: 14px;")
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
            (success: bool, tier_jump: int) - tier_jump is 0 if failed
            Note: tier_jump is kept for backwards compatibility
        """
        return (self.is_success, self.tier_jump if self.is_success else 0)
    
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
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Bar dimensions
        bar_y = 20
        bar_height = 30
        bar_width = self.width() - 20
        x_offset = 10
        
        # Draw tier zones
        cumulative_x = x_offset
        for tier, width in zip(self.TIERS, self.zone_widths):
            if width <= 0:
                continue
            zone_width = (width / 100) * bar_width
            color = QtGui.QColor(self.TIER_COLORS[tier])
            painter.fillRect(
                int(cumulative_x), bar_y,
                int(zone_width), bar_height,
                color
            )
            # Zone label (only if wide enough)
            if zone_width > 35:
                painter.setPen(QtGui.QColor("#ffffff"))
                painter.setFont(QtGui.QFont("Arial", 8, QtGui.QFont.Bold))
                painter.drawText(
                    int(cumulative_x), bar_y,
                    int(zone_width), bar_height,
                    QtCore.Qt.AlignCenter, tier[:3]
                )
            cumulative_x += zone_width
        
        # Draw border
        painter.setPen(QtGui.QPen(QtGui.QColor("#333"), 2))
        painter.drawRect(x_offset, bar_y, bar_width, bar_height)
        
        # Draw marker
        marker_x = x_offset + (self.position / 100) * bar_width
        current_tier = self.get_tier_at_position(self.position)
        marker_color = self.TIER_COLORS.get(current_tier, "#fff")
        
        # Marker triangle
        painter.setBrush(QtGui.QColor(marker_color))
        painter.setPen(QtGui.QPen(QtGui.QColor("#000"), 1))
        triangle = [
            QtCore.QPointF(marker_x, bar_y - 5),
            QtCore.QPointF(marker_x - 6, bar_y - 15),
            QtCore.QPointF(marker_x + 6, bar_y - 15)
        ]
        painter.drawPolygon(triangle)
        
        # Marker line
        painter.setPen(QtGui.QPen(QtGui.QColor(marker_color), 3))
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
        win_color = QtGui.QColor("#4caf50")
        if self.result_won is True:
            win_color = QtGui.QColor("#66bb6a")  # Brighter on win
        painter.fillRect(x_offset, bar_y, int(win_width), bar_height, win_color)
        
        # Lose zone (red, right side)
        lose_width = (lose_pct / 100) * bar_width
        lose_color = QtGui.QColor("#f44336")
        if self.result_won is False:
            lose_color = QtGui.QColor("#ef5350")  # Brighter on lose
        painter.fillRect(int(x_offset + win_width), bar_y, int(lose_width), bar_height, lose_color)
        
        # Labels
        painter.setPen(QtGui.QColor("#ffffff"))
        painter.setFont(QtGui.QFont("Arial", 9, QtGui.QFont.Bold))
        if win_width > 30:
            painter.drawText(x_offset, bar_y, int(win_width), bar_height,
                           QtCore.Qt.AlignCenter, f"WIN {win_pct:.0f}%")
        if lose_width > 40:
            painter.drawText(int(x_offset + win_width), bar_y, int(lose_width), bar_height,
                           QtCore.Qt.AlignCenter, f"LOSE {lose_pct:.0f}%")
        
        # Border
        painter.setPen(QtGui.QPen(QtGui.QColor("#333"), 2))
        painter.drawRect(x_offset, bar_y, bar_width, bar_height)
        
        # Marker
        marker_x = x_offset + (self.position / 100) * bar_width
        in_win_zone = self.position < win_pct
        marker_color = "#4caf50" if in_win_zone else "#f44336"
        
        # Marker triangle
        painter.setBrush(QtGui.QColor(marker_color))
        painter.setPen(QtGui.QPen(QtGui.QColor("#000"), 1))
        triangle = [
            QtCore.QPointF(marker_x, bar_y - 5),
            QtCore.QPointF(marker_x - 6, bar_y - 15),
            QtCore.QPointF(marker_x + 6, bar_y - 15)
        ]
        painter.drawPolygon(triangle)
        
        # Marker line
        painter.setPen(QtGui.QPen(QtGui.QColor(marker_color), 3))
        painter.drawLine(int(marker_x), bar_y, int(marker_x), bar_y + bar_height)


class WaterLotteryDialog(QtWidgets.QDialog):
    """Two-stage lottery for Water/Hydration tracking.
    
    Stage 1: Tier Roll (rarity based on glass number - moving window)
        Uses [5, 15, 60, 15, 5] distribution centered on glass tier:
        - Glass 1: Common-centered [60+15+5=80% C, 15% U, 5% R, 0% E, 0% L]
        - Glass 2: Uncommon-centered [20% C, 60% U, 15% R, 5% E, 0% L]
        - Glass 3: Rare-centered [5% C, 15% U, 60% R, 15% E, 5% L]
        - Glass 4: Epic-centered [0% C, 5% U, 15% R, 60% E, 20% L]
        - Glass 5: Legendary-centered [0% C, 0% U, 5% R, 15% E, 80% L]
    
    Stage 2: Win/Lose Roll (progressive chance)
        - Starts at 1%, adds +1% per accumulated roll
        - Resets to 0 after a WIN
    
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
            lottery_attempts: Cumulative lottery attempts (determines win chance)
            story_id: Story theme for item generation
            parent: Parent widget
        """
        super().__init__(parent)
        self.glass_number = glass_number
        self.lottery_attempts = lottery_attempts
        self.story_id = story_id
        
        # Win chance: 1% + 1% per attempt, capped at 99%
        self.win_chance = min(0.99, (lottery_attempts + 1) / 100.0)
        
        # Pre-roll tier result
        self.tier_roll = random.random() * 100
        self.rolled_tier = self._determine_tier(self.tier_roll)
        
        # Pre-roll win/lose result  
        self.win_roll = random.random() * 100
        self.won = self.win_roll < (self.win_chance * 100)
        
        # Generate item if won
        self.won_item = None
        if self.won:
            try:
                from gamification import generate_item
                self.won_item = generate_item(rarity=self.rolled_tier, story_id=story_id)
            except (ImportError, Exception):
                # Fallback if gamification unavailable
                self.won_item = {"name": f"{self.rolled_tier} Item", "rarity": self.rolled_tier, "power": 10}
        
        # Attempt counter logic: +1 always, reset to 0 on win
        self.new_attempts = 0 if self.won else (lottery_attempts + 1)
        
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
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QtWidgets.QLabel(f"💧 Glass #{self.glass_number} Lottery")
        header.setFont(QtGui.QFont("Arial", 16, QtGui.QFont.Bold))
        header.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(header)
        
        # Attempt counter info
        attempt_info = QtWidgets.QLabel(f"🎰 Attempt #{self.lottery_attempts + 1} • Win chance: {self.win_chance*100:.0f}%")
        attempt_info.setFont(QtGui.QFont("Arial", 10))
        attempt_info.setAlignment(QtCore.Qt.AlignCenter)
        attempt_info.setStyleSheet("color: #888;")
        layout.addWidget(attempt_info)
        
        # Stage 1: Tier Roll
        self.stage1_frame = QtWidgets.QFrame()
        self.stage1_frame.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        stage1_layout = QtWidgets.QVBoxLayout(self.stage1_frame)
        
        self.stage1_title = QtWidgets.QLabel(f"✨ Stage 1: What Tier? (Glass #{self.glass_number})")
        self.stage1_title.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        stage1_layout.addWidget(self.stage1_title)
        
        self.tier_slider = WaterTierSliderWidget(self.glass_number)
        stage1_layout.addWidget(self.tier_slider)
        
        self.stage1_result = QtWidgets.QLabel("Rolling...")
        self.stage1_result.setFont(QtGui.QFont("Arial", 10))
        stage1_layout.addWidget(self.stage1_result)
        
        layout.addWidget(self.stage1_frame)
        
        # Stage 2: Win/Lose Roll (initially dimmed)
        self.stage2_frame = QtWidgets.QFrame()
        self.stage2_frame.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        self.stage2_frame.setEnabled(False)
        self.stage2_frame.setStyleSheet("QFrame { opacity: 0.4; }")
        stage2_layout = QtWidgets.QVBoxLayout(self.stage2_frame)
        
        self.stage2_title = QtWidgets.QLabel(f"🎲 Stage 2: Win or Lose? ({self.win_chance*100:.0f}% chance)")
        self.stage2_title.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        stage2_layout.addWidget(self.stage2_title)
        
        self.win_slider = WaterWinSliderWidget(self.win_chance)
        stage2_layout.addWidget(self.win_slider)
        
        self.stage2_result = QtWidgets.QLabel("Waiting...")
        self.stage2_result.setFont(QtGui.QFont("Arial", 10))
        stage2_layout.addWidget(self.stage2_result)
        
        layout.addWidget(self.stage2_frame)
        
        # Final result area
        self.final_result = QtWidgets.QLabel("")
        self.final_result.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
        self.final_result.setAlignment(QtCore.Qt.AlignCenter)
        self.final_result.hide()
        layout.addWidget(self.final_result)
        
        layout.addStretch()
    
    def _start_stage_1(self):
        """Start tier roll animation."""
        self.current_stage = 1
        self.stage1_frame.setStyleSheet("QFrame { border: 2px solid #ff9800; }")
        
        self._anim_start_time = None
        self._anim_duration = 9000
        self._anim_bounces = 5
        self._anim_target = self.tier_roll
        self._anim_slider = self.tier_slider
        self._anim_result = self.stage1_result
        self._anim_callback = self._finish_stage_1
        
        self._anim_timer = QtCore.QTimer(self)
        self._anim_timer.timeout.connect(self._animate_step)
        self._anim_timer.start(16)
    
    def _finish_stage_1(self):
        """Finish tier roll, show result and start stage 2."""
        tier_colors = {
            "Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3",
            "Epic": "#9c27b0", "Legendary": "#ff9800"
        }
        color = tier_colors.get(self.rolled_tier, "#fff")
        self.stage1_result.setText(f"<b style='color:{color};'>🎯 {self.rolled_tier.upper()}!</b>")
        self.stage1_result.setTextFormat(QtCore.Qt.RichText)
        
        self.stage1_frame.setStyleSheet("QFrame { border: 2px solid #4caf50; }")
        
        # Update stage 2 title
        self.stage2_title.setText(f"🎲 Stage 2: Claim your {self.rolled_tier}! ({self.win_chance*100:.0f}% chance)")
        
        # Enable and start stage 2
        QtCore.QTimer.singleShot(800, self._start_stage_2)
    
    def _start_stage_2(self):
        """Start win/lose roll animation."""
        self.current_stage = 2
        self.stage2_frame.setEnabled(True)
        self.stage2_frame.setStyleSheet("QFrame { border: 2px solid #ff9800; }")
        
        self._anim_start_time = None
        self._anim_duration = 8000
        self._anim_bounces = 4
        self._anim_target = self.win_roll
        self._anim_slider = self.win_slider
        self._anim_result = self.stage2_result
        self._anim_callback = self._finish_stage_2
        
        self._anim_timer = QtCore.QTimer(self)
        self._anim_timer.timeout.connect(self._animate_step)
        self._anim_timer.start(16)
    
    def _finish_stage_2(self):
        """Finish win/lose roll, show final result."""
        win_pct = self.win_chance * 100
        
        if self.won:
            self.stage2_result.setText(f"<b style='color:#4caf50;'>✅ WIN! ({self.win_roll:.1f}% < {win_pct:.0f}%)</b>")
            self.stage2_frame.setStyleSheet("QFrame { border: 2px solid #4caf50; }")
            
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
            self.stage2_result.setText(f"<b style='color:#f44336;'>❌ LOSE ({self.win_roll:.1f}% ≥ {win_pct:.0f}%)</b>")
            self.stage2_frame.setStyleSheet("QFrame { border: 2px solid #f44336; }")
            
            next_chance = min(99, (self.new_attempts + 1))
            self.final_result.setText(f"💔 Not this time... Next attempt: {next_chance}% chance!")
            self.final_result.setStyleSheet("color: #f44336;")
        
        self.stage2_result.setTextFormat(QtCore.Qt.RichText)
        self.final_result.show()
        
        # Auto-close after delay
        QtCore.QTimer.singleShot(2500, self._finish)
    
    def _animate_step(self):
        """Single animation frame using EaseOutQuart with bounces."""
        if self._anim_start_time is None:
            self._anim_start_time = time.time() * 1000
        
        elapsed = time.time() * 1000 - self._anim_start_time
        t = min(1.0, elapsed / self._anim_duration)
        
        # EaseOutQuart
        ease = 1 - pow(1 - t, 4)
        
        # Smooth bouncing effect (no random - use deterministic oscillation)
        if t < 1.0:
            bounce_amplitude = (1 - t) * 50
            bounce_freq = self._anim_bounces * 2 * 3.14159
            # Use math.sin directly for smooth oscillation
            bounce = bounce_amplitude * math.sin(t * bounce_freq)
            pos = self._anim_target + bounce * (1 - ease)
            pos = max(0, min(100, pos))
        else:
            pos = self._anim_target
        
        self._anim_slider.set_position(pos)
        
        # Update result text during animation
        if self.current_stage == 1:
            tier = self.tier_slider.get_tier_at_position(pos)
            tier_colors = {
                "Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3",
                "Epic": "#9c27b0", "Legendary": "#ff9800"
            }
            color = tier_colors.get(tier, "#fff")
            self._anim_result.setStyleSheet(f"color: {color}; font-size: 14px;")
            self._anim_result.setText(f"🎲 {pos:.1f}% → {tier}")
        else:
            win_pct = self.win_chance * 100
            if pos < win_pct:
                self._anim_result.setStyleSheet("color: #4caf50; font-size: 14px;")
                self._anim_result.setText(f"🎲 {pos:.1f}% (WIN ZONE!)")
            else:
                self._anim_result.setStyleSheet("color: #f44336; font-size: 14px;")
                self._anim_result.setText(f"🎲 {pos:.1f}%")
        
        if t >= 1.0:
            self._anim_timer.stop()
            self._anim_slider.set_position(self._anim_target)
            self._anim_callback()
    
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
        save_dialog_geometry(self, "WaterLotteryDialog")
        if hasattr(self, '_anim_timer'):
            self._anim_timer.stop()
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
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        bar_y = 20
        bar_height = 35
        bar_width = w - 20
        x_offset = 10
        
        # Draw tier zones
        cumulative_x = x_offset
        for tier, width in zip(self.TIERS, self.zone_widths):
            if width <= 0:
                continue
            zone_width = (width / 100) * bar_width
            color = QtGui.QColor(self.TIER_COLORS[tier])
            
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
            
            # Zone label with percentage
            if zone_width > 30:
                painter.setOpacity(1.0)
                painter.setPen(QtGui.QColor("#ffffff"))
                painter.setFont(QtGui.QFont("Arial", 9, QtGui.QFont.Bold))
                label = f"{tier[:3]}"
                painter.drawText(
                    int(cumulative_x), bar_y,
                    int(zone_width), bar_height,
                    QtCore.Qt.AlignCenter, label
                )
            cumulative_x += zone_width
        
        painter.setOpacity(1.0)
        
        # Draw border
        painter.setPen(QtGui.QPen(QtGui.QColor("#333"), 2))
        painter.drawRect(x_offset, bar_y, bar_width, bar_height)
        
        # Draw marker
        marker_x = x_offset + (self.position / 100) * bar_width
        current_tier = self.get_tier_at_position(self.position)
        marker_color = self.TIER_COLORS.get(current_tier, "#fff")
        
        # Glow effect for result
        if self.result_tier:
            glow_color = self.TIER_COLORS.get(self.result_tier, "#fff")
            for i in range(3):
                glow_size = 10 + (3-i) * 3
                painter.setBrush(QtGui.QColor(glow_color))
                painter.setOpacity(0.3)
                painter.drawEllipse(
                    QtCore.QPointF(marker_x, bar_y + bar_height // 2),
                    glow_size, glow_size
                )
            painter.setOpacity(1.0)
        
        # Marker triangle
        painter.setBrush(QtGui.QColor(marker_color))
        painter.setPen(QtGui.QPen(QtGui.QColor("#fff"), 2))
        triangle = [
            QtCore.QPointF(marker_x, bar_y - 3),
            QtCore.QPointF(marker_x - 8, bar_y - 15),
            QtCore.QPointF(marker_x + 8, bar_y - 15)
        ]
        painter.drawPolygon(triangle)
        
        # Marker line
        painter.setPen(QtGui.QPen(QtGui.QColor(marker_color), 3))
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
        self.setMinimumSize(400, 260)
        load_dialog_geometry(self, "FocusTimerLotteryDialog", QtCore.QSize(500, 320))
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        container = QtWidgets.QWidget()
        container.setStyleSheet("""
            QWidget {
                background: #1a1a2e;
                border: 3px solid #ffd700;
                border-radius: 12px;
            }
        """)
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setSpacing(12)
        container_layout.setContentsMargins(24, 16, 24, 16)
        
        # Header
        header = QtWidgets.QLabel("🎁 Session Reward! 🎁")
        header.setAlignment(QtCore.Qt.AlignCenter)
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffd700;")
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
            QFrame { background: #252540; border: 2px solid #ff9800; border-radius: 8px; }
        """)
        lottery_layout = QtWidgets.QVBoxLayout(lottery_frame)
        lottery_layout.setContentsMargins(12, 10, 12, 10)
        
        lottery_title = QtWidgets.QLabel("✨ Rolling for Item Tier...")
        lottery_title.setStyleSheet("color: #ff9800; font-size: 14px; font-weight: bold;")
        lottery_layout.addWidget(lottery_title)
        
        # Tier slider
        self.tier_slider = FocusTimerTierSliderWidget(self.session_minutes, self.streak_days)
        self.tier_slider.setFixedHeight(70)
        lottery_layout.addWidget(self.tier_slider)
        
        # Distribution legend
        dist_layout = QtWidgets.QHBoxLayout()
        colors = {"Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3", 
                  "Epic": "#9c27b0", "Legendary": "#ff9800"}
        for i, (tier, width) in enumerate(zip(self.tier_slider.TIERS, self.tier_slider.zone_widths)):
            if width > 0:
                color = colors.get(tier, "#888")
                label = QtWidgets.QLabel(f"<b style='color:{color};'>{tier[:3]}</b>:{width:.0f}%")
                label.setStyleSheet("font-size: 10px; color: #aaa;")
                dist_layout.addWidget(label)
        dist_layout.addStretch()
        lottery_layout.addLayout(dist_layout)
        
        self.lottery_result = QtWidgets.QLabel("🎲 Rolling...")
        self.lottery_result.setAlignment(QtCore.Qt.AlignCenter)
        self.lottery_result.setStyleSheet("color: #aaa; font-size: 14px;")
        lottery_layout.addWidget(self.lottery_result)
        
        container_layout.addWidget(lottery_frame)
        
        # Item reveal area (hidden until animation complete)
        self.item_frame = QtWidgets.QFrame()
        self.item_frame.setStyleSheet("""
            QFrame { background: #252540; border: 2px solid #333; border-radius: 8px; }
        """)
        self.item_frame.hide()
        item_layout = QtWidgets.QVBoxLayout(self.item_frame)
        item_layout.setContentsMargins(12, 10, 12, 10)
        
        self.item_label = QtWidgets.QLabel("")
        self.item_label.setAlignment(QtCore.Qt.AlignCenter)
        self.item_label.setWordWrap(True)
        self.item_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        item_layout.addWidget(self.item_label)
        
        container_layout.addWidget(self.item_frame)
        
        layout.addWidget(container)
    
    def _start_animation(self):
        """Start tier roll animation."""
        self._anim_start_time = None
        self._anim_duration = 8000  # 8 seconds
        self._anim_bounces = 5
        
        self._anim_timer = QtCore.QTimer(self)
        self._anim_timer.timeout.connect(self._animate_step)
        self._anim_timer.start(16)
    
    def _animate_step(self):
        """Animation frame."""
        if self._anim_start_time is None:
            self._anim_start_time = time.time() * 1000
        
        elapsed = time.time() * 1000 - self._anim_start_time
        t = min(1.0, elapsed / self._anim_duration)
        
        # EaseOutQuart
        ease = 1 - pow(1 - t, 4)
        
        # Smooth bouncing
        if t < 1.0:
            bounce_amplitude = (1 - t) * 40
            bounce_freq = self._anim_bounces * 2 * 3.14159
            bounce = bounce_amplitude * math.sin(t * bounce_freq)
            pos = self.tier_roll + bounce * (1 - ease)
            pos = max(0, min(100, pos))
        else:
            pos = self.tier_roll
        
        self.tier_slider.set_position(pos)
        
        # Update rolling text
        current_tier = self.tier_slider.get_tier_at_position(pos)
        tier_colors = {
            "Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3",
            "Epic": "#9c27b0", "Legendary": "#ff9800"
        }
        color = tier_colors.get(current_tier, "#fff")
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
        
        # Auto-close after delay
        QtCore.QTimer.singleShot(3000, self._finish)
    
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


# Backwards compatibility aliases
MergeSliderWidget = LotterySliderWidget
MergeRollAnimationDialog = LotteryRollDialog
