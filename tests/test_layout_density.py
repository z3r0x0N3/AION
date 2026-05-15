from aion.layout_density import DensityManager, LayoutDensity, DENSITY_VALUES


class TestDensityManager:
    def test_default_is_normal(self):
        dm = DensityManager()
        assert dm.current == LayoutDensity.NORMAL

    def test_set_density(self):
        dm = DensityManager()
        dm.current = LayoutDensity.COMPACT
        assert dm.current == LayoutDensity.COMPACT

    def test_values(self):
        dm = DensityManager()
        vals = dm.values()
        assert "padding" in vals
        assert "margin" in vals
        assert "spacing" in vals

    def test_compact_values(self):
        dm = DensityManager()
        dm.current = LayoutDensity.COMPACT
        v = dm.values()
        assert v["padding"] == 2
        assert v["spacing"] == 2

    def test_comfortable_values(self):
        dm = DensityManager()
        dm.current = LayoutDensity.COMFORTABLE
        v = dm.values()
        assert v["padding"] == 12
        assert v["margin"] == 8

    def test_on_change(self):
        dm = DensityManager()
        calls = []
        dm.on_change(lambda d: calls.append(d))
        dm.current = LayoutDensity.COMPACT
        assert calls == [LayoutDensity.COMPACT]

    def test_enum_values(self):
        assert LayoutDensity.COMPACT.value == "compact"
        assert LayoutDensity.NORMAL.value == "normal"
        assert LayoutDensity.COMFORTABLE.value == "comfortable"
