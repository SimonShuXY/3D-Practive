# 3D-Practive: OV3D / OV-SAM3D Open-Vocabulary 3D Reproduction Notes

This repository stores the isolated open-vocabulary 3D reproduction branch built after the IPFP/PTv3 experiments.

The current executable scaffold is an OV-SAM3D/OV3D-style visual closed loop on nuScenes-mini.
It now contains two stages:

1. A first OWL-ViT box projection scaffold.
2. A SAM + CLIP upgrade with lightweight lidarseg diagnostics and multi-frame fusion.

```text
nuScenes-mini multi-camera images
-> OWL-ViT open-vocabulary 2D detections
-> optional SAM mask refinement + CLIP crop tagging
-> LiDAR-camera projection
-> 3D point label aggregation
-> BEV / camera / PLY visualizations
```

This is not yet a faithful official OV-SAM3D implementation. It uses OWL-ViT as the open-vocabulary detector and SAM as the mask refiner, with CLIP crop scores used as a lightweight RAM/Tag2Text substitute.

## Contents

- `scripts/run_open_vocab_nuscenes_owlvit.py`: runnable nuScenes-mini open-vocabulary 2D-to-3D visualization scaffold.
- `scripts/run_sam_clip_eval_multiframe.py`: SAM-refined masks, CLIP crop tags, lidarseg mapped diagnostics, and multi-frame semantic fusion.
- `docs/DATA_MANIFEST.md`: remote data symlink layout and isolation policy.
- `docs/OVSAM3D_OV3D_REPRO_STATUS.md`: current result summary, limitations, and next steps.
- `results/ovsam3d_owlvit_nuscenes_mini/`: generated visualizations for five nuScenes-mini samples.
- `results/ovsam3d_sam_clip_eval_nuscenes_mini/`: SAM/CLIP upgraded visualizations and diagnostics for five nuScenes-mini samples.

## Main Results

### SAM / CLIP / Evaluation / Multi-frame Upgrade

This run advances the scaffold in four directions at once:

- OWL-ViT boxes are refined into SAM masks.
- CLIP crop labels are stored as automatic open-vocabulary tags.
- Point labels are mapped to nuScenes lidarseg classes for a lightweight quality check.
- Five frames are fused into a global-coordinate semantic map.

| Sample | Points | Box assigned ratio | SAM assigned ratio | Box mapped accuracy | SAM mapped accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| sample_000 | 34688 | 0.311 | 0.171 | 0.072 | 0.134 |
| sample_001 | 34720 | 0.371 | 0.248 | 0.231 | 0.336 |
| sample_002 | 34720 | 0.154 | 0.105 | 0.036 | 0.045 |
| sample_003 | 34688 | 0.327 | 0.265 | 0.240 | 0.336 |
| sample_004 | 34752 | 0.347 | 0.214 | 0.341 | 0.489 |

The SAM stage assigns fewer points than raw boxes, but mapped accuracy improves on all five checked samples. This is the desired direction for this diagnostic: SAM reduces broad box spillover, while the remaining errors are mostly label calibration and open-vocabulary-to-nuScenes mismatch.

Key visualizations:

![SAM masks and CLIP tags](results/ovsam3d_sam_clip_eval_nuscenes_mini/contact_sheet_sam_clip_masks.jpg)

![SAM point projection](results/ovsam3d_sam_clip_eval_nuscenes_mini/contact_sheet_sam_point_projection.jpg)

![SAM BEV versus lidarseg GT](results/ovsam3d_sam_clip_eval_nuscenes_mini/contact_sheet_sam_bev_vs_gt.jpg)

![Multi-frame SAM open-vocabulary map](results/ovsam3d_sam_clip_eval_nuscenes_mini/multiframe_sam_open_vocab_bev.png)

See `results/ovsam3d_sam_clip_eval_nuscenes_mini/SAM_CLIP_EVAL_MULTIFRAME_REPORT.md` for the compact run report and `run_summary.json` for per-region diagnostics.

### Initial OWL-ViT Box Scaffold

Five nuScenes-mini samples were processed. Each sample includes:

- six-camera 2D open-vocabulary detection montages,
- six-camera LiDAR depth projection montages,
- six-camera projected open-vocabulary point label montages,
- BEV open-vocabulary point labels,
- BEV nuScenes lidarseg GT reference using raw ids,
- colored `.ply` point cloud,
- per-sample `summary.json`.

Top-level contact sheets:

- `results/ovsam3d_owlvit_nuscenes_mini/contact_sheet_open_vocab_boxes.jpg`
- `results/ovsam3d_owlvit_nuscenes_mini/contact_sheet_open_vocab_projection.jpg`
- `results/ovsam3d_owlvit_nuscenes_mini/contact_sheet_bev_vs_gt.jpg`

## Reproduction

Use the existing isolated remote data layout:

```text
/root/autodl-tmp/open_vocab3d_repro/data/nuscenes_mini
/root/autodl-tmp/open_vocab3d_repro/data/semantic_kitti
```

Example:

```bash
cd /root/autodl-tmp/open_vocab3d_repro
HF_HOME=/root/autodl-tmp/open_vocab3d_repro/weights/hf_home \
TRANSFORMERS_CACHE=/root/autodl-tmp/open_vocab3d_repro/weights/hf_cache \
/root/autodl-tmp/ipfp_repro/.venv/bin/python \
  scripts/run_open_vocab_nuscenes_owlvit.py \
  --sample-index 0 \
  --threshold 0.06
```

SAM / CLIP upgraded run:

```bash
cd /root/autodl-tmp/open_vocab3d_repro
HF_HOME=/root/autodl-tmp/open_vocab3d_repro/weights/hf_home \
TRANSFORMERS_CACHE=/root/autodl-tmp/open_vocab3d_repro/weights/hf_cache \
/root/autodl-tmp/ipfp_repro/.venv/bin/python \
  scripts/run_sam_clip_eval_multiframe.py \
  --sample-indices 0-4 \
  --max-detections-per-camera 12 \
  --out-dir outputs/ovsam3d_sam_clip_eval_nuscenes_mini
```

## Current Caveats

- The current tagger is CLIP crop scoring, not a full RAM/Tag2Text/VLM captioning stack.
- Object-like categories work better than stuff categories such as road and sidewalk.
- Open-vocabulary prompt labels do not perfectly match nuScenes closed-set semantic labels.
- Treat the current result as a visual reproduction and diagnostic scaffold, not a benchmark reproduction.

## Next Steps

1. Calibrate prompt-to-class mapping, especially `person`/`pedestrian`, trailer, construction vehicle, and barrier.
2. Add per-class IoU / precision / recall summaries after label merging.
3. Add SemanticKITTI front-camera mode for comparison with prior closed-set experiments.
4. If official OV-SAM3D/OV3D code becomes available, adapt its 2D mask/tag stage into this output interface.
