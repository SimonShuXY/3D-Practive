#!/usr/bin/env python3
"""Minimal open-vocabulary 2D-to-3D visualization on nuScenes-mini.

This is an isolated reproduction scaffold for OV-SAM3D/OV3D-style pipelines:
2D open-vocabulary predictions -> LiDAR-camera projection -> 3D point labels -> rich visualizations.
It intentionally does not modify the previous IPFP project.
"""
import argparse
import json
import math
import os
from pathlib import Path

import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont
from pyquaternion import Quaternion

from nuscenes.nuscenes import NuScenes
from nuscenes.utils.data_classes import LidarPointCloud
from nuscenes.utils.geometry_utils import view_points

CAMERAS = [
    'CAM_FRONT', 'CAM_FRONT_LEFT', 'CAM_FRONT_RIGHT',
    'CAM_BACK', 'CAM_BACK_LEFT', 'CAM_BACK_RIGHT',
]
PROMPTS = [
    'car', 'truck', 'bus', 'trailer', 'construction vehicle',
    'pedestrian', 'person', 'bicycle', 'motorcycle',
    'traffic cone', 'barrier', 'road sign', 'traffic light',
]
COLORS = np.array([
    [230, 25, 75], [60, 180, 75], [255, 225, 25], [0, 130, 200],
    [245, 130, 48], [145, 30, 180], [70, 240, 240], [240, 50, 230],
    [210, 245, 60], [250, 190, 190], [0, 128, 128], [230, 190, 255],
    [170, 110, 40], [255, 250, 200], [128, 0, 0], [170, 255, 195],
], dtype=np.uint8)
UNKNOWN_COLOR = np.array([128, 128, 128], dtype=np.uint8)


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def load_owlvit(model_name: str, device: str):
    from transformers import OwlViTProcessor, OwlViTForObjectDetection
    processor = OwlViTProcessor.from_pretrained(model_name)
    model = OwlViTForObjectDetection.from_pretrained(model_name).to(device)
    model.eval()
    return processor, model


@torch.no_grad()
def detect_open_vocab(image: Image.Image, prompts, processor, model, device, threshold: float):
    text = [[f'a photo of a {p}' for p in prompts]]
    inputs = processor(text=text, images=image, return_tensors='pt').to(device)
    outputs = model(**inputs)
    target_sizes = torch.tensor([image.size[::-1]], device=device)
    results = processor.post_process_object_detection(
        outputs=outputs, target_sizes=target_sizes, threshold=threshold
    )[0]
    boxes = results['boxes'].detach().cpu().numpy()
    scores = results['scores'].detach().cpu().numpy()
    labels = results['labels'].detach().cpu().numpy()
    keep = []
    # Keep a bounded number per image to make visualizations readable.
    order = np.argsort(-scores)
    for idx in order[:40]:
        x1, y1, x2, y2 = boxes[idx]
        if x2 <= x1 or y2 <= y1:
            continue
        keep.append({
            'box': [float(x1), float(y1), float(x2), float(y2)],
            'score': float(scores[idx]),
            'label_id': int(labels[idx]),
            'label': prompts[int(labels[idx])],
        })
    return keep


def project_lidar_to_camera(nusc, dataroot: Path, sample, cam_name: str):
    lidar_token = sample['data']['LIDAR_TOP']
    cam_token = sample['data'][cam_name]
    lidar_sd = nusc.get('sample_data', lidar_token)
    cam_sd = nusc.get('sample_data', cam_token)
    pc = LidarPointCloud.from_file(str(dataroot / lidar_sd['filename']))
    raw_xyz = pc.points[:3, :].T.copy()

    cs = nusc.get('calibrated_sensor', lidar_sd['calibrated_sensor_token'])
    pc.rotate(Quaternion(cs['rotation']).rotation_matrix)
    pc.translate(np.array(cs['translation']))

    pose = nusc.get('ego_pose', lidar_sd['ego_pose_token'])
    pc.rotate(Quaternion(pose['rotation']).rotation_matrix)
    pc.translate(np.array(pose['translation']))

    pose = nusc.get('ego_pose', cam_sd['ego_pose_token'])
    pc.translate(-np.array(pose['translation']))
    pc.rotate(Quaternion(pose['rotation']).rotation_matrix.T)

    cs = nusc.get('calibrated_sensor', cam_sd['calibrated_sensor_token'])
    pc.translate(-np.array(cs['translation']))
    pc.rotate(Quaternion(cs['rotation']).rotation_matrix.T)

    image = Image.open(dataroot / cam_sd['filename']).convert('RGB')
    w, h = image.size
    depths = pc.points[2, :]
    uv = view_points(pc.points[:3, :], np.array(cs['camera_intrinsic']), normalize=True)[:2, :].T
    mask = (depths > 1.0) & (uv[:, 0] >= 0) & (uv[:, 0] < w) & (uv[:, 1] >= 0) & (uv[:, 1] < h)
    return image, raw_xyz, uv, depths, mask, cam_sd


def assign_boxes_to_points(uv, mask, detections, scores_accum, labels_accum):
    idxs = np.where(mask)[0]
    if not len(idxs):
        return
    pts = uv[idxs]
    for det in detections:
        x1, y1, x2, y2 = det['box']
        inside = (pts[:, 0] >= x1) & (pts[:, 0] <= x2) & (pts[:, 1] >= y1) & (pts[:, 1] <= y2)
        if not np.any(inside):
            continue
        target = idxs[inside]
        better = det['score'] > scores_accum[target]
        target = target[better]
        scores_accum[target] = det['score']
        labels_accum[target] = det['label_id']


def draw_boxes(image, detections, prompts, out_path):
    im = image.copy()
    draw = ImageDraw.Draw(im)
    w, h = im.size
    for det in detections:
        color = tuple(int(c) for c in COLORS[det['label_id'] % len(COLORS)])
        x1, y1, x2, y2 = det['box']
        x1 = max(0, min(float(x1), w - 1)); x2 = max(0, min(float(x2), w - 1))
        y1 = max(0, min(float(y1), h - 1)); y2 = max(0, min(float(y2), h - 1))
        if x2 <= x1 or y2 <= y1:
            continue
        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
        text = f"{det['label']} {det['score']:.2f}"
        label_w = min(w - x1, max(60, 8 * len(text)))
        label_y0 = max(0, y1 - 18)
        label_y1 = max(label_y0 + 1, y1)
        draw.rectangle([x1, label_y0, x1 + label_w, label_y1], fill=color)
        draw.text((x1 + 2, label_y0 + 2), text, fill=(0, 0, 0))
    im.save(out_path)


def draw_projection(image, uv, depths, mask, labels, out_path, color_by='depth'):
    im = np.array(image).copy()
    idxs = np.where(mask)[0]
    if len(idxs):
        if color_by == 'label':
            colors = np.repeat(UNKNOWN_COLOR[None, :], len(idxs), axis=0)
            assigned = labels[idxs] >= 0
            colors[assigned] = COLORS[labels[idxs][assigned] % len(COLORS)]
        else:
            d = depths[idxs]
            norm = (d - np.percentile(d, 2)) / (np.percentile(d, 98) - np.percentile(d, 2) + 1e-6)
            norm = np.clip(norm, 0, 1)
            cmap = (plt.cm.turbo(1 - norm)[:, :3] * 255).astype(np.uint8)
            colors = cmap
        for (x, y), c in zip(uv[idxs].astype(int), colors):
            cv2.circle(im, (int(x), int(y)), 2, tuple(int(v) for v in c.tolist()), -1)
    Image.fromarray(im).save(out_path)


def draw_bev(points, labels, out_path, title):
    fig, ax = plt.subplots(figsize=(9, 9), dpi=180)
    ax.set_facecolor('#101010')
    xy = points[:, :2]
    assigned = labels >= 0
    ax.scatter(xy[~assigned, 0], xy[~assigned, 1], s=0.08, c='#777777', alpha=0.20, linewidths=0)
    for lid in sorted(set(labels[assigned].tolist())):
        pts = xy[labels == lid]
        color = COLORS[lid % len(COLORS)] / 255.0
        ax.scatter(pts[:, 0], pts[:, 1], s=0.35, c=[color], alpha=0.9, linewidths=0, label=PROMPTS[lid])
    ax.set_xlim(-55, 55); ax.set_ylim(-55, 55)
    ax.set_xlabel('x / meters'); ax.set_ylabel('y / meters')
    ax.set_title(title)
    ax.grid(color='white', alpha=0.08, linewidth=0.5)
    if assigned.any():
        ax.legend(loc='upper right', fontsize=7, markerscale=8, framealpha=0.85)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def draw_gt_bev(nusc, dataroot: Path, sample, points, out_path):
    lidar_token = sample['data']['LIDAR_TOP']
    try:
        lidarseg = nusc.get('lidarseg', lidar_token)
        labels = np.fromfile(dataroot / lidarseg['filename'], dtype=np.uint8)
    except Exception as exc:
        return {'available': False, 'error': str(exc)}
    fig, ax = plt.subplots(figsize=(9, 9), dpi=180)
    ax.set_facecolor('#101010')
    uniq = sorted(np.unique(labels).tolist())
    for lab in uniq:
        pts = points[labels == lab, :2]
        color = COLORS[int(lab) % len(COLORS)] / 255.0
        ax.scatter(pts[:, 0], pts[:, 1], s=0.12, c=[color], alpha=0.75, linewidths=0, label=str(lab))
    ax.set_xlim(-55, 55); ax.set_ylim(-55, 55)
    ax.set_title('nuScenes lidarseg GT reference (raw ids)')
    ax.grid(color='white', alpha=0.08, linewidth=0.5)
    ax.legend(loc='upper right', fontsize=5, ncol=2, markerscale=6, framealpha=0.85)
    fig.tight_layout(); fig.savefig(out_path); plt.close(fig)
    return {'available': True, 'unique_ids': uniq, 'path': str(out_path)}


def write_ply(points, labels, scores, out_path):
    colors = np.repeat(UNKNOWN_COLOR[None, :], len(points), axis=0)
    assigned = labels >= 0
    colors[assigned] = COLORS[labels[assigned] % len(COLORS)]
    with open(out_path, 'w') as f:
        f.write('ply\nformat ascii 1.0\n')
        f.write(f'element vertex {len(points)}\n')
        f.write('property float x\nproperty float y\nproperty float z\n')
        f.write('property uchar red\nproperty uchar green\nproperty uchar blue\n')
        f.write('property int label_id\nproperty float score\nend_header\n')
        for p, c, lab, sc in zip(points, colors, labels, scores):
            f.write(f'{p[0]:.4f} {p[1]:.4f} {p[2]:.4f} {int(c[0])} {int(c[1])} {int(c[2])} {int(lab)} {float(sc):.4f}\n')


def make_montage(paths, out_path, cols=3):
    imgs = [Image.open(p).convert('RGB') for p in paths if Path(p).exists()]
    if not imgs:
        return
    w = min(640, max(im.width for im in imgs))
    resized = []
    for im in imgs:
        scale = w / im.width
        resized.append(im.resize((w, int(im.height * scale))))
    rows = math.ceil(len(resized) / cols)
    h = max(im.height for im in resized)
    canvas = Image.new('RGB', (cols * w, rows * h), (245, 245, 245))
    for i, im in enumerate(resized):
        canvas.paste(im, ((i % cols) * w, (i // cols) * h))
    canvas.save(out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dataroot', default='data/nuscenes_mini/raw')
    ap.add_argument('--version', default='v1.0-mini')
    ap.add_argument('--sample-index', type=int, default=0)
    ap.add_argument('--out-dir', default='outputs/ovsam3d_owlvit_nuscenes_mini')
    ap.add_argument('--model', default='google/owlvit-base-patch32')
    ap.add_argument('--threshold', type=float, default=0.06)
    ap.add_argument('--device', default='cuda' if torch.cuda.is_available() else 'cpu')
    args = ap.parse_args()

    out = Path(args.out_dir) / f'sample_{args.sample_index:03d}'
    ensure_dir(out)
    nusc = NuScenes(version=args.version, dataroot=args.dataroot, verbose=False)
    sample = nusc.sample[args.sample_index]
    dataroot = Path(args.dataroot)

    processor, model = load_owlvit(args.model, args.device)

    # Load a base point cloud once for global accumulation.
    lidar_sd = nusc.get('sample_data', sample['data']['LIDAR_TOP'])
    base_pc = LidarPointCloud.from_file(str(dataroot / lidar_sd['filename']))
    points = base_pc.points[:3, :].T.copy()
    labels = np.full(points.shape[0], -1, dtype=np.int32)
    scores = np.zeros(points.shape[0], dtype=np.float32)

    cam_summaries = []
    box_paths, proj_paths, label_proj_paths = [], [], []
    for cam in CAMERAS:
        cam_out = out / cam
        ensure_dir(cam_out)
        image, raw_xyz, uv, depths, mask, cam_sd = project_lidar_to_camera(nusc, dataroot, sample, cam)
        dets = detect_open_vocab(image, PROMPTS, processor, model, args.device, args.threshold)
        assign_boxes_to_points(uv, mask, dets, scores, labels)

        raw_path = cam_out / 'image_raw.jpg'
        box_path = cam_out / 'image_open_vocab_boxes.jpg'
        proj_path = cam_out / 'image_lidar_depth_projection.jpg'
        label_proj_path = cam_out / 'image_open_vocab_point_projection.jpg'
        image.save(raw_path)
        draw_boxes(image, dets, PROMPTS, box_path)
        draw_projection(image, uv, depths, mask, labels, proj_path, 'depth')
        draw_projection(image, uv, depths, mask, labels, label_proj_path, 'label')
        with open(cam_out / 'detections.json', 'w') as f:
            json.dump(dets, f, indent=2)
        box_paths.append(box_path); proj_paths.append(proj_path); label_proj_paths.append(label_proj_path)
        cam_summaries.append({
            'camera': cam,
            'image': cam_sd['filename'],
            'projected_points': int(mask.sum()),
            'detections': len(dets),
            'top_detections': dets[:8],
            'outputs': {
                'raw': str(raw_path),
                'boxes': str(box_path),
                'depth_projection': str(proj_path),
                'open_vocab_projection': str(label_proj_path),
            }
        })

    draw_bev(points, labels, out / 'bev_open_vocab_labels.png', 'OV-SAM3D/OV3D-style open-vocabulary point labels')
    gt_info = draw_gt_bev(nusc, dataroot, sample, points, out / 'bev_lidarseg_gt_reference.png')
    write_ply(points, labels, scores, out / 'open_vocab_labeled_points.ply')
    make_montage(box_paths, out / 'montage_open_vocab_boxes.jpg', cols=3)
    make_montage(proj_paths, out / 'montage_lidar_depth_projection.jpg', cols=3)
    make_montage(label_proj_paths, out / 'montage_open_vocab_point_projection.jpg', cols=3)

    assigned = labels >= 0
    label_hist = {PROMPTS[i]: int((labels == i).sum()) for i in sorted(set(labels[assigned].tolist()))}
    summary = {
        'status': 'OK',
        'method': 'OV-SAM3D/OV3D-style minimal 2D open-vocabulary to 3D projection scaffold',
        'note': 'Uses OWL-ViT open-vocabulary 2D detections as a replaceable 2D prior. SAM/RAM masks can replace boxes later.',
        'version': args.version,
        'dataroot': args.dataroot,
        'sample_index': args.sample_index,
        'sample_token': sample['token'],
        'scene_token': sample['scene_token'],
        'model': args.model,
        'threshold': args.threshold,
        'device': args.device,
        'prompts': PROMPTS,
        'points_total': int(points.shape[0]),
        'points_assigned_open_vocab': int(assigned.sum()),
        'assigned_ratio': float(assigned.mean()),
        'label_histogram': label_hist,
        'camera_summaries': cam_summaries,
        'gt_reference': gt_info,
        'outputs': {
            'bev_open_vocab': str(out / 'bev_open_vocab_labels.png'),
            'bev_lidarseg_gt_reference': str(out / 'bev_lidarseg_gt_reference.png'),
            'ply': str(out / 'open_vocab_labeled_points.ply'),
            'montage_boxes': str(out / 'montage_open_vocab_boxes.jpg'),
            'montage_depth_projection': str(out / 'montage_lidar_depth_projection.jpg'),
            'montage_open_vocab_projection': str(out / 'montage_open_vocab_point_projection.jpg'),
        }
    }
    with open(out / 'summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2)[:4000])
    print('OUTPUT_DIR', out)


if __name__ == '__main__':
    main()
