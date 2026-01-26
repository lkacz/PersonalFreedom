"""
Preview script to test animated city SVGs in isolation.
This helps diagnose if WebEngine SVG animations work outside the main app context.
"""

import sys
from pathlib import Path

from PySide6 import QtCore, QtWidgets
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings

# Path to city icons
CITY_ICONS_PATH = Path(__file__).parent / "icons" / "city"

# List of buildings to preview
BUILDINGS = [
    "goldmine",
    "forge", 
    "royal_mint",
    "market",
    "training_ground",
    "library",
    "university",
    "observatory",
    "artisan_guild",
    "wonder"
]


class AnimatedSVGPreview(QtWidgets.QWidget):
    """Widget that displays an animated SVG using QWebEngineView."""
    
    def __init__(self, svg_path: str, parent=None):
        super().__init__(parent)
        self.svg_path = svg_path
        self.setFixedSize(140, 160)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # WebEngine view for SVG
        self.web_view = QWebEngineView(self)
        self.web_view.setFixedSize(128, 128)
        
        # Configure for transparent background
        self.web_view.page().setBackgroundColor(QtCore.Qt.transparent)
        self.web_view.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        
        # Settings
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.ShowScrollBars, False)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, False)
        
        self._load_svg()
        layout.addWidget(self.web_view, alignment=QtCore.Qt.AlignCenter)
        
        # Label with filename
        name = Path(svg_path).stem.replace("_animated", "")
        label = QtWidgets.QLabel(name)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet("color: white; font-size: 11px;")
        layout.addWidget(label)
    
    def _load_svg(self):
        """Load the SVG into WebEngine with proper HTML wrapper."""
        try:
            with open(self.svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
        except Exception as e:
            print(f"Error loading {self.svg_path}: {e}")
            svg_content = '<svg></svg>'
        
        # HTML wrapper for proper rendering
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
        
        # Load with file:// base URL to allow SMIL animations
        base_url = QtCore.QUrl.fromLocalFile(str(Path(self.svg_path).parent) + '/')
        self.web_view.setHtml(html, base_url)


class PreviewWindow(QtWidgets.QMainWindow):
    """Main window showing all animated city building SVGs."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("City Animated SVG Preview")
        self.setStyleSheet("background: #1a1a2e;")
        
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        
        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QtWidgets.QLabel("🏰 City Building Animated SVGs Preview")
        title.setStyleSheet("color: #FFD700; font-size: 18px; font-weight: bold;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)
        
        info = QtWidgets.QLabel("If animations are working, you should see:\n"
                                 "• Sparkling gold nuggets (Goldmine)\n"
                                 "• Flickering flames (Forge)\n"
                                 "• Spinning coin (Royal Mint)\n"
                                 "• Rotating elements & color changes")
        info.setStyleSheet("color: #aaa; font-size: 12px;")
        info.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(info)
        
        # Grid of SVG previews
        grid_widget = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(grid_widget)
        grid.setSpacing(10)
        
        row, col = 0, 0
        for building_id in BUILDINGS:
            svg_path = CITY_ICONS_PATH / f"{building_id}_animated.svg"
            if svg_path.exists():
                preview = AnimatedSVGPreview(str(svg_path))
                grid.addWidget(preview, row, col)
                col += 1
                if col >= 5:
                    col = 0
                    row += 1
            else:
                print(f"Missing: {svg_path}")
        
        layout.addWidget(grid_widget)
        
        # Status
        self.status = QtWidgets.QLabel("Loading animated SVGs...")
        self.status.setStyleSheet("color: #888; font-size: 11px;")
        self.status.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.status)
        
        # Update status after a delay
        QtCore.QTimer.singleShot(2000, self._update_status)
    
    def _update_status(self):
        self.status.setText("✓ All SVGs loaded. Animations should be playing if SMIL is supported.")


def main():
    app = QtWidgets.QApplication(sys.argv)
    
    # Enable high DPI
    app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    
    window = PreviewWindow()
    window.resize(800, 500)
    window.show()
    
    print("Preview window opened.")
    print("Check if the SVG animations are playing.")
    print("Close the window to exit.")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
