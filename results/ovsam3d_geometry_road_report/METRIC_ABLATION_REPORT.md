# SAM / CLIP Metric and Label Ablation Report

## Run-Level Summary

| Run | Label mode | Merge person | CLIP min | Stage | Coverage | Mapped acc | Macro P | Macro R | Macro IoU | Classes |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ovsam3d_ablation_owl_merge_person_nuscenes_mini | owl | True | 0.12 | box | 0.302 | 0.328 | 0.130 | 0.260 | 0.097 | 13 |
| ovsam3d_ablation_owl_merge_person_nuscenes_mini | owl | True | 0.12 | sam | 0.201 | 0.464 | 0.189 | 0.254 | 0.134 | 13 |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | owl | True | 0.12 | box | 0.302 | 0.328 | 0.130 | 0.260 | 0.097 | 13 |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | owl | True | 0.12 | sam | 0.201 | 0.464 | 0.189 | 0.254 | 0.134 | 13 |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | owl | True | 0.12 | superpoint | 0.215 | 0.464 | 0.196 | 0.232 | 0.144 | 13 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | owl | True | 0.12 | box | 0.302 | 0.328 | 0.130 | 0.260 | 0.097 | 13 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | owl | True | 0.12 | sam | 0.201 | 0.464 | 0.189 | 0.254 | 0.134 | 13 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | owl | True | 0.12 | superpoint | 0.215 | 0.464 | 0.196 | 0.232 | 0.144 | 13 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | owl | True | 0.12 | road_fused | 0.548 | 0.685 | 0.260 | 0.294 | 0.198 | 13 |

## Split Metrics

This table separates the SAM/superpoint/road-fused stage score into all mapped classes, object-like prompts, frequent object classes, and stuff/background classes. `Assigned acc` is micro precision over the points assigned to that group.

| Run | Label mode | Stage | Group | Coverage | Group pred ratio | Assigned acc | Micro R | Micro IoU | Macro IoU | Classes |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ovsam3d_ablation_owl_merge_person_nuscenes_mini | owl | sam | full | 0.201 | 0.200 | 0.464 | 0.134 | 0.116 | 0.134 | 13 |
| ovsam3d_ablation_owl_merge_person_nuscenes_mini | owl | sam | object | 0.201 | 0.200 | 0.464 | 0.692 | 0.385 | 0.194 | 9 |
| ovsam3d_ablation_owl_merge_person_nuscenes_mini | owl | sam | stuff | 0.201 | 0.000 | n/a | 0.000 | 0.000 | 0.000 | 4 |
| ovsam3d_ablation_owl_merge_person_nuscenes_mini | owl | sam | frequent_object | 0.201 | 0.184 | 0.506 | 0.694 | 0.413 | 0.350 | 5 |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | owl | sam | full | 0.201 | 0.200 | 0.464 | 0.134 | 0.116 | 0.134 | 13 |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | owl | sam | object | 0.201 | 0.200 | 0.464 | 0.692 | 0.385 | 0.194 | 9 |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | owl | sam | stuff | 0.201 | 0.000 | n/a | 0.000 | 0.000 | 0.000 | 4 |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | owl | sam | frequent_object | 0.201 | 0.184 | 0.506 | 0.694 | 0.413 | 0.350 | 5 |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | owl | superpoint | full | 0.215 | 0.215 | 0.464 | 0.143 | 0.123 | 0.144 | 13 |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | owl | superpoint | object | 0.215 | 0.215 | 0.464 | 0.743 | 0.400 | 0.208 | 9 |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | owl | superpoint | stuff | 0.215 | 0.000 | n/a | 0.000 | 0.000 | 0.000 | 4 |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | owl | superpoint | frequent_object | 0.215 | 0.195 | 0.512 | 0.744 | 0.436 | 0.375 | 5 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | owl | sam | full | 0.201 | 0.200 | 0.464 | 0.134 | 0.116 | 0.134 | 13 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | owl | sam | object | 0.201 | 0.200 | 0.464 | 0.692 | 0.385 | 0.194 | 9 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | owl | sam | stuff | 0.201 | 0.000 | n/a | 0.000 | 0.000 | 0.000 | 4 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | owl | sam | frequent_object | 0.201 | 0.184 | 0.506 | 0.694 | 0.413 | 0.350 | 5 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | owl | superpoint | full | 0.215 | 0.215 | 0.464 | 0.143 | 0.123 | 0.144 | 13 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | owl | superpoint | object | 0.215 | 0.215 | 0.464 | 0.743 | 0.400 | 0.208 | 9 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | owl | superpoint | stuff | 0.215 | 0.000 | n/a | 0.000 | 0.000 | 0.000 | 4 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | owl | superpoint | frequent_object | 0.215 | 0.195 | 0.512 | 0.744 | 0.436 | 0.375 | 5 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | owl | road_fused | full | 0.548 | 0.548 | 0.685 | 0.540 | 0.433 | 0.198 | 13 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | owl | road_fused | object | 0.548 | 0.215 | 0.464 | 0.743 | 0.400 | 0.208 | 9 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | owl | road_fused | stuff | 0.548 | 0.333 | 0.828 | 0.492 | 0.446 | 0.174 | 4 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | owl | road_fused | frequent_object | 0.548 | 0.195 | 0.512 | 0.744 | 0.436 | 0.375 | 5 |

## Main Reading

- Compare `box` and `sam` rows inside the same run to estimate how much SAM reduces box spillover.
- Compare `hybrid`, `owl`, and `clip` runs to estimate whether the label bottleneck comes from the detector label or CLIP crop retagging.
- Use merged-person rows as the default diagnostic when matching nuScenes lidarseg because `person` and `pedestrian` share the same closed-set target.
- Read the full macro IoU together with object/stuff split metrics. The current prompt route is object-centric, so missing stuff predictions can depress full-scene macro IoU even when object assigned accuracy is improving.
- Read `frequent_object` as the cleanest current object-mask diagnostic: it removes background and also avoids tiny long-tail classes dominating a five-sample mini split.
- Compare `sam` with `superpoint` rows to test whether 3D overlap voting improves precision enough to offset lower coverage.
- Compare `road_fused` with `superpoint` rows to estimate whether a simple geometry prior can lift full/stuff scores before adding a real dense stuff model.

## Lowest SAM IoU Classes

| Run | Class | TP | Pred | GT | Precision | Recall | IoU |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ovsam3d_ablation_owl_merge_person_nuscenes_mini | road | 0 | 0 | 59005 | n/a | 0.000 | 0.000 |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | road | 0 | 0 | 59005 | n/a | 0.000 | 0.000 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | road | 0 | 0 | 59005 | n/a | 0.000 | 0.000 |
| ovsam3d_ablation_owl_merge_person_nuscenes_mini | building | 0 | 0 | 19685 | n/a | 0.000 | 0.000 |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | building | 0 | 0 | 19685 | n/a | 0.000 | 0.000 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | building | 0 | 0 | 19685 | n/a | 0.000 | 0.000 |
| ovsam3d_ablation_owl_merge_person_nuscenes_mini | vegetation | 0 | 0 | 16345 | n/a | 0.000 | 0.000 |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | vegetation | 0 | 0 | 16345 | n/a | 0.000 | 0.000 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | vegetation | 0 | 0 | 16345 | n/a | 0.000 | 0.000 |
| ovsam3d_ablation_owl_merge_person_nuscenes_mini | sidewalk | 0 | 0 | 2277 | n/a | 0.000 | 0.000 |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | sidewalk | 0 | 0 | 2277 | n/a | 0.000 | 0.000 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | sidewalk | 0 | 0 | 2277 | n/a | 0.000 | 0.000 |
| ovsam3d_ablation_owl_merge_person_nuscenes_mini | construction vehicle | 0 | 0 | 32 | n/a | 0.000 | 0.000 |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | construction vehicle | 0 | 0 | 32 | n/a | 0.000 | 0.000 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | construction vehicle | 0 | 0 | 32 | n/a | 0.000 | 0.000 |
| ovsam3d_ablation_owl_merge_person_nuscenes_mini | bicycle | 0 | 8 | 10 | 0.000 | 0.000 | 0.000 |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | bicycle | 0 | 8 | 10 | 0.000 | 0.000 | 0.000 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | bicycle | 0 | 8 | 10 | 0.000 | 0.000 | 0.000 |
| ovsam3d_ablation_owl_merge_person_nuscenes_mini | bus | 0 | 53 | 8 | 0.000 | 0.000 | 0.000 |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | bus | 0 | 53 | 8 | 0.000 | 0.000 | 0.000 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | bus | 0 | 53 | 8 | 0.000 | 0.000 | 0.000 |
| ovsam3d_ablation_owl_merge_person_nuscenes_mini | trailer | 0 | 2782 | 0 | 0.000 | n/a | 0.000 |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | trailer | 0 | 2782 | 0 | 0.000 | n/a | 0.000 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | trailer | 0 | 2782 | 0 | 0.000 | n/a | 0.000 |

## Label Source Changes

| Run | Regions | Changed from OWL | Changed ratio | CLIP wins | OWL wins | Top final labels |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| ovsam3d_ablation_owl_merge_person_nuscenes_mini | 193 | 0 | 0.000 | 0 | 193 | car:56, barrier:42, pedestrian:28, truck:25, traffic light:12, traffic cone:11, road sign:9, trailer:6 |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | 193 | 0 | 0.000 | 0 | 193 | car:56, barrier:42, pedestrian:28, truck:25, traffic light:12, traffic cone:11, road sign:9, trailer:6 |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | 193 | 0 | 0.000 | 0 | 193 | car:56, barrier:42, pedestrian:28, truck:25, traffic light:12, traffic cone:11, road sign:9, trailer:6 |

CSV files:

- `run_level_metrics.csv`
- `sample_level_metrics.csv`
- `group_metrics.csv`
- `OBJECT_ONLY_DIAGNOSTIC_REPORT.md`
- `per_class_metrics.csv`
- `label_source_transitions.csv`
