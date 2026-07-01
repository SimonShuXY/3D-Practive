# OV3D / OV-SAM3D Open-Vocabulary 3D Reproduction Notes

This repository stores the isolated open-vocabulary 3D reproduction branch built after the IPFP/PTv3 experiments.

The current executable scaffold is an OV-SAM3D/OV3D-style visual closed loop on nuScenes-mini:

```text
nuScenes-mini multi-camera images
-> OWL-ViT open-vocabulary 2D detections
-> LiDAR-camera projection
-> 3D point label aggregation
-> BEV / camera / PLY visualizations
```

This is not yet a faithful official OV-SAM3D implementation. It uses OWL-ViT boxes as the first replaceable 2D prior because a stable public OV-SAM3D code entry was not available during the initial setup. The projection, aggregation, output layout, and visualization interface are ready for replacing boxes with SAM masks plus RAM/Tag2Text/CLIP tags.

## Contents

- `scripts/run_open_vocab_nuscenes_owlvit.py`: runnable nuScenes-mini open-vocabulary 2D-to-3D visualization scaffold.
- `docs/DATA_MANIFEST.md`: remote data symlink layout and isolation policy.
- `docs/OVSAM3D_OV3D_REPRO_STATUS.md`: current result summary, limitations, and next steps.
- `results/ovsam3d_owlvit_nuscenes_mini/`: generated visualizations for five nuScenes-mini samples.

## Main Results

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

## Current Caveats

- The current 2D prior is OWL-ViT boxes, not SAM masks plus RAM tags.
- Object-like categories work better than stuff categories such as road and sidewalk.
- Current labels are open-vocabulary prompt labels, not nuScenes closed-set semantic labels.
- Treat the current result as a visualization scaffold, not a benchmark reproduction.

## Next Steps

1. Replace OWL-ViT boxes with SAM masks.
2. Add RAM/Tag2Text or CLIP crop tagging for automatic labels instead of fixed prompts.
3. Add a SemanticKITTI front-camera mode for comparison with prior closed-set experiments.
4. If official OV-SAM3D/OV3D code becomes available, adapt its 2D mask/tag stage into this output interface.
