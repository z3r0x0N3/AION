from aion.sound_engine import SoundEngine, SOUND_EVENTS


class TestSoundEngine:
    def test_create(self):
        engine = SoundEngine()
        assert engine.volume == 0.5
        assert engine.muted is False

    def test_mute_unmute(self):
        engine = SoundEngine()
        assert engine.muted is False
        engine.mute()
        assert engine.muted is True
        engine.unmute()
        assert engine.muted is False

    def test_set_volume(self):
        engine = SoundEngine()
        engine.set_volume(0.8)
        assert engine.volume == 0.8

    def test_play_muted_does_not_error(self):
        engine = SoundEngine()
        engine.mute()
        engine.play("tab_switch")  # should not raise

    def test_available_events(self):
        engine = SoundEngine()
        assert isinstance(engine.available_events, list)

    def test_sound_events_list(self):
        assert "tab_switch" in SOUND_EVENTS
        assert "error" in SOUND_EVENTS
        assert len(SOUND_EVENTS) == 20
