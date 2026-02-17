"""
Lightweight performance telemetry helpers for hero rendering paths.

This module is intentionally dependency-free so it can be reused by UI and
tooling code without pulling Qt objects into tests.
"""

from __future__ import annotations

import logging
import math
import os
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Optional


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name, "1" if default else "0")
    return str(raw).strip().lower() not in {"0", "false", "no", "off"}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return int(default)
    try:
        return max(1, int(str(raw).strip()))
    except (TypeError, ValueError):
        return int(default)


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return float(default)
    try:
        return max(0.05, float(str(raw).strip()))
    except (TypeError, ValueError):
        return float(default)


def _metric_env_token(metric: str) -> str:
    token = "".join(ch if ch.isalnum() else "_" for ch in str(metric))
    token = token.strip("_").upper()
    return token or "METRIC"


DEFAULT_P95_WARN_THRESHOLDS_MS: dict[str, float] = {
    "paint_event_ms": 16.6,
    "render_content_ms": 16.6,
    "web.compose_html_ms": 16.6,
    "web.update_content_ms": 25.0,
    "web.inject_html_ms": 16.6,
    "hero.equip_change_ms": 50.0,
    "hero.refresh_all_ms": 80.0,
    "hero.refresh_slot_combos_ms": 50.0,
    "hero.refresh_character_ms": 50.0,
    "hero.refresh_inventory_ms": 50.0,
}


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(float(v) for v in values)
    if len(sorted_values) == 1:
        return sorted_values[0]
    q = max(0.0, min(100.0, float(q)))
    rank = (len(sorted_values) - 1) * (q / 100.0)
    lower = int(math.floor(rank))
    upper = int(math.ceil(rank))
    if lower == upper:
        return sorted_values[lower]
    weight = rank - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


@dataclass
class RollingMetricWindow:
    max_samples: int = 240
    _samples: deque[float] = field(default_factory=deque, init=False)

    def __post_init__(self) -> None:
        self._samples = deque(maxlen=max(1, int(self.max_samples)))

    def add(self, value_ms: float) -> None:
        try:
            self._samples.append(float(value_ms))
        except (TypeError, ValueError):
            return

    def snapshot(self) -> dict:
        values = list(self._samples)
        if not values:
            return {
                "count": 0,
                "avg_ms": 0.0,
                "p50_ms": 0.0,
                "p95_ms": 0.0,
                "max_ms": 0.0,
                "last_ms": 0.0,
            }
        count = len(values)
        avg = sum(values) / float(count)
        return {
            "count": count,
            "avg_ms": avg,
            "p50_ms": _percentile(values, 50.0),
            "p95_ms": _percentile(values, 95.0),
            "max_ms": max(values),
            "last_ms": values[-1],
        }


class HeroPerfTelemetry:
    """Rolling metric collection + periodic summary logging."""

    def __init__(
        self,
        *,
        enabled: bool = False,
        scope: str = "hero",
        sample_size: int = 240,
        log_interval_s: float = 5.0,
        min_samples_to_log: int = 20,
        warn_enabled: bool = True,
        warn_interval_s: float = 15.0,
        default_warn_p95_ms: float = 0.0,
        metric_warn_p95_ms: Optional[dict[str, float]] = None,
        logger_obj: Optional[logging.Logger] = None,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        self.enabled = bool(enabled)
        self.scope = str(scope or "hero")
        self.sample_size = max(1, int(sample_size))
        self.log_interval_s = max(0.05, float(log_interval_s))
        self.min_samples_to_log = max(1, int(min_samples_to_log))
        self.warn_enabled = bool(warn_enabled)
        self.warn_interval_s = max(0.05, float(warn_interval_s))
        self.default_warn_p95_ms = max(0.0, float(default_warn_p95_ms))
        self.metric_warn_p95_ms = {
            str(metric): max(0.0, float(value))
            for metric, value in (metric_warn_p95_ms or {}).items()
        }
        self.logger = logger_obj or logging.getLogger(__name__)
        self._clock = clock or time.perf_counter
        self._windows: dict[str, RollingMetricWindow] = {}
        self._last_log_at: dict[str, float] = {}
        self._last_warn_at: dict[str, float] = {}

    @classmethod
    def from_env(
        cls,
        *,
        prefix: str = "PF_HERO_PERF",
        scope: str = "hero",
        logger_obj: Optional[logging.Logger] = None,
        clock: Optional[Callable[[], float]] = None,
    ) -> "HeroPerfTelemetry":
        enabled = _env_bool(f"{prefix}_TELEMETRY", False)
        sample_size = _env_int(f"{prefix}_SAMPLE_SIZE", 240)
        log_interval_ms = _env_float(f"{prefix}_LOG_INTERVAL_MS", 5000.0)
        min_samples = _env_int(f"{prefix}_MIN_SAMPLES", 20)
        warn_enabled = _env_bool(f"{prefix}_WARNINGS", True)
        warn_interval_ms = _env_float(f"{prefix}_WARN_INTERVAL_MS", 15000.0)
        default_warn_p95_ms = _env_float(f"{prefix}_WARN_DEFAULT_P95_MS", 0.0)
        metric_warn_p95_ms: dict[str, float] = dict(DEFAULT_P95_WARN_THRESHOLDS_MS)
        for metric in list(metric_warn_p95_ms.keys()):
            env_key = f"{prefix}_WARN_{_metric_env_token(metric)}_P95_MS"
            metric_warn_p95_ms[metric] = _env_float(env_key, metric_warn_p95_ms[metric])
        return cls(
            enabled=enabled,
            scope=scope,
            sample_size=sample_size,
            log_interval_s=log_interval_ms / 1000.0,
            min_samples_to_log=min_samples,
            warn_enabled=warn_enabled,
            warn_interval_s=warn_interval_ms / 1000.0,
            default_warn_p95_ms=default_warn_p95_ms,
            metric_warn_p95_ms=metric_warn_p95_ms,
            logger_obj=logger_obj,
            clock=clock,
        )

    def _window(self, metric: str) -> RollingMetricWindow:
        key = str(metric)
        window = self._windows.get(key)
        if window is None:
            window = RollingMetricWindow(max_samples=self.sample_size)
            self._windows[key] = window
        return window

    def record(self, metric: str, elapsed_ms: float, *, context: Optional[dict] = None) -> None:
        if not self.enabled:
            return
        key = str(metric)
        window = self._window(key)
        window.add(elapsed_ms)

        snap = window.snapshot()
        if snap["count"] < self.min_samples_to_log:
            return

        now = float(self._clock())
        last_log = float(self._last_log_at.get(key, 0.0))
        if (now - last_log) < self.log_interval_s:
            return
        self._last_log_at[key] = now

        ctx = ""
        if context:
            parts = [f"{k}={v}" for k, v in sorted(context.items())]
            if parts:
                ctx = " " + " ".join(parts)
        self.logger.info(
            "[%s] %s avg=%.2fms p95=%.2fms max=%.2fms n=%d%s",
            self.scope,
            key,
            snap["avg_ms"],
            snap["p95_ms"],
            snap["max_ms"],
            snap["count"],
            ctx,
        )
        self._maybe_warn(key, snap, now=now, context=context)

    def _warn_threshold(self, metric: str) -> float:
        metric_threshold = self.metric_warn_p95_ms.get(str(metric))
        if metric_threshold is not None and metric_threshold > 0.0:
            return float(metric_threshold)
        if self.default_warn_p95_ms > 0.0:
            return float(self.default_warn_p95_ms)
        return 0.0

    def _maybe_warn(self, metric: str, snap: dict, *, now: float, context: Optional[dict]) -> None:
        if not self.warn_enabled:
            return
        threshold = self._warn_threshold(metric)
        if threshold <= 0.0:
            return
        p95 = float(snap.get("p95_ms", 0.0))
        if p95 <= threshold:
            return
        last_warn = float(self._last_warn_at.get(metric, 0.0))
        if (now - last_warn) < self.warn_interval_s:
            return
        self._last_warn_at[metric] = now

        ctx = ""
        if context:
            parts = [f"{k}={v}" for k, v in sorted(context.items())]
            if parts:
                ctx = " " + " ".join(parts)
        self.logger.warning(
            "[%s] %s p95 breach: p95=%.2fms threshold=%.2fms avg=%.2fms max=%.2fms n=%d%s",
            self.scope,
            metric,
            p95,
            threshold,
            float(snap.get("avg_ms", 0.0)),
            float(snap.get("max_ms", 0.0)),
            int(snap.get("count", 0)),
            ctx,
        )

    def breach_snapshot(self) -> dict[str, dict]:
        breaches: dict[str, dict] = {}
        for metric, window in self._windows.items():
            snap = window.snapshot()
            threshold = self._warn_threshold(metric)
            if threshold <= 0.0:
                continue
            if float(snap.get("p95_ms", 0.0)) <= threshold:
                continue
            breaches[metric] = {
                "threshold_p95_ms": threshold,
                **snap,
            }
        return breaches

    def snapshot(self) -> dict[str, dict]:
        return {metric: window.snapshot() for metric, window in self._windows.items()}
