import sys
from PySide6 import QtWidgets, QtCore, QtGui, QtSvg
from pathlib import Path

# Import necessary internals from hero_svg_system
import hero_svg_system

def generate_preview():
    # Only create QApplication if one doesn't exist
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)
    
    scenarios = [
        ("Base (No Boots)", None),
        ("Common Boots", {"Boots": {"rarity": "common"}}),
        ("Uncommon Boots", {"Boots": {"rarity": "uncommon"}}),
        ("Rare Boots", {"Boots": {"rarity": "rare"}}),
        ("Epic Boots", {"Boots": {"rarity": "epic"}}),
        ("Legendary Boots", {"Boots": {"rarity": "legendary"}}),
        # Celestial might not exist or falls back, checking folder list it exists
        ("Celestial Boots", {"Boots": {"rarity": "celestial"}}),
    ]
    
    # CSS for the preview page
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { background-color: #1a1a2e; color: #fff; font-family: 'Segoe UI', sans-serif; display: flex; flex-wrap: wrap; gap: 20px; padding: 20px; justify-content: center; }
            .card { text-align: center; background: #222; padding: 10px; border-radius: 8px; border: 1px solid #444; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
            .label { margin-bottom: 10px; font-weight: bold; color: #a5b4fc; }
            .hero-container { position: relative; width: 180px; height: 220px; background: #2a2a3a; border-radius: 4px; overflow: hidden; }
            .layer { position: absolute; transform-origin: center center; }
            /* Animation pulse for fun */
            @keyframes pulse { 0% { opacity: 0.8; } 50% { opacity: 1; } 100% { opacity: 0.8; } }
            .hero-container:hover { border: 1px solid #666; }
        </style>
    </head>
    <body>
    """
    
    base_dir = Path.cwd()
    story_theme = "space_pirate"
    manifest = hero_svg_system.load_hero_manifest(story_theme, base_dir=base_dir)
    target_rect = QtCore.QRectF(0, 0, hero_svg_system.HERO_CANVAS_WIDTH, hero_svg_system.HERO_CANVAS_HEIGHT)

    print(f"Generating preview for {len(scenarios)} scenarios...")

    for label, gear in scenarios:
        layers = hero_svg_system.build_hero_layer_plan(
            story_theme=story_theme,
            equipped=gear,
            power_tier="common", 
            base_dir=base_dir,
            manifest=manifest
        )
        
        div_content = ""
        
        for i, layer in enumerate(layers):
            renderer = hero_svg_system._get_cached_renderer(layer.path)
            if not renderer:
                continue
            
            layer_cfg = hero_svg_system._layer_layout_config(manifest, layer, base_dir=base_dir)
            if layer.kind == "gear" and not bool(layer_cfg.get("visible", True)):
                continue

            rect = hero_svg_system.resolve_layer_target_rect(
                layer=layer,
                renderer=renderer,
                target_rect=target_rect,
                manifest=manifest,
                base_dir=base_dir,
            )
            
            rotation_deg = 0.0
            try:
                rotation_deg = float(layer_cfg.get("rotation_deg", layer_cfg.get("rotation", 0.0)) or 0.0)
            except (TypeError, ValueError):
                pass
            
            # Use file protocol for local viewing
            file_url = QtCore.QUrl.fromLocalFile(str(layer.path)).toString()
            
            # Additional Style for SVG animations if needed
            style = (
                f"left: {rect.x()}px; "
                f"top: {rect.y()}px; "
                f"width: {rect.width()}px; "
                f"height: {rect.height()}px; "
                f"z-index: {i};"
            )
            if abs(rotation_deg) > 0.001:
                style += f" transform: rotate({rotation_deg}deg);"
            
            # Use 'data' for object or 'src' for img. Img is safer for layout but sometimes object supports more interact features. 
            # However, for pure preview, img is fine and supports internal SMIL in most modern browsers.
            div_content += f'<img src="{file_url}" class="layer" style="{style}" />\n'
        
        html += f"""
        <div class="card">
            <div class="label">{label}</div>
            <div class="hero-container">
                {div_content}
            </div>
        </div>
        """
        
    html += "</body></html>"
    
    with open("preview_pirate_boots.html", "w", encoding="utf-8") as f:
        f.write(html)
        
    print("Generated preview_pirate_boots.html")

if __name__ == "__main__":
    generate_preview()
