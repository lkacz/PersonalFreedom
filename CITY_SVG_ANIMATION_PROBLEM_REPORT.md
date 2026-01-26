# City Tab SVG Animation Problem Report

## Problem Summary

Animated SVG icons display correctly (crisp, with SMIL animations playing) in:
1. A standalone preview script (`preview_city_animated.py`)
2. The Entitidex tab (`entitidex_tab.py` using `AnimatedSvgWidget`)

But the **same approach fails** in the City tab (`city_tab.py` using `AnimatedBuildingWidget`):
- SVGs appear **static** (no animation)
- SVGs appear **blurry** (not crisp/native resolution)

## Environment

- **OS**: Windows
- **Python**: 3.12.9
- **GUI Framework**: PySide6 (Qt 6)
- **WebEngine**: PySide6.QtWebEngineWidgets (confirmed working via import test)
- **SVG Format**: 128x128 viewBox with SMIL `<animate>` and `<animateTransform>` elements

## Working Implementation (Entitidex Tab)

### AnimatedSvgWidget Class (entitidex_tab.py lines 412-545)

```python
class AnimatedSvgWidget(QtWidgets.QWidget):
    __slots__ = ('svg_path', 'web_view', 'svg_widget')
    
    def __init__(self, svg_path: str, parent=None):
        super().__init__(parent)
        self.svg_path = svg_path
        self.web_view: Optional[QWebEngineView] = None
        self.svg_widget: Optional[QSvgWidget] = None
        self.setFixedSize(128, 128)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        if HAS_WEBENGINE:
            self.web_view = QWebEngineView(self)
            self.web_view.setFixedSize(128, 128)
            
            self.web_view.page().setBackgroundColor(QtCore.Qt.transparent)
            self.web_view.setAttribute(QtCore.Qt.WA_TranslucentBackground)
            
            settings = self.web_view.settings()
            settings.setAttribute(QWebEngineSettings.ShowScrollBars, False)
            settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
            
            self._load_svg()
            layout.addWidget(self.web_view)
        # ... fallback to QSvgWidget
    
    def _load_svg(self):
        if not self.web_view:
            return
            
        svg_content = self._get_cached_svg_content(self.svg_path)
        
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
        
        base_url = QtCore.QUrl.fromLocalFile(str(Path(self.svg_path).parent) + '/')
        self.web_view.setHtml(html, base_url)
```

### How It's Used in EntityCard (entitidex_tab.py lines 930-970)

```python
# In EntityCard.__init__():
svg_container = QtWidgets.QWidget()
svg_layout = QtWidgets.QHBoxLayout(svg_container)
svg_layout.addStretch()
svg_layout.setContentsMargins(0, 0, 0, 0)

if svg_path and os.path.exists(svg_path):
    if self.is_collected:
        if HAS_WEBENGINE:
            icon_widget = AnimatedSvgWidget(svg_path, svg_container)
        # ...
        self._icon_widget = icon_widget

svg_layout.addWidget(icon_widget)
svg_layout.addStretch()
layout.addWidget(svg_container)
```

### Key Characteristics of Working Implementation:
1. EntityCard has **fixed size** (180x220)
2. Widget is created **once** in `__init__`, never recreated
3. AnimatedSvgWidget is added to a simple HBoxLayout with stretches
4. No stacked widgets or complex nesting

---

## Failing Implementation (City Tab)

### AnimatedBuildingWidget Class (city_tab.py lines 241-360)

```python
class AnimatedBuildingWidget(QtWidgets.QWidget):
    # IDENTICAL to AnimatedSvgWidget above - copied exactly
    __slots__ = ('svg_path', 'web_view', 'svg_widget')
    
    def __init__(self, svg_path: str, parent=None):
        super().__init__(parent)
        # ... same implementation as AnimatedSvgWidget
```

### CityCell Structure (city_tab.py)

```python
class CityCell(QtWidgets.QFrame):
    def __init__(self, row: int, col: int, parent=None):
        super().__init__(parent)
        self._animated_widget = None
        
        self.setFixedSize(140, 140)  # Fixed size
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)
        
        # Using QStackedWidget to switch between static and animated
        self.icon_stack = QtWidgets.QStackedWidget()
        self.icon_stack.setFixedSize(128, 128)
        
        # Page 0: Static icon label
        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setFixedSize(128, 128)
        self.icon_stack.addWidget(self.icon_label)
        
        # Page 1: Animated widget container
        self.animated_container = QtWidgets.QWidget()
        self.animated_container.setFixedSize(128, 128)
        animated_layout = QtWidgets.QVBoxLayout(self.animated_container)
        animated_layout.setContentsMargins(0, 0, 0, 0)
        self.icon_stack.addWidget(self.animated_container)
        
        layout.addWidget(self.icon_stack, 0, QtCore.Qt.AlignCenter)
```

### How AnimatedBuildingWidget is Created (city_tab.py set_cell_state method)

```python
def set_cell_state(self, cell_state, building_def=None, adhd_buster=None):
    # State change detection to avoid recreating widgets
    old_building_id = self._cell_state.get("building_id") if self._cell_state else None
    old_status = self._cell_state.get("status") if self._cell_state else None
    new_building_id = cell_state.get("building_id") if cell_state else None
    new_status = cell_state.get("status") if cell_state else None
    
    state_changed = (old_building_id != new_building_id or old_status != new_status)
    
    if state_changed:
        if self._animated_widget:
            self._animated_widget.setParent(None)
            self._animated_widget.deleteLater()
            self._animated_widget = None
        
        self.icon_stack.setCurrentIndex(0)  # Default to static
    
    if state_changed and building_id and status == CellStatus.COMPLETE.value:
        svg_path = CITY_ICONS_PATH / f"{building_id}_animated.svg"
        if svg_path.exists():
            self._animated_widget = AnimatedBuildingWidget(str(svg_path), self.animated_container)
            self.animated_container.layout().addWidget(self._animated_widget)
            self.icon_stack.setCurrentIndex(1)  # Switch to animated
```

### Key Differences from Working Implementation:

1. **QStackedWidget usage** - Entitidex doesn't use a stacked widget
2. **Widget is added to a container inside the stacked widget** - Extra nesting level
3. **Widget may be recreated** when `set_cell_state` is called (though state change detection was added)
4. **CityCell is a QFrame** while EntityCard is also a QFrame - same base class
5. **City grid updates frequently** via `_refresh_city()` which calls `update_grid()` on every cell

---

## Working Preview Script (preview_city_animated.py)

```python
class AnimatedSVGPreview(QtWidgets.QWidget):
    def __init__(self, svg_path: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(140, 160)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # WebEngine view for SVG - DIRECTLY added to layout
        self.web_view = QWebEngineView(self)
        self.web_view.setFixedSize(128, 128)
        
        self.web_view.page().setBackgroundColor(QtCore.Qt.transparent)
        self.web_view.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.ShowScrollBars, False)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        
        self._load_svg()
        layout.addWidget(self.web_view, alignment=QtCore.Qt.AlignCenter)
```

**This works perfectly** - crisp 128x128 animated SVGs.

---

## SVG File Verification

The animated SVG files have been verified:
- Path: `icons/city/goldmine_animated.svg` (and 9 other buildings)
- ViewBox: `0 0 128 128`
- Contains SMIL animations: 13+ `<animate>` elements, `<animateTransform>` elements
- File content is identical when loaded in all three contexts

---

## Symptoms

| Context | Animation | Quality |
|---------|-----------|---------|
| Preview script | ✅ Working | ✅ Crisp 128x128 |
| Entitidex tab | ✅ Working | ✅ Crisp 128x128 |
| City tab | ❌ Static | ❌ Blurry/scaled |

---

## Hypotheses to Investigate

1. **QStackedWidget interference** - Does QStackedWidget affect WebEngineView rendering or visibility in a way that stops animations?

2. **Widget parent chain** - AnimatedBuildingWidget → animated_container → QStackedWidget → CityCell → CityGrid → CityTab. Does this deep nesting cause issues?

3. **Widget visibility/show timing** - Is the WebEngineView being created before it's visible? Does setCurrentIndex trigger proper show events?

4. **DPI/scaling** - Is there a DPI scaling issue specific to how the stacked widget or grid layout handles child widgets?

5. **Qt stylesheet cascade** - CityCell has radial gradient backgrounds. Could these stylesheets affect child WebEngineView rendering?

6. **Layout stretch factors** - The city grid uses HBoxLayout with spacing but no stretch. Could this cause sizing issues?

7. **Widget update/repaint** - Is set_cell_state being called in a context that prevents proper WebEngine initialization?

---

## Questions for Investigation

1. What is the correct way to embed QWebEngineView inside a QStackedWidget?

2. Does QWebEngineView require specific parent widget attributes or show events to render correctly?

3. Are there known issues with QWebEngineView and Qt layouts that cause blurry rendering?

4. Does QWebEngineView have DPI awareness settings that need to be configured?

5. Is there a timing issue where `setHtml()` is called before the widget is properly added to the visible widget tree?

6. What is the difference in how Qt handles WebEngine rendering in a directly-added widget vs one nested in QStackedWidget?

---

## Attempted Solutions (All Failed)

1. ✅ Added base_url to setHtml() - Required for SMIL but didn't fix the issue
2. ✅ Matched AnimatedBuildingWidget exactly to AnimatedSvgWidget code
3. ✅ Used QStackedWidget with fixed 128x128 sizes
4. ✅ Added state change detection to avoid recreating widgets
5. ✅ Set fixed size on CityCell (140x140)
6. ✅ Removed extra WebEngine settings (WebGLEnabled, etc.)

---

## Files to Review

1. `city_tab.py` - Lines 241-360 (AnimatedBuildingWidget), Lines 390-470 (CityCell), Lines 600-680 (set_cell_state)
2. `entitidex_tab.py` - Lines 412-545 (AnimatedSvgWidget), Lines 920-980 (EntityCard icon setup)
3. `preview_city_animated.py` - Full file (working standalone)

---

## Request

Please analyze the PySide6/Qt6 documentation for QWebEngineView, QStackedWidget, and widget embedding to identify why the same WebEngine SVG rendering code works in one context but not another. Focus on:

1. Widget visibility and show event requirements for WebEngine
2. QStackedWidget behavior with complex child widgets
3. DPI scaling and WebEngineView
4. Any known issues with WebEngineView in nested layouts
