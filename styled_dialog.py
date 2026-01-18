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


# Convenience functions for quick styled message boxes
def styled_info(parent, title: str, message: str, detail: str = "") -> str:
    return StyledMessageBox.information(parent, title, message, detail)

def styled_warning(parent, title: str, message: str, detail: str = "") -> str:
    return StyledMessageBox.warning(parent, title, message, detail)

def styled_error(parent, title: str, message: str, detail: str = "") -> str:
    return StyledMessageBox.error(parent, title, message, detail)

def styled_question(parent, title: str, message: str, buttons: list[str] = None) -> str:
    return StyledMessageBox.question(parent, title, message, buttons)

def styled_input(parent, title: str, prompt: str, default: str = "", icon: str = "✏️") -> tuple[str, bool]:
    return StyledInputDialog.get_text(parent, title, prompt, default, "", icon)
