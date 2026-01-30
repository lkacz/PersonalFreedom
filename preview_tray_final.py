from PySide6 import QtGui, QtCore, QtWidgets
import sys
from pathlib import Path

# Initialize application for font rendering if not already running
if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)
else:
    app = QtWidgets.QApplication.instance()

def create_final_preview(minutes: int, size: int = 128):
    """Generate final preview with linear gradients."""
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtCore.Qt.transparent)

    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setRenderHint(QtGui.QPainter.TextAntialiasing)

    # Scale values from base 64px
    border_width = int(size * (4/64))
    outer_margin = int(size * (2/64))
    inner_margin = outer_margin + border_width
    
    # Draw Legendary Orange Gradient Border (bottom to top) - STRONG CONTRAST
    orange_gradient = QtGui.QLinearGradient(0, size, 0, 0)  # bottom to top
    orange_gradient.setColorAt(0, QtGui.QColor("#E65100"))  # Dark orange at bottom
    orange_gradient.setColorAt(1, QtGui.QColor("#FFE0B2"))  # Very light orange at top
    
    painter.setBrush(orange_gradient)
    painter.setPen(QtCore.Qt.NoPen)
    painter.drawEllipse(outer_margin, outer_margin, size - 2*outer_margin, size - 2*outer_margin)
    
    # Draw Rare Blue Gradient Background (top to bottom) - STRONG CONTRAST
    blue_gradient = QtGui.QLinearGradient(0, 0, 0, size)  # top to bottom
    blue_gradient.setColorAt(0, QtGui.QColor("#90CAF9"))  # Very light blue at top
    blue_gradient.setColorAt(1, QtGui.QColor("#0D47A1"))  # Very dark blue at bottom
    
    painter.setBrush(blue_gradient)
    painter.setPen(QtCore.Qt.NoPen)
    painter.drawEllipse(inner_margin, inner_margin, size - 2*inner_margin, size - 2*inner_margin)

    # Draw Number
    painter.setPen(QtGui.QColor("white"))
    
    # Scaling logic for font size
    text = str(minutes)
    
    if len(text) >= 3:
        base_font_size = 20
    elif len(text) == 2:
        base_font_size = 26
    else:
        base_font_size = 32
        
    font_size = int(base_font_size * (size / 64))
    
    font = QtGui.QFont("Arial", font_size, QtGui.QFont.Bold)
    painter.setFont(font)
    
    rect = QtCore.QRect(0, 0, size, size)
    painter.drawText(rect, QtCore.Qt.AlignCenter, text)

    painter.end()
    return pixmap

def main():
    output_dir = Path("preview_icons")
    output_dir.mkdir(exist_ok=True)
    
    examples = [120, 99, 45, 10, 5, 1]
    
    print(f"Generating final preview icons with linear gradients in {output_dir.absolute()}...")
    
    for mins in examples:
        pixmap = create_final_preview(mins)
        filename = output_dir / f"final_preview_{mins}min.png"
        pixmap.save(str(filename))
        print(f"  ✓ {filename.name}")

if __name__ == "__main__":
    main()
