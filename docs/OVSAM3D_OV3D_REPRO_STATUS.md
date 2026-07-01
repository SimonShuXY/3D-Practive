# OV-SAM3D / OV3D Reproduction Status

## Current status

This branch is isolated from the previous IPFP work under `/root/autodl-tmp/open_vocab3d_repro`.
Raw datasets are referenced through symlinks recorded in `docs/DATA_MANIFEST.md`.

Official OV-SAM3D code was not found through the initial public GitHub probes, so the first executable scaffold implements an OV-SAM3D/OV3D-style route:

`nuScenes-mini multi-camera images -> OWL-ViT open-vocabulary 2D detections -> LiDAR-camera projection -> 3D point label aggregation -> BEV / camera / PLY visualizations`.

This is not yet a faithful SAM/RAM mask reproduction. It is the first visual closed loop and a replaceable interface for SAM/RAM masks once code or weights are confirmed.

## Generated samples

| Sample | Points | Open-vocab assigned points | Assigned ratio | Label histogram |
| --- | ---: | ---: | ---: | --- |
| sample_000 | 34688 | 10951 | 0.316 | car:4576, truck:693, construction vehicle:178, pedestrian:2, person:94, traffic cone:26, barrier:5348, road sign:6, traffic light:28 |
| sample_001 | 34720 | 13807 | 0.398 | car:4881, truck:1345, trailer:2968, person:11, traffic cone:78, barrier:4445, road sign:77, traffic light:2 |
| sample_002 | 34720 | 5914 | 0.170 | car:59, truck:3177, trailer:369, pedestrian:58, person:172, bicycle:1, traffic cone:92, barrier:1948, road sign:30, traffic light:8 |
| sample_003 | 34688 | 11407 | 0.329 | car:49, truck:7413, bus:24, pedestrian:7, person:15, traffic cone:63, barrier:3813, road sign:5, traffic light:18 |
| sample_004 | 34752 | 12518 | 0.360 | car:174, truck:3939, trailer:3025, pedestrian:5, person:872, traffic cone:51, barrier:4410, traffic light:42 |

## Main visualizations

- `outputs/ovsam3d_owlvit_nuscenes_mini/contact_sheet_bev_vs_gt.jpg`
- `outputs/ovsam3d_owlvit_nuscenes_mini/contact_sheet_open_vocab_projection.jpg`
- `outputs/ovsam3d_owlvit_nuscenes_mini/contact_sheet_open_vocab_boxes.jpg`

Each sample folder also contains:

- `montage_open_vocab_boxes.jpg`: six-camera 2D open-vocabulary detections.
- `montage_lidar_depth_projection.jpg`: six-camera LiDAR depth projection.
- `montage_open_vocab_point_projection.jpg`: projected points colored by open-vocabulary label.
- `bev_open_vocab_labels.png`: 3D BEV point labels aggregated across cameras.
- `bev_lidarseg_gt_reference.png`: nuScenes lidarseg GT reference, raw ids.
- `open_vocab_labeled_points.ply`: colored 3D point cloud for external viewers.
- `summary.json`: per-sample quantitative summary and output paths.

## Caveats

- Current 2D prior is OWL-ViT boxes, not SAM masks plus RAM tags.
- This favors object-like categories and does not segment stuff classes such as road/sidewalk.
- Current labels are open-vocabulary prompts, not nuScenes closed-set labels.
- The result should be treated as a visual reproduction scaffold, not benchmark reproduction.

## Next implementation steps

1. Replace boxes with SAM masks, using the same projection and aggregation code.
2. Add RAM/Tag2Text or CLIP crop tagging for automatic labels instead of fixed prompts.
3. Add SemanticKITTI front-camera mode for comparison with existing closed-set results.
4. If an official OV-SAM3D/OV3D repository becomes available, adapt its 2D mask/tag stage into this output interface.
