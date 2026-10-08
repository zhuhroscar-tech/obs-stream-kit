import pytest
from obsbuild import layout as L
from obsbuild.applier import Applier
from obsbuild.layout import Box, Item


def creates(fake):
    return [c for c, _ in fake.calls if c.startswith("Create")]


def test_ensure_scene_is_idempotent(fake):
    a = Applier(fake)
    a.ensure_scene("Gaming")
    a.ensure_scene("Gaming")
    assert creates(fake) == ["CreateScene"]


def test_ensure_input_creates_then_updates(fake):
    fake.scenes["Lib"] = {}
    a = Applier(fake)
    a.ensure_input("Lib", "Chat", "browser_source", {"url": "a"})
    a.ensure_input("Lib", "Chat", "browser_source", {"url": "b"})
    assert creates(fake) == ["CreateInput"]
    assert fake.inputs["Chat"][1]["url"] == "b"


def test_place_sends_top_left_bounded_transform_and_visibility(fake):
    fake.scenes["S"] = {}
    a = Applier(fake)
    iid = a.ensure_item("S", "Cam")
    a.place("S", iid, Item("Cam", Box(48, 807, 400, 225), visible=False))
    t = [d for c, d in fake.calls if c == "SetSceneItemTransform"][-1]["sceneItemTransform"]
    assert (t["positionX"], t["positionY"], t["boundsWidth"], t["boundsHeight"]) == (48, 807, 400, 225)
    assert t["alignment"] == 5 and t["boundsType"] == "OBS_BOUNDS_SCALE_INNER"
    assert ("SetSceneItemEnabled", {"sceneName": "S", "sceneItemId": iid, "sceneItemEnabled": False}) in fake.calls


def test_build_scene_orders_items_bottom_to_top(fake):
    Applier(fake).build_scene("S", (Item("A", L.FULL), Item("B", L.FULL)))
    idx = [(d["sceneItemId"], d["sceneItemIndex"]) for c, d in fake.calls if c == "SetSceneItemIndex"]
    assert idx == [(fake.scenes["S"]["A"], 0), (fake.scenes["S"]["B"], 1)]


def test_build_scene_prune_removes_items_not_in_spec(fake):
    a = Applier(fake)
    a.build_scene("S", (Item("A", L.FULL), Item("Old", L.FULL)))
    a.build_scene("S", (Item("A", L.FULL),), prune=True)
    assert set(fake.scenes["S"]) == {"A"}


def test_build_scene_without_prune_keeps_extra_items(fake):
    a = Applier(fake)
    a.build_scene("S", (Item("A", L.FULL), Item("Mine", L.FULL)))
    a.build_scene("S", (Item("A", L.FULL),))
    assert set(fake.scenes["S"]) == {"A", "Mine"}


def test_ensure_filter_creates_then_updates(fake):
    a = Applier(fake)
    a.ensure_filter("Mic", "Limiter", "limiter_filter", {"threshold": -3.0})
    a.ensure_filter("Mic", "Limiter", "limiter_filter", {"threshold": -2.0})
    assert creates(fake) == ["CreateSourceFilter"]
    assert ("SetSourceFilterSettings", {"sourceName": "Mic", "filterName": "Limiter",
                                        "filterSettings": {"threshold": -2.0}, "overlay": True}) in fake.calls


def test_select_device_by_display_name(fake):
    fake.inputs["Camera"] = ("macos-avcapture", {})
    Applier(fake).select_device("Camera", "device", "oscar Camera")
    assert fake.inputs["Camera"][1]["device"] == "UUID-1"


def test_select_device_error_lists_choices(fake):
    fake.inputs["Camera"] = ("macos-avcapture", {})
    with pytest.raises(ValueError, match="available: oscar Camera"):
        Applier(fake).select_device("Camera", "device", "Nope")


def test_collection_and_profile_created_once_then_selected(fake):
    a = Applier(fake)
    a.ensure_collection("Stream Kit")
    a.ensure_profile("Stream Kit")
    fake.current_collection, fake.current_profile = "Untitled", "Untitled"
    a.ensure_collection("Stream Kit")
    a.ensure_profile("Stream Kit")
    assert creates(fake) == ["CreateSceneCollection", "CreateProfile"]
    assert fake.current_collection == "Stream Kit" and fake.current_profile == "Stream Kit"
