#!/usr/bin/env python3
"""SAM/CLIP upgraded open-vocabulary 2D-to-3D pipeline on nuScenes-mini.

This script advances the first visual scaffold in four directions:

1. OWL-ViT boxes are refined with SAM masks.
2. Predicted open-vocabulary point labels are evaluated against nuScenes lidarseg.
3. CLIP crop tagging is recorded as a RAM-style automatic tag substitute.
4. Multiple frames are fused into a global-coordinate semantic map.

The goal is still a practical reproduction scaffold, not an official benchmark
implementation of OV-SAM3D or OV3D.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from PIL import Image, ImageDraw
from pyquaternion import Quaternion

from nuscenes.nuscenes import NuScenes
from nuscenes.utils.data_classes import LidarPointCloud
from nuscenes.utils.geometry_utils import view_points


CAMERAS = [
    "CAM_FRONT",
    "CAM_FRONT_LEFT",
    "CAM_FRONT_RIGHT",
    "CAM_BACK",
    "CAM_BACK_LEFT",
    "CAM_BACK_RIGHT",
]

LABELS = [
    "car",
    "truck",
    "bus",
    "trailer",
    "construction vehicle",
    "pedestrian",
    "person",
    "bicycle",
    "motorcycle",
    "traffic cone",
    "barrier",
    "road sign",
    "traffic light",
    "road",
    "sidewalk",
    "building",
    "vegetation",
]

OWL_PROMPTS = [
    "car",
    "truck",
    "bus",
    "trailer",
    "construction vehicle",
    "pedestrian",
    "person",
    "bicycle",
    "motorcycle",
    "traffic cone",
    "barrier",
    "road sign",
    "traffic light",
]

COLORS = np.array(
    [
        [230, 25, 75],
        [60, 180, 75],
        [255, 225, 25],
        [0, 130, 200],
        [245, 130, 48],
        [145, 30, 180],
        [70, 240, 240],
        [240, 50, 230],
        [210, 245, 60],
        [250, 190, 190],
        [0, 128, 128],
        [230, 190, 255],
        [170, 110, 40],
        [255, 250, 200],
        [128, 0, 0],
        [170, 255, 195],
        [0, 0, 128],
    ],
    dtype=np.uint8,
)
UNKNOWN_COLOR = np.array([128, 128, 128], dtype=np.uint8)

PROMPT_TO_GT_NAMES = {
    "car": ["vehicle.car"],
    "truck": ["vehicle.truck"],
    "bus": ["vehicle.bus.bendy", "vehicle.bus.rigid"],
    "trailer": ["vehicle.trailer"],
    "construction vehicle": ["vehicle.construction"],
    "pedestrian": [
        "human.pedestrian.adult",
        "human.pedestrian.child",
        "human.pedestrian.construction_worker",
        "human.pedestrian.police_officer",
        "human.pedestrian.personal_mobility",
        "human.pedestrian.stroller",
        "human.pedestrian.wheelchair",
    ],
    "person": [
        "human.pedestrian.adult",
        "human.pedestrian.child",
        "human.pedestrian.construction_worker",
        "human.pedestrian.police_officer",
        "human.pedestrian.personal_mobility",
        "human.pedestrian.stroller",
        "human.pedestrian.wheelchair",
    ],
    "bicycle": ["vehicle.bicycle"],
    "motorcycle": ["vehicle.motorcycle"],
    "traffic cone": ["movable_object.trafficcone"],
    "barrier": ["movable_object.barrier"],
    "road": ["flat.driveable_surface"],
    "sidewalk": ["flat.sidewalk"],
    "building": ["static.manmade"],
    "vegetation": ["static.vegetation"],
}


@dataclass
class DetectedRegion:
    box: List[float]
    owl_label: str
    owl_score: float
    clip_label: Optional[str] = None
    clip_score: Optional[float] = None
    final_label: Optional[str] = None
    final_score: float = 0.0
    sam_iou: Optional[float] = None
    mask: Optional[np.ndarray] = None


def normalize_label(label: str, merge_person_labels: bool = False) -> str:
    if merge_person_labels and label == "person":
        return "pedestrian"
    return label


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def label_id(name: str) -> int:
    return LABELS.index(name)


def color_for(label: str) -> Tuple[int, int, int]:
    return tuple(int(v) for v in COLORS[label_id(label) % len(COLORS)])


def load_models(args):
    from transformers import (
        CLIPModel,
        CLIPProcessor,
        OwlViTForObjectDetection,
        OwlViTProcessor,
        SamModel,
        SamProcessor,
    )

    owl_processor = OwlViTProcessor.from_pretrained(args.owl_model)
    owl_model = OwlViTForObjectDetection.from_pretrained(args.owl_model).to(args.device).eval()

    sam_processor = SamProcessor.from_pretrained(args.sam_model)
    sam_model = SamModel.from_pretrained(args.sam_model).to(args.device).eval()

    clip_processor = CLIPProcessor.from_pretrained(args.clip_model)
    clip_model = CLIPModel.from_pretrained(args.clip_model).to(args.device).eval()
    return owl_processor, owl_model, sam_processor, sam_model, clip_processor, clip_model


@torch.no_grad()
def owl_detect(
    image: Image.Image,
    prompts: Sequence[str],
    processor,
    model,
    device: str,
    threshold: float,
    max_detections: int,
) -> List[DetectedRegion]:
    text = [[f"a photo of a {p}" for p in prompts]]
    inputs = processor(text=text, images=image, return_tensors="pt").to(device)
    outputs = model(**inputs)
    target_sizes = torch.tensor([image.size[::-1]], device=device)
    results = processor.post_process_object_detection(
        outputs=outputs, target_sizes=target_sizes, threshold=threshold
    )[0]
    boxes = results["boxes"].detach().cpu().numpy()
    scores = results["scores"].detach().cpu().numpy()
    labels = results["labels"].detach().cpu().numpy()

    regions: List[DetectedRegion] = []
    order = np.argsort(-scores)
    width, height = image.size
    for idx in order[:max_detections]:
        x1, y1, x2, y2 = boxes[idx].astype(float).tolist()
        x1 = max(0.0, min(x1, width - 1.0))
        x2 = max(0.0, min(x2, width - 1.0))
        y1 = max(0.0, min(y1, height - 1.0))
        y2 = max(0.0, min(y2, height - 1.0))
        if x2 <= x1 or y2 <= y1:
            continue
        owl_label = prompts[int(labels[idx])]
        regions.append(
            DetectedRegion(
                box=[x1, y1, x2, y2],
                owl_label=owl_label,
                owl_score=float(scores[idx]),
                final_label=owl_label,
                final_score=float(scores[idx]),
            )
        )
    return regions


@torch.no_grad()
def sam_refine_masks(
    image: Image.Image,
    regions: List[DetectedRegion],
    processor,
    model,
    device: str,
    batch_size: int = 12,
) -> None:
    if not regions:
        return
    for start in range(0, len(regions), batch_size):
        chunk = regions[start : start + batch_size]
        boxes = [r.box for r in chunk]
        inputs = processor(image, input_boxes=[boxes], return_tensors="pt").to(device)
        outputs = model(**inputs)
        masks = processor.image_processor.post_process_masks(
            outputs.pred_masks.detach().cpu(),
            inputs["original_sizes"].detach().cpu(),
            inputs["reshaped_input_sizes"].detach().cpu(),
        )[0]
        iou_scores = outputs.iou_scores.detach().cpu()[0]
        # masks: num_boxes x num_multimask x H x W
        for idx, region in enumerate(chunk):
            best = int(torch.argmax(iou_scores[idx]).item())
            mask = masks[idx, best].numpy().astype(bool)
            region.mask = mask
            region.sam_iou = float(iou_scores[idx, best].item())


def crop_for_region(image: Image.Image, region: DetectedRegion) -> Image.Image:
    x1, y1, x2, y2 = region.box
    crop = image.crop((int(x1), int(y1), int(x2), int(y2))).convert("RGB")
    if region.mask is None:
        return crop
    local = region.mask[int(y1) : int(y2), int(x1) : int(x2)]
    if local.size == 0:
        return crop
    arr = np.array(crop)
    if local.shape[:2] == arr.shape[:2]:
        arr[~local] = (240, 240, 240)
    return Image.fromarray(arr)


@torch.no_grad()
def clip_tag_regions(
    image: Image.Image,
    regions: List[DetectedRegion],
    processor,
    model,
    device: str,
    candidates: Sequence[str],
    batch_size: int = 16,
    min_clip_score: float = 0.12,
    label_mode: str = "hybrid",
    merge_person_labels: bool = False,
) -> None:
    if not regions:
        return
    texts = [f"a photo of a {label}" for label in candidates]
    for start in range(0, len(regions), batch_size):
        chunk = regions[start : start + batch_size]
        crops = [crop_for_region(image, r) for r in chunk]
        inputs = processor(text=texts, images=crops, return_tensors="pt", padding=True).to(device)
        outputs = model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1).detach().cpu().numpy()
        for row, region in zip(probs, chunk):
            best = int(np.argmax(row))
            clip_label = candidates[best]
            clip_score = float(row[best])
            region.clip_label = clip_label
            region.clip_score = clip_score
            if label_mode == "owl":
                region.final_label = normalize_label(region.owl_label, merge_person_labels)
                region.final_score = region.owl_score
            elif label_mode == "clip":
                region.final_label = normalize_label(clip_label, merge_person_labels)
                region.final_score = clip_score
            elif clip_score >= min_clip_score and clip_label in LABELS:
                # CLIP is treated as a RAM-style tag candidate. Keep OWL if CLIP is weak.
                region.final_label = normalize_label(clip_label, merge_person_labels)
                region.final_score = float(max(region.owl_score, clip_score))
            else:
                region.final_label = normalize_label(region.owl_label, merge_person_labels)
                region.final_score = region.owl_score


def load_lidar_raw_points(nusc: NuScenes, dataroot: Path, sample) -> np.ndarray:
    lidar_sd = nusc.get("sample_data", sample["data"]["LIDAR_TOP"])
    pc = LidarPointCloud.from_file(str(dataroot / lidar_sd["filename"]))
    return pc.points[:3, :].T.copy()


def load_lidar_global_points(nusc: NuScenes, dataroot: Path, sample) -> np.ndarray:
    lidar_sd = nusc.get("sample_data", sample["data"]["LIDAR_TOP"])
    pc = LidarPointCloud.from_file(str(dataroot / lidar_sd["filename"]))
    cs = nusc.get("calibrated_sensor", lidar_sd["calibrated_sensor_token"])
    pc.rotate(Quaternion(cs["rotation"]).rotation_matrix)
    pc.translate(np.array(cs["translation"]))
    pose = nusc.get("ego_pose", lidar_sd["ego_pose_token"])
    pc.rotate(Quaternion(pose["rotation"]).rotation_matrix)
    pc.translate(np.array(pose["translation"]))
    return pc.points[:3, :].T.copy()


def load_gt_labels(nusc: NuScenes, dataroot: Path, sample) -> Optional[np.ndarray]:
    lidar_token = sample["data"]["LIDAR_TOP"]
    try:
        lidarseg = nusc.get("lidarseg", lidar_token)
        return np.fromfile(dataroot / lidarseg["filename"], dtype=np.uint8)
    except Exception:
        return None


def project_lidar_to_camera(nusc: NuScenes, dataroot: Path, sample, cam_name: str):
    lidar_token = sample["data"]["LIDAR_TOP"]
    cam_token = sample["data"][cam_name]
    lidar_sd = nusc.get("sample_data", lidar_token)
    cam_sd = nusc.get("sample_data", cam_token)
    pc = LidarPointCloud.from_file(str(dataroot / lidar_sd["filename"]))

    cs = nusc.get("calibrated_sensor", lidar_sd["calibrated_sensor_token"])
    pc.rotate(Quaternion(cs["rotation"]).rotation_matrix)
    pc.translate(np.array(cs["translation"]))

    pose = nusc.get("ego_pose", lidar_sd["ego_pose_token"])
    pc.rotate(Quaternion(pose["rotation"]).rotation_matrix)
    pc.translate(np.array(pose["translation"]))

    pose = nusc.get("ego_pose", cam_sd["ego_pose_token"])
    pc.translate(-np.array(pose["translation"]))
    pc.rotate(Quaternion(pose["rotation"]).rotation_matrix.T)

    cs = nusc.get("calibrated_sensor", cam_sd["calibrated_sensor_token"])
    pc.translate(-np.array(cs["translation"]))
    pc.rotate(Quaternion(cs["rotation"]).rotation_matrix.T)

    image = Image.open(dataroot / cam_sd["filename"]).convert("RGB")
    width, height = image.size
    depths = pc.points[2, :]
    uv = view_points(pc.points[:3, :], np.array(cs["camera_intrinsic"]), normalize=True)[:2, :].T
    mask = (
        (depths > 1.0)
        & (uv[:, 0] >= 0)
        & (uv[:, 0] < width)
        & (uv[:, 1] >= 0)
        & (uv[:, 1] < height)
    )
    return image, uv, depths, mask, cam_sd


def assign_regions_to_points(
    uv: np.ndarray,
    visible_mask: np.ndarray,
    regions: Sequence[DetectedRegion],
    box_labels: np.ndarray,
    box_scores: np.ndarray,
    sam_labels: np.ndarray,
    sam_scores: np.ndarray,
) -> None:
    visible_idxs = np.where(visible_mask)[0]
    if not len(visible_idxs):
        return
    pts = uv[visible_idxs]
    x_int = np.clip(np.rint(pts[:, 0]).astype(int), 0, 10**9)
    y_int = np.clip(np.rint(pts[:, 1]).astype(int), 0, 10**9)
    for region in regions:
        label = label_id(region.final_label or region.owl_label)
        x1, y1, x2, y2 = region.box
        inside_box = (pts[:, 0] >= x1) & (pts[:, 0] <= x2) & (pts[:, 1] >= y1) & (pts[:, 1] <= y2)
        if np.any(inside_box):
            targets = visible_idxs[inside_box]
            better = region.final_score > box_scores[targets]
            targets = targets[better]
            box_labels[targets] = label
            box_scores[targets] = region.final_score
        if region.mask is not None:
            h, w = region.mask.shape[:2]
            valid = (x_int >= 0) & (x_int < w) & (y_int >= 0) & (y_int < h)
            inside_sam = np.zeros(len(visible_idxs), dtype=bool)
            inside_sam[valid] = region.mask[y_int[valid], x_int[valid]]
            if np.any(inside_sam):
                targets = visible_idxs[inside_sam]
                score = region.final_score * max(0.1, float(region.sam_iou or 1.0))
                better = score > sam_scores[targets]
                targets = targets[better]
                sam_labels[targets] = label
                sam_scores[targets] = score


def idx_to_name_mapping(nusc: NuScenes) -> Dict[int, str]:
    if hasattr(nusc, "lidarseg_idx2name_mapping"):
        return {int(k): v for k, v in nusc.lidarseg_idx2name_mapping.items()}
    mapping = getattr(nusc, "lidarseg_name2idx_mapping", {})
    return {int(v): k for k, v in mapping.items()}


def gt_sets_by_label(nusc: NuScenes) -> Dict[str, List[int]]:
    name_to_idx = getattr(nusc, "lidarseg_name2idx_mapping", {})
    out: Dict[str, List[int]] = {}
    for label, names in PROMPT_TO_GT_NAMES.items():
        ids = [int(name_to_idx[name]) for name in names if name in name_to_idx]
        if ids:
            out[label] = ids
    return out


def evaluate_point_labels(pred: np.ndarray, gt: Optional[np.ndarray], gt_sets: Dict[str, List[int]]):
    assigned = pred >= 0
    result = {
        "assigned_points": int(assigned.sum()),
        "assigned_ratio": float(assigned.mean()) if len(pred) else 0.0,
        "mapped_assigned_points": 0,
        "mapped_assigned_accuracy": None,
        "per_label": {},
    }
    if gt is None:
        return result
    correct_total = 0
    mapped_total = 0
    for label, gt_ids in gt_sets.items():
        lid = label_id(label)
        pred_mask = pred == lid
        if not pred_mask.any() and not np.isin(gt, gt_ids).any():
            continue
        gt_mask = np.isin(gt, gt_ids)
        tp = int((pred_mask & gt_mask).sum())
        pred_count = int(pred_mask.sum())
        gt_count = int(gt_mask.sum())
        precision = tp / pred_count if pred_count else None
        recall = tp / gt_count if gt_count else None
        denom = pred_count + gt_count - tp
        iou = tp / denom if denom else None
        result["per_label"][label] = {
            "tp": tp,
            "pred": pred_count,
            "gt": gt_count,
            "precision": precision,
            "recall": recall,
            "iou": iou,
        }
        correct_total += tp
        mapped_total += pred_count
    result["mapped_assigned_points"] = int(mapped_total)
    result["mapped_assigned_accuracy"] = correct_total / mapped_total if mapped_total else None
    return result


def label_hist(labels: np.ndarray) -> Dict[str, int]:
    assigned = labels >= 0
    hist = {}
    for idx in sorted(set(labels[assigned].tolist())):
        hist[LABELS[int(idx)]] = int((labels == idx).sum())
    return hist


def draw_regions(image: Image.Image, regions: Sequence[DetectedRegion], out_path: Path) -> None:
    base = np.array(image).astype(np.float32)
    overlay = base.copy()
    for region in regions:
        label = region.final_label or region.owl_label
        color = np.array(color_for(label), dtype=np.float32)
        if region.mask is not None:
            overlay[region.mask] = 0.55 * overlay[region.mask] + 0.45 * color
    out = Image.fromarray(np.clip(overlay, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(out)
    width, height = out.size
    for region in regions:
        label = region.final_label or region.owl_label
        color = color_for(label)
        x1, y1, x2, y2 = region.box
        x1 = max(0, min(float(x1), width - 1))
        x2 = max(0, min(float(x2), width - 1))
        y1 = max(0, min(float(y1), height - 1))
        y2 = max(0, min(float(y2), height - 1))
        if x2 <= x1 or y2 <= y1:
            continue
        draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
        tag = label
        if region.clip_label and region.clip_label != region.owl_label:
            tag = f"{label} | owl:{region.owl_label}"
        text = f"{tag} {region.final_score:.2f}"
        label_w = min(width - x1, max(80, 7 * len(text)))
        label_y0 = max(0, y1 - 18)
        label_y1 = max(label_y0 + 1, y1)
        draw.rectangle([x1, label_y0, x1 + label_w, label_y1], fill=color)
        draw.text((x1 + 2, label_y0 + 2), text, fill=(0, 0, 0))
    out.save(out_path)


def draw_projection(
    image: Image.Image,
    uv: np.ndarray,
    visible_mask: np.ndarray,
    labels: np.ndarray,
    out_path: Path,
    point_size: int = 2,
) -> None:
    canvas = np.array(image).copy()
    idxs = np.where(visible_mask)[0]
    for idx in idxs:
        lab = labels[idx]
        if lab < 0:
            color = UNKNOWN_COLOR
        else:
            color = COLORS[int(lab) % len(COLORS)]
        x, y = uv[idx].astype(int)
        cv2.circle(canvas, (int(x), int(y)), point_size, tuple(int(v) for v in color.tolist()), -1)
    Image.fromarray(canvas).save(out_path)


def draw_bev(points: np.ndarray, labels: np.ndarray, out_path: Path, title: str, lim: float = 55.0) -> None:
    fig, ax = plt.subplots(figsize=(9, 9), dpi=180)
    ax.set_facecolor("#101010")
    xy = points[:, :2]
    assigned = labels >= 0
    if (~assigned).any():
        ax.scatter(xy[~assigned, 0], xy[~assigned, 1], s=0.08, c="#777777", alpha=0.15, linewidths=0)
    for lid in sorted(set(labels[assigned].tolist())):
        pts = xy[labels == lid]
        color = COLORS[int(lid) % len(COLORS)] / 255.0
        ax.scatter(pts[:, 0], pts[:, 1], s=0.35, c=[color], alpha=0.88, linewidths=0, label=LABELS[int(lid)])
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_xlabel("x / meters")
    ax.set_ylabel("y / meters")
    ax.set_title(title)
    ax.grid(color="white", alpha=0.08, linewidth=0.5)
    if assigned.any():
        ax.legend(loc="upper right", fontsize=7, markerscale=8, framealpha=0.85)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def draw_gt_bev(points: np.ndarray, gt: Optional[np.ndarray], idx2name: Dict[int, str], out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 9), dpi=180)
    ax.set_facecolor("#101010")
    if gt is not None:
        for lab in sorted(np.unique(gt).tolist()):
            pts = points[gt == lab, :2]
            color = COLORS[int(lab) % len(COLORS)] / 255.0
            name = idx2name.get(int(lab), str(lab)).split(".")[-1]
            ax.scatter(pts[:, 0], pts[:, 1], s=0.12, c=[color], alpha=0.72, linewidths=0, label=name)
    ax.set_xlim(-55, 55)
    ax.set_ylim(-55, 55)
    ax.set_title("nuScenes lidarseg GT reference")
    ax.grid(color="white", alpha=0.08, linewidth=0.5)
    if gt is not None:
        ax.legend(loc="upper right", fontsize=5, ncol=2, markerscale=6, framealpha=0.85)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def write_ply(points: np.ndarray, labels: np.ndarray, scores: np.ndarray, out_path: Path) -> None:
    colors = np.repeat(UNKNOWN_COLOR[None, :], len(points), axis=0)
    assigned = labels >= 0
    colors[assigned] = COLORS[labels[assigned] % len(COLORS)]
    with open(out_path, "w") as f:
        f.write("ply\nformat ascii 1.0\n")
        f.write(f"element vertex {len(points)}\n")
        f.write("property float x\nproperty float y\nproperty float z\n")
        f.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
        f.write("property int label_id\nproperty float score\nend_header\n")
        for p, c, lab, sc in zip(points, colors, labels, scores):
            f.write(
                f"{p[0]:.4f} {p[1]:.4f} {p[2]:.4f} "
                f"{int(c[0])} {int(c[1])} {int(c[2])} {int(lab)} {float(sc):.4f}\n"
            )


def make_montage(paths: Sequence[Path], out_path: Path, cols: int = 3, width: int = 640) -> None:
    imgs = [Image.open(p).convert("RGB") for p in paths if Path(p).exists()]
    if not imgs:
        return
    resized = []
    for im in imgs:
        scale = width / im.width
        resized.append(im.resize((width, int(im.height * scale))))
    rows = math.ceil(len(resized) / cols)
    height = max(im.height for im in resized)
    canvas = Image.new("RGB", (cols * width, rows * height), (245, 245, 245))
    for i, im in enumerate(resized):
        canvas.paste(im, ((i % cols) * width, (i // cols) * height))
    canvas.save(out_path)


def process_sample(
    nusc: NuScenes,
    dataroot: Path,
    sample_index: int,
    args,
    models,
    gt_sets: Dict[str, List[int]],
    idx2name: Dict[int, str],
):
    owl_processor, owl_model, sam_processor, sam_model, clip_processor, clip_model = models
    sample = nusc.sample[sample_index]
    out = Path(args.out_dir) / f"sample_{sample_index:03d}"
    ensure_dir(out)
    points = load_lidar_raw_points(nusc, dataroot, sample)
    global_points = load_lidar_global_points(nusc, dataroot, sample)
    gt = load_gt_labels(nusc, dataroot, sample)

    box_labels = np.full(points.shape[0], -1, dtype=np.int32)
    box_scores = np.zeros(points.shape[0], dtype=np.float32)
    sam_labels = np.full(points.shape[0], -1, dtype=np.int32)
    sam_scores = np.zeros(points.shape[0], dtype=np.float32)

    mask_paths, box_proj_paths, sam_proj_paths = [], [], []
    camera_summaries = []

    for cam_name in CAMERAS:
        cam_out = out / cam_name
        ensure_dir(cam_out)
        image, uv, depths, visible_mask, cam_sd = project_lidar_to_camera(nusc, dataroot, sample, cam_name)
        regions = owl_detect(
            image,
            OWL_PROMPTS,
            owl_processor,
            owl_model,
            args.device,
            args.owl_threshold,
            args.max_detections_per_camera,
        )
        sam_refine_masks(image, regions, sam_processor, sam_model, args.device, args.sam_batch_size)
        clip_tag_regions(
            image,
            regions,
            clip_processor,
            clip_model,
            args.device,
            LABELS,
            args.clip_batch_size,
            args.min_clip_score,
            args.label_mode,
            args.merge_person_labels,
        )
        assign_regions_to_points(uv, visible_mask, regions, box_labels, box_scores, sam_labels, sam_scores)

        raw_path = cam_out / "image_raw.jpg"
        mask_path = cam_out / "image_sam_clip_masks.jpg"
        box_proj_path = cam_out / "image_box_point_projection.jpg"
        sam_proj_path = cam_out / "image_sam_point_projection.jpg"
        image.save(raw_path)
        draw_regions(image, regions, mask_path)
        draw_projection(image, uv, visible_mask, box_labels, box_proj_path)
        draw_projection(image, uv, visible_mask, sam_labels, sam_proj_path)
        mask_paths.append(mask_path)
        box_proj_paths.append(box_proj_path)
        sam_proj_paths.append(sam_proj_path)
        det_records = []
        for region in regions:
            det_records.append(
                {
                    "box": region.box,
                    "owl_label": region.owl_label,
                    "owl_score": region.owl_score,
                    "clip_label": region.clip_label,
                    "clip_score": region.clip_score,
                    "final_label": region.final_label,
                    "final_score": region.final_score,
                    "sam_iou": region.sam_iou,
                    "mask_pixels": int(region.mask.sum()) if region.mask is not None else 0,
                }
            )
        with open(cam_out / "regions.json", "w") as f:
            json.dump(det_records, f, indent=2)
        camera_summaries.append(
            {
                "camera": cam_name,
                "image": cam_sd["filename"],
                "projected_points": int(visible_mask.sum()),
                "regions": len(regions),
                "owl_labels": {k: int(sum(r.owl_label == k for r in regions)) for k in sorted(set(r.owl_label for r in regions))},
                "final_labels": {
                    k: int(sum((r.final_label or r.owl_label) == k for r in regions))
                    for k in sorted(set((r.final_label or r.owl_label) for r in regions))
                },
            }
        )

    draw_bev(points, box_labels, out / "bev_box_open_vocab_labels.png", "Box-level open-vocabulary point labels")
    draw_bev(points, sam_labels, out / "bev_sam_open_vocab_labels.png", "SAM-refined open-vocabulary point labels")
    draw_gt_bev(points, gt, idx2name, out / "bev_lidarseg_gt_reference.png")
    write_ply(points, sam_labels, sam_scores, out / "sam_open_vocab_labeled_points.ply")
    make_montage(mask_paths, out / "montage_sam_clip_masks.jpg")
    make_montage(box_proj_paths, out / "montage_box_point_projection.jpg")
    make_montage(sam_proj_paths, out / "montage_sam_point_projection.jpg")

    eval_box = evaluate_point_labels(box_labels, gt, gt_sets)
    eval_sam = evaluate_point_labels(sam_labels, gt, gt_sets)
    summary = {
        "status": "OK",
        "sample_index": sample_index,
        "sample_token": sample["token"],
        "scene_token": sample["scene_token"],
        "points_total": int(points.shape[0]),
        "box_label_histogram": label_hist(box_labels),
        "sam_label_histogram": label_hist(sam_labels),
        "box_eval": eval_box,
        "sam_eval": eval_sam,
        "camera_summaries": camera_summaries,
        "outputs": {
            "bev_box": str(out / "bev_box_open_vocab_labels.png"),
            "bev_sam": str(out / "bev_sam_open_vocab_labels.png"),
            "bev_gt": str(out / "bev_lidarseg_gt_reference.png"),
            "montage_masks": str(out / "montage_sam_clip_masks.jpg"),
            "montage_box_projection": str(out / "montage_box_point_projection.jpg"),
            "montage_sam_projection": str(out / "montage_sam_point_projection.jpg"),
            "ply": str(out / "sam_open_vocab_labeled_points.ply"),
        },
        "config": {
            "label_mode": args.label_mode,
            "merge_person_labels": bool(args.merge_person_labels),
            "owl_threshold": args.owl_threshold,
            "min_clip_score": args.min_clip_score,
            "max_detections_per_camera": args.max_detections_per_camera,
        },
    }
    with open(out / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    return summary, global_points, sam_labels, sam_scores, gt


def make_contact_sheet(base: Path, summaries: Sequence[dict]) -> None:
    def tile(paths: List[Path], labels: List[str], out_path: Path, thumb_w: int) -> None:
        items = []
        for p, label in zip(paths, labels):
            if not p.exists():
                continue
            im = Image.open(p).convert("RGB")
            scale = thumb_w / im.width
            im = im.resize((thumb_w, int(im.height * scale)))
            header = Image.new("RGB", (thumb_w, 34), (30, 30, 30))
            ImageDraw.Draw(header).text((10, 9), label, fill=(255, 255, 255))
            canvas = Image.new("RGB", (thumb_w, header.height + im.height), (255, 255, 255))
            canvas.paste(header, (0, 0))
            canvas.paste(im, (0, header.height))
            items.append(canvas)
        if not items:
            return
        cols = 2
        rows = math.ceil(len(items) / cols)
        h = max(im.height for im in items)
        contact = Image.new("RGB", (cols * thumb_w, rows * h), (245, 245, 245))
        for i, im in enumerate(items):
            contact.paste(im, ((i % cols) * thumb_w, (i // cols) * h))
        contact.save(out_path)

    mask_paths, mask_labels, bev_paths, bev_labels = [], [], [], []
    proj_paths, proj_labels = [], []
    for summary in summaries:
        sid = f"sample_{summary['sample_index']:03d}"
        outputs = summary["outputs"]
        mask_paths.append(base / sid / "montage_sam_clip_masks.jpg")
        mask_labels.append(f"{sid} SAM masks + CLIP tags")
        proj_paths.append(base / sid / "montage_sam_point_projection.jpg")
        proj_labels.append(f"{sid} SAM point projection")
        bev_paths += [Path(outputs["bev_sam"]), Path(outputs["bev_gt"])]
        bev_labels += [f"{sid} SAM BEV", f"{sid} lidarseg GT"]
    tile(mask_paths, mask_labels, base / "contact_sheet_sam_clip_masks.jpg", 760)
    tile(proj_paths, proj_labels, base / "contact_sheet_sam_point_projection.jpg", 760)
    tile(bev_paths, bev_labels, base / "contact_sheet_sam_bev_vs_gt.jpg", 560)


def make_multiframe_outputs(
    out_dir: Path,
    global_points_list: Sequence[np.ndarray],
    label_list: Sequence[np.ndarray],
    score_list: Sequence[np.ndarray],
) -> Dict[str, str]:
    points = np.concatenate(global_points_list, axis=0)
    labels = np.concatenate(label_list, axis=0)
    scores = np.concatenate(score_list, axis=0)
    # Center the map for easier plotting.
    xy_center = np.median(points[:, :2], axis=0)
    centered = points.copy()
    centered[:, 0] -= xy_center[0]
    centered[:, 1] -= xy_center[1]
    draw_bev(centered, labels, out_dir / "multiframe_sam_open_vocab_bev.png", "Multi-frame SAM open-vocabulary map", lim=65)
    write_ply(centered, labels, scores, out_dir / "multiframe_sam_open_vocab_points.ply")
    return {
        "multiframe_bev": str(out_dir / "multiframe_sam_open_vocab_bev.png"),
        "multiframe_ply": str(out_dir / "multiframe_sam_open_vocab_points.ply"),
    }


def write_report(out_dir: Path, summaries: Sequence[dict], multiframe_outputs: Dict[str, str]) -> None:
    rows = []
    for s in summaries:
        rows.append(
            "| sample_{:03d} | {} | {:.3f} | {:.3f} | {} | {} |".format(
                s["sample_index"],
                s["points_total"],
                s["box_eval"]["assigned_ratio"],
                s["sam_eval"]["assigned_ratio"],
                (
                    "n/a"
                    if s["box_eval"]["mapped_assigned_accuracy"] is None
                    else f"{s['box_eval']['mapped_assigned_accuracy']:.3f}"
                ),
                (
                    "n/a"
                    if s["sam_eval"]["mapped_assigned_accuracy"] is None
                    else f"{s['sam_eval']['mapped_assigned_accuracy']:.3f}"
                ),
            )
        )
    report = f"""# SAM / CLIP / Evaluation / Multi-frame Results

This run upgrades the initial OWL-ViT box scaffold in four ways:

1. OWL-ViT boxes are refined with SAM masks.
2. CLIP crop tags are recorded as RAM-style automatic labels.
3. Open-vocabulary point labels are mapped to nuScenes lidarseg classes for a lightweight quality check.
4. Per-frame predictions are fused into a multi-frame global-coordinate semantic map.

## Summary

Config: `label_mode={summaries[0].get('config', {}).get('label_mode', 'hybrid')}`,
`merge_person_labels={summaries[0].get('config', {}).get('merge_person_labels', False)}`.

| Sample | Points | Box assigned ratio | SAM assigned ratio | Box mapped accuracy | SAM mapped accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(rows)}

## Visualizations

- `contact_sheet_sam_clip_masks.jpg`
- `contact_sheet_sam_point_projection.jpg`
- `contact_sheet_sam_bev_vs_gt.jpg`
- `{multiframe_outputs['multiframe_bev']}`
- `{multiframe_outputs['multiframe_ply']}`

## Interpretation

SAM masks are expected to reduce the broad box spillover seen in the first scaffold.
The assigned ratio can drop after SAM refinement, which is healthy when box labels were
over-covering background points. The mapped accuracy is only a lightweight diagnostic:
open-vocabulary labels do not perfectly match nuScenes lidarseg classes, and unmapped
labels such as road sign / traffic light are ignored by the current metric.
"""
    (out_dir / "SAM_CLIP_EVAL_MULTIFRAME_REPORT.md").write_text(report)


def parse_sample_indices(text: str) -> List[int]:
    out = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataroot", default="data/nuscenes_mini/raw")
    ap.add_argument("--version", default="v1.0-mini")
    ap.add_argument("--sample-indices", default="0-4")
    ap.add_argument("--out-dir", default="outputs/ovsam3d_sam_clip_eval_nuscenes_mini")
    ap.add_argument("--owl-model", default="google/owlvit-base-patch32")
    ap.add_argument("--sam-model", default="facebook/sam-vit-base")
    ap.add_argument("--clip-model", default="openai/clip-vit-base-patch32")
    ap.add_argument("--owl-threshold", type=float, default=0.06)
    ap.add_argument("--min-clip-score", type=float, default=0.12)
    ap.add_argument("--max-detections-per-camera", type=int, default=18)
    ap.add_argument("--sam-batch-size", type=int, default=8)
    ap.add_argument("--clip-batch-size", type=int, default=16)
    ap.add_argument("--label-mode", choices=["hybrid", "owl", "clip"], default="hybrid")
    ap.add_argument("--merge-person-labels", action="store_true")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    ensure_dir(out_dir)
    nusc = NuScenes(version=args.version, dataroot=args.dataroot, verbose=False)
    dataroot = Path(args.dataroot)
    gt_sets = gt_sets_by_label(nusc)
    idx2name = idx_to_name_mapping(nusc)
    models = load_models(args)

    summaries = []
    global_points_list, label_list, score_list = [], [], []
    for sample_index in parse_sample_indices(args.sample_indices):
        summary, global_points, labels, scores, _gt = process_sample(
            nusc, dataroot, sample_index, args, models, gt_sets, idx2name
        )
        summaries.append(summary)
        global_points_list.append(global_points)
        label_list.append(labels)
        score_list.append(scores)
        print(
            f"sample_{sample_index:03d}",
            "box_ratio",
            round(summary["box_eval"]["assigned_ratio"], 3),
            "sam_ratio",
            round(summary["sam_eval"]["assigned_ratio"], 3),
            "sam_acc",
            summary["sam_eval"]["mapped_assigned_accuracy"],
        )

    make_contact_sheet(out_dir, summaries)
    multiframe_outputs = make_multiframe_outputs(out_dir, global_points_list, label_list, score_list)
    write_report(out_dir, summaries, multiframe_outputs)
    with open(out_dir / "run_summary.json", "w") as f:
        json.dump(
            {
                "status": "OK",
                "sample_indices": parse_sample_indices(args.sample_indices),
                "config": {
                    "label_mode": args.label_mode,
                    "merge_person_labels": bool(args.merge_person_labels),
                    "owl_threshold": args.owl_threshold,
                    "min_clip_score": args.min_clip_score,
                    "max_detections_per_camera": args.max_detections_per_camera,
                },
                "summaries": summaries,
                "multiframe_outputs": multiframe_outputs,
            },
            f,
            indent=2,
        )
    print("OUTPUT_DIR", out_dir)


if __name__ == "__main__":
    main()
