from obsbuild import layout as L


def _item(scene, source):
    return next(i for i in L.scenes()[scene] if i.source == source)


def test_main_scene_names_and_order():
    assert tuple(L.scenes()) == L.MAIN_SCENES


def test_every_box_is_inside_the_canvas():
    for scene, items in L.scenes().items():
        for it in items:
            assert it.box.inside_canvas(), (scene, it)


def test_gaming_cam_brand_and_alert_zone_never_overlap():
    cam, brand = _item("Gaming", L.CAM).box, _item("Gaming", L.BRAND).box
    alert = L.Box(*L.ALERT_ZONE)
    assert not cam.intersects(brand)
    assert not cam.intersects(alert)
    assert not brand.intersects(alert)


def test_chat_hidden_while_gaming_and_visible_in_talk_scenes():
    assert _item("Gaming", L.CHAT).visible is False
    assert _item("Just Chatting", L.CHAT).visible is True
    assert _item("React", L.CHAT).visible is True


def test_move_transition_needs_same_names_across_live_scenes():
    for scene in ("Gaming", "Just Chatting", "React"):
        names = [i.source for i in L.scenes()[scene]]
        assert L.CAM in names and L.BRAND in names and L.ALERTS in names


def test_cam_is_always_16_by_9():
    for scene in ("Gaming", "Just Chatting", "React"):
        b = _item(scene, L.CAM).box
        assert b.w * 9 == b.h * 16, scene


def test_chat_is_anchored_bottom_left_everywhere():
    for scene, items in L.scenes().items():
        for it in items:
            if it.source == L.CHAT:
                assert it.align == L.ALIGN_BOTTOM_LEFT, scene


def test_privacy_shows_only_the_privacy_screen_with_music():
    assert [i.source for i in L.scenes()["Privacy"]] == [L.SCREEN["privacy"], L.MUSIC]


def test_mic_is_physically_absent_from_brb_and_privacy():
    # Audio only plays from sources in the program scene, so leaving Mic out is a hard mute
    # that cannot fail the way an automation macro can.
    for scene, items in L.scenes().items():
        has_mic = L.MIC in [i.source for i in items]
        assert has_mic == (scene not in ("BRB", "Privacy")), scene


def test_desktop_audio_only_in_live_scenes():
    for scene, items in L.scenes().items():
        has_desktop = L.AUDIO in [i.source for i in items]
        assert has_desktop == (scene in ("Gaming", "Just Chatting", "React")), scene
