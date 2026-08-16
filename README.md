# F1 Circuit Outline Generator

Generates a clean circuit-outline silhouette from **real F1 telemetry** (via [FastF1](https://github.com/theOehrly/Fast-F1)), traced from a session's fastest lap — built for use as a poster background element or standalone graphic.

## What it does

Pulls the fastest lap of any F1 session (race, qualifying, or practice) and plots its X/Y position telemetry as a smooth line — the actual racing line that driver took around the circuit, not a schematic. Outputs two PNGs: a white-background version and a transparent-background version (for layering into a poster design).

## Setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python generate_track_outline.py
```

Or customise via CLI flags:

```bash
python generate_track_outline.py --year 2023 --grand-prix Monza --session Q --color "#c0392b" --width 6
```

| Flag | Default | Description |
|---|---|---|
| `--year` | `2023` | Season year |
| `--grand-prix` | `Silverstone` | Circuit/event name (also accepts country names, e.g. `British`) |
| `--session` | `R` | `R` (race), `Q` (qualifying), `FP1`/`FP2`/`FP3`, `S` (sprint), `SQ` (sprint quali) |
| `--color` | `#1a1a1a` | Line colour (hex) |
| `--width` | `5` | Line width |
| `--no-cache` | off | Disable the local FastF1 cache |
| `--output-dir` | `.` | Where to save the PNGs |

Or edit the `CONFIG` block at the top of `generate_track_outline.py` directly and run with no arguments.

## Notes

- The first run for a given session downloads real telemetry from the F1 live timing API via FastF1, so it needs internet access and can take anywhere from a few seconds to a couple of minutes. The local cache (`f1_cache/`, on by default) makes repeat runs for the same session near-instant.
- **Network-failure handling**: FastF1 doesn't always raise an exception when it fails to reach the live timing API — in some cases it logs warnings internally and silently returns a session with 0 drivers loaded, which used to surface as a confusing raw `DataNotLoadedError` traceback several calls later. This script now catches that specific failure mode and reports it as a clear, actionable error instead.
- If the fetch fails, double-check you have internet access, and that the event name / session code are valid for that year — very recent sessions sometimes don't have full timing data available yet.

## Example

```bash
python generate_track_outline.py --grand-prix Monza --year 2023 --session Q
# Loading 2023 Monza Q session...
# Fastest lap: VER — 0 days 00:01:20.161000
# Saved: ./monza_2023_track_outline.png and ./monza_2023_track_outline_transparent.png
```

## Project status

Personal project for generating poster-ready circuit graphics from real telemetry data rather than schematic track maps. Verified to run cleanly and fail gracefully on network issues; the actual telemetry download depends on live access to the F1 timing API, which varies by environment.
