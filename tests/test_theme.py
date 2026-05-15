import json
import tempfile
from pathlib import Path

from aion.theme import Theme, load_theme, default_theme, CYBER_DARK_DEFAULT


class TestTheme:
    def test_default_theme_has_colors(self):
        theme = default_theme()
        assert theme.name == "aion-cyber-dark"
        assert theme.color_hex("background") == "#0a0e1a"
        assert theme.color_hex("accent_primary") == "#00f0ff"

    def test_color_qcolor(self):
        theme = default_theme()
        c = theme.color("accent_primary")
        assert c.name() == "#00f0ff"

    def test_font(self):
        theme = default_theme()
        font = theme.font("font_family_ui")
        assert font.family() in ("Inter", "SF Pro")

    def test_font_size(self):
        theme = default_theme()
        assert theme.font_size("font_size_normal") == 13
        assert theme.font_size("font_size_title") == 24

    def test_spacing(self):
        theme = default_theme()
        normal = theme.spacing("normal")
        assert normal["padding"] == 8
        compact = theme.spacing("compact")
        assert compact["padding"] == 4

    def test_animation_ms(self):
        theme = default_theme()
        assert theme.animation_ms("duration_medium_ms") == 250
        assert theme.animation_ms("duration_short_ms") == 150

    def test_to_palette(self):
        theme = default_theme()
        palette = theme.to_palette()
        assert palette is not None

    def test_to_stylesheet(self):
        theme = default_theme()
        ss = theme.to_stylesheet()
        assert "#0a0e1a" in ss
        assert "#00f0ff" in ss

    def test_load_theme(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(CYBER_DARK_DEFAULT, f)
            path = f.name
        try:
            theme = load_theme(path)
            assert theme.name == "aion-cyber-dark"
            assert theme.path == path
        finally:
            Path(path).unlink()

    def test_custom_theme(self):
        data = dict(CYBER_DARK_DEFAULT)
        data["colors"]["background"] = "#111111"
        theme = Theme(data)
        assert theme.color_hex("background") == "#111111"
