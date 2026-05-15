from aion.customisation import CustomisationManager, ComponentOverrides


class TestCustomisation:
    def test_get_overrides_creates_default(self):
        mgr = CustomisationManager()
        ov = mgr.get_overrides("panel1")
        assert ov.font_family_ui is None
        assert ov.background_opacity == 1.0
        assert ov.animation_speed == 1.0

    def test_set_font_family(self):
        mgr = CustomisationManager()
        mgr.set_font_family("panel1", "Arial")
        assert mgr.get_overrides("panel1").font_family_ui == "Arial"

    def test_set_font_size(self):
        mgr = CustomisationManager()
        mgr.set_font_size("panel1", 16)
        assert mgr.get_overrides("panel1").font_size_ui == 16

    def test_set_font_size_mono(self):
        mgr = CustomisationManager()
        mgr.set_font_size("terminal", 14, mono=True)
        assert mgr.get_overrides("terminal").font_size_mono == 14

    def test_set_opacity(self):
        mgr = CustomisationManager()
        mgr.set_opacity("overlay", 0.5)
        assert mgr.get_overrides("overlay").background_opacity == 0.5

    def test_set_opacity_clamped(self):
        mgr = CustomisationManager()
        mgr.set_opacity("x", 1.5)
        assert mgr.get_overrides("x").background_opacity == 1.0
        mgr.set_opacity("y", -0.5)
        assert mgr.get_overrides("y").background_opacity == 0.0

    def test_set_animation_speed(self):
        mgr = CustomisationManager()
        mgr.set_animation_speed("panel1", 2.0)
        assert mgr.get_overrides("panel1").animation_speed == 2.0

    def test_global_speed(self):
        mgr = CustomisationManager()
        assert mgr.global_speed == 1.0
        mgr.set_global_speed(0.5)
        assert mgr.global_speed == 0.5

    def test_font_for(self):
        mgr = CustomisationManager()
        mgr.set_font_family("panel1", "Roboto")
        fonts = mgr.font_for("panel1")
        assert fonts["ui"].family() == "Roboto"
        assert fonts["mono"].family() == "JetBrains Mono"

    def test_animation_duration(self):
        mgr = CustomisationManager()
        assert mgr.animation_duration(200) == 200
        mgr.set_global_speed(2.0)
        assert mgr.animation_duration(200) == 100
        mgr.set_global_speed(0.5)
        assert mgr.animation_duration(200) == 400

    def test_on_change_callback(self):
        mgr = CustomisationManager()
        calls = []
        mgr.on_change(lambda c: calls.append(c))
        mgr.set_font_family("x", "Arial")
        assert calls == ["x"]
