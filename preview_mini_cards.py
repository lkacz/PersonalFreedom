"""
Preview: Entity Mini-Cards Comparison

Shows current style vs proposed cleaner style with no internal borders.
"""

import sys
from PySide6 import QtWidgets, QtCore, QtGui

try:
    from PySide6.QtSvg import QSvgRenderer
    HAS_SVG = True
except ImportError:
    HAS_SVG = False


def create_current_style_card(name: str, value: str, icon_emoji: str, is_exceptional: bool = False) -> QtWidgets.QFrame:
    """Create card with CURRENT style (has internal elements)."""
    card = QtWidgets.QFrame()
    
    if is_exceptional:
        card.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 2px;
            }
        """)
    else:
        card.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 2px;
            }
        """)
    
    card_layout = QtWidgets.QVBoxLayout(card)
    card_layout.setContentsMargins(6, 4, 6, 4)
    card_layout.setSpacing(2)
    
    # Icon (simulated with emoji + border)
    icon_lbl = QtWidgets.QLabel(icon_emoji)
    icon_lbl.setFixedSize(32, 32)
    icon_lbl.setAlignment(QtCore.Qt.AlignCenter)
    icon_lbl.setStyleSheet("font-size: 20px; background: #333; border: 1px solid #444; border-radius: 4px;")
    card_layout.addWidget(icon_lbl, alignment=QtCore.Qt.AlignCenter)
    
    # Name
    display_name = name[:12] + "..." if len(name) > 15 else name
    if is_exceptional:
        name_style = "color: #ffd700; font-weight: bold; font-size: 9px;"
    else:
        name_style = "color: #bbb; font-size: 9px;"
    
    name_lbl = QtWidgets.QLabel(display_name)
    name_lbl.setStyleSheet(name_style)
    name_lbl.setAlignment(QtCore.Qt.AlignCenter)
    card_layout.addWidget(name_lbl)
    
    # Value
    value_lbl = QtWidgets.QLabel(value)
    value_lbl.setStyleSheet("color: #4caf50; font-size: 10px; font-weight: bold;")
    value_lbl.setAlignment(QtCore.Qt.AlignCenter)
    card_layout.addWidget(value_lbl)
    
    return card


def create_clean_style_card(name: str, value: str, icon_emoji: str, is_exceptional: bool = False) -> QtWidgets.QFrame:
    """Create card with CLEAN style (NO internal borders, just outer card border)."""
    card = QtWidgets.QFrame()
    
    if is_exceptional:
        card.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 2px;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)
    else:
        card.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 2px;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)
    
    card_layout = QtWidgets.QVBoxLayout(card)
    card_layout.setContentsMargins(6, 4, 6, 4)
    card_layout.setSpacing(2)
    
    # Icon (NO border, just transparent bg)
    icon_lbl = QtWidgets.QLabel(icon_emoji)
    icon_lbl.setFixedSize(32, 32)
    icon_lbl.setAlignment(QtCore.Qt.AlignCenter)
    icon_lbl.setStyleSheet("font-size: 20px;")  # No border!
    card_layout.addWidget(icon_lbl, alignment=QtCore.Qt.AlignCenter)
    
    # Name (no extra styling beyond color/font)
    display_name = name[:12] + "..." if len(name) > 15 else name
    if is_exceptional:
        name_lbl = QtWidgets.QLabel(display_name)
        name_lbl.setStyleSheet("color: #ffd700; font-weight: bold; font-size: 9px;")
    else:
        name_lbl = QtWidgets.QLabel(display_name)
        name_lbl.setStyleSheet("color: #bbb; font-size: 9px;")
    
    name_lbl.setAlignment(QtCore.Qt.AlignCenter)
    card_layout.addWidget(name_lbl)
    
    # Value (no extra styling beyond color/font)
    value_lbl = QtWidgets.QLabel(value)
    value_lbl.setStyleSheet("color: #4caf50; font-size: 10px; font-weight: bold;")
    value_lbl.setAlignment(QtCore.Qt.AlignCenter)
    card_layout.addWidget(value_lbl)
    
    return card


def main():
    app = QtWidgets.QApplication(sys.argv)
    
    # Dark theme
    app.setStyleSheet("""
        QWidget {
            background-color: #1e1e1e;
            color: #ffffff;
            font-family: 'Segoe UI', sans-serif;
        }
    """)
    
    window = QtWidgets.QWidget()
    window.setWindowTitle("Entity Mini-Cards Style Comparison")
    window.setMinimumSize(800, 400)
    
    main_layout = QtWidgets.QVBoxLayout(window)
    main_layout.setSpacing(20)
    
    # Title
    title = QtWidgets.QLabel("Entity Mini-Cards Style Comparison")
    title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4fc3f7; padding: 10px;")
    title.setAlignment(QtCore.Qt.AlignCenter)
    main_layout.addWidget(title)
    
    # Sample data
    entities = [
        ("War Horse Thunder", "+8% ⚡", "🐴", True),
        ("Archive Phoenix", "+8% ⚡", "🐦", True),
        ("White Mouse Arc...", "+5% ⚡", "🐭", True),
        ("Library Mouse Pip", "+2% ⚡", "🐭", False),
        ("Study Owl Athena", "+2% ⚡", "🦉", False),
        ("Road Dog Wayfarer", "-10m 🍶", "🐕", False),
    ]
    
    # === CURRENT STYLE ===
    current_section = QtWidgets.QGroupBox("CURRENT Style (with internal borders on icon)")
    current_section.setStyleSheet("""
        QGroupBox {
            color: #ff9800;
            font-weight: bold;
            border: 1px solid #444;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
    """)
    current_layout = QtWidgets.QHBoxLayout(current_section)
    current_layout.setSpacing(6)
    current_layout.setContentsMargins(10, 20, 10, 10)
    
    for name, value, emoji, is_exc in entities:
        card = create_current_style_card(name, value, emoji, is_exc)
        current_layout.addWidget(card)
    current_layout.addStretch()
    
    main_layout.addWidget(current_section)
    
    # === CLEAN STYLE ===
    clean_section = QtWidgets.QGroupBox("PROPOSED Style (NO internal borders - cleaner)")
    clean_section.setStyleSheet("""
        QGroupBox {
            color: #4caf50;
            font-weight: bold;
            border: 1px solid #444;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
    """)
    clean_layout = QtWidgets.QHBoxLayout(clean_section)
    clean_layout.setSpacing(6)
    clean_layout.setContentsMargins(10, 20, 10, 10)
    
    for name, value, emoji, is_exc in entities:
        card = create_clean_style_card(name, value, emoji, is_exc)
        clean_layout.addWidget(card)
    clean_layout.addStretch()
    
    main_layout.addWidget(clean_section)
    
    # Note
    note = QtWidgets.QLabel(
        "💡 The PROPOSED style removes the border around the icon area,\n"
        "leaving only the outer card border for a cleaner, less busy appearance."
    )
    note.setStyleSheet("color: #888; font-style: italic; padding: 10px;")
    note.setAlignment(QtCore.Qt.AlignCenter)
    main_layout.addWidget(note)
    
    main_layout.addStretch()
    
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
