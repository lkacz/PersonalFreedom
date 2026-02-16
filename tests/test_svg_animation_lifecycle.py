"""Regression tests for tab-level SVG/WebEngine animation lifecycle guards."""

from __future__ import annotations

import city_tab
import entitidex_tab
import focus_blocker_qt
from city_tab import CityTab


class _DummyPage:
    def __init__(self) -> None:
        self.visible_calls: list[bool] = []
        self.lifecycle_calls: list[object] = []
        self.js_calls: list[str] = []

    def setVisible(self, value: bool) -> None:
        self.visible_calls.append(bool(value))

    def setLifecycleState(self, state) -> None:
        self.lifecycle_calls.append(state)

    def runJavaScript(self, script: str) -> None:
        self.js_calls.append(str(script))


class _DummyWebView:
    def __init__(self, page: _DummyPage) -> None:
        self._page = page

    def page(self) -> _DummyPage:
        return self._page


class _DummyCell:
    def __init__(self, page: _DummyPage, *, visible: bool = True) -> None:
        self._web_view = _DummyWebView(page)
        self._visible = bool(visible)

    def isVisible(self) -> bool:
        return self._visible


class _DummyDeferredLoader:
    def __init__(self) -> None:
        self.web_view = object()
        self._loaded = False
        self._visible = True
        self.load_calls = 0

    def isVisible(self) -> bool:
        return self._visible

    def _load_svg(self) -> None:
        self.load_calls += 1


class _DummyCityWebView:
    def __init__(self) -> None:
        self.set_html_calls = 0

    def setHtml(self, *_args, **_kwargs) -> None:
        self.set_html_calls += 1


class _DummyCityDeferredLoader:
    def __init__(self) -> None:
        self.web_view = _DummyCityWebView()
        self._loaded = False
        self._visible = True
        self.svg_path = "icons/city/example.svg"
        self.set_active_calls: list[bool] = []

    def isVisible(self) -> bool:
        return self._visible

    def _get_cached_svg_content(self, _svg_path: str) -> str:
        return "<svg></svg>"

    def set_active(self, active: bool) -> None:
        self.set_active_calls.append(bool(active))


class _DummyCharacterCanvas:
    """Minimal state carrier for calling CharacterCanvas instance methods."""

    def __init__(self, page: _DummyPage) -> None:
        self.web_view = _DummyWebView(page)
        self._web_content_loaded = True
        self._manage_svg_animations = True
        self._animations_requested = True
        self._svg_sync_calls = 0
        self._mark_dirty_calls = 0
        self._update_calls = 0
        self._web_active_calls: list[bool] = []

    def _update_svg_animation_activity(self) -> None:
        pass

    def _sync_svg_renderer_bindings(self) -> None:
        self._svg_sync_calls += 1

    def _is_web_renderer_active(self) -> bool:
        return True

    def isVisible(self) -> bool:
        return True

    def _mark_render_dirty(self) -> None:
        self._mark_dirty_calls += 1

    def update(self) -> None:
        self._update_calls += 1

    def _set_web_page_active(self, active: bool) -> None:
        self._web_active_calls.append(bool(active))


class _DummyCounter:
    def __init__(self) -> None:
        self.resume_calls = 0
        self.pause_calls = 0
        self.session_active_calls: list[bool] = []
        self.refresh_calls = 0

    def _resume_all_animations(self) -> None:
        self.resume_calls += 1

    def _pause_all_animations(self) -> None:
        self.pause_calls += 1

    def set_session_active(self, active: bool) -> None:
        self.session_active_calls.append(bool(active))

    def refresh_all(self) -> None:
        self.refresh_calls += 1


class _DummyTabs:
    def __init__(self, widget) -> None:
        self._widget = widget

    def widget(self, _index: int):
        return self._widget


class _DummyRestoreTab:
    def __init__(self, *, visible: bool) -> None:
        self._visible = bool(visible)
        self.restore_calls = 0

    def isVisible(self) -> bool:
        return self._visible

    def on_window_restored(self) -> None:
        self.restore_calls += 1


def test_city_pause_resume_uses_nested_cell_shape_and_skips_hidden_cells(monkeypatch):
    """City lifecycle loops must iterate row->cell and not wake hidden cells."""
    visible_page = _DummyPage()
    hidden_page = _DummyPage()
    dummy = type("Dummy", (), {})()
    dummy.city_grid = type("Grid", (), {})()
    dummy.city_grid.cells = [[_DummyCell(visible_page, visible=True), _DummyCell(hidden_page, visible=False)]]
    dummy.isVisible = lambda: True

    monkeypatch.setattr(city_tab, "HAS_WEBENGINE", True)

    CityTab._pause_all_animations(dummy)
    assert visible_page.visible_calls[-1] is False
    assert hidden_page.visible_calls[-1] is False
    if city_tab.QWebEnginePage is not None:
        assert visible_page.lifecycle_calls[-1] == city_tab.QWebEnginePage.LifecycleState.Frozen
        assert hidden_page.lifecycle_calls[-1] == city_tab.QWebEnginePage.LifecycleState.Frozen

    CityTab._resume_all_animations(dummy)
    assert visible_page.visible_calls[-1] is True
    if city_tab.QWebEnginePage is not None:
        assert visible_page.lifecycle_calls[-1] == city_tab.QWebEnginePage.LifecycleState.Active

    # Hidden cell should remain paused during resume.
    assert hidden_page.visible_calls[-1] is False


def test_city_on_window_restored_requires_tab_visibility():
    """Restore hook must not resume city animations while city tab is hidden."""
    calls = {"count": 0, "visible": False}
    dummy = type("Dummy", (), {})()
    dummy.isVisible = lambda: calls["visible"]
    dummy._resume_all_animations = lambda: calls.__setitem__("count", calls["count"] + 1)

    # Hidden tab: no resume.
    calls["visible"] = False
    CityTab.on_window_restored(dummy)
    assert calls["count"] == 0

    # Visible tab: resume exactly once.
    calls["visible"] = True
    CityTab.on_window_restored(dummy)
    assert calls["count"] == 1


def test_city_resume_all_animations_requires_tab_visibility(monkeypatch):
    """City _resume_all_animations should not wake pages if tab is hidden."""
    page = _DummyPage()
    dummy = type("Dummy", (), {})()
    dummy.city_grid = type("Grid", (), {})()
    dummy.city_grid.cells = [[_DummyCell(page, visible=True)]]
    dummy.isVisible = lambda: False

    monkeypatch.setattr(city_tab, "HAS_WEBENGINE", True)
    CityTab._resume_all_animations(dummy)

    assert page.visible_calls == []
    assert page.lifecycle_calls == []


def test_city_refresh_is_noop_while_hidden():
    """_refresh_city should not touch WebEngine/grid state while tab is hidden."""
    calls = {"count": 0}
    dummy = type("Dummy", (), {})()
    dummy.isVisible = lambda: False
    dummy.city_grid = type("Grid", (), {"update_grid": lambda *_args, **_kwargs: calls.__setitem__("count", calls["count"] + 1)})()

    assert not dummy.isVisible()
    CityTab._refresh_city(dummy)
    assert calls["count"] == 0


def test_entitidex_animated_widget_ensure_loaded_requires_visibility() -> None:
    """Deferred loader should not load SVG HTML after a show->hide race."""
    dummy = _DummyDeferredLoader()
    dummy._visible = False

    entitidex_tab.AnimatedSvgWidget.ensure_loaded(dummy)
    assert dummy._loaded is False
    assert dummy.load_calls == 0

    dummy._visible = True
    entitidex_tab.AnimatedSvgWidget.ensure_loaded(dummy)
    assert dummy._loaded is True
    assert dummy.load_calls == 1


def test_city_animated_widget_ensure_loaded_requires_visibility() -> None:
    """City deferred loader should not load SVG HTML while hidden."""
    dummy = _DummyCityDeferredLoader()
    dummy._visible = False

    city_tab.AnimatedBuildingWidget.ensure_loaded(dummy)
    assert dummy._loaded is False
    assert dummy.web_view.set_html_calls == 0

    dummy._visible = True
    city_tab.AnimatedBuildingWidget.ensure_loaded(dummy)
    assert dummy._loaded is True
    assert dummy.web_view.set_html_calls == 1
    assert dummy.set_active_calls and dummy.set_active_calls[-1] is True


def test_character_canvas_web_page_active_toggles_visibility_and_css(monkeypatch):
    """Hero canvas should explicitly pause/resume WebEngine page lifecycle + CSS animation state."""
    page = _DummyPage()
    dummy = type("Dummy", (), {})()
    dummy.web_view = _DummyWebView(page)
    dummy._web_content_loaded = True

    monkeypatch.setattr(focus_blocker_qt, "HAS_WEBENGINE", True)

    focus_blocker_qt.CharacterCanvas._set_web_page_active(dummy, True)
    assert page.visible_calls[-1] is True
    assert page.js_calls and "animationPlayState = ''" in page.js_calls[-1]
    if focus_blocker_qt.QWebEnginePage is not None:
        assert page.lifecycle_calls[-1] == focus_blocker_qt.QWebEnginePage.LifecycleState.Active

    focus_blocker_qt.CharacterCanvas._set_web_page_active(dummy, False)
    assert page.visible_calls[-1] is False
    assert page.js_calls and "animationPlayState = 'paused'" in page.js_calls[-1]
    if focus_blocker_qt.QWebEnginePage is not None:
        assert page.lifecycle_calls[-1] == focus_blocker_qt.QWebEnginePage.LifecycleState.Frozen


def test_character_canvas_pause_resume_controls_web_page_state() -> None:
    """Hero canvas pause/resume should freeze and reactivate WebEngine when active."""
    page = _DummyPage()
    dummy = _DummyCharacterCanvas(page)

    focus_blocker_qt.CharacterCanvas.pause_animations(dummy)
    assert dummy._animations_requested is False
    assert dummy._web_active_calls[-1] is False

    focus_blocker_qt.CharacterCanvas.resume_animations(dummy)
    assert dummy._animations_requested is True
    assert dummy._svg_sync_calls == 1
    assert dummy._web_active_calls[-1] is True
    assert dummy._mark_dirty_calls == 1
    assert dummy._update_calls == 1


def test_character_canvas_pause_resume_controls_web_page_even_when_html_not_loaded() -> None:
    """Lifecycle state should still toggle while HTML load is in-flight."""
    page = _DummyPage()
    dummy = _DummyCharacterCanvas(page)
    dummy._web_content_loaded = False

    focus_blocker_qt.CharacterCanvas.pause_animations(dummy)
    assert dummy._animations_requested is False
    assert dummy._web_active_calls[-1] is False

    focus_blocker_qt.CharacterCanvas.resume_animations(dummy)
    assert dummy._animations_requested is True
    assert dummy._web_active_calls[-1] is True


def test_entitidex_resume_all_animations_requires_tab_visibility() -> None:
    """Entitidex should not mark itself visible on hidden resume calls."""
    dummy = type("Dummy", (), {})()
    dummy._initialized = True
    dummy._is_visible = False
    dummy.theme_tabs = {}
    dummy._current_theme_index = 0
    dummy._all_cards = []
    dummy._celebration_cards = []
    dummy.isVisible = lambda: False
    dummy._get_theme_keys = lambda: []

    entitidex_tab.EntitidexTab._resume_all_animations(dummy)
    assert dummy._is_visible is False


def test_entity_card_resume_animations_requires_visibility() -> None:
    """Entity card should keep paused state when resume is requested offscreen."""
    class _Icon:
        def __init__(self) -> None:
            self.calls = 0

        def restart_animations(self) -> None:
            self.calls += 1

    dummy = type("Dummy", (), {})()
    dummy._animations_paused = True
    dummy._glow_animation = None
    dummy._icon_opacity_anim = None
    dummy._shimmer_timer = None
    dummy._icon_widget = _Icon()
    dummy.isVisible = lambda: False

    entitidex_tab.EntityCard.resume_animations(dummy)

    assert dummy._animations_paused is True
    assert dummy._icon_widget.calls == 0


def test_celebration_card_resume_animations_requires_visibility() -> None:
    """Celebration card should keep paused state when resume is requested offscreen."""
    class _Svg:
        def __init__(self) -> None:
            self.calls = 0

        def restart_animations(self) -> None:
            self.calls += 1

    dummy = type("Dummy", (), {})()
    dummy._animations_paused = True
    dummy._glow_animation = None
    dummy._shimmer_timer = None
    dummy._svg_widget = _Svg()
    dummy.isVisible = lambda: False

    entitidex_tab.CelebrationCard.resume_animations(dummy)

    assert dummy._animations_paused is True
    assert dummy._svg_widget.calls == 0


def test_adhd_tab_resume_all_animations_requires_visibility() -> None:
    """Hero tab manager should not resume canvas while tab is hidden."""
    class _Canvas:
        def __init__(self) -> None:
            self.calls = 0

        def resume_animations(self) -> None:
            self.calls += 1

    dummy = type("Dummy", (), {})()
    dummy.char_canvas = _Canvas()
    dummy.isVisible = lambda: False

    focus_blocker_qt.ADHDBusterTab._resume_all_animations(dummy)
    assert dummy.char_canvas.calls == 0


def test_main_tab_changed_does_not_resume_animations_when_window_hidden(monkeypatch) -> None:
    """Main tab-change handler should keep animated tabs paused offscreen."""
    monkeypatch.setattr(focus_blocker_qt, "GAMIFICATION_AVAILABLE", True)

    entitidex = _DummyCounter()
    adhd = _DummyCounter()
    city = _DummyCounter()

    dummy = type("Dummy", (), {})()
    dummy.entitidex_tab = entitidex
    dummy.adhd_tab = adhd
    dummy.city_tab = city
    dummy.tabs = _DummyTabs(entitidex)
    dummy.isVisible = lambda: False
    dummy.isMinimized = lambda: False
    dummy._load_deferred_tab_for_index = lambda _index: None

    focus_blocker_qt.FocusBlockerWindow._on_tab_changed(dummy, 0)

    assert entitidex.resume_calls == 0
    assert entitidex.pause_calls == 1
    assert adhd.resume_calls == 0
    assert adhd.pause_calls == 1
    assert city.resume_calls == 0
    assert city.pause_calls == 1


def test_main_tab_changed_resumes_only_selected_when_window_visible(monkeypatch) -> None:
    """Visible app should resume only selected animated tab and pause others."""
    monkeypatch.setattr(focus_blocker_qt, "GAMIFICATION_AVAILABLE", True)

    entitidex = _DummyCounter()
    adhd = _DummyCounter()
    city = _DummyCounter()

    dummy = type("Dummy", (), {})()
    dummy.entitidex_tab = entitidex
    dummy.adhd_tab = adhd
    dummy.city_tab = city
    dummy.tabs = _DummyTabs(adhd)
    dummy.isVisible = lambda: True
    dummy.isMinimized = lambda: False
    dummy._load_deferred_tab_for_index = lambda _index: None
    dummy.timer_tab = type("TimerTab", (), {"timer_running": False})()

    focus_blocker_qt.FocusBlockerWindow._on_tab_changed(dummy, 0)

    assert entitidex.resume_calls == 0
    assert entitidex.pause_calls == 1
    assert adhd.resume_calls == 1
    assert adhd.pause_calls == 0
    assert city.resume_calls == 0
    assert city.pause_calls == 1


def test_restore_from_tray_resumes_only_visible_tabs() -> None:
    """Tray restore should only invoke per-tab restore hooks for visible tabs."""
    entitidex = _DummyRestoreTab(visible=False)
    adhd = _DummyRestoreTab(visible=True)
    city = _DummyRestoreTab(visible=False)

    class _DummyWindow:
        def __init__(self) -> None:
            self._defer_tabs_until_visible = True
            self._deferred_tabs_started = False
            self.deferred_starts = 0
            self.show_normal_calls = 0
            self.raise_calls = 0
            self.activate_calls = 0
            self.entitidex_tab = entitidex
            self.adhd_tab = adhd
            self.city_tab = city

        def showNormal(self) -> None:
            self.show_normal_calls += 1

        def raise_(self) -> None:
            self.raise_calls += 1

        def activateWindow(self) -> None:
            self.activate_calls += 1

        def _start_deferred_tab_loading(self) -> None:
            self.deferred_starts += 1
            self._deferred_tabs_started = True

    dummy = _DummyWindow()

    focus_blocker_qt.FocusBlockerWindow._restore_from_tray(dummy)

    assert dummy.show_normal_calls == 1
    assert dummy.raise_calls == 1
    assert dummy.activate_calls == 1
    assert dummy.deferred_starts == 1
    assert entitidex.restore_calls == 0
    assert adhd.restore_calls == 1
    assert city.restore_calls == 0


def test_character_canvas_defers_web_html_update_while_hidden(monkeypatch) -> None:
    """Hero WebEngine HTML updates should be deferred until the canvas is visible."""
    class _DummyCanvas:
        BASE_W = 180
        BASE_H = 220

        def __init__(self) -> None:
            self.web_view = object()
            self.story_theme = "warrior"
            self.equipped = {}
            self.tier = "pathetic"
            self._web_content_dirty = False
            self._inject_calls = 0
            self._visible = False

        def isVisible(self) -> bool:
            return self._visible

        def _inject_scaled_html(self, _html: str) -> None:
            self._inject_calls += 1

    monkeypatch.setattr(
        focus_blocker_qt,
        "generate_hero_composed_html",
        lambda **_kwargs: "<html><body>ok</body></html>",
    )

    dummy = _DummyCanvas()
    focus_blocker_qt.CharacterCanvas._update_web_engine_content(dummy)
    assert dummy._web_content_dirty is True
    assert dummy._inject_calls == 0

    dummy._visible = True
    focus_blocker_qt.CharacterCanvas._update_web_engine_content(dummy)
    assert dummy._web_content_dirty is False
    assert dummy._inject_calls == 1
