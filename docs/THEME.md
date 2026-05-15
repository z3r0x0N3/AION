# AION Theme System

## File Format

Themes are JSON files with the following structure:

```json
{
  "theme_name": "my-custom-theme",
  "colors": {
    "background": "#0a0e1a",
    "background_secondary": "#111827",
    "background_tertiary": "#1a2235",
    "surface": "#1e293b",
    "surface_hover": "#263548",
    "border": "#2a3a5c",
    "border_focus": "#00f0ff",
    "text_primary": "#e2e8f0",
    "text_secondary": "#94a3b8",
    "text_accent": "#00f0ff",
    "accent_primary": "#00f0ff",
    "accent_secondary": "#ff00aa",
    "accent_warning": "#ffaa00",
    "accent_error": "#ff3355",
    "accent_success": "#00ff88",
    "glow_accent": "rgba(0, 240, 255, 0.3)",
    "glow_warning": "rgba(255, 170, 0, 0.3)",
    "glow_error": "rgba(255, 51, 85, 0.3)"
  },
  "typography": {
    "font_family_ui": "Inter, SF Pro, sans-serif",
    "font_family_mono": "JetBrains Mono, Fira Code, monospace",
    "font_size_small": 11,
    "font_size_normal": 13,
    "font_size_large": 15,
    "font_size_header": 18,
    "font_size_title": 24
  },
  "spacing": {
    "compact": { "padding": 4, "margin": 2, "gap": 2 },
    "normal": { "padding": 8, "margin": 4, "gap": 4 },
    "comfortable": { "padding": 12, "margin": 8, "gap": 8 }
  },
  "animation": {
    "duration_short_ms": 150,
    "duration_medium_ms": 250,
    "duration_long_ms": 400,
    "easing": "ease_in_out_quad",
    "global_speed_multiplier": 1.0
  }
}
```

## Color Tokens (60+)

| Token | Purpose |
|-------|---------|
| `background` | Main window background |
| `background_secondary` | Panel/tab background |
| `background_tertiary` | Inset/alternate background |
| `surface` | Widget surface |
| `surface_hover` | Hover state |
| `border` | Default border |
| `border_focus` | Focus/active border |
| `text_primary` | Primary text |
| `text_secondary` | Dimmed text |
| `text_accent` | Accent-colored text |
| `accent_primary` | Cyan accent (#00f0ff) |
| `accent_secondary` | Magenta accent (#ff00aa) |
| `accent_warning` | Amber warning |
| `accent_error` | Red error |
| `accent_success` | Green success |
| `glow_*` | Drop shadow glow colors |

## Usage

```python
from aion.theme import load_theme, apply_theme

theme = load_theme("~/.aion/themes/my_theme.json")
apply_theme(theme)
```
