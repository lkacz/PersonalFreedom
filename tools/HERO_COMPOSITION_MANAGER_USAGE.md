# Hero Composition Manager

Run:

```powershell
python tools/hero_composition_manager.py
```

Optional startup args:

```powershell
python tools/hero_composition_manager.py --theme underdog
python tools/hero_composition_manager.py --theme robot --profile artifacts/hero_composition/robot_composition_profile.json
```

## What It Does

- Loads selected theme `hero_base.svg`.
- Loads one gear layer per slot with selected rarity.
- Lets you drag layers in canvas.
- Lets you scale selected layer with `Ctrl + mouse wheel`.
- Lets you rotate selected layer with `Shift + mouse wheel`.
- Saves and loads composition profiles.
- App runtime automatically consumes saved profiles from `artifacts/hero_composition/`.

## Save Format

Profiles are written to:

- `artifacts/hero_composition/<theme>_composition_profile.json`

Current schema is `schema_version: 2` and stores transforms per `slot + rarity`.

Backward compatibility:

- Older v1 slot-only profiles still load.
