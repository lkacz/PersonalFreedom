"""Styled Dialog Base Class

Provides a consistent, frameless dark-themed dialog appearance across the app.
Features:
- No system title bar
- Custom styled header with emoji support  
- Rounded corners with gold border
- Translucent background effect
- Clean, integrated dark theme
- Draggable by header
"""

from PySide6 import QtWidgets, QtCore, QtGui
from typing import Optional


class StyledDialog(QtWidgets.QDialog):
    """Base class for all styled dialogs in the app.
    
    Provides frameless window with custom header, dark theme, gold accents.
    Subclasses should override _build_content() to add their widgets.
    """
    
    # Style constants
    BORDER_COLOR = "#FFD700"  # Gold
    HEADER_COLOR = "#FFD700"
    BG_GRADIENT_TOP = "#1A1A2E"
    BG_GRADIENT_BOTTOM = "#0D0D1A"
    TEXT_COLOR = "#E0E0E0"
    BUTTON_GRADIENT_TOP = "#4A4A6A"
    BUTTON_GRADIENT_BOTTOM = "#2A2A4A"
    
    def __init__(
        self, 
        parent: Optional[QtWidgets.QWidget] = None,
        title: str = "Dialog",
        header_icon: str = "",  # Emoji like "🎉" or ""
        min_width: int = 400,
        max_width: int = 600,
        modal: bool = True,
        closable: bool = True,
    ):
        super().__init__(parent)
        
        self._title = title
        self._header_icon = header_icon
        self._closable = closable
        self._drag_pos = None
        
        # Window setup
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Dialog)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setModal(modal)
        self.setMinimumWidth(min_width)
        self.setMaximumWidth(max_width)
        
        # Build UI
        self._setup_styles()
        self._build_ui()
    
    def _setup_styles(self):
        """Set up the dialog stylesheet."""
        self.setStyleSheet(f"""
            QDialog {{
                background: transparent;
            }}
            QFrame#dialogFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.BG_GRADIENT_TOP}, stop:1 {self.BG_GRADIENT_BOTTOM});
                border: 2px solid {self.BORDER_COLOR};
                border-radius: 16px;
            }}
            QFrame#headerFrame {{
                background: transparent;
                border: none;
                border-bottom: 1px solid #333344;
            }}
            QLabel {{
                color: {self.TEXT_COLOR};
                background: transparent;
            }}
            QLabel#headerLabel {{
                color: {self.HEADER_COLOR};
                font-size: 16px;
                font-weight: bold;
                padding: 5px;
            }}
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.BUTTON_GRADIENT_TOP}, stop:1 {self.BUTTON_GRADIENT_BOTTOM});
                color: {self.HEADER_COLOR};
                border: 1px solid {self.BORDER_COLOR};
                border-radius: 8px;
                padding: 8px 20px;
                font-weight: bold;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5A5A7A, stop:1 #3A3A5A);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3A3A5A, stop:1 #2A2A3A);
            }}
            QPushButton#closeButton {{
                background: transparent;
                border: none;
                color: #888888;
                font-size: 18px;
                font-weight: bold;
                padding: 5px 10px;
                min-width: 30px;
            }}
            QPushButton#closeButton:hover {{
                color: #FF6B6B;
                background: rgba(255, 100, 100, 0.1);
                border-radius: 4px;
            }}
            QPushButton#primaryButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFD700, stop:1 #CC9900);
                color: #1A1A2E;
                border: none;
            }}
            QPushButton#primaryButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFE44D, stop:1 #DDAA00);
            }}
            QPushButton#dangerButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8B0000, stop:1 #5C0000);
                color: #FFFFFF;
                border: 1px solid #FF4444;
            }}
            QPushButton#dangerButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #AA0000, stop:1 #6C0000);
            }}
            QLineEdit, QTextEdit, QPlainTextEdit {{
                background: #0D0D1A;
                color: {self.TEXT_COLOR};
                border: 1px solid #444466;
                border-radius: 6px;
                padding: 8px;
                selection-background-color: {self.BORDER_COLOR};
                selection-color: #1A1A2E;
            }}
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border: 1px solid {self.BORDER_COLOR};
            }}
            QComboBox {{
                background: #0D0D1A;
                color: {self.TEXT_COLOR};
                border: 1px solid #444466;
                border-radius: 6px;
                padding: 8px;
                min-width: 100px;
            }}
            QComboBox:focus {{
                border: 1px solid {self.BORDER_COLOR};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {self.TEXT_COLOR};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background: #1A1A2E;
                color: {self.TEXT_COLOR};
                selection-background-color: {self.BORDER_COLOR};
                selection-color: #1A1A2E;
                border: 1px solid #444466;
            }}
            QCheckBox {{
                color: {self.TEXT_COLOR};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
            }}
            QCheckBox::indicator:unchecked {{
                border: 1px solid #666;
                background: #2A2A4A;
            }}
            QCheckBox::indicator:checked {{
                border: 1px solid {self.BORDER_COLOR};
                background: #4A4A6A;
            }}
            QCheckBox::indicator:checked::after {{
                content: "✓";
            }}
            QRadioButton {{
                color: {self.TEXT_COLOR};
                spacing: 8px;
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 9px;
            }}
            QRadioButton::indicator:unchecked {{
                border: 1px solid #666;
                background: #2A2A4A;
            }}
            QRadioButton::indicator:checked {{
                border: 1px solid {self.BORDER_COLOR};
                background: #4A4A6A;
            }}
            QSpinBox, QDoubleSpinBox {{
                background: #0D0D1A;
                color: {self.TEXT_COLOR};
                border: 1px solid #444466;
                border-radius: 6px;
                padding: 6px;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 1px solid {self.BORDER_COLOR};
            }}
            QGroupBox {{
                color: {self.HEADER_COLOR};
                border: 1px solid #444466;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
            }}
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: #1A1A2E;
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: #4A4A6A;
                border-radius: 6px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #5A5A7A;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QListWidget {{
                background: #0D0D1A;
                color: {self.TEXT_COLOR};
                border: 1px solid #444466;
                border-radius: 6px;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 6px;
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background: {self.BORDER_COLOR};
                color: #1A1A2E;
            }}
            QListWidget::item:hover {{
                background: #2A2A4A;
            }}
            QTableWidget {{
                background: #0D0D1A;
                color: {self.TEXT_COLOR};
                border: 1px solid #444466;
                border-radius: 6px;
                gridline-color: #333344;
            }}
            QTableWidget::item {{
                padding: 6px;
            }}
            QTableWidget::item:selected {{
                background: {self.BORDER_COLOR};
                color: #1A1A2E;
            }}
            QHeaderView::section {{
                background: #2A2A4A;
                color: {self.HEADER_COLOR};
                padding: 8px;
                border: none;
                border-bottom: 1px solid #444466;
            }}
            QProgressBar {{
                background: #0D0D1A;
                border: 1px solid #444466;
                border-radius: 6px;
                text-align: center;
                color: {self.TEXT_COLOR};
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.BORDER_COLOR}, stop:1 #CC9900);
                border-radius: 5px;
            }}
            QSlider::groove:horizontal {{
                background: #0D0D1A;
                height: 8px;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {self.BORDER_COLOR};
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QSlider::sub-page:horizontal {{
                background: {self.BORDER_COLOR};
                border-radius: 4px;
            }}
        """)
    
    def _build_ui(self):
        """Build the dialog UI structure."""
        # Outer layout (no margins for transparent background)
        outer_layout = QtWidgets.QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        
        # Main frame with border and background
        self._frame = QtWidgets.QFrame()
        self._frame.setObjectName("dialogFrame")
        outer_layout.addWidget(self._frame)
        
        # Frame layout
        frame_layout = QtWidgets.QVBoxLayout(self._frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)
        
        # Header frame (draggable)
        self._header_frame = QtWidgets.QFrame()
        self._header_frame.setObjectName("headerFrame")
        self._header_frame.setCursor(QtCore.Qt.OpenHandCursor)
        header_layout = QtWidgets.QHBoxLayout(self._header_frame)
        header_layout.setContentsMargins(20, 15, 10, 10)
        
        # Header text
        header_text = self._title
        if self._header_icon:
            header_text = f"{self._header_icon} {self._title} {self._header_icon}"
        self._header_label = QtWidgets.QLabel(header_text)
        self._header_label.setObjectName("headerLabel")
        header_layout.addWidget(self._header_label)
        
        header_layout.addStretch()
        
        # Close button (optional)
        if self._closable:
            close_btn = QtWidgets.QPushButton("✕")
            close_btn.setObjectName("closeButton")
            close_btn.setCursor(QtCore.Qt.PointingHandCursor)
            close_btn.clicked.connect(self.reject)
            header_layout.addWidget(close_btn)
        
        frame_layout.addWidget(self._header_frame)
        
        # Content area
        self._content_widget = QtWidgets.QWidget()
        self._content_layout = QtWidgets.QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(25, 15, 25, 20)
        self._content_layout.setSpacing(15)
        frame_layout.addWidget(self._content_widget)
        
        # Build content (override in subclass)
        self._build_content(self._content_layout)
    
    def _build_content(self, layout: QtWidgets.QVBoxLayout):
        """Override in subclass to add dialog content.
        
        Args:
            layout: The content layout to add widgets to
        """
        pass
    
    def set_header(self, title: str, icon: str = ""):
        """Update the header text and icon."""
        self._title = title
        self._header_icon = icon
        header_text = title
        if icon:
            header_text = f"{icon} {title} {icon}"
        self._header_label.setText(header_text)
    
    def add_button_row(
        self, 
        layout: QtWidgets.QVBoxLayout,
        buttons: list[tuple[str, str, callable]],  # (text, style, callback)
        centered: bool = True
    ) -> dict[str, QtWidgets.QPushButton]:
        """Add a row of buttons to the layout.
        
        Args:
            layout: Layout to add buttons to
            buttons: List of (text, style, callback) tuples
                     style can be: "primary", "danger", "default"
            centered: Whether to center the buttons
            
        Returns:
            Dict mapping button text to QPushButton widgets
        """
        btn_layout = QtWidgets.QHBoxLayout()
        if centered:
            btn_layout.addStretch()
        
        button_widgets = {}
        for text, style, callback in buttons:
            btn = QtWidgets.QPushButton(text)
            if style == "primary":
                btn.setObjectName("primaryButton")
            elif style == "danger":
                btn.setObjectName("dangerButton")
            if callback:
                btn.clicked.connect(callback)
            btn_layout.addWidget(btn)
            button_widgets[text] = btn
        
        if centered:
            btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        return button_widgets
    
    # Dragging support
    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            # Check if clicking on header
            header_rect = self._header_frame.geometry()
            if header_rect.contains(event.pos()):
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                self._header_frame.setCursor(QtCore.Qt.ClosedHandCursor)
                event.accept()
    
    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self._drag_pos is not None and event.buttons() == QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        self._drag_pos = None
        self._header_frame.setCursor(QtCore.Qt.OpenHandCursor)


class StyledMessageBox(StyledDialog):
    """Styled replacement for QMessageBox."""
    
    # Message types
    INFORMATION = "info"
    WARNING = "warning"
    ERROR = "error"
    QUESTION = "question"
    
    # Icons for each type
    TYPE_ICONS = {
        INFORMATION: "ℹ️",
        WARNING: "⚠️",
        ERROR: "❌",
        QUESTION: "❓",
    }
    
    TYPE_TITLES = {
        INFORMATION: "Information",
        WARNING: "Warning",
        ERROR: "Error",
        QUESTION: "Question",
    }
    
    def __init__(
        self,
        parent: Optional[QtWidgets.QWidget] = None,
        msg_type: str = INFORMATION,
        title: str = "",
        message: str = "",
        detail: str = "",
        buttons: list[str] = None,  # ["OK"], ["Yes", "No"], etc.
    ):
        self._msg_type = msg_type
        self._message = message
        self._detail = detail
        self._buttons = buttons or ["OK"]
        self._result_button = None
        
        # Auto-generate title if not provided
        if not title:
            title = self.TYPE_TITLES.get(msg_type, "Dialog")
        
        super().__init__(
            parent=parent,
            title=title,
            header_icon=self.TYPE_ICONS.get(msg_type, ""),
            min_width=350,
            max_width=500,
        )
    
    def _build_content(self, layout: QtWidgets.QVBoxLayout):
        # Message
        msg_label = QtWidgets.QLabel(self._message)
        msg_label.setWordWrap(True)
        msg_label.setAlignment(QtCore.Qt.AlignCenter)
        msg_label.setFont(QtGui.QFont("Segoe UI", 11))
        layout.addWidget(msg_label)
        
        # Detail (if any)
        if self._detail:
            detail_label = QtWidgets.QLabel(self._detail)
            detail_label.setWordWrap(True)
            detail_label.setStyleSheet("color: #888888; font-size: 10px;")
            layout.addWidget(detail_label)
        
        layout.addSpacing(10)
        
        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()
        
        for i, btn_text in enumerate(self._buttons):
            btn = QtWidgets.QPushButton(btn_text)
            # First button is primary for most dialogs
            if i == 0 and self._msg_type != self.QUESTION:
                btn.setObjectName("primaryButton")
            elif btn_text.lower() in ("yes", "ok", "confirm", "save"):
                btn.setObjectName("primaryButton")
            elif btn_text.lower() in ("delete", "remove", "cancel"):
                pass  # Default style
            
            btn.clicked.connect(lambda checked, t=btn_text: self._button_clicked(t))
            btn_layout.addWidget(btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _button_clicked(self, button_text: str):
        self._result_button = button_text
        if button_text.lower() in ("yes", "ok", "confirm", "save"):
            self.accept()
        else:
            self.reject()
    
    def get_result(self) -> str:
        """Get which button was clicked."""
        return self._result_button
    
    @classmethod
    def information(cls, parent, title: str, message: str, detail: str = "") -> str:
        """Show an information message box."""
        dlg = cls(parent, cls.INFORMATION, title, message, detail, ["OK"])
        dlg.exec()
        return dlg.get_result()
    
    @classmethod
    def warning(cls, parent, title: str, message: str, detail: str = "") -> str:
        """Show a warning message box."""
        dlg = cls(parent, cls.WARNING, title, message, detail, ["OK"])
        dlg.exec()
        return dlg.get_result()
    
    @classmethod
    def error(cls, parent, title: str, message: str, detail: str = "") -> str:
        """Show an error message box."""
        dlg = cls(parent, cls.ERROR, title, message, detail, ["OK"])
        dlg.exec()
        return dlg.get_result()
    
    @classmethod
    def question(cls, parent, title: str, message: str, buttons: list[str] = None) -> str:
        """Show a question message box with custom buttons."""
        if buttons is None:
            buttons = ["Yes", "No"]
        dlg = cls(parent, cls.QUESTION, title, message, "", buttons)
        dlg.exec()
        return dlg.get_result()


class StyledInputDialog(StyledDialog):
    """Styled replacement for QInputDialog."""
    
    def __init__(
        self,
        parent: Optional[QtWidgets.QWidget] = None,
        title: str = "Input",
        header_icon: str = "✏️",
        prompt: str = "Enter value:",
        default_value: str = "",
        placeholder: str = "",
    ):
        self._prompt = prompt
        self._default_value = default_value
        self._placeholder = placeholder
        self._input_widget = None
        self._result_value = None
        
        super().__init__(
            parent=parent,
            title=title,
            header_icon=header_icon,
            min_width=350,
            max_width=450,
        )
    
    def _build_content(self, layout: QtWidgets.QVBoxLayout):
        # Prompt
        prompt_label = QtWidgets.QLabel(self._prompt)
        prompt_label.setWordWrap(True)
        layout.addWidget(prompt_label)
        
        # Input field
        self._input_widget = QtWidgets.QLineEdit()
        self._input_widget.setText(self._default_value)
        self._input_widget.setPlaceholderText(self._placeholder)
        self._input_widget.returnPressed.connect(self._on_ok)
        layout.addWidget(self._input_widget)
        
        layout.addSpacing(10)
        
        # Buttons
        self.add_button_row(layout, [
            ("Cancel", "default", self.reject),
            ("OK", "primary", self._on_ok),
        ])
        
        # Focus input
        self._input_widget.setFocus()
        self._input_widget.selectAll()
    
    def _on_ok(self):
        self._result_value = self._input_widget.text()
        self.accept()
    
    def get_value(self) -> Optional[str]:
        """Get the entered value (None if cancelled)."""
        return self._result_value if self.result() == QtWidgets.QDialog.Accepted else None
    
    @classmethod
    def get_text(
        cls, 
        parent, 
        title: str, 
        prompt: str, 
        default: str = "",
        placeholder: str = "",
        icon: str = "✏️"
    ) -> tuple[str, bool]:
        """Show input dialog and get text.
        
        Returns:
            Tuple of (text, ok_pressed)
        """
        dlg = cls(parent, title, icon, prompt, default, placeholder)
        result = dlg.exec()
        return (dlg._result_value or "", result == QtWidgets.QDialog.Accepted)


class ItemRewardDialog(StyledDialog):
    """Dialog for showing item rewards with comparison to currently equipped gear."""
    
    RARITY_COLORS = {
        "Common": "#9e9e9e",
        "Uncommon": "#4caf50", 
        "Rare": "#2196f3",
        "Epic": "#9c27b0",
        "Legendary": "#ff9800"
    }
    
    def __init__(
        self,
        parent: Optional[QtWidgets.QWidget] = None,
        title: str = "🎁 Item Reward!",
        header_emoji: str = "🎁",
        source_label: str = "",  # e.g., "Activity", "Sleep", "Focus Session"
        items_earned: list = None,  # List of item dicts
        equipped: dict = None,  # Current equipped items by slot
        coins_earned: int = 0,
        extra_messages: list = None,  # Additional info messages
    ):
        self._source_label = source_label
        self._items_earned = items_earned or []
        self._equipped = equipped or {}
        self._coins_earned = coins_earned
        self._extra_messages = extra_messages or []
        
        super().__init__(parent, title, header_emoji, 450, 650, closable=True)
    
    def _build_content(self, layout: QtWidgets.QVBoxLayout) -> None:
        """Build the item reward content with comparisons."""
        
        # Source label if provided
        if self._source_label:
            source_lbl = QtWidgets.QLabel(f"<b>{self._source_label}</b>")
            source_lbl.setAlignment(QtCore.Qt.AlignCenter)
            source_lbl.setStyleSheet("color: #FFD700; font-size: 14px;")
            layout.addWidget(source_lbl)
            layout.addSpacing(10)
        
        # Scroll area for items (in case of many)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(350)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollArea > QWidget > QWidget { background: transparent; }
        """)
        
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(12)
        scroll_layout.setContentsMargins(5, 5, 5, 5)
        
        # Display each item with comparison
        for item in self._items_earned:
            item_widget = self._create_item_card(item)
            scroll_layout.addWidget(item_widget)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Extra messages
        if self._extra_messages:
            layout.addSpacing(10)
            for msg in self._extra_messages:
                msg_lbl = QtWidgets.QLabel(msg)
                msg_lbl.setWordWrap(True)
                msg_lbl.setStyleSheet("color: #B0B0B0; font-size: 11px;")
                layout.addWidget(msg_lbl)
        
        # Coins earned
        if self._coins_earned > 0:
            layout.addSpacing(10)
            coins_lbl = QtWidgets.QLabel(f"💰 <b>+{self._coins_earned} Coins earned!</b>")
            coins_lbl.setAlignment(QtCore.Qt.AlignCenter)
            coins_lbl.setStyleSheet("color: #f59e0b; font-size: 13px;")
            layout.addWidget(coins_lbl)
        
        layout.addSpacing(10)
        self.add_button_row(layout, [("OK", "primary", self.accept)])
    
    def _create_item_card(self, item: dict) -> QtWidgets.QWidget:
        """Create a card showing the new item and comparison to equipped."""
        card = QtWidgets.QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid #444;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setSpacing(6)
        card_layout.setContentsMargins(10, 8, 10, 8)
        
        # Item name and rarity (handle None values)
        rarity = item.get("rarity") or "Common"
        name = item.get("name") or "Unknown Item"
        slot = item.get("slot") or "Unknown"
        power = item.get("power") or 0
        color = self.RARITY_COLORS.get(rarity, "#9e9e9e")
        
        name_lbl = QtWidgets.QLabel(f"<span style='color:{color}; font-weight:bold;'>{name}</span>")
        name_lbl.setWordWrap(True)
        card_layout.addWidget(name_lbl)
        
        # Rarity, slot, power
        info_lbl = QtWidgets.QLabel(
            f"<span style='color:{color};'>[{rarity}]</span> • "
            f"<span style='color:#8bc34a;'>{slot}</span> • "
            f"⚔ Power: <b>{power}</b>"
        )
        info_lbl.setStyleSheet("font-size: 11px; color: #ccc;")
        card_layout.addWidget(info_lbl)
        
        # Lucky options if present
        lucky_options = item.get("lucky_options") or {}
        if lucky_options:
            lucky_parts = []
            if lucky_options.get("coin_discount"):
                lucky_parts.append(f"💰 -{lucky_options['coin_discount']}% Merge")
            if lucky_options.get("xp_bonus"):
                lucky_parts.append(f"✨ +{lucky_options['xp_bonus']}% XP")
            if lucky_options.get("merge_luck"):
                lucky_parts.append(f"🎲 +{lucky_options['merge_luck']}% Merge Luck")
            if lucky_parts:
                lucky_lbl = QtWidgets.QLabel(" | ".join(lucky_parts))
                lucky_lbl.setStyleSheet("color: #ffd700; font-size: 10px;")
                card_layout.addWidget(lucky_lbl)
        
        # Comparison to equipped item in same slot
        equipped_item = self._equipped.get(slot)
        if equipped_item and isinstance(equipped_item, dict):
            eq_rarity = equipped_item.get("rarity") or "Common"
            eq_name = equipped_item.get("name") or "Unknown"
            eq_power = equipped_item.get("power") or 0
            eq_color = self.RARITY_COLORS.get(eq_rarity, "#9e9e9e")
            
            power_diff = power - eq_power
            diff_color = "#4caf50" if power_diff > 0 else ("#f44336" if power_diff < 0 else "#888")
            diff_sign = "+" if power_diff > 0 else ""
            
            # Separator
            sep = QtWidgets.QFrame()
            sep.setFrameShape(QtWidgets.QFrame.HLine)
            sep.setStyleSheet("background: #444; max-height: 1px;")
            card_layout.addWidget(sep)
            
            # Comparison header
            cmp_header = QtWidgets.QLabel("📊 <b>vs Currently Equipped:</b>")
            cmp_header.setStyleSheet("color: #888; font-size: 10px;")
            card_layout.addWidget(cmp_header)
            
            # Equipped item info
            eq_lbl = QtWidgets.QLabel(
                f"<span style='color:{eq_color};'>{eq_name}</span> • ⚔ {eq_power}"
            )
            eq_lbl.setStyleSheet("color: #888; font-size: 10px;")
            card_layout.addWidget(eq_lbl)
            
            # Power difference
            diff_lbl = QtWidgets.QLabel(
                f"<span style='color:{diff_color}; font-weight:bold;'>{diff_sign}{power_diff} Power</span>"
            )
            diff_lbl.setStyleSheet("font-size: 11px;")
            card_layout.addWidget(diff_lbl)
            
            # Lucky options comparison
            eq_lucky = equipped_item.get("lucky_options") or {}
            if lucky_options or eq_lucky:
                lucky_diffs = []
                for key, label in [("coin_discount", "💰 Merge"), ("xp_bonus", "✨ XP"), ("merge_luck", "🎲 Luck")]:
                    new_val = lucky_options.get(key, 0)
                    old_val = eq_lucky.get(key, 0)
                    if new_val != old_val:
                        diff = new_val - old_val
                        d_sign = "+" if diff > 0 else ""
                        d_color = "#4caf50" if diff > 0 else "#f44336"
                        lucky_diffs.append(f"<span style='color:{d_color};'>{label}: {d_sign}{diff}%</span>")
                
                if lucky_diffs:
                    luck_diff_lbl = QtWidgets.QLabel(" | ".join(lucky_diffs))
                    luck_diff_lbl.setStyleSheet("font-size: 10px;")
                    card_layout.addWidget(luck_diff_lbl)
        else:
            # No item equipped in this slot
            sep = QtWidgets.QFrame()
            sep.setFrameShape(QtWidgets.QFrame.HLine)
            sep.setStyleSheet("background: #444; max-height: 1px;")
            card_layout.addWidget(sep)
            
            empty_lbl = QtWidgets.QLabel(
                f"<span style='color:#4caf50;'>✓ {slot} slot was empty - auto-equipped!</span>"
            )
            empty_lbl.setStyleSheet("font-size: 10px;")
            card_layout.addWidget(empty_lbl)
        
        return card


class OptimizeGearDialog(StyledDialog):
    """Styled dialog for gear optimization strategy selection."""
    
    def __init__(
        self,
        parent,
        current_coins: int,
        optimize_cost: int,
        has_entity_perk: bool = False,
        perk_description: str = "",
    ):
        self.current_coins = current_coins
        self.optimize_cost = optimize_cost
        self.has_entity_perk = has_entity_perk
        self.perk_description = perk_description
        self.selected_mode = "power"
        self.selected_target = "all"
        super().__init__(parent, "⚡ Optimize Gear", header_icon="⚔️")
    
    def _build_content(self, layout):
        """Build the optimization strategy selection UI."""
        # Coin balance display at top
        coin_layout = QtWidgets.QHBoxLayout()
        coin_layout.addStretch()
        coin_layout.addWidget(QtWidgets.QLabel("🪙"))
        coin_label = QtWidgets.QLabel(f"<b style='color: #ffd700;'>{self.current_coins:,}</b>")
        coin_layout.addWidget(coin_label)
        layout.addLayout(coin_layout)
        
        # Cost info (with entity perk if applicable)
        if self.has_entity_perk:
            if self.optimize_cost == 0:
                cost_text = f"<span style='color: #00ff88;'>{self.perk_description}</span>"
            else:
                cost_text = f"<span style='color: #ffd700;'>{self.perk_description}</span>"
        else:
            cost_text = f"<span style='color: #aaa;'>Cost: {self.optimize_cost} coins</span>"
        
        cost_label = QtWidgets.QLabel(cost_text)
        cost_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(cost_label)
        
        # Strategy selection label
        select_label = QtWidgets.QLabel("Select an optimization strategy:")
        select_label.setStyleSheet("font-size: 13px; color: #ddd;")
        layout.addWidget(select_label)
        
        # Radio buttons for strategy
        self.btn_group = QtWidgets.QButtonGroup(self)
        
        rb_power = QtWidgets.QRadioButton("Maximize Power (Default)")
        rb_power.setToolTip("Equip items that give the highest total power, considering set bonuses.")
        rb_power.setChecked(True)
        rb_power.setStyleSheet(self._radio_style())
        self.btn_group.addButton(rb_power, 0)
        layout.addWidget(rb_power)
        
        rb_options = QtWidgets.QRadioButton("Maximize Lucky Options")
        rb_options.setToolTip("Equip items with the best lucky bonuses (Coins, XP, etc). Power is secondary.")
        rb_options.setStyleSheet(self._radio_style())
        self.btn_group.addButton(rb_options, 1)
        layout.addWidget(rb_options)
        
        rb_balanced = QtWidgets.QRadioButton("Balanced (Power + Options)")
        rb_balanced.setToolTip("Find a balance between raw power and lucky bonuses.")
        rb_balanced.setStyleSheet(self._radio_style())
        self.btn_group.addButton(rb_balanced, 2)
        layout.addWidget(rb_balanced)
        
        # Options sub-selection (hidden unless Options/Balanced selected)
        self.options_frame = QtWidgets.QFrame()
        self.options_frame.setStyleSheet("background: transparent;")
        options_layout = QtWidgets.QHBoxLayout(self.options_frame)
        options_layout.setContentsMargins(20, 5, 0, 5)
        
        target_label = QtWidgets.QLabel("Target:")
        target_label.setStyleSheet("color: #bbb;")
        options_layout.addWidget(target_label)
        
        self.combo_target = QtWidgets.QComboBox()
        self.combo_target.addItems([
            "All Lucky Options 🍀",
            "Coin Discount 💰",
            "XP Bonus ✨",
            "Merge Luck ⚒️"
        ])
        self.combo_target.setStyleSheet("""
            QComboBox {
                background: #333;
                color: #fff;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 150px;
            }
            QComboBox:hover { border-color: #d4a537; }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background: #2a2a2a;
                color: #fff;
                selection-background-color: #d4a537;
            }
        """)
        options_layout.addWidget(self.combo_target)
        options_layout.addStretch()
        
        layout.addWidget(self.options_frame)
        self.options_frame.setVisible(False)
        
        # Toggle visibility of target combo
        rb_power.toggled.connect(self._update_options_visibility)
        rb_options.toggled.connect(self._update_options_visibility)
        rb_balanced.toggled.connect(self._update_options_visibility)
        
        # Buttons
        layout.addSpacing(10)
        self.add_button_row(
            layout,
            [
                ("Cancel", "default", self.reject),
                ("Optimize ⚡", "primary", self._on_accept),
            ]
        )
    
    def _radio_style(self) -> str:
        """Return stylesheet for radio buttons."""
        return """
            QRadioButton {
                color: #fff;
                font-size: 12px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 2px solid #666;
                background: #333;
            }
            QRadioButton::indicator:checked {
                border-color: #d4a537;
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.4, fx:0.5, fy:0.5, stop:0 #d4a537, stop:1 #333);
            }
            QRadioButton::indicator:hover {
                border-color: #888;
            }
        """
    
    def _update_options_visibility(self):
        """Show/hide target combo based on selected strategy."""
        btn = self.btn_group.checkedButton()
        show_options = btn and btn.text() != "Maximize Power (Default)"
        self.options_frame.setVisible(show_options)
    
    def _on_accept(self):
        """Store selected values and accept dialog."""
        btn_id = self.btn_group.checkedId()
        mode_map = {0: "power", 1: "options", 2: "balanced"}
        self.selected_mode = mode_map.get(btn_id, "power")
        
        target_map = {
            0: "all",
            1: "coin_discount",
            2: "xp_bonus", 
            3: "merge_luck"
        }
        self.selected_target = target_map.get(self.combo_target.currentIndex(), "all")
        
        self.accept()
    
    def get_selections(self) -> tuple:
        """Return the selected mode and target.
        
        Returns:
            (mode, target) tuple where mode is 'power', 'options', or 'balanced'
            and target is 'all', 'coin_discount', 'xp_bonus', or 'merge_luck'
        """
        return self.selected_mode, self.selected_target


# Helper functions for easy use
def styled_info(parent, title: str, message: str, detail: str = None) -> str:
    return StyledMessageBox.information(parent, title, message, detail)

def styled_warning(parent, title: str, message: str, detail: str = None) -> str:
    return StyledMessageBox.warning(parent, title, message, detail)

def styled_error(parent, title: str, message: str, detail: str = None):
    return StyledMessageBox.error(parent, title, message, detail)

def styled_question(parent, title: str, message: str, buttons: list[str] = None) -> str:
    return StyledMessageBox.question(parent, title, message, buttons)

def styled_input(parent, title: str, prompt: str, default: str = "", icon: str = "✏️") -> tuple[str, bool]:
    return StyledInputDialog.get_text(parent, title, prompt, default, "", icon)


# ═══════════════════════════════════════════════════════════════════════════════
# Tab Help System - "?" button that explains what each tab does with sarcastic humor
# ═══════════════════════════════════════════════════════════════════════════════

# Help content for each tab - sarcastic but informative
TAB_HELP_CONTENT = {
    "timer": {
        "title": "⏱ Timer Tab",
        "icon": "⏱",
        "content": """<b>What it does:</b><br>
Start focus sessions that block distracting websites. 
Yes, it's that simple. No, you can't cheat.<br><br>

<b>Modes:</b><br>
• <b>Normal:</b> For people with self-control (rare species)<br>
• <b>Strict 🔐:</b> Needs password to quit. Good luck remembering it.<br>
• <b>Hardcore 💪:</b> Solve math problems to escape. Panicked arithmetic!<br>
• <b>Pomodoro 🍅:</b> 25 min work, 5 min break. The Italian way.<br><br>

<b>Bonus features:</b><br>
• <b>Priority check-ins:</b> Periodic prompts to log what you worked on<br>
• <b>Strategic priorities:</b> Get 2.5x coins for important tasks!<br>
• Presets: Quick-start 15/25/45/60 min sessions<br><br>

<b>Pro tip:</b> The timer keeps running even if you close the app. We're onto you. 👀"""
    },
    "sites": {
        "title": "🌐 Sites Tab",
        "icon": "🌐",
        "content": """<b>What it does:</b><br>
Manage which websites get blocked or whitelisted. 
Your nemesis list, basically.<br><br>

<b>Features:</b><br>
• <b>Blocked Sites:</b> Add sites that ruin your productivity. You know which ones.<br>
• <b>Whitelist:</b> Sites that NEVER get blocked. Use responsibly (you won't).<br>
• <b>Import/Export:</b> Share your shame list with friends!<br><br>

<b>Pro tip:</b> "reddit.com" counts as one site. "reddit.com/r/cats", "reddit.com/r/memes" - still same site. Nice try. 🙄"""
    },
    "categories": {
        "title": "📁 Categories Tab",
        "icon": "📁",
        "content": """<b>What it does:</b><br>
Pre-made bundles of sites to block. For when listing sites one-by-one 
feels like cataloging your failures.<br><br>

<b>Why use this:</b><br>
• Enable "Social Media" = goodbye Facebook, Twitter, Instagram, etc.<br>
• Enable "Video Streaming" = bye Netflix, YouTube, Twitch...<br>
• One click, maximum protection from yourself.<br><br>

<b>Pro tip:</b> Yes, we know about that "educational" YouTube excuse. 
Still gets blocked. 📚🚫"""
    },
    "schedule": {
        "title": "📅 Schedule Tab",
        "icon": "📅",
        "content": """<b>What it does:</b><br>
Set up automatic blocking schedules. Like a responsible adult. 
Or like someone who knows they can't be trusted. Same thing.<br><br>

<b>How it works:</b><br>
• Pick days (Mon-Sun)<br>
• Pick time range (e.g., 9 AM - 5 PM)<br>
• Blocking activates automatically<br>
• No willpower required!<br><br>

<b>Pro tip:</b> "I'll just disable the schedule" - That's future-you's problem, 
and past-you clearly didn't trust them. 🗓️"""
    },
    "stats": {
        "title": "📊 Productivity Tab",
        "icon": "📊",
        "content": """<b>What it does:</b><br>
Shows your focus stats so you can feel proud or 
deeply concerned about your life choices.<br><br>

<b>Metrics:</b><br>
• <b>⏱️ Total Focus Time:</b> All your hard work, quantified<br>
• <b>✅ Sessions Completed:</b> How often you actually tried<br>
• <b>🔥 Streak:</b> Consecutive focus days<br>
• <b>🎯 Weekly/Monthly Goals:</b> Set targets, feel accomplished<br>
• <b>📊 Weekly Chart:</b> Daily breakdown of focus time<br>
• <b>📈 Productivity Analytics:</b> Trends, patterns, charts<br><br>

<b>Pro tip:</b> Stats update in real-time. 
Refreshing won't make bad numbers better. 
Only actual focus sessions do that. Sorry! 📈"""
    },
    "settings": {
        "title": "⚙ Settings Tab",
        "icon": "⚙",
        "content": """<b>What it does:</b><br>
All the knobs and buttons for power users 
(and people who break things).<br><br>

<b>Features:</b><br>
• <b>👤 User Profile:</b> Switch between users<br>
• <b>🔐 Password:</b> Set one for Strict Mode. Write it down. Lose the paper. Cry.<br>
• <b>🍅 Pomodoro:</b> Customize work/break durations<br>
• <b>💾 Backup/Restore:</b> Save your data before experimenting<br>
• <b>🧹 Emergency Cleanup:</b> The "I broke everything" button<br>
• <b>🎙️ Voice Settings:</b> Pick TTS voice for routines<br>
• <b>🖥️ System Tray:</b> Hide to tray on close<br>
• <b>🚨 Factory Reset:</b> Nuclear option. Think twice.<br><br>

<b>Pro tip:</b> "Emergency Cleanup" removes blocked sites. 
It's for bugs, not for cheating. We're watching. 🔧"""
    },
    "weight": {
        "title": "⚖ Weight Tab",
        "icon": "⚖",
        "content": """<b>What it does:</b><br>
Track your weight over time. The app won't judge. 
(The mirror, however...)<br><br>

<b>Features:</b><br>
• Log daily weight<br>
• Set goal weight (optional guilt trip)<br>
• Pretty charts showing trends<br>
• BMI calculation (for what it's worth)<br>
• Earn coins for consistency!<br><br>

<b>Pro tip:</b> Weight fluctuates 1-2 kg daily from water alone. 
Don't panic. Unless you ate an entire cake. Then maybe a little panic. 🍰"""
    },
    "activity": {
        "title": "🏃 Activity Tab",
        "icon": "🏃",
        "content": """<b>What it does:</b><br>
Log physical activities and earn rewards. 
Yes, walking to the fridge counts (barely).<br><br>

<b>Features:</b><br>
• Log various activities (walking, running, swimming, etc.)<br>
• Track duration and intensity<br>
• Earn coins and XP for moving<br>
• Weekly summaries<br><br>

<b>Pro tip:</b> "Aggressive keyboard typing" is not an activity type. 
We checked. ⌨️"""
    },
    "sleep": {
        "title": "😴 Sleep Tab",
        "icon": "😴",
        "content": """<b>What it does:</b><br>
Track your sleep because apparently we all need reminders 
that 3 AM is not a reasonable bedtime.<br><br>

<b>Features:</b><br>
• Log bedtime and wake time<br>
• Rate sleep quality<br>
• Track disruptions (kids, pets, existential dread...)<br>
• Earn rewards for good sleep habits<br><br>

<b>Pro tip:</b> 7-9 hours is recommended. 
"But I function fine on 4 hours" - No, you don't. 
Your coworkers are just too polite to say it. 💤"""
    },
    "water": {
        "title": "💧 Water Tab",
        "icon": "💧",
        "content": """<b>What it does:</b><br>
Track water intake. Because apparently we need an app 
to remember that drinking water is a thing.<br><br>

<b>Features:</b><br>
• Log glasses of water (max 5/day for safety)<br>
• 2-hour cooldown between logs (to prevent gaming the system)<br>
• Earn rewards for staying hydrated<br>
• Timeline showing when you drank<br><br>

<b>Pro tip:</b> Coffee is not water. 
Energy drinks are not water. 
Beer is definitely not water. 
We're onto you. 🚰"""
    },
    "eye": {
        "title": "🌬️ Eye & Breath Tab",
        "icon": "👁",
        "content": """<b>What it does:</b><br>
Guided eye exercises AND breathing routines. 
Your optometrist AND your yoga instructor would be proud.<br><br>

<b>The 2-step routine:</b><br>
1. <b>Gentle Blinks:</b> 5 slow blinks. Close, hold, open. Repeat. Surprisingly relaxing.<br>
2. <b>Far Gaze + Breathing:</b> Look 20+ feet away for 20 seconds while doing:<br>
&nbsp;&nbsp;&nbsp;• 4 seconds inhale (rising bar)<br>
&nbsp;&nbsp;&nbsp;• 6 seconds exhale (falling bar)<br>
3. <b>Done!</b> Earn rewards. Eyes feel less like sandpaper.<br><br>

<b>Pro tip:</b> Voice guidance available! Or sound effects. Or silence, 
if you're in a meeting pretending to pay attention. 👁️👁️"""
    },
    "hero": {
        "title": "🦸 Hero Tab",
        "icon": "🦸",
        "content": """<b>What it does:</b><br>
Your character, equipment, and inventory! 
Yes, we turned productivity into an RPG. You're welcome.<br><br>

<b>Features:</b><br>
• <b>Equip gear</b> to boost your Power level<br>
• <b>Merge duplicates</b> for better gear (3 items → 1 upgraded)<br>
• <b>Set bonuses:</b> Matching items = extra power<br>
• <b>Entity Patrons:</b> Collected entities boost your hero!<br>
• <b>🔍 Analysis button:</b> See exactly how your power is calculated<br>
• <b>Story selection:</b> Choose your adventure theme<br><br>

<b>Pro tip:</b> Use "⚡ Optimize Gear" to auto-equip best items. 
We did the math so you don't have to. ⚔️"""
    },
    "entitidex": {
        "title": "📖 Entitidex Tab",
        "icon": "📖",
        "content": """<b>What it does:</b><br>
Your collection of discovered entities! 
Gotta catch 'em all. Wait, wrong franchise.<br><br>

<b>Features:</b><br>
• View all entities organized by story theme<br>
• See which ones you've encountered (uncollected = silhouettes)<br>
• <b>✨ Active Perks:</b> Entities give permanent bonuses!<br>
• <b>📦 Saved Encounters:</b> Replay any encounter later<br>
• Track completion progress per theme<br><br>

<b>Entity Perks:</b> Each entity gives unique bonuses:<br>
&nbsp;• Extra XP, coins, or Power<br>
&nbsp;• Better merge luck<br>
&nbsp;• Free optimize gear, and more!<br><br>

<b>Pro tip:</b> Collect entities by completing focus sessions. 
The rarer the entity, the better the perk! 🎴"""
    },
    "ai": {
        "title": "🧠 AI Insights Tab",
        "icon": "🧠",
        "content": """<b>What it does:</b><br>
AI-powered productivity analysis. 
It's like having a very judgmental robot coach.<br><br>

<b>Features:</b><br>
• <b>💡 Productivity Insights:</b> AI analyzes your habits<br>
• <b>🏆 Achievements:</b> Unlock trophies for milestones<br>
• <b>🎯 Daily Challenges:</b> Fresh goals every day<br>
• <b>📋 Custom Goals:</b> Set and track your own targets<br>
• <b>📈 AI Statistics:</b> Deep analysis of your patterns<br><br>

<b>Note:</b> Requires AI dependencies to be installed.
Without them, you get a lonely "AI not available" message.<br><br>

<b>Pro tip:</b> The AI knows when you're procrastinating. 
It just doesn't say it out loud. Much. 🤖"""
    },
    "dev": {
        "title": "🛠️ Dev Tab",
        "icon": "🛠️",
        "content": """<b>What it does:</b><br>
Developer cheats and testing tools. 
If you're here, you either know what you're doing 
or you're about to break something.<br><br>

<b>Features:</b><br>
• Generate items (any rarity)<br>
• Add coins and XP<br>
• Reset cooldowns<br>
• Test entity encounters<br>
• Basically: god mode<br><br>

<b>Pro tip:</b> Using these defeats the purpose of the gamification system. 
But we're not your mom. Do what you want. 🔓"""
    },
}


def create_tab_help_button(tab_id: str, parent: QtWidgets.QWidget = None) -> QtWidgets.QPushButton:
    """Create a styled ? help button for a tab.
    
    Args:
        tab_id: Key in TAB_HELP_CONTENT dict (e.g., "timer", "sites")
        parent: Parent widget
        
    Returns:
        QPushButton configured as help button
    """
    btn = QtWidgets.QPushButton("?")
    btn.setFixedSize(28, 28)
    btn.setCursor(QtCore.Qt.PointingHandCursor)
    btn.setToolTip("Click for help about this tab")
    btn.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #4A4A6A, stop:1 #2A2A4A);
            color: #FFD700;
            border: 2px solid #FFD700;
            border-radius: 14px;
            font-size: 16px;
            font-weight: bold;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #5A5A7A, stop:1 #3A3A5A);
            border-color: #FFEA00;
        }
        QPushButton:pressed {
            background: #2A2A4A;
        }
    """)
    
    def show_help():
        help_data = TAB_HELP_CONTENT.get(tab_id, {})
        if not help_data:
            return
        
        title = help_data.get("title", "Help")
        content = help_data.get("content", "No help available.")
        icon = help_data.get("icon", "❓")
        
        # Create custom help dialog
        dialog = TabHelpDialog(parent, title, icon, content)
        dialog.exec()
    
    btn.clicked.connect(show_help)
    return btn


class TabHelpDialog(StyledDialog):
    """Dialog for displaying tab help content with sarcastic flair."""
    
    def __init__(
        self,
        parent: Optional[QtWidgets.QWidget] = None,
        title: str = "Help",
        icon: str = "❓",
        content: str = "",
    ):
        self._help_content = content
        super().__init__(
            parent=parent,
            title=title,
            header_icon=icon,
            min_width=420,
            max_width=500,
            modal=True,
        )
    
    def _build_content(self, layout: QtWidgets.QVBoxLayout) -> None:
        """Build the help content area."""
        # Scrollable content area
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(350)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        content_widget = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content_widget)
        content_layout.setContentsMargins(5, 5, 5, 5)
        
        # Help text
        help_label = QtWidgets.QLabel(self._help_content)
        help_label.setWordWrap(True)
        help_label.setStyleSheet("""
            QLabel {
                color: #E0E0E0;
                font-size: 12px;
                line-height: 1.5;
                padding: 10px;
                background: rgba(0, 0, 0, 0.2);
                border-radius: 8px;
            }
        """)
        help_label.setTextFormat(QtCore.Qt.RichText)
        content_layout.addWidget(help_label)
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        # Got it button
        layout.addSpacing(10)
        self.add_button_row(layout, [("Got it! 👍", "primary", self.accept)])


def add_help_button_to_header(
    layout: QtWidgets.QHBoxLayout,
    tab_id: str,
    parent: QtWidgets.QWidget = None,
    add_stretch_before: bool = True
) -> QtWidgets.QPushButton:
    """Helper to add a ? button to an existing header row layout.
    
    Args:
        layout: The QHBoxLayout header row to add to
        tab_id: Key in TAB_HELP_CONTENT
        parent: Parent widget for the dialog
        add_stretch_before: Whether to add stretch before the button
        
    Returns:
        The created help button
    """
    if add_stretch_before:
        layout.addStretch()
    
    btn = create_tab_help_button(tab_id, parent)
    layout.addWidget(btn)
    return btn
