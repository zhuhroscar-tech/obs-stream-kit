from obsbuild import layout as L
from obsbuild.doctor import doctor_checks


def test_all_green_on_a_correct_setup(fake):
    for s in L.MAIN_SCENES:
        fake.scenes[s] = {}
    assert all(ok for ok, _ in doctor_checks(fake))


def test_flags_global_mic_duplicate_and_missing_plugin(fake):
    fake.special["mic1"] = "Mic/Aux"
    fake.kinds["filter"] = []
    failed = [msg for ok, msg in doctor_checks(fake) if not ok]
    assert any("Mic/Aux" in m for m in failed)
    assert any("obs_composite_blur" in m for m in failed)
