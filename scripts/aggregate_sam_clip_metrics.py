#!/usr/bin/env python3
"""Aggregate SAM/CLIP open-vocabulary 3D diagnostic runs.

The input is one or more directories produced by
`run_sam_clip_eval_multiframe.py`. The script writes a compact report plus CSV
tables for run-level, sample-level, class-group, per-class, and label-source
diagnostics.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


def fnum(value: Optional[float], digits: int = 3) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def canonical_label(label: str, merge_person_labels: bool) -> str:
    if merge_person_labels and label == "person":
        return "pedestrian"
    return label


def safe_div(num: float, den: float) -> Optional[float]:
    return None if den == 0 else num / den


OBJECT_CLASSES = {
    "barrier",
    "bicycle",
    "bus",
    "car",
    "construction vehicle",
    "motorcycle",
    "pedestrian",
    "traffic cone",
    "trailer",
    "truck",
}

STUFF_CLASSES = {
    "building",
    "road",
    "sidewalk",
    "vegetation",
}

BASE_CLASS_GROUPS: Tuple[Tuple[str, Optional[set[str]]], ...] = (
    ("full", None),
    ("object", OBJECT_CLASSES),
    ("stuff", STUFF_CLASSES),
)


def summarize_eval(
    summaries: Sequence[dict],
    stage: str,
    merge_person_labels: bool,
) -> Tuple[dict, Dict[str, dict]]:
    total_points = 0
    assigned_points = 0
    per_class = defaultdict(lambda: {"tp": 0, "pred": 0, "gt": 0})

    for sample in summaries:
        total_points += int(sample["points_total"])
        ev = sample[f"{stage}_eval"]
        assigned_points += int(ev["assigned_points"])

        # Add gt once per canonical class per sample. This avoids double counting
        # the same nuScenes pedestrian gt when `person` and `pedestrian` are merged.
        gt_once = defaultdict(int)
        for label, metrics in ev.get("per_label", {}).items():
            cls = canonical_label(label, merge_person_labels)
            per_class[cls]["tp"] += int(metrics.get("tp", 0))
            per_class[cls]["pred"] += int(metrics.get("pred", 0))
            gt_once[cls] = max(gt_once[cls], int(metrics.get("gt", 0)))
        for cls, gt in gt_once.items():
            per_class[cls]["gt"] += int(gt)

    tp_total = sum(v["tp"] for v in per_class.values())
    pred_total = sum(v["pred"] for v in per_class.values())
    class_rows: Dict[str, dict] = {}
    for cls, counts in sorted(per_class.items()):
        tp, pred, gt = counts["tp"], counts["pred"], counts["gt"]
        precision = safe_div(tp, pred)
        recall = safe_div(tp, gt)
        iou = safe_div(tp, pred + gt - tp)
        class_rows[cls] = {
            "class": cls,
            "tp": tp,
            "pred": pred,
            "gt": gt,
            "precision": precision,
            "recall": recall,
            "iou": iou,
        }

    scored = [row for row in class_rows.values() if row["pred"] > 0 or row["gt"] > 0]
    macro_iou = safe_div(sum(row["iou"] or 0.0 for row in scored), len(scored))
    macro_precision = safe_div(sum(row["precision"] or 0.0 for row in scored), len(scored))
    macro_recall = safe_div(sum(row["recall"] or 0.0 for row in scored), len(scored))
    run_row = {
        "total_points": total_points,
        "assigned_points": assigned_points,
        "assigned_ratio": safe_div(assigned_points, total_points),
        "mapped_pred_points": pred_total,
        "mapped_accuracy": safe_div(tp_total, pred_total),
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_iou": macro_iou,
        "classes_scored": len(scored),
    }
    return run_row, class_rows


def summarize_group_metrics(run_row: dict, class_rows: Dict[str, dict], frequent_object_min_gt: int) -> List[dict]:
    rows = []
    total_points = int(run_row["total_points"])
    assigned_points = int(run_row["assigned_points"])
    frequent_object_classes = {
        cls
        for cls, row in class_rows.items()
        if cls in OBJECT_CLASSES and int(row["gt"]) >= frequent_object_min_gt
    }
    group_specs = (*BASE_CLASS_GROUPS, ("frequent_object", frequent_object_classes))

    for group, class_filter in group_specs:
        scored = [
            row
            for cls, row in class_rows.items()
            if (class_filter is None or cls in class_filter) and (row["pred"] > 0 or row["gt"] > 0)
        ]
        tp = sum(row["tp"] for row in scored)
        pred = sum(row["pred"] for row in scored)
        gt = sum(row["gt"] for row in scored)
        micro_precision = safe_div(tp, pred)
        micro_recall = safe_div(tp, gt)
        micro_iou = safe_div(tp, pred + gt - tp)
        macro_precision = safe_div(sum(row["precision"] or 0.0 for row in scored), len(scored))
        macro_recall = safe_div(sum(row["recall"] or 0.0 for row in scored), len(scored))
        macro_iou = safe_div(sum(row["iou"] or 0.0 for row in scored), len(scored))

        rows.append(
            {
                "group": group,
                "total_points": total_points,
                "assigned_points": assigned_points,
                "assigned_ratio": safe_div(assigned_points, total_points),
                "group_pred_points": pred,
                "group_pred_ratio": safe_div(pred, total_points),
                "group_gt_points": gt,
                "group_gt_ratio": safe_div(gt, total_points),
                "tp": tp,
                "assigned_accuracy": micro_precision,
                "micro_precision": micro_precision,
                "micro_recall": micro_recall,
                "micro_iou": micro_iou,
                "macro_precision": macro_precision,
                "macro_recall": macro_recall,
                "macro_iou": macro_iou,
                "classes_scored": len(scored),
                "frequent_object_min_gt": frequent_object_min_gt if group == "frequent_object" else None,
                "classes": ", ".join(row["class"] for row in scored),
            }
        )

    return rows


def summarize_sample(sample: dict, stage: str, merge_person_labels: bool) -> dict:
    run_row, _ = summarize_eval([sample], stage, merge_person_labels)
    return {
        "sample": f"sample_{sample['sample_index']:03d}",
        "points": sample["points_total"],
        **run_row,
    }


def iter_region_files(run_dir: Path) -> Iterable[Path]:
    yield from sorted(run_dir.glob("sample_*/CAM_*/regions.json"))


def summarize_label_sources(run_dir: Path, merge_person_labels: bool) -> Tuple[dict, List[dict]]:
    transitions = Counter()
    totals = Counter()
    changed = 0
    total = 0
    clip_wins = 0
    owl_wins = 0

    for path in iter_region_files(run_dir):
        try:
            records = json.loads(path.read_text())
        except Exception:
            continue
        for record in records:
            owl = canonical_label(record.get("owl_label") or "unknown", merge_person_labels)
            clip = canonical_label(record.get("clip_label") or "unknown", merge_person_labels)
            final = canonical_label(record.get("final_label") or owl, merge_person_labels)
            transitions[(owl, clip, final)] += 1
            totals[final] += 1
            total += 1
            if owl != final:
                changed += 1
            if final == clip and clip != owl:
                clip_wins += 1
            if final == owl:
                owl_wins += 1

    summary = {
        "regions": total,
        "changed_from_owl": changed,
        "changed_ratio": safe_div(changed, total),
        "clip_wins": clip_wins,
        "owl_wins": owl_wins,
        "top_final_labels": ", ".join(f"{k}:{v}" for k, v in totals.most_common(8)),
    }
    rows = [
        {
            "owl_label": owl,
            "clip_label": clip,
            "final_label": final,
            "count": count,
        }
        for (owl, clip, final), count in transitions.most_common()
    ]
    return summary, rows


def read_run(run_dir: Path) -> dict:
    summary_path = run_dir / "run_summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing {summary_path}")
    data = json.loads(summary_path.read_text())
    data["_run_dir"] = run_dir
    data["_run_name"] = run_dir.name
    return data


def available_stages(run: dict) -> List[str]:
    stages = ["box", "sam"]
    summaries = run.get("summaries") or []
    if any(sample.get("superpoint_eval") for sample in summaries):
        stages.append("superpoint")
    return stages


def write_csv(path: Path, rows: Sequence[dict], fields: Sequence[str]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def short_run_name(name: str) -> str:
    if name == "ovsam3d_sam_clip_eval_nuscenes_mini":
        return "baseline"
    prefix = "ovsam3d_ablation_"
    suffix = "_merge_person_nuscenes_mini"
    if name.startswith(prefix):
        name = name[len(prefix) :]
    if name.endswith(suffix):
        name = name[: -len(suffix)]
    return name


def make_object_only_report(
    out_dir: Path,
    group_rows: Sequence[dict],
    per_class_rows: Sequence[dict],
) -> None:
    object_rows = [
        row
        for row in group_rows
        if row["stage"] in {"sam", "superpoint"} and row["group"] in {"object", "frequent_object"}
    ]
    best_object = max(
        (row for row in object_rows if row["group"] == "object" and row["micro_iou"] is not None),
        key=lambda row: row["micro_iou"],
        default=None,
    )
    best_frequent = max(
        (row for row in object_rows if row["group"] == "frequent_object" and row["micro_iou"] is not None),
        key=lambda row: row["micro_iou"],
        default=None,
    )

    lines = [
        "# Object-Only SAM Diagnostic Report",
        "",
        "This report intentionally removes stuff/background classes from the main reading. It is a diagnostic for the current object-mask route, not a full-scene semantic segmentation benchmark. When present, `superpoint` is an official-like 3D overlap-voting post-process over SAM point labels.",
        "",
        "## Object Groups",
        "",
        "| Run | Label mode | Stage | Group | Assigned acc | Micro R | Micro IoU | Macro IoU | Classes | Class list |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in object_rows:
        lines.append(
            "| {run} | {label_mode} | {stage} | {group} | {acc} | {recall} | {miou_micro} | {miou_macro} | {classes} | {class_list} |".format(
                run=short_run_name(row["run"]),
                label_mode=row.get("label_mode", "unknown"),
                stage=row["stage"],
                group=row["group"],
                acc=fnum(row["assigned_accuracy"]),
                recall=fnum(row["micro_recall"]),
                miou_micro=fnum(row["micro_iou"]),
                miou_macro=fnum(row["macro_iou"]),
                classes=row["classes_scored"],
                class_list=row["classes"],
            )
        )

    if best_object:
        lines += [
            "",
            "## Best Object-Only Route",
            "",
            "- Best object-only run: `{}`.".format(best_object["run"]),
            "- Best object-only stage: `{}`.".format(best_object["stage"]),
            "- Object assigned accuracy: `{}`.".format(fnum(best_object["assigned_accuracy"])),
            "- Object micro IoU: `{}`.".format(fnum(best_object["micro_iou"])),
            "- Object macro IoU: `{}`.".format(fnum(best_object["macro_iou"])),
        ]
    if best_frequent:
        lines += [
            "",
            "## Frequent-Object Reading",
            "",
            "`frequent_object` keeps object classes with enough ground-truth support in this mini split. It is useful for checking whether the object-mask chain works before long-tail classes dominate the macro average.",
            "",
            "- Best frequent-object run: `{}`.".format(best_frequent["run"]),
            "- Best frequent-object stage: `{}`.".format(best_frequent["stage"]),
            "- Frequent-object assigned accuracy: `{}`.".format(fnum(best_frequent["assigned_accuracy"])),
            "- Frequent-object micro IoU: `{}`.".format(fnum(best_frequent["micro_iou"])),
            "- Frequent-object macro IoU: `{}`.".format(fnum(best_frequent["macro_iou"])),
            "- Frequent-object classes: `{}`.".format(best_frequent["classes"]),
        ]

    if best_object:
        best_classes = [
            row
            for row in per_class_rows
            if row["run"] == best_object["run"] and row["stage"] == best_object["stage"] and row["class"] in OBJECT_CLASSES
        ]
        best_classes.sort(key=lambda row: (row["iou"] or 0.0), reverse=True)
        lines += [
            "",
            "## Best Run Per-Object Classes",
            "",
            "| Class | TP | Pred | GT | Precision | Recall | IoU |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
        for row in best_classes:
            lines.append(
                f"| {row['class']} | {row['tp']} | {row['pred']} | {row['gt']} | "
                f"{fnum(row['precision'])} | {fnum(row['recall'])} | {fnum(row['iou'])} |"
            )

    lines += [
        "",
        "## Reading Rule",
        "",
        "- Use `object` to evaluate the object-mask route without background classes.",
        "- Use `frequent_object` to inspect classes with enough support in the current mini split.",
        "- Keep `full` and `stuff` metrics visible elsewhere so the report does not claim full-scene segmentation.",
    ]
    (out_dir / "OBJECT_ONLY_DIAGNOSTIC_REPORT.md").write_text("\n".join(lines) + "\n")


def make_report(
    out_dir: Path,
    run_rows: Sequence[dict],
    sample_rows: Sequence[dict],
    group_rows: Sequence[dict],
    per_class_rows: Sequence[dict],
    transition_rows: Sequence[dict],
) -> None:
    lines = [
        "# SAM / CLIP Metric and Label Ablation Report",
        "",
        "## Run-Level Summary",
        "",
        "| Run | Label mode | Merge person | CLIP min | Stage | Coverage | Mapped acc | Macro P | Macro R | Macro IoU | Classes |",
        "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in run_rows:
        lines.append(
            "| {run} | {label_mode} | {merge_person_labels} | {min_clip_score} | {stage} | {coverage} | {acc} | {mp} | {mr} | {miou} | {classes} |".format(
                run=row["run"],
                label_mode=row.get("label_mode", "unknown"),
                merge_person_labels=row.get("merge_person_labels", False),
                min_clip_score=(
                    "n/a" if row.get("min_clip_score") is None else f"{float(row['min_clip_score']):.2f}"
                ),
                stage=row["stage"],
                coverage=fnum(row["assigned_ratio"]),
                acc=fnum(row["mapped_accuracy"]),
                mp=fnum(row["macro_precision"]),
                mr=fnum(row["macro_recall"]),
                miou=fnum(row["macro_iou"]),
                classes=row["classes_scored"],
            )
        )

    lines += [
        "",
        "## Split Metrics",
        "",
        "This table separates the SAM/superpoint-stage score into all mapped classes, object-like prompts, frequent object classes, and stuff/background classes. `Assigned acc` is micro precision over the points assigned to that group.",
        "",
        "| Run | Label mode | Stage | Group | Coverage | Group pred ratio | Assigned acc | Micro R | Micro IoU | Macro IoU | Classes |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in group_rows:
        if row["stage"] not in {"sam", "superpoint"}:
            continue
        lines.append(
            "| {run} | {label_mode} | {stage} | {group} | {coverage} | {pred_ratio} | {acc} | {recall} | {miou_micro} | {miou_macro} | {classes} |".format(
                run=row["run"],
                label_mode=row.get("label_mode", "unknown"),
                stage=row["stage"],
                group=row["group"],
                coverage=fnum(row["assigned_ratio"]),
                pred_ratio=fnum(row["group_pred_ratio"]),
                acc=fnum(row["assigned_accuracy"]),
                recall=fnum(row["micro_recall"]),
                miou_micro=fnum(row["micro_iou"]),
                miou_macro=fnum(row["macro_iou"]),
                classes=row["classes_scored"],
            )
        )

    lines += [
        "",
        "## Main Reading",
        "",
        "- Compare `box` and `sam` rows inside the same run to estimate how much SAM reduces box spillover.",
        "- Compare `hybrid`, `owl`, and `clip` runs to estimate whether the label bottleneck comes from the detector label or CLIP crop retagging.",
        "- Use merged-person rows as the default diagnostic when matching nuScenes lidarseg because `person` and `pedestrian` share the same closed-set target.",
        "- Read the full macro IoU together with object/stuff split metrics. The current prompt route is object-centric, so missing stuff predictions can depress full-scene macro IoU even when object assigned accuracy is improving.",
        "- Read `frequent_object` as the cleanest current object-mask diagnostic: it removes background and also avoids tiny long-tail classes dominating a five-sample mini split.",
        "- Compare `sam` with `superpoint` rows to test whether 3D overlap voting improves precision enough to offset lower coverage.",
        "",
        "## Lowest SAM IoU Classes",
        "",
        "| Run | Class | TP | Pred | GT | Precision | Recall | IoU |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    sam_classes = [r for r in per_class_rows if r["stage"] == "sam" and (r["pred"] or r["gt"])]
    sam_classes.sort(key=lambda r: ((r["iou"] if r["iou"] is not None else -1), -r["gt"]))
    for row in sam_classes[:24]:
        lines.append(
            f"| {row['run']} | {row['class']} | {row['tp']} | {row['pred']} | {row['gt']} | "
            f"{fnum(row['precision'])} | {fnum(row['recall'])} | {fnum(row['iou'])} |"
        )

    lines += [
        "",
        "## Label Source Changes",
        "",
        "| Run | Regions | Changed from OWL | Changed ratio | CLIP wins | OWL wins | Top final labels |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    seen = set()
    for row in transition_rows:
        key = row["run"]
        if key in seen:
            continue
        seen.add(key)
        lines.append(
            f"| {row['run']} | {row['regions']} | {row['changed_from_owl']} | "
            f"{fnum(row['changed_ratio'])} | {row['clip_wins']} | {row['owl_wins']} | {row['top_final_labels']} |"
        )

    lines += [
        "",
        "CSV files:",
        "",
        "- `run_level_metrics.csv`",
        "- `sample_level_metrics.csv`",
        "- `group_metrics.csv`",
        "- `OBJECT_ONLY_DIAGNOSTIC_REPORT.md`",
        "- `per_class_metrics.csv`",
        "- `label_source_transitions.csv`",
    ]
    (out_dir / "METRIC_ABLATION_REPORT.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dirs", nargs="+", type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("results/ovsam3d_metric_ablation_report"))
    ap.add_argument("--merge-person-labels", action="store_true")
    ap.add_argument(
        "--frequent-object-min-gt",
        type=int,
        default=100,
        help="Minimum GT points for a class to enter the frequent_object diagnostic group.",
    )
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    runs = [read_run(path) for path in args.run_dirs]

    run_rows: List[dict] = []
    sample_rows: List[dict] = []
    group_rows: List[dict] = []
    per_class_rows: List[dict] = []
    transition_rows: List[dict] = []

    for run in runs:
        name = run["_run_name"]
        config = run.get("config") or (run.get("summaries", [{}])[0].get("config", {}))
        label_mode = config.get("label_mode", "unknown")
        merge_in_run = bool(config.get("merge_person_labels", False))
        min_clip_score = config.get("min_clip_score")
        owl_threshold = config.get("owl_threshold")
        stages = available_stages(run)
        for stage in stages:
            row, class_rows = summarize_eval(run["summaries"], stage, args.merge_person_labels)
            meta = {
                "run": name,
                "label_mode": label_mode,
                "merge_person_labels": merge_in_run,
                "min_clip_score": min_clip_score,
                "owl_threshold": owl_threshold,
                "posthoc_merge_person": args.merge_person_labels,
                "stage": stage,
            }
            run_rows.append({**meta, **row})
            for group_row in summarize_group_metrics(row, class_rows, args.frequent_object_min_gt):
                group_rows.append({**meta, **group_row})
            for cls, cls_row in class_rows.items():
                per_class_rows.append(
                    {
                        "run": name,
                        "label_mode": label_mode,
                        "merge_person_labels": merge_in_run,
                        "min_clip_score": min_clip_score,
                        "owl_threshold": owl_threshold,
                        "posthoc_merge_person": args.merge_person_labels,
                        "stage": stage,
                        **cls_row,
                    }
                )
        for sample in run["summaries"]:
            for stage in stages:
                sample_rows.append(
                    {
                        "run": name,
                        "label_mode": label_mode,
                        "merge_person_labels": merge_in_run,
                        "min_clip_score": min_clip_score,
                        "owl_threshold": owl_threshold,
                        "posthoc_merge_person": args.merge_person_labels,
                        "stage": stage,
                        **summarize_sample(sample, stage, args.merge_person_labels),
                    }
                )
        label_summary, transitions = summarize_label_sources(run["_run_dir"], args.merge_person_labels)
        transition_rows.append({"run": name, **label_summary})
        for row in transitions:
            transition_rows.append({"run": name, **row})

    write_csv(
        args.out_dir / "run_level_metrics.csv",
        run_rows,
        [
            "run",
            "label_mode",
            "merge_person_labels",
            "min_clip_score",
            "owl_threshold",
            "posthoc_merge_person",
            "stage",
            "total_points",
            "assigned_points",
            "assigned_ratio",
            "mapped_pred_points",
            "mapped_accuracy",
            "macro_precision",
            "macro_recall",
            "macro_iou",
            "classes_scored",
        ],
    )
    write_csv(
        args.out_dir / "group_metrics.csv",
        group_rows,
        [
            "run",
            "label_mode",
            "merge_person_labels",
            "min_clip_score",
            "owl_threshold",
            "posthoc_merge_person",
            "stage",
            "group",
            "total_points",
            "assigned_points",
            "assigned_ratio",
            "group_pred_points",
            "group_pred_ratio",
            "group_gt_points",
            "group_gt_ratio",
            "tp",
            "assigned_accuracy",
            "micro_precision",
            "micro_recall",
            "micro_iou",
            "macro_precision",
            "macro_recall",
            "macro_iou",
            "classes_scored",
            "frequent_object_min_gt",
            "classes",
        ],
    )
    write_csv(
        args.out_dir / "sample_level_metrics.csv",
        sample_rows,
        [
            "run",
            "label_mode",
            "merge_person_labels",
            "min_clip_score",
            "owl_threshold",
            "posthoc_merge_person",
            "sample",
            "stage",
            "points",
            "assigned_points",
            "assigned_ratio",
            "mapped_accuracy",
            "macro_precision",
            "macro_recall",
            "macro_iou",
            "classes_scored",
        ],
    )
    write_csv(
        args.out_dir / "per_class_metrics.csv",
        per_class_rows,
        [
            "run",
            "label_mode",
            "merge_person_labels",
            "min_clip_score",
            "owl_threshold",
            "posthoc_merge_person",
            "stage",
            "class",
            "tp",
            "pred",
            "gt",
            "precision",
            "recall",
            "iou",
        ],
    )
    write_csv(
        args.out_dir / "label_source_transitions.csv",
        transition_rows,
        [
            "run",
            "regions",
            "changed_from_owl",
            "changed_ratio",
            "clip_wins",
            "owl_wins",
            "top_final_labels",
            "owl_label",
            "clip_label",
            "final_label",
            "count",
        ],
    )
    make_report(args.out_dir, run_rows, sample_rows, group_rows, per_class_rows, transition_rows)
    make_object_only_report(args.out_dir, group_rows, per_class_rows)
    with (args.out_dir / "metrics_summary.json").open("w") as f:
        json.dump(
            {
                "run_level": run_rows,
                "sample_level": sample_rows,
                "group_level": group_rows,
                "per_class": per_class_rows,
                "label_source": transition_rows,
            },
            f,
            indent=2,
        )
    print("OUTPUT_DIR", args.out_dir)


if __name__ == "__main__":
    main()
