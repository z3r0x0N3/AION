from aion.cyber_visuals import HexGridOverlay, ScanLineOverlay, ParticleSystem


class TestHexGridOverlay:
    def test_create(self, qapp):
        hg = HexGridOverlay()
        assert hg._hex_size == 30
        assert abs(hg._opacity - 0.15) < 0.001

    def test_set_opacity(self, qapp):
        hg = HexGridOverlay()
        hg.set_opacity(0.5)
        assert abs(hg._opacity - 0.5) < 0.001

    def test_set_hex_size(self, qapp):
        hg = HexGridOverlay()
        hg.set_hex_size(50)
        assert hg._hex_size == 50


class TestScanLineOverlay:
    def test_create(self, qapp):
        sl = ScanLineOverlay()
        assert sl._line_spacing == 3


class TestParticleSystem:
    def test_create(self, qapp):
        ps = ParticleSystem()
        assert ps._max_particles == 50
