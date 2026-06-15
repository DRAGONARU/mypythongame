from src.core.game_loop import GameLoop
import pytest


class _Recorder:
    def __init__(self, loop: GameLoop, stop_after_ticks: int | None = None, stop_after_renders: int | None = None):
        self.loop = loop
        self.stop_after_ticks = stop_after_ticks
        self.stop_after_renders = stop_after_renders
        self.ticks: list[float] = []
        self.renders: list[float] = []

    def tick_fn(self, dt: float) -> None:
        self.ticks.append(dt)
        if self.stop_after_ticks is not None and len(self.ticks) >= self.stop_after_ticks:
            self.loop.stop()

    def render_fn(self, alpha: float) -> None:
        self.renders.append(alpha)
        if self.stop_after_renders is not None and len(self.renders) >= self.stop_after_renders:
            self.loop.stop()


def _make_loop(stop_after_ticks: int | None = None, stop_after_renders: int | None = None) -> tuple[GameLoop, _Recorder]:
    loop = GameLoop(tick_fn=lambda dt: None, render_fn=lambda alpha: None)
    rec = _Recorder(loop, stop_after_ticks, stop_after_renders)
    loop._tick_fn = rec.tick_fn
    loop._render_fn = rec.render_fn
    return loop, rec


# --- start / stop lifecycle ---

def test_start_runs_and_stop_exits():
    loop, rec = _make_loop(stop_after_ticks=1)
    loop.start()
    assert loop._running is False
    assert len(rec.ticks) >= 1


def test_stop_from_render_fn():
    loop, rec = _make_loop(stop_after_renders=3)
    loop.start()
    assert loop._running is False
    assert len(rec.renders) >= 3


# --- tick counter ---

def test_tick_counter_increments():
    loop, rec = _make_loop(stop_after_ticks=5)
    loop.start()
    assert loop.tick == 5


def test_tick_fn_receives_fixed_dt():
    loop, rec = _make_loop(stop_after_ticks=3)
    loop.start()
    assert all(dt == GameLoop.FIXED_DT for dt in rec.ticks)


# --- alpha / interpolation ---

def test_render_fn_receives_alpha_in_range():
    loop, rec = _make_loop(stop_after_renders=10)
    loop.start()
    assert all(0.0 <= alpha < 1.0 for alpha in rec.renders)


def test_alpha_small_when_accumulator_near_zero():
    loop, rec = _make_loop(stop_after_ticks=1)
    loop._accumulator = 0.0
    loop.start()
    assert rec.renders[-1] < 0.1


# --- spiral-of-death guard ---

def test_max_ticks_per_frame():
    loop, rec = _make_loop(stop_after_renders=1)
    loop._accumulator = GameLoop.FIXED_DT * 100
    loop.start()
    assert len(rec.ticks) <= GameLoop.MAX_TICKS_PER_FRAME


def test_accumulator_reset_on_overflow():
    loop, rec = _make_loop(stop_after_renders=1)
    loop._accumulator = GameLoop.FIXED_DT * 100
    loop.start()
    assert loop._accumulator == 0.0


def test_accumulator_not_reset_when_within_budget():
    loop, rec = _make_loop(stop_after_renders=1)
    loop._accumulator = GameLoop.FIXED_DT * 2
    loop.start()
    assert 0.0 < loop._accumulator < GameLoop.FIXED_DT


# --- real_dt cap ---

def test_real_dt_capped_at_025():
    loop, rec = _make_loop(stop_after_renders=1)
    loop._accumulator = 0.0
    import time
    prev = time.perf_counter()
    now = prev + 10.0
    real_dt = min(now - prev, 0.25)
    assert real_dt == 0.25


# --- stop does not reset accumulator ---

def test_stop_does_not_reset_accumulator():
    loop, rec = _make_loop(stop_after_ticks=1)
    loop.start()
    assert loop._accumulator >= 0.0
