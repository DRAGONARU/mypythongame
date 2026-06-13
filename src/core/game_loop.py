from typing import Callable
import time


class GameLoop:
    """Fixed-timestep game loop with accumulator pattern.

    Runs logic at a constant 120 Hz tick rate regardless of frame rate.
    Accumulates real elapsed time and consumes it in FIXED_DT chunks.
    If the accumulator grows too large (spiral of death), it is reset
    after MAX_TICKS_PER_FRAME ticks in a single frame.

    Rendering receives an interpolation alpha [0, 1) for smooth visual
    positioning between logic ticks.

    Attributes:
        FIXED_DT: Duration of one logic tick in seconds (1/120).
        MAX_TICKS_PER_FRAME: Maximum ticks processed per frame to guard
            against spiral of death.
    """

    FIXED_DT: float = 1.0 / 120.0
    MAX_TICKS_PER_FRAME: int = 5

    def __init__(
            self,
            tick_fn: Callable[[float], None],
            render_fn: Callable[[float], None],
    ):
        """Initialise the game loop.

        Args:
            tick_fn: Called once per logic tick with FIXED_DT as argument.
            render_fn: Called once per frame with interpolation alpha [0, 1).
        """
        self._tick_fn = tick_fn
        self._render_fn = render_fn
        self._accumulator: float = 0.0
        self._running: bool = False
        self._tick: int = 0

    @property
    def tick(self) -> int:
        """Current logic tick count, incremented after each tick_fn call."""
        return self._tick

    def start(self) -> None:
        """Run the main loop until stop() is called.

        Measures real elapsed time with time.perf_counter, caps single
        frame delta at 0.25 s to avoid huge spikes after a freeze, and
        resets the accumulator when it exceeds one tick after hitting
        MAX_TICKS_PER_FRAME (spiral-of-death guard).
        """
        self._running = True
        prev_time = time.perf_counter()

        while self._running:
            now = time.perf_counter()
            real_dt = min(now - prev_time, 0.25)
            prev_time = now
            self._accumulator += real_dt
            ticks_done = 0
            while self._accumulator >= self.FIXED_DT and ticks_done < self.MAX_TICKS_PER_FRAME:
                self._tick_fn(self.FIXED_DT)
                self._tick += 1
                self._accumulator -= self.FIXED_DT
                ticks_done += 1

            if self._accumulator > self.FIXED_DT:
                self._accumulator = 0.0

            alpha = self._accumulator / self.FIXED_DT
            self._render_fn(alpha)

    def stop(self) -> None:
        """Signal the loop to exit after the current frame completes."""
        self._running = False
