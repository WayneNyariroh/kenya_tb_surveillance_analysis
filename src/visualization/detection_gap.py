from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .common import ensure_dir, read_required_csv
from .theme import apply_theme, save_figure


def plot_detection_gap(
    analysis_dir: Path | str = "data/analysis/detection_gap",
    output_dir: Path | str = "outputs/figures/detection_gap",
) -> dict[str, Path]:
    apply_theme()
    analysis_dir = Path(analysis_dir)
    output_dir = ensure_dir(output_dir)

    path = analysis_dir / "detection_gap_by_year.csv"
    df = read_required_csv(path, {"year"})
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    outputs = {}

    if {"estimated_incident_tb", "notifications"}.issubset(df.columns):
        plot_df = df.copy()
        plot_df["estimated_incident_tb"] = pd.to_numeric(
            plot_df["estimated_incident_tb"], errors="coerce"
        )
        plot_df["notifications"] = pd.to_numeric(
            plot_df["notifications"], errors="coerce"
        )

        fig, ax = plt.subplots()
        ax.plot(
            plot_df["year"],
            plot_df["estimated_incident_tb"],
            marker="o",
            label="Estimated incident TB",
        )
        ax.plot(
            plot_df["year"],
            plot_df["notifications"],
            marker="o",
            label="Notified TB cases",
        )
        ax.set_title("Estimated TB incidence and notifications")
        ax.set_xlabel("Year")
        ax.set_ylabel("People")
        ax.legend()
        fig.tight_layout()

        out = output_dir / "incidence_vs_notifications.png"
        save_figure(fig, out)
        plt.close(fig)
        outputs["incidence_vs_notifications"] = out

    if "notification_incidence_gap" in df.columns:
        gap = pd.to_numeric(df["notification_incidence_gap"], errors="coerce")
        fig, ax = plt.subplots()
        ax.bar(df["year"], gap)
        ax.axhline(0, linewidth=0.8)
        ax.set_title("Estimated incidence minus notified TB cases")
        ax.set_xlabel("Year")
        ax.set_ylabel("Estimated people not represented in notifications")
        fig.tight_layout()

        out = output_dir / "notification_incidence_gap.png"
        save_figure(fig, out)
        plt.close(fig)
        outputs["notification_incidence_gap"] = out

    if "notification_to_incidence_ratio" in df.columns:
        ratio = pd.to_numeric(df["notification_to_incidence_ratio"], errors="coerce")
        fig, ax = plt.subplots()
        ax.plot(df["year"], ratio, marker="o")
        ax.axhline(100, linestyle="--", linewidth=1)
        ax.set_title("Notifications relative to estimated TB incidence")
        ax.set_xlabel("Year")
        ax.set_ylabel("Notification-to-incidence ratio (%)")
        fig.tight_layout()

        out = output_dir / "notification_to_incidence_ratio.png"
        save_figure(fig, out)
        plt.close(fig)
        outputs["notification_to_incidence_ratio"] = out

    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot TB notification-incidence gap.")
    parser.add_argument("--analysis-dir", default="data/analysis/detection_gap")
    parser.add_argument("--output-dir", default="outputs/figures/detection_gap")
    args = parser.parse_args()
    plot_detection_gap(args.analysis_dir, args.output_dir)


if __name__ == "__main__":
    main()
