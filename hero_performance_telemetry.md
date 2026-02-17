# Hero Performance Telemetry

## Runtime Telemetry

The Hero tab and hero canvas now expose rolling latency telemetry via `HeroPerfTelemetry`.

Enable with environment variables:

- `PF_HERO_PERF_TELEMETRY=1`
- `PF_HERO_PERF_SAMPLE_SIZE=240` (rolling window size)
- `PF_HERO_PERF_LOG_INTERVAL_MS=5000`
- `PF_HERO_PERF_MIN_SAMPLES=20`
- `PF_HERO_PERF_WARNINGS=1`
- `PF_HERO_PERF_WARN_INTERVAL_MS=15000`
- Optional global fallback threshold: `PF_HERO_PERF_WARN_DEFAULT_P95_MS=25`
- Optional per-metric override:
  - Example: `PF_HERO_PERF_WARN_PAINT_EVENT_MS_P95_MS=16.6`
  - Example: `PF_HERO_PERF_WARN_HERO_REFRESH_INVENTORY_MS_P95_MS=50`

Logged metrics include:

- `hero.refresh_all_ms`
- `hero.equip_change_ms`
- `hero.refresh_slot_combos_ms`
- `hero.refresh_inventory_ms`
- `hero.refresh_character_ms`
- `web.compose_html_ms`
- `web.update_content_ms`
- `web.inject_html_ms`
- `paint_event_ms`
- `render_content_ms`

Snapshot APIs:

- `ADHDBusterTab.get_performance_snapshot()`
- `CharacterCanvas.get_performance_snapshot()`

Snapshots now include:

- `metrics`: rolling avg/p50/p95/max by metric
- `breaches`: current p95 threshold violations

## Baseline Benchmark Script

Use the reproducible benchmark tool:

```bash
python tools/benchmark_hero_rendering.py --iterations 120 --include-fallback-render --output-md artifacts/hero_perf_baseline.md
```

Recommended first run:

```bash
python tools/benchmark_hero_rendering.py --iterations 80 --themes thief space_pirate robot zoo_worker --tiers legendary godlike --output-md artifacts/hero_perf_baseline.md
```

This reports per scenario:

- composed HTML generation avg/p95/max (ms)
- optional fallback painter path avg/p95/max (ms)
- generated HTML size
