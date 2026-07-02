# SAM / CLIP / Evaluation / Multi-frame Results

This run upgrades the initial OWL-ViT box scaffold in four ways:

1. OWL-ViT boxes are refined with SAM masks.
2. CLIP crop tags are recorded as RAM-style automatic labels.
3. Open-vocabulary point labels are mapped to nuScenes lidarseg classes for a lightweight quality check.
4. Per-frame predictions are fused into a multi-frame global-coordinate semantic map.

## Summary

Config: `label_mode=owl`,
`merge_person_labels=True`.

| Sample | Points | Box assigned ratio | SAM assigned ratio | Box mapped accuracy | SAM mapped accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| sample_000 | 34688 | 0.311 | 0.171 | 0.079 | 0.138 |
| sample_001 | 34720 | 0.371 | 0.248 | 0.116 | 0.173 |
| sample_002 | 34720 | 0.154 | 0.105 | 0.643 | 0.852 |
| sample_003 | 34688 | 0.327 | 0.265 | 0.605 | 0.706 |
| sample_004 | 34752 | 0.347 | 0.214 | 0.376 | 0.570 |

## Visualizations

- `contact_sheet_sam_clip_masks.jpg`
- `contact_sheet_sam_point_projection.jpg`
- `contact_sheet_sam_bev_vs_gt.jpg`
- `outputs/ovsam3d_ablation_owl_merge_person_nuscenes_mini/multiframe_sam_open_vocab_bev.png`
- `outputs/ovsam3d_ablation_owl_merge_person_nuscenes_mini/multiframe_sam_open_vocab_points.ply`

## Interpretation

SAM masks are expected to reduce the broad box spillover seen in the first scaffold.
The assigned ratio can drop after SAM refinement, which is healthy when box labels were
over-covering background points. The mapped accuracy is only a lightweight diagnostic:
open-vocabulary labels do not perfectly match nuScenes lidarseg classes, and unmapped
labels such as road sign / traffic light are ignored by the current metric.
