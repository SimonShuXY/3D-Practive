# SAM / CLIP / Evaluation / Multi-frame Results

This run upgrades the initial OWL-ViT box scaffold in four ways:

1. OWL-ViT boxes are refined with SAM masks.
2. CLIP crop tags are recorded as RAM-style automatic labels.
3. Open-vocabulary point labels are mapped to nuScenes lidarseg classes for a lightweight quality check.
4. Optional 3D superpoint overlap voting smooths SAM point labels in an official-like post-processing step.
5. Optional geometry-road filling adds a simple LiDAR ground prior for the `road` class.
6. Per-frame predictions are fused into a multi-frame global-coordinate semantic map.

## Summary

Config: `label_mode=owl`,
`merge_person_labels=True`.

| Sample | Points | Box assigned ratio | SAM assigned ratio | Superpoint assigned ratio | Road-fused assigned ratio | Box mapped accuracy | SAM mapped accuracy | Superpoint mapped accuracy | Road-fused mapped accuracy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| sample_000 | 34688 | 0.311 | 0.171 | 0.185 | 0.513 | 0.079 | 0.138 | 0.101 | 0.547 |
| sample_001 | 34720 | 0.371 | 0.248 | 0.252 | 0.548 | 0.116 | 0.173 | 0.152 | 0.473 |
| sample_002 | 34720 | 0.154 | 0.105 | 0.103 | 0.534 | 0.643 | 0.852 | 0.877 | 0.815 |
| sample_003 | 34688 | 0.327 | 0.265 | 0.279 | 0.585 | 0.605 | 0.706 | 0.754 | 0.823 |
| sample_004 | 34752 | 0.347 | 0.214 | 0.257 | 0.561 | 0.376 | 0.570 | 0.552 | 0.753 |

## Visualizations

- `contact_sheet_sam_clip_masks.jpg`
- `contact_sheet_sam_point_projection.jpg`
- `contact_sheet_sam_bev_vs_gt.jpg`
- `outputs/ovsam3d_geometry_road_superpoint_owl_nuscenes_mini/multiframe_sam_open_vocab_bev.png`
- `outputs/ovsam3d_geometry_road_superpoint_owl_nuscenes_mini/multiframe_sam_open_vocab_points.ply`

## Interpretation

SAM masks are expected to reduce the broad box spillover seen in the first scaffold.
The assigned ratio can drop after SAM refinement, which is healthy when box labels were
over-covering background points. The mapped accuracy is only a lightweight diagnostic:
open-vocabulary labels do not perfectly match nuScenes lidarseg classes, and unmapped
labels such as road sign / traffic light are ignored by the current metric.
Superpoint voting is a precision-oriented post-processing step. If its assigned ratio drops
while mapped accuracy rises, it is filtering noisy point-level mask spillover. If both drop,
the superpoint thresholds are too strict for the current sparse LiDAR sampling.
Geometry-road filling is a recall-oriented stuff/background baseline. It should be read as
an intentionally simple lower bound for `road`, not as a mature dense 2D/3D stuff model.
