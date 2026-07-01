# Open-Vocabulary 3D Reproduction Data Manifest

This directory isolates the OV-SAM3D / OV3D reproduction branch from the previous IPFP branch.
Large datasets are referenced by symlink only.

## Source data

| Name | Symlink | Source | Intended use |
| --- | --- | --- | --- |
| nuScenes mini + lidarseg mini | `data/nuscenes_mini` | `/root/autodl-tmp/ipfp_repro/data/nuscenes_mini` | primary open-vocabulary 3D demo / visualization target |
| SemanticKITTI + KITTI odometry color/calib/velodyne/labels | `data/semantic_kitti` | `/root/autodl-tmp/ipfp_repro/data/semantic_kitti` | optional front-camera projection / closed-set reference |

## Isolation policy

- Do not edit or move `/root/autodl-tmp/ipfp_repro`.
- Do not duplicate raw datasets.
- Put code under `repos/`, environments under `envs/`, visualizations under `outputs/`, and run notes under `docs/`.
- If a method needs external model weights, store them under `weights/` and record the URL/checksum when possible.
