"""
Generate a clean circuit-outline silhouette from real FastF1 telemetry,
for use as a poster background element or standalone graphic.

Setup (run once):
    pip install -r requirements.txt

Usage:
    python generate_track_outline.py
    python generate_track_outline.py --year 2023 --grand-prix Monza --session Q
    python generate_track_outline.py --grand-prix Silverstone --color "#c0392b" --width 6

Or edit the CONFIG block below directly and run with no arguments.

Notes:
- The first run for a given session downloads real telemetry from the F1
  live timing API via FastF1, so it needs internet access and can take a
  few seconds to a couple of minutes depending on the session. Enable
  CACHE_ENABLED (on by default) so repeat runs for the same session are
  instant.
- If FastF1 can't reach the data source (offline, or the session doesn't
  have timing data available yet), this script exits with a clear error
  rather than a raw traceback — see `load_fastest_lap_telemetry`.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass

import fastf1
import matplotlib.pyplot as plt

# ---------------- CONFIG (used when no CLI args are given) ----------------
YEAR = 2023
GRAND_PRIX = "Silverstone"  # FastF1 also accepts a country/circuit name, e.g. "British"
SESSION = "R"               # "R" = Race, "Q" = Qualifying, "FP1"/"FP2"/"FP3" also work
LINE_COLOR = "#1a1a1a"      # swap to match your poster's colour scheme
LINE_WIDTH = 5
CACHE_ENABLED = True        # verified working against fastf1 3.8.3 in a clean install
CACHE_DIR = "./f1_cache"
# ----------------------------------------------------------------------------


@dataclass
class TrackOutlineConfig:
    year: int
    grand_prix: str
    session: str
    line_color: str
    line_width: float
    cache_enabled: bool = True
    cache_dir: str = "./f1_cache"

    @property
    def output_name(self) -> str:
        return f"{self.grand_prix.lower().replace(' ', '_')}_{self.year}_track_outline"


def load_fastest_lap_telemetry(config: TrackOutlineConfig):
    """Loads the session and returns (fastest_lap, telemetry, event_name).
    Raises a RuntimeError with a clear message on failure, instead of
    letting a raw FastF1/network traceback surface to the user."""
    if config.cache_enabled:
        os.makedirs(config.cache_dir, exist_ok=True)
        fastf1.Cache.enable_cache(config.cache_dir)

    print(f"Loading {config.year} {config.grand_prix} {config.session} session...")
    try:
        session = fastf1.get_session(config.year, config.grand_prix, config.session)
        # NOTE: FastF1 does not always raise on a failed/partial data load (e.g.
        # no network access to the live timing API) — it can log warnings and
        # return having loaded 0 drivers. So we can't rely on session.load()
        # raising; we have to check session.laps afterwards too, and treat
        # DataNotLoadedError from that access as the same failure mode.
        session.load(telemetry=True, laps=True, weather=False)
        laps = session.laps
    except fastf1.exceptions.DataNotLoadedError as exc:
        raise RuntimeError(
            f"Could not load session data for {config.year} {config.grand_prix} "
            f"{config.session}. FastF1 loaded 0 drivers for this session — this "
            f"usually means there's no network access to the F1 live timing API "
            f"right now, or this session doesn't have timing data available yet. "
            f"Original error: {exc}"
        ) from exc
    except Exception as exc:  # invalid event/session name, etc.
        raise RuntimeError(
            f"Could not load session data for {config.year} {config.grand_prix} "
            f"{config.session}. Check the event name and session code are valid. "
            f"Original error: {exc}"
        ) from exc

    if laps is None or len(laps) == 0:
        raise RuntimeError(
            f"Session loaded but contains no lap data for {config.year} "
            f"{config.grand_prix} {config.session} — nothing to plot."
        )

    fastest_lap = laps.pick_fastest()
    telemetry = fastest_lap.get_telemetry()
    return fastest_lap, telemetry, session.event["EventName"]


def render_track_outline(config: TrackOutlineConfig, output_dir: str = ".") -> tuple[str, str]:
    """Runs the full pipeline and writes two PNGs (solid-background and
    transparent). Returns their file paths."""
    fastest_lap, telemetry, event_name = load_fastest_lap_telemetry(config)
    x, y = telemetry["X"], telemetry["Y"]

    print(f"Fastest lap: {fastest_lap['Driver']} — {fastest_lap['LapTime']}")

    os.makedirs(output_dir, exist_ok=True)
    solid_path = os.path.join(output_dir, f"{config.output_name}.png")
    transparent_path = os.path.join(output_dir, f"{config.output_name}_transparent.png")

    # ---- solid background version ----
    fig, ax = plt.subplots(figsize=(9, 6.5), dpi=200)
    ax.plot(x, y, color=config.line_color, linewidth=config.line_width,
            solid_capstyle="round", solid_joinstyle="round")
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(
        f"{event_name} {config.year} — Circuit Outline\n"
        f"(traced from {fastest_lap['Driver']}'s fastest lap telemetry)",
        fontsize=10.5, color="#555555", pad=12,
    )
    fig.tight_layout()
    fig.savefig(solid_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    # ---- transparent background version (poster watermark use) ----
    fig2, ax2 = plt.subplots(figsize=(9, 6.5), dpi=200)
    ax2.plot(x, y, color=config.line_color, linewidth=config.line_width,
              solid_capstyle="round", solid_joinstyle="round")
    ax2.set_aspect("equal")
    ax2.axis("off")
    fig2.tight_layout()
    fig2.savefig(transparent_path, bbox_inches="tight", transparent=True)
    plt.close(fig2)

    print(f"Saved: {solid_path} and {transparent_path}")
    return solid_path, transparent_path


def parse_args() -> TrackOutlineConfig:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--year", type=int, default=YEAR)
    parser.add_argument("--grand-prix", type=str, default=GRAND_PRIX)
    parser.add_argument("--session", type=str, default=SESSION, help="R, Q, FP1, FP2, FP3, S, SQ")
    parser.add_argument("--color", type=str, default=LINE_COLOR, dest="line_color")
    parser.add_argument("--width", type=float, default=LINE_WIDTH, dest="line_width")
    parser.add_argument("--no-cache", action="store_true", help="disable local FastF1 cache")
    parser.add_argument("--output-dir", type=str, default=".")
    args = parser.parse_args()
    return TrackOutlineConfig(
        year=args.year,
        grand_prix=args.grand_prix,
        session=args.session,
        line_color=args.line_color,
        line_width=args.line_width,
        cache_enabled=not args.no_cache,
        cache_dir=CACHE_DIR,
    ), args.output_dir


if __name__ == "__main__":
    config, output_dir = parse_args()
    try:
        render_track_outline(config, output_dir=output_dir)
    except RuntimeError as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        sys.exit(1)
