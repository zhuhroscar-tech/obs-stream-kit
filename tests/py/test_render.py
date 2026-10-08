import pytest
from obsbuild.render import MODES, config_js, render, screen_html


def test_config_js_only_exposes_public_keys():
    js = config_js({"display_name": "Oscar", "socials": ["a"],
                    "streamelements_alertbox_url": "https://secret", "chat_url": "https://x"})
    assert js.startswith("window.KIT = ")
    assert "Oscar" in js and "secret" not in js and "https://x" not in js


def test_screen_html_injects_mode_once():
    out = screen_html("<html><body><p>x</p></body></html>", "brb")
    assert out.count('<body data-mode="brb">') == 1


def test_screen_html_rejects_unknown_mode_and_bad_template():
    with pytest.raises(ValueError):
        screen_html("<body>", "nope")
    with pytest.raises(ValueError):
        screen_html("<html></html>", "brb")


def test_render_writes_config_and_every_screen(tmp_path):
    (tmp_path / "overlays").mkdir()
    (tmp_path / "overlays" / "screen.template.html").write_text("<body></body>", encoding="utf-8")
    paths = render({"display_name": "X"}, tmp_path)
    assert sorted(p.name for p in paths) == sorted(["config.js"] + [f"screen-{m}.html" for m in MODES])
    assert all(p.exists() for p in paths)
