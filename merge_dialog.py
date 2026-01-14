"""
Lucky Merge Dialog - Industry-Standard UX
==========================================
Professional merge UI with visual feedback, animations, and comprehensive information display.
"""

import random
from datetime import datetime
from typing import Optional
from PySide6 import QtWidgets, QtCore, QtGui

try:
    from gamification import (
        calculate_merge_success_rate, 
        get_merge_result_rarity,
        perform_lucky_merge,
        ITEM_RARITIES,
        RARITY_POWER,
        RARITY_ORDER,
        RARITY_UPGRADE,
        COIN_COSTS,
        MERGE_BOOST_BONUS
    )
    GAMIFICATION_AVAILABLE = True
except ImportError:
    GAMIFICATION_AVAILABLE = False
    COIN_COSTS = {"merge_base": 50, "merge_boost": 50, "merge_tier_upgrade": 50, "merge_retry_bump": 50, "merge_claim": 100}
    MERGE_BOOST_BONUS = 0.25
    RARITY_ORDER = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
    RARITY_UPGRADE = {"Common": "Uncommon", "Uncommon": "Rare", "Rare": "Epic", "Epic": "Legendary", "Legendary": "Legendary"}


class MergeRollAnimationDialog(QtWidgets.QDialog):
    """Dramatic slider animation for merge roll reveal."""
    
    finished_signal = QtCore.Signal(bool)  # Emits success/failure when done
    
    def __init__(self, target_roll: float, success_threshold: float, 
                 parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.target_roll = target_roll * 100  # Convert to percentage
        self.success_threshold = success_threshold * 100
        self.current_position = 50.0  # Start in the middle
        self.is_success = target_roll < success_threshold
        
        # Industry Standard "Ping-Pong" Deceleration Animation
        # Slider bounces off walls, losing speed (quadratic friction),
        # eventually stopping exactly on the target.
        self.tick_interval = 16  # 60 FPS
        self.elapsed_time = 0.0
        self.animation_duration = 5.0  # Seconds
        
        # 1. Generate path segments
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
        
        # 2. Pre-calculate distance segments for O(1) interpolation
        self.segments = []
        self.total_distance = 0.0
        
        for i in range(len(self.path_points) - 1):
            start = self.path_points[i]
            end = self.path_points[i+1]
            dist = abs(end - start)
            
            # Skip zero-length segments if any
            if dist > 0.001:
                self.segments.append({
                    "start": start,
                    "end": end,
                    "dist": dist,
                    "cum_start": self.total_distance,
                    "cum_end": self.total_distance + dist
                })
                self.total_distance += dist
        
        self._setup_ui()
        self._start_animation()
    
    def _setup_ui(self):
        """Build the slider animation UI."""
        self.setWindowTitle("🎲 Rolling...")
        self.setModal(True)
        self.setFixedSize(500, 200)
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
        title = QtWidgets.QLabel("🎲 Rolling the Dice...")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffd700;")
        container_layout.addWidget(title)
        
        # The slider track widget (custom painted)
        self.slider_widget = MergeSliderWidget(self.success_threshold)
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
        # Starts fast, slows down significantly at the end
        eased_progress = 1.0 - (1.0 - t) ** 4
        
        # Calculate current distance traveled along the path
        current_travel = eased_progress * self.total_distance
        
        # Find which segment we are in
        # O(N) search is fine since N is small (< 10)
        found_pos = self.target_roll # Default fallback
        
        for seg in self.segments:
            if current_travel >= seg["cum_start"] and current_travel <= seg["cum_end"]:
                # Interpolate within this segment
                # local_t = how far into this segment (0.0 to 1.0)
                local_dist = current_travel - seg["cum_start"]
                local_progress = local_dist / seg["dist"]
                
                # Lerp: start + (end - start) * progress
                found_pos = seg["start"] + (seg["end"] - seg["start"]) * local_progress
                break
            elif current_travel > seg["cum_end"]:
                # Past this segment, keep checking
                continue
            else:
                # Before first segment (shouldn't happen with 0 start)
                break
        else:
            # If loop finishes without break, we are at the end
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
            
        # Update display
        # Ensure bounds 0-100 just in case
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
        speed = 4 * (1.0 - t) ** 3  # derivative of 1-(1-t)^4
        if speed > 2.0:
            self.status_label.setText("⚡ Spinning...")
        elif speed > 0.8:
            self.status_label.setText("🎯 Slowing down...")
        elif speed > 0.2:
            self.status_label.setText("🎲 Almost there...")
        else:
            self.status_label.setText("✨ Settling...")
        
        # Clamp to valid range (with bounce visualization logic if needed, but simple clamp is fine)
        self.current_position = max(0.0, min(100.0, self.current_position))
        
        # Update display
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
        
        # Update status based on elapsed time phases
        if t < 1.0:
            self.status_label.setText("⚡ Spinning...")
        elif t < 3.0:
            self.status_label.setText("🎯 Slowing down...")
        elif t < 4.0:
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
            self.status_label.setText("✨ SUCCESS! ✨")
            self.status_label.setStyleSheet("color: #4caf50; font-size: 16px; font-weight: bold;")
            self.slider_widget.set_result(True)
        else:
            self.roll_label.setStyleSheet("""
                font-size: 28px; font-weight: bold; color: #f44336;
                font-family: 'Consolas', 'Monaco', monospace;
            """)
            self.status_label.setText("💔 FAILED 💔")
            self.status_label.setStyleSheet("color: #f44336; font-size: 16px; font-weight: bold;")
            self.slider_widget.set_result(False)
        
        # Auto-close after showing result
        QtCore.QTimer.singleShot(1200, self.accept)


class MergeSliderWidget(QtWidgets.QWidget):
    """Custom widget that draws the probability bar with sliding marker."""
    
    def __init__(self, threshold: float, parent=None):
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


class ItemPreviewWidget(QtWidgets.QWidget):
    """Visual preview card for a single item in the merge."""
    
    def __init__(self, item: dict, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.item = item
        self.setFixedSize(140, 180)
        self._build_ui()
    
    def _build_ui(self):
        """Build the item preview card."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # Rarity color
        rarity = self.item.get("rarity", "Common")
        rarity_info = ITEM_RARITIES.get(rarity, ITEM_RARITIES["Common"])
        color = rarity_info.get("color", "#9e9e9e")
        
        # Item icon/emoji
        emoji = self._get_item_emoji()
        icon_label = QtWidgets.QLabel(emoji)
        icon_label.setAlignment(QtCore.Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            font-size: 48px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {color}, stop:1 {self._darken_color(color)});
            border-radius: 12px;
            padding: 15px;
            color: white;
        """)
        layout.addWidget(icon_label)
        
        # Item name
        name = self.item.get("name", "Unknown Item")
        name_label = QtWidgets.QLabel(name)
        name_label.setWordWrap(True)
        name_label.setAlignment(QtCore.Qt.AlignCenter)
        name_label.setStyleSheet(f"""
            font-weight: bold;
            font-size: 11px;
            color: {color};
        """)
        layout.addWidget(name_label)
        
        # Rarity stars
        stars = min(5, max(1, list(ITEM_RARITIES.keys()).index(rarity) + 1))
        stars_label = QtWidgets.QLabel("★" * stars)
        stars_label.setAlignment(QtCore.Qt.AlignCenter)
        stars_label.setStyleSheet(f"color: {color}; font-size: 14px;")
        layout.addWidget(stars_label)
        
        # Power
        power = self.item.get("power", 0)
        power_label = QtWidgets.QLabel(f"⚔ {power}")
        power_label.setAlignment(QtCore.Qt.AlignCenter)
        power_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(power_label)
        
        # Card border
        self.setStyleSheet(f"""
            ItemPreviewWidget {{
                background: white;
                border: 2px solid {color};
                border-radius: 8px;
            }}
        """)
    
    def _get_item_emoji(self) -> str:
        """Get emoji representation for the item."""
        slot = self.item.get("slot", "").lower()
        emoji_map = {
            "helmet": "⛑️",
            "chestplate": "🛡️",
            "gauntlets": "🧤",
            "boots": "👢",
            "shield": "🛡️",
            "weapon": "⚔️",
            "cloak": "🧥",
            "amulet": "📿"
        }
        return emoji_map.get(slot, "🎁")
    
    def _darken_color(self, hex_color: str, factor: float = 0.8) -> str:
        """Darken a hex color."""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"


class SuccessRateWidget(QtWidgets.QWidget):
    """Visual success rate display with progress bar and breakdown."""
    
    def __init__(self, rate: float, breakdown: dict, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.rate = rate
        self.breakdown = breakdown
        self.progress_bar = None
        self.breakdown_details = None  # Store reference for updates
        self._build_ui()
    
    def update_rate(self, new_rate: float, boost_active: bool = False):
        """Update the displayed success rate and breakdown."""
        self.rate = new_rate
        if self.progress_bar:
            self.progress_bar.setValue(int(self.rate * 100))
            
            # Format with boost indicator
            boost_text = " 🚀" if boost_active else ""
            self.progress_bar.setFormat(f"{self.rate * 100:.1f}%{boost_text}")
            
            # Update breakdown to show/hide boost
            if self.breakdown_details:
                breakdown_text = ""
                for component, value in self.breakdown.items():
                    breakdown_text += f"  • {component}: +{value}%\n"
                if boost_active:
                    breakdown_text += f"  • <b style='color:#64b5f6;'>🚀 Boost: +25%</b>\n"
                self.breakdown_details.setText(breakdown_text.strip())
            
            # Update color
            if self.rate >= 0.7:
                color = "#4caf50"  # Green
            elif self.rate >= 0.4:
                color = "#ff9800"  # Orange
            else:
                color = "#f44336"  # Red
            
            self.progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 2px solid #555;
                    border-radius: 8px;
                    text-align: center;
                    font-weight: bold;
                    font-size: 16px;
                    color: white;
                    background-color: #2a2a3a;
                    height: 32px;
                }}
                QProgressBar::chunk {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {color}, stop:1 {self._lighten_color(color)});
                    border-radius: 6px;
                }}
            """)
    
    def _build_ui(self):
        """Build the success rate visualization."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Header
        header = QtWidgets.QLabel("🎲 Success Probability")
        header.setStyleSheet("font-weight: bold; font-size: 14px; color: #fff;")
        layout.addWidget(header)
        
        # Progress bar
        progress_container = QtWidgets.QWidget()
        progress_layout = QtWidgets.QHBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(int(self.rate * 100))
        self.progress_bar.setFormat(f"{self.rate * 100:.1f}%")
        self.progress_bar.setTextVisible(True)
        
        # Color based on rate
        if self.rate >= 0.7:
            color = "#4caf50"  # Green
        elif self.rate >= 0.4:
            color = "#ff9800"  # Orange
        else:
            color = "#f44336"  # Red
        
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #555;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                font-size: 16px;
                color: white;
                background-color: #2a2a3a;
                height: 32px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color}, stop:1 {self._lighten_color(color)});
                border-radius: 6px;
            }}
        """)
        progress_layout.addWidget(self.progress_bar)
        layout.addWidget(progress_container)
        
        # Breakdown
        breakdown_label = QtWidgets.QLabel("<b>Calculation Breakdown:</b>")
        breakdown_label.setStyleSheet("color: #aaa; font-size: 11px;")
        layout.addWidget(breakdown_label)
        
        breakdown_text = ""
        for component, value in self.breakdown.items():
            breakdown_text += f"  • {component}: +{value}%\n"
        
        self.breakdown_details = QtWidgets.QLabel(breakdown_text.strip())
        self.breakdown_details.setStyleSheet("color: #888; font-size: 10px; padding-left: 10px;")
        self.breakdown_details.setTextFormat(QtCore.Qt.RichText)  # Enable rich text for boost styling
        layout.addWidget(self.breakdown_details)
    
    def _lighten_color(self, hex_color: str, factor: float = 1.2) -> str:
        """Lighten a hex color."""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        return f"#{r:02x}{g:02x}{b:02x}"


class ResultPreviewWidget(QtWidgets.QWidget):
    """Preview of potential merge result."""
    
    def __init__(self, result_rarity: str, items: list = None, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.result_rarity = result_rarity
        self.items = items if items is not None else []
        self._build_ui()
    
    def _build_ui(self):
        """Build the result preview."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        rarity_info = ITEM_RARITIES.get(self.result_rarity, ITEM_RARITIES["Common"])
        color = rarity_info.get("color", "#9e9e9e")
        power = RARITY_POWER.get(self.result_rarity, 10)
        
        # Result icon
        icon = QtWidgets.QLabel("✨")
        icon.setAlignment(QtCore.Qt.AlignCenter)
        icon.setStyleSheet(f"""
            font-size: 56px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {color}, stop:1 {self._darken_color(color)});
            border-radius: 16px;
            padding: 20px;
        """)
        layout.addWidget(icon)
        
        # Result title
        title = QtWidgets.QLabel("Possible Result")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 12px; color: #aaa;")
        layout.addWidget(title)
        
        # Rarity - show range since tier jump is random
        # Calculate minimum (lowest item tier) and maximum (with max tier jump + upgrade)
        min_rarity_idx = min([RARITY_ORDER.index(item.get("rarity", "Common")) for item in self.items if item])
        max_tier_jump = 4  # Maximum possible tier jump
        max_rarity_idx = min(min_rarity_idx + max_tier_jump, len(RARITY_ORDER) - 1)
        
        if hasattr(self, 'tier_upgrade_enabled') and self.tier_upgrade_enabled:
            max_rarity_idx = min(max_rarity_idx + 1, len(RARITY_ORDER) - 1)
        
        min_rarity = RARITY_ORDER[min_rarity_idx]
        max_rarity = RARITY_ORDER[max_rarity_idx]
        
        if min_rarity == max_rarity:
            rarity_text = f"<b>{max_rarity}</b> Item"
        else:
            rarity_text = f"<b>{min_rarity}</b> to <b>{max_rarity}</b>"
        
        rarity_label = QtWidgets.QLabel(rarity_text)
        rarity_label.setAlignment(QtCore.Qt.AlignCenter)
        rarity_label.setStyleSheet(f"color: {color}; font-size: 14px;")
        layout.addWidget(rarity_label)
        
        # Add explanation about tier jumps
        if min_rarity != max_rarity:
            tier_note = QtWidgets.QLabel("✨ Lucky tier jumps possible!")
            tier_note.setAlignment(QtCore.Qt.AlignCenter)
            tier_note.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
            layout.addWidget(tier_note)
        elif getattr(self, "all_legendary", False):
            reroll_note = QtWidgets.QLabel("Legendary reroll: result stays Legendary, slot/type may change.")
            reroll_note.setAlignment(QtCore.Qt.AlignCenter)
            reroll_note.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
            layout.addWidget(reroll_note)
        
        # Stars
        stars = min(5, max(1, list(ITEM_RARITIES.keys()).index(self.result_rarity) + 1))
        stars_label = QtWidgets.QLabel("★" * stars)
        stars_label.setAlignment(QtCore.Qt.AlignCenter)
        stars_label.setStyleSheet(f"color: {color}; font-size: 16px;")
        layout.addWidget(stars_label)
        
        # Power range
        power_label = QtWidgets.QLabel(f"⚔ ~{power}")
        power_label.setAlignment(QtCore.Qt.AlignCenter)
        power_label.setStyleSheet("color: #aaa; font-size: 12px;")
        layout.addWidget(power_label)
        
        self.setStyleSheet(f"""
            ResultPreviewWidget {{
                background: #2a2a3a;
                border: 2px dashed {color};
                border-radius: 12px;
            }}
        """)
    
    def _darken_color(self, hex_color: str, factor: float = 0.8) -> str:
        """Darken a hex color."""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"


class LuckyMergeDialog(QtWidgets.QDialog):
    """
    Industry-standard merge dialog with visual feedback and comprehensive UX.
    
    Features:
    - Visual item preview cards
    - Success rate progress bar with breakdown
    - Result preview
    - Risk/reward clarity
    - Animated execution feedback
    - Accessibility-compliant colors
    - Optional boost for +25% success rate
    """
    
    def __init__(self, items: list, luck: int, equipped: dict, 
                 parent: Optional[QtWidgets.QWidget] = None, player_coins: int = 0, coin_discount: int = 0):
        super().__init__(parent)
        self.items = items
        self.luck = luck
        self.equipped = equipped
        self.merge_result = None
        self.player_coins = player_coins
        self.boost_enabled = False
        self.tier_upgrade_enabled = False  # +50 coins to upgrade result tier
        self.coin_discount = coin_discount  # Discount percentage from equipped gear (0-90)
        self.all_legendary = all(i.get("rarity") == "Legendary" for i in items if i)
        
        # Import discount helper from gamification
        from gamification import apply_coin_discount
        
        # DEBUG: Check discount values
        print(f"[MERGE DEBUG] coin_discount passed: {coin_discount}%")
        print(f"[MERGE DEBUG] Original merge_base cost: {COIN_COSTS.get('merge_base', 50)}")
        
        # Use centralized costs from COIN_COSTS with discount applied
        self.merge_cost = apply_coin_discount(COIN_COSTS.get("merge_base", 50), coin_discount)
        self.boost_cost = apply_coin_discount(COIN_COSTS.get("merge_boost", 50), coin_discount)
        self.tier_upgrade_cost = apply_coin_discount(COIN_COSTS.get("merge_tier_upgrade", 50), coin_discount)
        self.retry_bump_cost = apply_coin_discount(COIN_COSTS.get("merge_retry_bump", 50), coin_discount)
        self.claim_cost = apply_coin_discount(COIN_COSTS.get("merge_claim", 100), coin_discount)  # Claim item on near-miss
        self.boost_bonus = MERGE_BOOST_BONUS  # +25% success rate
        
        print(f"[MERGE DEBUG] Discounted merge_cost: {self.merge_cost}")
        
        self.retry_cost_accumulated = 0
        self.near_miss_claimed = False
        self.salvage_requested = False
        
        # Calculate merge luck from ITEMS BEING MERGED (not equipped gear)
        # This encourages players to sacrifice items with merge_luck for better odds
        self.items_merge_luck = 0
        for item in items:
            if item and isinstance(item, dict):
                lucky_opts = item.get("lucky_options", {})
                if isinstance(lucky_opts, dict):
                    self.items_merge_luck += lucky_opts.get("merge_luck", 0)
        
        if GAMIFICATION_AVAILABLE:
            self.base_success_rate = calculate_merge_success_rate(
                items, items_merge_luck=self.items_merge_luck
            )
            self.success_rate = self.base_success_rate
            self.result_rarity = get_merge_result_rarity(items)
        else:
            self.base_success_rate = 0.5
            self.success_rate = 0.5
            self.result_rarity = "Rare"
        
        # Calculate upgraded result rarity (for tier upgrade option)
        try:
            result_idx = RARITY_ORDER.index(self.result_rarity)
            self.upgraded_rarity = RARITY_ORDER[min(result_idx + 1, len(RARITY_ORDER) - 1)]
        except (ValueError, IndexError):
            self.upgraded_rarity = self.result_rarity
        
        # Determine which items affect tier (non-Common only)
        self.tier_affecting_items = [i for i in items if i and i.get("rarity", "Common") != "Common"]
        self.fuel_items = [i for i in items if i and i.get("rarity", "Common") == "Common"]
        
        # Calculate breakdown (matches gamification.py constants)
        base_rate = 0.25  # MERGE_BASE_SUCCESS_RATE from gamification.py
        item_bonus = max(0, len(items) - 2) * 0.03  # +3% per item after first two
        items_merge_bonus = self.items_merge_luck / 100.0
        
        self.breakdown = {
            "Base Rate": int(base_rate * 100),
            f"Item Count ({len(items)} items)": int(item_bonus * 100),
        }
        if self.items_merge_luck > 0:
            self.breakdown["Items Merge Luck"] = self.items_merge_luck
        
        self.setWindowTitle("⚡ Lucky Merge")
        self.setMinimumSize(700, 500)
        self.setMaximumHeight(800)  # Limit max height
        self._build_ui()
    
    def _build_ui(self):
        """Build the complete merge dialog UI."""
        # Main layout for the dialog
        dialog_layout = QtWidgets.QVBoxLayout(self)
        dialog_layout.setSpacing(0)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area to handle overflow
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1e1e2e;
            }
            QScrollBar:vertical {
                background-color: #2d2d3d;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #555;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666;
            }
        """)
        
        # Content widget inside scroll area
        content_widget = QtWidgets.QWidget()
        content_widget.setStyleSheet("background-color: #1e1e2e;")
        main_layout = QtWidgets.QVBoxLayout(content_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(24, 24, 24, 24)
        
        # Top bar with coin balance
        top_bar = QtWidgets.QWidget()
        top_bar_layout = QtWidgets.QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        
        top_bar_layout.addStretch()
        
        # Coin balance display
        coin_icon = QtWidgets.QLabel("🪙")
        coin_icon.setStyleSheet("font-size: 20px;")
        top_bar_layout.addWidget(coin_icon)
        
        self.coin_balance_label = QtWidgets.QLabel(f"{self.player_coins:,}")
        self.coin_balance_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #ffd700;
            padding-left: 4px;
        """)
        top_bar_layout.addWidget(self.coin_balance_label)
        
        main_layout.addWidget(top_bar)
        
        # Header
        header = QtWidgets.QLabel("⚡ Lucky Merge")
        header.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #fff;
            padding: 10px;
        """)
        header.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(header)
        
        # Subtitle with cost info
        if self.coin_discount > 0:
            original_cost = COIN_COSTS.get("merge_base", 50)
            cost_text = f"Combining {len(self.items)} items • Cost: <span style='text-decoration: line-through; color: #666;'>{original_cost}</span> {self.merge_cost} coins 🪙 <span style='color: #8b5cf6;'>(✨ {self.coin_discount}% off = -{original_cost - self.merge_cost} saved!)</span>"
        else:
            cost_text = f"Combining {len(self.items)} items • Cost: {self.merge_cost} coins 🪙"
        subtitle = QtWidgets.QLabel(cost_text)
        subtitle.setStyleSheet("color: #aaa; font-size: 12px;")
        subtitle.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(subtitle)
        
        # Separator
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setStyleSheet("background-color: #555;")
        main_layout.addWidget(line)
        
        # Items preview section
        items_section = self._create_items_section()
        main_layout.addWidget(items_section)
        
        # Arrow
        arrow = QtWidgets.QLabel("⬇")
        arrow.setAlignment(QtCore.Qt.AlignCenter)
        arrow.setStyleSheet("font-size: 32px; color: #999;")
        main_layout.addWidget(arrow)
        
        # Result preview and success rate side by side
        middle_section = QtWidgets.QWidget()
        middle_layout = QtWidgets.QHBoxLayout(middle_section)
        middle_layout.setSpacing(20)
        
        # Success rate on left - store reference for boost updates
        self.success_widget = SuccessRateWidget(self.success_rate, self.breakdown)
        middle_layout.addWidget(self.success_widget, stretch=2)
        
        # Result preview on right
        result_widget = self._create_result_preview_with_info()
        middle_layout.addWidget(result_widget, stretch=1)
        
        main_layout.addWidget(middle_section)
        
        # Boost section (optional +25% for 50 coins)
        boost_section = self._create_boost_section()
        main_layout.addWidget(boost_section)
        
        # Tier upgrade section (optional +1 tier for 50 coins)
        tier_upgrade_section = self._create_tier_upgrade_section()
        main_layout.addWidget(tier_upgrade_section)
        
        # Warning section
        warning_box = self._create_warning_box()
        main_layout.addWidget(warning_box)
        
        # Spacer
        main_layout.addStretch()
        
        # Buttons
        button_box = self._create_button_box()
        main_layout.addWidget(button_box)
        
        # Add content widget to scroll area
        scroll_area.setWidget(content_widget)
        dialog_layout.addWidget(scroll_area)
        
        # Set dialog style
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
            }
            QPushButton {
                padding: 10px 24px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
        """)
    
    def _create_items_section(self) -> QtWidgets.QWidget:
        """Create the items preview section as a list."""
        section = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(section)
        layout.setSpacing(8)
        
        # Title
        title = QtWidgets.QLabel("📦 Items to Merge")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #fff;")
        layout.addWidget(title)
        
        # Items list (text-based for readability)
        for item in self.items:
            rarity = item.get("rarity", "Common")
            rarity_info = ITEM_RARITIES.get(rarity, ITEM_RARITIES.get("Common", {}))
            color = rarity_info.get("color", "#9e9e9e")
            name = item.get("name", "Unknown Item")
            power = item.get("power", 0)
            slot = item.get("slot", "Unknown")
            
            item_label = QtWidgets.QLabel(
                f"• <span style='color:{color};'><b>{name}</b></span> "
                f"<span style='color:#888;'>({slot}, +{power} power) [{rarity}]</span>"
            )
            item_label.setTextFormat(QtCore.Qt.RichText)
            item_label.setStyleSheet("font-size: 12px; padding: 4px 0;")
            layout.addWidget(item_label)
        
        return section
    
    def _create_warning_box(self) -> QtWidgets.QWidget:
        """Create the risk warning box."""
        warning = QtWidgets.QWidget()
        warning_layout = QtWidgets.QHBoxLayout(warning)
        warning_layout.setContentsMargins(16, 12, 16, 12)
        
        # Warning icon
        icon = QtWidgets.QLabel("⚠️")
        icon.setStyleSheet("font-size: 28px;")
        warning_layout.addWidget(icon)
        
        # Warning text
        if getattr(self, "all_legendary", False):
            warning_msg = (
                "<b>Legendary Reroll:</b> Failure destroys all Legendary items. "
                "Success creates a new Legendary (slot/type may change)."
            )
        else:
            warning_msg = (
                "<b>Warning:</b> Merge failure will destroy ALL selected items permanently. "
                "This action cannot be undone!"
            )

        text = QtWidgets.QLabel(warning_msg)
        text.setWordWrap(True)
        text.setStyleSheet("color: #ff6b6b; font-size: 12px;")
        warning_layout.addWidget(text, stretch=1)
        
        warning.setStyleSheet("""
            QWidget {
                background-color: #3a2020;
                border: 2px solid #f44336;
                border-radius: 8px;
            }
        """)
        
        return warning
    
    def _create_boost_section(self) -> QtWidgets.QWidget:
        """Create the boost option section."""
        boost_frame = QtWidgets.QWidget()
        boost_layout = QtWidgets.QHBoxLayout(boost_frame)
        boost_layout.setContentsMargins(16, 12, 16, 12)
        
        # Boost icon
        icon = QtWidgets.QLabel("🚀")
        icon.setStyleSheet("font-size: 24px;")
        boost_layout.addWidget(icon)
        
        # Boost checkbox
        self.boost_checkbox = QtWidgets.QCheckBox("Boost Success Rate (+25%)")
        self.boost_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                font-weight: bold;
                color: #64b5f6;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
        """)
        self.boost_checkbox.toggled.connect(self._on_boost_toggled)
        boost_layout.addWidget(self.boost_checkbox)
        
        # Cost label with discount info
        if self.coin_discount > 0:
            original_boost = COIN_COSTS.get("merge_boost", 50)
            savings = original_boost - self.boost_cost
            self.boost_cost_label = QtWidgets.QLabel(f"(+{self.boost_cost} 🪙) <span style='color: #8b5cf6;'>✨ Save {savings}</span>")
        else:
            self.boost_cost_label = QtWidgets.QLabel(f"(+{self.boost_cost} 🪙)")
        self.boost_cost_label.setStyleSheet("font-size: 13px; color: #aaa;")
        boost_layout.addWidget(self.boost_cost_label)
        
        boost_layout.addStretch()
        
        # Total cost display
        self.total_cost_label = QtWidgets.QLabel(f"Total: {self.merge_cost} 🪙")
        self.total_cost_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #fff;")
        boost_layout.addWidget(self.total_cost_label)
        
        # Check if player can afford boost
        can_afford_boost = self.player_coins >= (self.merge_cost + self.boost_cost)
        if not can_afford_boost:
            self.boost_checkbox.setEnabled(False)
            self.boost_checkbox.setToolTip(f"Need {self.merge_cost + self.boost_cost} coins (you have {self.player_coins})")
            self.boost_cost_label.setStyleSheet("font-size: 13px; color: #666;")
        
        boost_frame.setStyleSheet("""
            QWidget {
                background-color: #1a3a5c;
                border: 2px solid #2196f3;
                border-radius: 8px;
            }
        """)
        
        return boost_frame
    
    def _on_boost_toggled(self, checked: bool):
        """Handle boost checkbox toggle."""
        self.boost_enabled = checked
        
        # Update success rate
        if checked:
            self.success_rate = min(self.base_success_rate + 0.25, 1.0)  # Cap at 100%
        else:
            self.success_rate = self.base_success_rate
        
        # Update total cost label
        self._update_total_cost()
        
        # Update success rate display via success widget
        if hasattr(self, 'success_widget') and self.success_widget:
            self.success_widget.update_rate(self.success_rate, boost_active=checked)
    
    def _update_total_cost(self):
        """Update the total cost label based on selected options."""
        total = self.merge_cost
        if self.boost_enabled:
            total += self.boost_cost
        if self.tier_upgrade_enabled:
            total += self.tier_upgrade_cost
        self.total_cost_label.setText(f"Total: {total} 🪙")
    
    def _create_result_preview_with_info(self) -> QtWidgets.QWidget:
        """Create result preview with tier determination explanation."""
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        rarity_info = ITEM_RARITIES.get(self.result_rarity, ITEM_RARITIES.get("Common", {}))
        color = rarity_info.get("color", "#9e9e9e")
        power = RARITY_POWER.get(self.result_rarity, 10) if GAMIFICATION_AVAILABLE else 10
        
        # Result title
        title = QtWidgets.QLabel("Possible Result")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 12px; color: #aaa;")
        layout.addWidget(title)
        
        # Calculate rarity range (minimum from lowest item, maximum with tier jumps)
        min_rarity_idx = min([RARITY_ORDER.index(item.get("rarity", "Common")) for item in self.items if item])
        max_tier_jump = 4  # Maximum possible tier jump
        max_rarity_idx = min(min_rarity_idx + max_tier_jump, len(RARITY_ORDER) - 1)
        
        if self.tier_upgrade_enabled:
            max_rarity_idx = min(max_rarity_idx + 1, len(RARITY_ORDER) - 1)
        
        min_rarity = RARITY_ORDER[min_rarity_idx]
        max_rarity = RARITY_ORDER[max_rarity_idx]
        
        # Rarity with emoji - show range
        if min_rarity == max_rarity:
            rarity_text = f"<b style='color:{color};'>✨ {max_rarity}</b>"
        else:
            min_color = ITEM_RARITIES.get(min_rarity, {}).get("color", "#9e9e9e")
            max_color = ITEM_RARITIES.get(max_rarity, {}).get("color", "#9e9e9e")
            rarity_text = f"<b style='color:{min_color};'>✨ {min_rarity}</b> to <b style='color:{max_color};'>{max_rarity}</b>"
        
        self.result_rarity_label = QtWidgets.QLabel(rarity_text)
        self.result_rarity_label.setAlignment(QtCore.Qt.AlignCenter)
        self.result_rarity_label.setStyleSheet("font-size: 18px;")
        layout.addWidget(self.result_rarity_label)
        
        # Add tier jump note if range exists
        if min_rarity != max_rarity:
            tier_note = QtWidgets.QLabel("✨ Lucky tier jumps possible!")
            tier_note.setAlignment(QtCore.Qt.AlignCenter)
            tier_note.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
            layout.addWidget(tier_note)
        
        # Power range
        power_label = QtWidgets.QLabel(f"⚔ ~{power} Power")
        power_label.setAlignment(QtCore.Qt.AlignCenter)
        power_label.setStyleSheet("color: #aaa; font-size: 12px;")
        layout.addWidget(power_label)
        
        # Separator
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setStyleSheet("background-color: #444;")
        layout.addWidget(sep)
        
        # Tier determination explanation
        info_label = QtWidgets.QLabel()
        info_label.setWordWrap(True)
        info_label.setAlignment(QtCore.Qt.AlignCenter)
        
        if self.tier_affecting_items:
            lowest_rarity = min(
                (i.get("rarity", "Common") for i in self.tier_affecting_items),
                key=lambda r: RARITY_ORDER.index(r) if r in RARITY_ORDER else 0
            )
            info_text = f"<span style='color:#888; font-size:10px;'>"
            info_text += f"Tier based on lowest non-Common: <b style='color:{ITEM_RARITIES.get(lowest_rarity, {}).get('color', '#fff')};'>{lowest_rarity}</b><br>"
            info_text += f"→ Upgrades to {self.result_rarity}"
            if len(self.fuel_items) > 0:
                info_text += f"<br><span style='color:#4caf50;'>+{len(self.fuel_items)} Common items as fuel (no tier loss)</span>"
            info_text += "</span>"
        else:
            info_text = "<span style='color:#4caf50; font-size:10px;'>All Common items → Upgrades to Uncommon</span>"
        
        info_label.setText(info_text)
        layout.addWidget(info_label)
        
        container.setStyleSheet(f"""
            QWidget {{
                background: #2a2a3a;
                border: 2px dashed {color};
                border-radius: 12px;
            }}
        """)
        
        return container
    
    def _create_tier_upgrade_section(self) -> QtWidgets.QWidget:
        """Create the tier upgrade option section (+50 coins for +1 tier)."""
        frame = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Icon
        icon = QtWidgets.QLabel("⬆️")
        icon.setStyleSheet("font-size: 24px;")
        layout.addWidget(icon)
        
        # Checkbox
        upgraded_color = ITEM_RARITIES.get(self.upgraded_rarity, {}).get("color", "#fff")
        self.tier_upgrade_checkbox = QtWidgets.QCheckBox(
            f"Upgrade Result (+1 Tier → {self.upgraded_rarity})"
        )
        self.tier_upgrade_checkbox.setStyleSheet(f"""
            QCheckBox {{
                font-size: 14px;
                font-weight: bold;
                color: {upgraded_color};
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
            }}
        """)
        self.tier_upgrade_checkbox.toggled.connect(self._on_tier_upgrade_toggled)
        layout.addWidget(self.tier_upgrade_checkbox)
        
        # Cost label with discount info
        if self.coin_discount > 0:
            original_tier = COIN_COSTS.get("merge_tier_upgrade", 50)
            savings = original_tier - self.tier_upgrade_cost
            cost_label = QtWidgets.QLabel(f"(+{self.tier_upgrade_cost} 🪙) <span style='color: #8b5cf6;'>✨ Save {savings}</span>")
        else:
            cost_label = QtWidgets.QLabel(f"(+{self.tier_upgrade_cost} 🪙)")
        cost_label.setStyleSheet("font-size: 13px; color: #aaa;")
        layout.addWidget(cost_label)
        
        layout.addStretch()
        
        # Can't upgrade if already Legendary
        if self.result_rarity == "Legendary":
            self.tier_upgrade_checkbox.setEnabled(False)
            self.tier_upgrade_checkbox.setText("Already Legendary!")
            self.tier_upgrade_checkbox.setStyleSheet("color: #666; font-size: 14px;")
        elif self.player_coins < (self.merge_cost + self.tier_upgrade_cost):
            self.tier_upgrade_checkbox.setEnabled(False)
            self.tier_upgrade_checkbox.setToolTip(f"Need {self.merge_cost + self.tier_upgrade_cost} coins")
        
        frame.setStyleSheet("""
            QWidget {
                background-color: #3a2a1a;
                border: 2px solid #ff9800;
                border-radius: 8px;
            }
        """)
        
        return frame
    
    def _on_tier_upgrade_toggled(self, checked: bool):
        """Handle tier upgrade checkbox toggle."""
        self.tier_upgrade_enabled = checked
        self._update_total_cost()
        
        # Update the result preview label
        if hasattr(self, 'result_rarity_label'):
            if checked:
                color = ITEM_RARITIES.get(self.upgraded_rarity, {}).get("color", "#fff")
                self.result_rarity_label.setText(f"<b style='color:{color};'>✨ {self.upgraded_rarity} ⬆️</b>")
            else:
                color = ITEM_RARITIES.get(self.result_rarity, {}).get("color", "#fff")
                self.result_rarity_label.setText(f"<b style='color:{color};'>✨ {self.result_rarity}</b>")
        
        # Tier upgrade doesn't affect success rate - don't update the display
        # (The success rate display should only show boost_active based on self.boost_enabled)

    def _create_button_box(self) -> QtWidgets.QWidget:
        """Create the action button box."""
        button_box = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(button_box)
        layout.setSpacing(12)
        
        # Cancel button
        cancel_btn = QtWidgets.QPushButton("❌ Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        # Spacer
        layout.addStretch()
        
        # Merge button
        merge_btn = QtWidgets.QPushButton("⚡ Merge Items")
        if self.success_rate >= 0.7:
            bg_color = "#4caf50"
            hover_color = "#388e3c"
        elif self.success_rate >= 0.4:
            bg_color = "#ff9800"
            hover_color = "#f57c00"
        else:
            bg_color = "#f44336"
            hover_color = "#d32f2f"
        
        merge_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                padding: 12px 32px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """)
        merge_btn.clicked.connect(self.execute_merge)
        layout.addWidget(merge_btn)
        
        return button_box
    
    def execute_merge(self):
        """Execute the merge with dramatic roll animation."""
        if not GAMIFICATION_AVAILABLE:
            msg = QtWidgets.QMessageBox(self)
            msg.setWindowTitle("Feature Unavailable")
            msg.setText("Gamification features are not available.")
            msg.setIcon(QtWidgets.QMessageBox.NoIcon)
            msg.setOption(QtWidgets.QMessageBox.DontUseNativeDialog, True)
            msg.exec_()
            return
        
        # Disable all buttons during merge
        for button in self.findChildren(QtWidgets.QPushButton):
            button.setEnabled(False)
        
        # Perform merge with boost if enabled
        story_id = self.items[0].get("story_theme", "warrior") if self.items else "warrior"
        # Add 25% boost bonus (as percentage points) if boost is enabled
        boost_bonus = 25 if self.boost_enabled else 0
        # Use merge_luck from items being merged (sacrificed) + boost
        total_items_merge_luck = self.items_merge_luck + boost_bonus
        self.merge_result = perform_lucky_merge(
            self.items,
            story_id=story_id,
            items_merge_luck=total_items_merge_luck
        )
        
        # Apply tier upgrade if enabled and merge succeeded
        if self.merge_result.get("success") and self.tier_upgrade_enabled:
            result_item = self.merge_result.get("result_item", {})
            if result_item:
                current_rarity = result_item.get("rarity", "Common")
                try:
                    current_idx = RARITY_ORDER.index(current_rarity)
                    new_idx = min(current_idx + 1, len(RARITY_ORDER) - 1)
                    result_item["rarity"] = RARITY_ORDER[new_idx]
                    # Update power based on new rarity
                    result_item["power"] = RARITY_POWER.get(result_item["rarity"], result_item.get("power", 10))
                    self.merge_result["tier_upgraded"] = True
                except (ValueError, IndexError):
                    pass
        
        # Show dramatic roll animation
        roll_value = self.merge_result.get("roll", 0)
        threshold = self.merge_result.get("needed", 0.5)
        
        animation_dialog = MergeRollAnimationDialog(roll_value, threshold, self)
        animation_dialog.exec_()
        
        # Show result after animation
        self._show_result()
    
    def _show_processing(self):
        """Show processing/merging animation overlay."""
        # Disable all buttons
        for button in self.findChildren(QtWidgets.QPushButton):
            button.setEnabled(False)
        
        # Create overlay
        overlay = QtWidgets.QWidget(self)
        overlay.setObjectName("processingOverlay")
        overlay.setGeometry(self.rect())
        overlay.setStyleSheet("""
            QWidget#processingOverlay {
                background-color: rgba(0, 0, 0, 0.7);
            }
        """)
        
        # Add label
        layout = QtWidgets.QVBoxLayout(overlay)
        label = QtWidgets.QLabel("⚡ Merging...\n✨")
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: white;
        """)
        layout.addWidget(label)
        
        overlay.show()
    
    def _show_result(self):
        """Show merge result dialog."""
        # Hide processing overlay
        overlay = self.findChild(QtWidgets.QWidget, "processingOverlay")
        if overlay:
            overlay.hide()
        
        # Show result
        if self.merge_result["success"]:
            self._show_success_dialog()
            self.accept()
        else:
            self._show_failure_dialog()
            
            # If retry was requested, restart the merge sequence
            if getattr(self, "is_retrying", False):
                self.is_retrying = False # Reset flag
                # Small delay to let dialog close and UI refresh
                QtCore.QTimer.singleShot(100, self.execute_merge)
                return # Do NOT close the main dialog
        
        self.accept()
    
    def _show_success_dialog(self):
        """Show success result dialog with optional 'Push Your Luck' re-roll."""
        result_item = self.merge_result.get("result_item", {}) if self.merge_result else {}
        rarity = result_item.get("rarity", "Common")
        
        # Check if Push Your Luck is available (not Legendary)
        if rarity != "Legendary":
            choice = self._show_push_your_luck_dialog(result_item)
            if choice == "reroll":
                # Player wants to risk it for next tier
                self._execute_push_your_luck()
                return  # Don't close dialog yet
        
        # Show standard success message (either kept item or reached Legendary)
        self._show_final_success_message(result_item)
    
    def _show_push_your_luck_dialog(self, current_item: dict) -> str:
        """Show dialog offering to keep item or risk for next tier. Returns 'keep' or 'reroll'."""
        rarity = current_item.get("rarity", "Common")
        name = current_item.get("name", "Unknown Item")
        power = current_item.get("power", 0)
        slot = current_item.get("slot", "Unknown Slot")
        
        # Calculate next tier and success chance
        rarity_order = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
        current_idx = rarity_order.index(rarity) if rarity in rarity_order else 0
        next_rarity = rarity_order[min(current_idx + 1, len(rarity_order) - 1)]
        
        # Get current success rate and apply 0.80 multiplier for push your luck
        push_luck_multiplier = getattr(self, 'push_luck_multiplier', 1.0)
        new_multiplier = push_luck_multiplier * 0.80
        reroll_chance = self.success_rate * new_multiplier
        
        rarity_color = ITEM_RARITIES.get(rarity, {}).get("color", "#9e9e9e")
        next_color = ITEM_RARITIES.get(next_rarity, {}).get("color", "#fff")
        
        # Create custom dialog
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("🎉 SUCCESS - Push Your Luck?")
        dialog.setModal(True)
        dialog.setMinimumWidth(500)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        layout.setSpacing(16)
        
        # Success header
        header = QtWidgets.QLabel("🎉 <b>MERGE SUCCESS!</b> 🎉")
        header.setAlignment(QtCore.Qt.AlignCenter)
        header.setStyleSheet("font-size: 18px; color: #4caf50; padding: 10px;")
        layout.addWidget(header)
        
        # Current item display
        current_box = QtWidgets.QGroupBox("✅ You Won:")
        current_layout = QtWidgets.QVBoxLayout(current_box)
        current_lbl = QtWidgets.QLabel(
            f"<p style='text-align:center;'>"
            f"<span style='font-size:16px; font-weight:bold;'>{name}</span><br>"
            f"<span style='color:{rarity_color}; font-size:14px;'>{rarity}</span> • "
            f"<span style='color:#aaa;'>⚔ {power} Power</span><br>"
            f"<span style='color:#8bc34a;'>Slot: {slot}</span>"
            f"</p>"
        )
        current_lbl.setTextFormat(QtCore.Qt.RichText)
        current_layout.addWidget(current_lbl)
        current_box.setStyleSheet(f"QGroupBox {{ background: #2a3a2a; border: 2px solid {rarity_color}; border-radius: 8px; padding: 12px; }}")
        layout.addWidget(current_box)
        
        # Separator
        sep = QtWidgets.QLabel("⬇️ <b>OR RISK IT ALL FOR...</b> ⬇️")
        sep.setAlignment(QtCore.Qt.AlignCenter)
        sep.setStyleSheet("font-size: 13px; color: #ff9800; padding: 8px;")
        layout.addWidget(sep)
        
        # Next tier preview
        next_box = QtWidgets.QGroupBox("🎲 Gamble for Higher Tier:")
        next_layout = QtWidgets.QVBoxLayout(next_box)
        next_lbl = QtWidgets.QLabel(
            f"<p style='text-align:center;'>"
            f"<span style='color:{next_color}; font-size:16px; font-weight:bold;'>{next_rarity}</span><br>"
            f"<span style='color:#aaa; font-size:12px;'>Success Chance: <b>{reroll_chance*100:.1f}%</b></span><br>"
            f"<span style='color:#f44336; font-size:11px;'>⚠️ Lose everything if you fail!</span>"
            f"</p>"
        )
        next_lbl.setTextFormat(QtCore.Qt.RichText)
        next_layout.addWidget(next_lbl)
        next_box.setStyleSheet(f"QGroupBox {{ background: #3a2a1a; border: 2px dashed {next_color}; border-radius: 8px; padding: 12px; }}")
        layout.addWidget(next_box)
        
        # Warning
        warning = QtWidgets.QLabel("⚠️ Each re-roll reduces success chance by 20% (×0.80)")
        warning.setAlignment(QtCore.Qt.AlignCenter)
        warning.setStyleSheet("font-size: 10px; color: #d32f2f; font-style: italic;")
        layout.addWidget(warning)
        
        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        
        keep_btn = QtWidgets.QPushButton("✅ Keep This Item")
        keep_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #388e3c; }
        """)
        keep_btn.clicked.connect(lambda: dialog.done(0))
        
        reroll_btn = QtWidgets.QPushButton(f"🎲 Risk for {next_rarity}!")
        reroll_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #f57c00; }
        """)
        reroll_btn.clicked.connect(lambda: dialog.done(1))
        
        btn_layout.addWidget(keep_btn)
        btn_layout.addWidget(reroll_btn)
        layout.addLayout(btn_layout)
        
        dialog.setStyleSheet("QDialog { background-color: #1e1e2e; }")
        
        result = dialog.exec_()
        return "reroll" if result == 1 else "keep"
    
    def _execute_push_your_luck(self):
        """Execute the push-your-luck re-roll with animation."""
        import random
        
        # Apply 0.80 multiplier to current success rate
        if not hasattr(self, 'push_luck_multiplier'):
            self.push_luck_multiplier = 1.0
        self.push_luck_multiplier *= 0.80
        
        adjusted_rate = self.success_rate * self.push_luck_multiplier
        roll = random.random()
        
        # Show dramatic roll animation
        animation_dialog = MergeRollAnimationDialog(roll, adjusted_rate, self)
        animation_dialog.exec_()
        
        current_item = self.merge_result.get("result_item", {})
        rarity = current_item.get("rarity", "Common")
        rarity_order = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
        current_idx = rarity_order.index(rarity) if rarity in rarity_order else 0
        next_rarity = rarity_order[min(current_idx + 1, len(rarity_order) - 1)]
        
        if roll < adjusted_rate:
            # SUCCESS! Upgrade to next tier
            from gamification import generate_item
            story_id = current_item.get("story_id", "warrior")
            new_item = generate_item(rarity=next_rarity, story_id=story_id)
            
            # Preserve some attributes from original
            if current_item.get("lucky_options"):
                new_item["lucky_options"] = current_item["lucky_options"]
            
            # Update merge result
            self.merge_result["result_item"] = new_item
            self.merge_result["success"] = True
            
            # Show success and offer another re-roll if not Legendary
            self._show_success_dialog()
        else:
            # FAILURE! Lose everything
            self.merge_result["success"] = False
            self.merge_result["push_luck_failed"] = True
            self.merge_result["roll"] = roll
            self.merge_result["needed"] = adjusted_rate
            
            # Show failure message
            self._show_push_luck_failure_dialog()
            self.accept()  # Close main dialog
    
    def _show_push_luck_failure_dialog(self):
        """Show failure message for push-your-luck."""
        roll = self.merge_result.get("roll", 0)
        needed = self.merge_result.get("needed", 0)
        
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("💥 GAMBLE FAILED!")
        msg.setIcon(QtWidgets.QMessageBox.NoIcon)
        
        text = f"""
        <div style='text-align: center;'>
            <h2 style='color: #f44336;'>💥 You Lost Everything! 💥</h2>
            <p style='color: #aaa;'>You rolled <b>{roll*100:.1f}%</b> (needed &lt; {needed*100:.1f}%)</p>
            <hr>
            <p style='color: #ff9800; font-size: 13px;'>
                ⚠️ The gamble didn't pay off this time.<br>
                All items have been lost.
            </p>
        </div>
        """
        
        msg.setText(text)
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.setStyleSheet("""
            QMessageBox { background-color: #2e1e1e; }
            QLabel { color: #fff; font-size: 13px; }
            QPushButton {
                background-color: #757575;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
            }
        """)
        msg.exec_()
    
    def _show_final_success_message(self, result_item: dict):
        """Show final success message (no more re-roll options)."""
        rarity = result_item.get("rarity", "Common")
        name = result_item.get("name", "Unknown Item")
        power = result_item.get("power", 0)
        slot = result_item.get("slot", "Unknown Slot")
        roll_raw = self.merge_result.get("roll", 0) if self.merge_result else 0
        needed_raw = self.merge_result.get("needed", 0) if self.merge_result else 0
        
        rarity_color = ITEM_RARITIES.get(rarity, {}).get("color", "#9e9e9e")
        
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("🎉 MERGE SUCCESS!")
        msg.setIcon(QtWidgets.QMessageBox.NoIcon)
        
        # Build breakdown text
        breakdown_parts = []
        if self.items_merge_luck > 0:
            breakdown_parts.append(f"+{self.items_merge_luck}% from items")
        if self.boost_enabled:
            breakdown_parts.append("+25% boost")
        breakdown_text = f" ({', '.join(breakdown_parts)})" if breakdown_parts else ""
        
        tier_upgrade_text = ""
        if self.merge_result.get("tier_upgraded"):
            tier_upgrade_text = "<p style='color: #ff9800;'>⬆️ <b>Tier Upgraded!</b> (+50 🪙)</p>"
        
        text = f"""
        <div style='text-align: center;'>
            <h2 style='color: {rarity_color};'>✨ Success! ✨</h2>
            <p style='color: #aaa;'><b>Roll:</b> {roll_raw*100:.1f}% (needed &lt; {needed_raw*100:.1f}%{breakdown_text})</p>
            {tier_upgrade_text}
            <hr>
            <p style='font-size: 16px; color: #fff;'><b>{name}</b></p>
            <p style='color: {rarity_color};'><b>{rarity}</b> • ⚔ Power: {power}</p>
            <p style='color: #8bc34a;'>Slot: {slot}</p>
        </div>
        """
        
        if result_item.get("lucky_options"):
            from gamification import format_lucky_options
            try:
                lucky_text = format_lucky_options(result_item["lucky_options"])
                if lucky_text:
                    text += f"<p style='color: #ffd700;'>✨ <b>Lucky Options:</b> {lucky_text}</p>"
            except Exception:
                pass
        
        msg.setText(text)
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.setStyleSheet(f"""
            QMessageBox {{ background-color: #1e2e1e; }}
            QLabel {{ color: #fff; font-size: 13px; }}
            QPushButton {{
                background-color: #4caf50;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }}
        """)
        msg.exec_()
    
    def _show_failure_dialog(self):
        """Show failure result dialog with retry, claim, and salvage options."""
        roll_raw = self.merge_result.get("roll", 0) if self.merge_result else 0
        needed_raw = self.merge_result.get("needed", 0) if self.merge_result else 0
        
        # Calculate how close the roll was
        margin = roll_raw - needed_raw  # positive = failed by this much
        is_near_miss = margin <= 0.05  # Within 5% of success
        
        # Calculate remaining coins after merge cost will be deducted
        # (merge cost is deducted AFTER dialog closes, so account for it here)
        total_merge_cost = self.merge_cost
        if self.boost_enabled:
            total_merge_cost += self.boost_cost
        if self.tier_upgrade_enabled:
            total_merge_cost += self.tier_upgrade_cost
            
        # Add accumulated retry costs
        total_merge_cost += self.retry_cost_accumulated
            
        remaining_coins = self.player_coins - total_merge_cost
        
        can_afford_retry = remaining_coins >= self.retry_bump_cost
        can_afford_claim = remaining_coins >= self.claim_cost

        # Salvage option - save one random item (discounted)
        salvage_cost = apply_coin_discount(COIN_COSTS.get("merge_salvage", 50), self.coin_discount)
        can_afford_salvage = remaining_coins >= salvage_cost
        
        # Check if retry would help
        new_needed = min(needed_raw + 0.05, 1.0)  # +5% boost
        would_succeed_with_retry = roll_raw < new_needed
        
        # Store result for claim action
        self.near_miss_claimed = False
        self.salvage_requested = False
        
        msg = QtWidgets.QDialog(self)
        msg.setWindowTitle("💔 Merge Failed")
        msg.setMinimumWidth(450)
        
        layout = QtWidgets.QVBoxLayout(msg)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Header
        header = QtWidgets.QLabel("<h2 style='color: #f44336;'>💔 Failed 💔</h2>")
        header.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(header)
        
        # Roll info
        roll_info = QtWidgets.QLabel(
            f"<p style='color: #aaa;'><b>Roll:</b> {roll_raw*100:.1f}% (needed &lt; {needed_raw*100:.1f}%)</p>"
            f"<p style='color: #888;'>Missed by: {margin*100:.1f}%</p>"
        )
        roll_info.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(roll_info)
        
        # Near-miss options (only if within 5%)
        if is_near_miss:
            options_frame = QtWidgets.QWidget()
            options_frame.setStyleSheet("""
                QWidget {
                    background-color: #3a3a1a;
                    border: 2px solid #ffeb3b;
                    border-radius: 8px;
                    padding: 12px;
                }
            """)
            options_layout = QtWidgets.QVBoxLayout(options_frame)
            options_layout.setSpacing(12)
            
            # Header for near-miss options
            near_miss_header = QtWidgets.QLabel(
                "<p style='color: #ffeb3b; font-size: 14px;'><b>⚡ SO CLOSE! Recovery Options:</b></p>"
            )
            near_miss_header.setAlignment(QtCore.Qt.AlignCenter)
            options_layout.addWidget(near_miss_header)
            
            # Option buttons layout
            btn_layout = QtWidgets.QHBoxLayout()
            btn_layout.setSpacing(12)
            
            # Retry button (50 coins to re-roll)
            retry_text = f"🎲 Retry\n{self.retry_bump_cost} 🪙"
            if self.coin_discount > 0:
                original_retry = COIN_COSTS.get("merge_retry_bump", 50)
                savings = original_retry - self.retry_bump_cost
                retry_text = f"🎲 Retry\n{self.retry_bump_cost} 🪙 ✨-{savings}"
            retry_btn = QtWidgets.QPushButton(retry_text)
            retry_btn.setMinimumHeight(60)
            if can_afford_retry:
                retry_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ff9800;
                        color: white;
                        padding: 8px 16px;
                        border-radius: 6px;
                        font-weight: bold;
                        font-size: 12px;
                    }
                    QPushButton:hover { background-color: #ffa726; }
                """)
                retry_btn.setToolTip("Pay to re-roll the merge")
            else:
                retry_btn.setEnabled(False)
                retry_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #555;
                        color: #888;
                        padding: 8px 16px;
                        border-radius: 6px;
                        font-size: 12px;
                    }
                """)
                retry_btn.setToolTip("Not enough coins")
            btn_layout.addWidget(retry_btn)
            
            # Claim button (+100 coins to get item directly)
            claim_text = f"✨ Claim Item\n{self.claim_cost} 🪙"
            if self.coin_discount > 0:
                original_claim = COIN_COSTS.get("merge_claim", 100)
                savings = original_claim - self.claim_cost
                claim_text = f"✨ Claim Item\n{self.claim_cost} 🪙 ✨-{savings}"
            claim_btn = QtWidgets.QPushButton(claim_text)
            claim_btn.setMinimumHeight(60)
            if can_afford_claim:
                claim_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #9c27b0;
                        color: white;
                        padding: 8px 16px;
                        border-radius: 6px;
                        font-weight: bold;
                        font-size: 12px;
                    }
                    QPushButton:hover { background-color: #ab47bc; }
                """)
                claim_btn.setToolTip("Pay to claim the merged item anyway!")
            else:
                claim_btn.setEnabled(False)
                claim_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #555;
                        color: #888;
                        padding: 8px 16px;
                        border-radius: 6px;
                        font-size: 12px;
                    }
                """)
                claim_btn.setToolTip("Not enough coins")
            btn_layout.addWidget(claim_btn)
            
            options_layout.addLayout(btn_layout)
            
            # Info text
            info_text = QtWidgets.QLabel(
                "<p style='color: #888; font-size: 10px;'>Retry: Re-roll the merge | Claim: Get the item directly</p>"
            )
            info_text.setAlignment(QtCore.Qt.AlignCenter)
            options_layout.addWidget(info_text)
            
            layout.addWidget(options_frame)
            
            # Connect buttons
            def on_claim():
                self.near_miss_claimed = True
                msg.accept()
            
            def on_retry():
                self.retry_cost_accumulated += self.retry_bump_cost
                self.is_retrying = True
                msg.reject()
            
            claim_btn.clicked.connect(on_claim)
            retry_btn.clicked.connect(on_retry)
        
        # Loss info
        loss_label = QtWidgets.QLabel(
            f"<p style='color: #ff6b6b;'><b>{len(self.items)} items lost forever.</b></p>"
        )
        loss_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(loss_label)
        
        # Salvage option - always available on failure
        salvage_frame = QtWidgets.QWidget()
        salvage_frame.setStyleSheet("""
            QWidget {
                background-color: #1a2e1a;
                border: 2px solid #4caf50;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        salvage_layout = QtWidgets.QVBoxLayout(salvage_frame)
        salvage_layout.setSpacing(8)
        
        salvage_header = QtWidgets.QLabel(
            "<p style='color: #4caf50; font-size: 12px;'><b>🛡️ Salvage Option:</b></p>"
        )
        salvage_header.setAlignment(QtCore.Qt.AlignCenter)
        salvage_layout.addWidget(salvage_header)
        
        salvage_btn = QtWidgets.QPushButton(f"🎁 Save Random Item ({salvage_cost} 🪙)")
        salvage_btn.setMinimumHeight(40)
        if can_afford_salvage and len(self.items) > 0:
            salvage_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4caf50;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover { background-color: #66bb6a; }
            """)
            salvage_btn.setToolTip("Save one random item from the merge")
        else:
            salvage_btn.setEnabled(False)
            salvage_btn.setStyleSheet("""
                QPushButton {
                    background-color: #555;
                    color: #888;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-size: 12px;
                }
            """)
            salvage_btn.setToolTip("Not enough coins" if not can_afford_salvage else "No items to salvage")
        
        def on_salvage():
            self.salvage_requested = True
            msg.accept()
        
        salvage_btn.clicked.connect(on_salvage)
        salvage_layout.addWidget(salvage_btn)
        
        salvage_info = QtWidgets.QLabel(
            "<p style='color: #888; font-size: 10px;'>One random item from the merge will be returned to your inventory</p>"
        )
        salvage_info.setAlignment(QtCore.Qt.AlignCenter)
        salvage_layout.addWidget(salvage_info)
        
        layout.addWidget(salvage_frame)
        
        # Accept Loss button
        ok_btn = QtWidgets.QPushButton("😢 Accept Loss")
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 10px 24px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #e53935; }
        """)
        ok_btn.clicked.connect(msg.accept)
        layout.addWidget(ok_btn)
        
        msg.setStyleSheet("background-color: #2e1e1e;")
        result = msg.exec_()
        
        # Handle salvage action first (if requested)
        if self.salvage_requested and can_afford_salvage and len(self.items) > 0:
            # Deduct coins
            self.player_coins -= salvage_cost
            # Pick a random item to save
            import random
            saved_item = random.choice(self.items)
            # Mark in merge_result that we salvaged one item
            self.merge_result["salvaged_item"] = saved_item
            self.merge_result["salvage_cost"] = salvage_cost
            # Show confirmation
            item_name = saved_item.get("name", "Unknown")
            item_rarity = saved_item.get("rarity", "Common")
            msg = QtWidgets.QMessageBox(self)
            msg.setWindowTitle("🎁 Item Salvaged!")
            msg.setText(
                f"<b style='color: #4caf50;'>{item_name}</b> ({item_rarity}) has been saved!<br><br>"
                f"It will be returned to your inventory."
            )
            msg.setIcon(QtWidgets.QMessageBox.NoIcon)
            msg.setOption(QtWidgets.QMessageBox.DontUseNativeDialog, True)
            msg.exec_()
            return
        
        # Handle claim action
        if self.near_miss_claimed and can_afford_claim:
            # Deduct coins and generate the item
            self.player_coins -= self.claim_cost
            # Generate the item that would have been created
            from gamification import generate_item
            claimed_item = generate_item(
                rarity=self.result_rarity,
                story_id=self.items[0].get("story_id") if self.items else None
            )
            # Apply tier upgrade if it was enabled
            if self.tier_upgrade_enabled:
                try:
                    current_idx = RARITY_ORDER.index(claimed_item.get("rarity", "Common"))
                    if current_idx < len(RARITY_ORDER) - 1:
                        new_rarity = RARITY_ORDER[current_idx + 1]
                        claimed_item["rarity"] = new_rarity
                        from gamification import RARITY_POWER
                        claimed_item["power"] = RARITY_POWER.get(new_rarity, claimed_item.get("power", 10))
                except (ValueError, IndexError):
                    pass
            
            # Update merge_result to show success
            self.merge_result["success"] = True
            self.merge_result["result_item"] = claimed_item
            self.merge_result["claimed_with_coins"] = True
            
            # Show success dialog for the claimed item
            self._show_success_dialog()
