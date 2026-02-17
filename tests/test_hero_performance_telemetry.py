from hero_performance_telemetry import HeroPerfTelemetry, RollingMetricWindow


class _DummyLogger:
    def __init__(self) -> None:
        self.info_calls: list[tuple] = []
        self.warning_calls: list[tuple] = []

    def info(self, *args, **kwargs) -> None:
        self.info_calls.append((args, kwargs))

    def warning(self, *args, **kwargs) -> None:
        self.warning_calls.append((args, kwargs))


def test_rolling_metric_window_snapshot() -> None:
    window = RollingMetricWindow(max_samples=5)
    for value in (10, 20, 30, 40, 50):
        window.add(value)

    snap = window.snapshot()
    assert snap["count"] == 5
    assert abs(snap["avg_ms"] - 30.0) < 0.001
    assert snap["p95_ms"] >= 45.0
    assert snap["max_ms"] == 50.0
    assert snap["last_ms"] == 50.0


def test_telemetry_disabled_keeps_snapshot_empty() -> None:
    telemetry = HeroPerfTelemetry(enabled=False)
    telemetry.record("paint_event_ms", 12.5)
    assert telemetry.snapshot() == {}


def test_telemetry_logs_after_interval() -> None:
    logger = _DummyLogger()
    now = [0.0]

    def _clock() -> float:
        return now[0]

    telemetry = HeroPerfTelemetry(
        enabled=True,
        scope="hero_tab",
        sample_size=16,
        log_interval_s=5.0,
        min_samples_to_log=1,
        logger_obj=logger,
        clock=_clock,
    )

    telemetry.record("equip_change_ms", 4.0)
    assert len(logger.info_calls) == 0

    now[0] = 5.1
    telemetry.record("equip_change_ms", 6.0, context={"slot": "Helmet"})
    assert len(logger.info_calls) == 1

    args, _kwargs = logger.info_calls[0]
    assert "hero_tab" in args[1]
    assert "equip_change_ms" in args[2]


def test_from_env_reads_configuration(monkeypatch) -> None:
    monkeypatch.setenv("PF_HERO_PERF_TELEMETRY", "1")
    monkeypatch.setenv("PF_HERO_PERF_SAMPLE_SIZE", "42")
    monkeypatch.setenv("PF_HERO_PERF_LOG_INTERVAL_MS", "2500")
    monkeypatch.setenv("PF_HERO_PERF_MIN_SAMPLES", "7")

    telemetry = HeroPerfTelemetry.from_env(scope="canvas")
    assert telemetry.enabled is True
    assert telemetry.sample_size == 42
    assert abs(telemetry.log_interval_s - 2.5) < 1e-6
    assert telemetry.min_samples_to_log == 7


def test_telemetry_warns_on_p95_breach_and_snapshot_reports_breach() -> None:
    logger = _DummyLogger()
    now = [0.0]

    def _clock() -> float:
        return now[0]

    telemetry = HeroPerfTelemetry(
        enabled=True,
        scope="hero_canvas",
        sample_size=16,
        log_interval_s=2.0,
        min_samples_to_log=1,
        warn_enabled=True,
        warn_interval_s=2.0,
        default_warn_p95_ms=0.0,
        metric_warn_p95_ms={"paint_event_ms": 8.0},
        logger_obj=logger,
        clock=_clock,
    )

    telemetry.record("paint_event_ms", 10.0)
    assert len(logger.warning_calls) == 0

    now[0] = 2.1
    telemetry.record("paint_event_ms", 12.0, context={"mode": "direct_render"})
    assert len(logger.warning_calls) == 1

    args, _kwargs = logger.warning_calls[0]
    assert "hero_canvas" in args[1]
    assert "paint_event_ms" in args[2]

    breaches = telemetry.breach_snapshot()
    assert "paint_event_ms" in breaches
    assert breaches["paint_event_ms"]["threshold_p95_ms"] == 8.0
