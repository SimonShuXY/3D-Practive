# SAM / CLIP Metric and Label Ablation Report

## Run-Level Summary

| Run | Label mode | Merge person | CLIP min | Stage | Coverage | Mapped acc | Macro P | Macro R | Macro IoU | Classes |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ovsam3d_sam_clip_eval_nuscenes_mini | unknown | False | n/a | box | 0.302 | 0.206 | 0.155 | 0.224 | 0.082 | 13 |
| ovsam3d_sam_clip_eval_nuscenes_mini | unknown | False | n/a | sam | 0.201 | 0.304 | 0.264 | 0.194 | 0.092 | 14 |
| ovsam3d_ablation_hybrid_merge_person_nuscenes_mini | hybrid | True | 0.12 | box | 0.302 | 0.206 | 0.155 | 0.224 | 0.082 | 13 |
| ovsam3d_ablation_hybrid_merge_person_nuscenes_mini | hybrid | True | 0.12 | sam | 0.201 | 0.304 | 0.264 | 0.194 | 0.092 | 14 |
| ovsam3d_ablation_owl_merge_person_nuscenes_mini | owl | True | 0.12 | box | 0.302 | 0.328 | 0.130 | 0.260 | 0.097 | 13 |
| ovsam3d_ablation_owl_merge_person_nuscenes_mini | owl | True | 0.12 | sam | 0.201 | 0.464 | 0.189 | 0.254 | 0.134 | 13 |
| ovsam3d_ablation_clip_merge_person_nuscenes_mini | clip | True | 0.12 | box | 0.302 | 0.196 | 0.153 | 0.221 | 0.080 | 13 |
| ovsam3d_ablation_clip_merge_person_nuscenes_mini | clip | True | 0.12 | sam | 0.201 | 0.298 | 0.264 | 0.193 | 0.091 | 14 |
| ovsam3d_ablation_hybrid_clip030_merge_person_nuscenes_mini | hybrid | True | 0.30 | box | 0.302 | 0.206 | 0.156 | 0.226 | 0.084 | 13 |
| ovsam3d_ablation_hybrid_clip030_merge_person_nuscenes_mini | hybrid | True | 0.30 | sam | 0.201 | 0.305 | 0.203 | 0.215 | 0.100 | 13 |
| ovsam3d_ablation_hybrid_clip045_merge_person_nuscenes_mini | hybrid | True | 0.45 | box | 0.302 | 0.222 | 0.169 | 0.238 | 0.097 | 13 |
| ovsam3d_ablation_hybrid_clip045_merge_person_nuscenes_mini | hybrid | True | 0.45 | sam | 0.201 | 0.329 | 0.236 | 0.228 | 0.126 | 13 |
| ovsam3d_ablation_hybrid_clip060_merge_person_nuscenes_mini | hybrid | True | 0.60 | box | 0.302 | 0.236 | 0.097 | 0.253 | 0.070 | 13 |
| ovsam3d_ablation_hybrid_clip060_merge_person_nuscenes_mini | hybrid | True | 0.60 | sam | 0.201 | 0.356 | 0.143 | 0.239 | 0.098 | 13 |

## Main Reading

- Compare `box` and `sam` rows inside the same run to estimate how much SAM reduces box spillover.
- Compare `hybrid`, `owl`, and `clip` runs to estimate whether the label bottleneck comes from the detector label or CLIP crop retagging.
- Use merged-person rows as the default diagnostic when matching nuScenes lidarseg because `person` and `pedestrian` share the same closed-set target.

## Lowest SAM IoU Classes

| Run | Class | TP | Pred | GT | Precision | Recall | IoU |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ovsam3d_ablation_owl_merge_person_nuscenes_mini | road | 0 | 0 | 59005 | n/a | 0.000 | 0.000 |
| ovsam3d_ablation_hybrid_clip060_merge_person_nuscenes_mini | road | 0 | 0 | 59005 | n/a | 0.000 | 0.000 |
| ovsam3d_sam_clip_eval_nuscenes_mini | building | 0 | 0 | 19685 | n/a | 0.000 | 0.000 |
| ovsam3d_ablation_hybrid_merge_person_nuscenes_mini | building | 0 | 0 | 19685 | n/a | 0.000 | 0.000 |
| ovsam3d_ablation_owl_merge_person_nuscenes_mini | building | 0 | 0 | 19685 | n/a | 0.000 | 0.000 |
| ovsam3d_ablation_clip_merge_person_nuscenes_mini | building | 0 | 0 | 19685 | n/a | 0.000 | 0.000 |
| ovsam3d_ablation_hybrid_clip030_merge_person_nuscenes_mini | building | 0 | 0 | 19685 | n/a | 0.000 | 0.000 |
| ovsam3d_ablation_hybrid_clip045_merge_person_nuscenes_mini | building | 0 | 0 | 19685 | n/a | 0.000 | 0.000 |
| ovsam3d_ablation_hybrid_clip060_merge_person_nuscenes_mini | building | 0 | 0 | 19685 | n/a | 0.000 | 0.000 |
| ovsam3d_ablation_owl_merge_person_nuscenes_mini | vegetation | 0 | 0 | 16345 | n/a | 0.000 | 0.000 |
| ovsam3d_ablation_hybrid_clip030_merge_person_nuscenes_mini | vegetation | 0 | 0 | 16345 | n/a | 0.000 | 0.000 |
| ovsam3d_ablation_hybrid_clip045_merge_person_nuscenes_mini | vegetation | 0 | 0 | 16345 | n/a | 0.000 | 0.000 |
| ovsam3d_ablation_hybrid_clip060_merge_person_nuscenes_mini | vegetation | 0 | 0 | 16345 | n/a | 0.000 | 0.000 |
| ovsam3d_sam_clip_eval_nuscenes_mini | sidewalk | 0 | 0 | 2277 | n/a | 0.000 | 0.000 |
| ovsam3d_ablation_hybrid_merge_person_nuscenes_mini | sidewalk | 0 | 0 | 2277 | n/a | 0.000 | 0.000 |
| ovsam3d_ablation_owl_merge_person_nuscenes_mini | sidewalk | 0 | 0 | 2277 | n/a | 0.000 | 0.000 |
| ovsam3d_ablation_clip_merge_person_nuscenes_mini | sidewalk | 0 | 0 | 2277 | n/a | 0.000 | 0.000 |
| ovsam3d_ablation_hybrid_clip030_merge_person_nuscenes_mini | sidewalk | 0 | 0 | 2277 | n/a | 0.000 | 0.000 |
| ovsam3d_ablation_hybrid_clip045_merge_person_nuscenes_mini | sidewalk | 0 | 0 | 2277 | n/a | 0.000 | 0.000 |
| ovsam3d_ablation_hybrid_clip060_merge_person_nuscenes_mini | sidewalk | 0 | 0 | 2277 | n/a | 0.000 | 0.000 |
| ovsam3d_sam_clip_eval_nuscenes_mini | construction vehicle | 0 | 457 | 32 | 0.000 | 0.000 | 0.000 |
| ovsam3d_ablation_hybrid_merge_person_nuscenes_mini | construction vehicle | 0 | 457 | 32 | 0.000 | 0.000 | 0.000 |
| ovsam3d_ablation_owl_merge_person_nuscenes_mini | construction vehicle | 0 | 0 | 32 | n/a | 0.000 | 0.000 |
| ovsam3d_ablation_clip_merge_person_nuscenes_mini | construction vehicle | 0 | 457 | 32 | 0.000 | 0.000 | 0.000 |

## Label Source Changes

| Run | Regions | Changed from OWL | Changed ratio | CLIP wins | OWL wins | Top final labels |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| ovsam3d_sam_clip_eval_nuscenes_mini | 193 | 87 | 0.451 | 87 | 106 | barrier:57, pedestrian:38, car:21, traffic cone:20, traffic light:15, trailer:15, truck:13, construction vehicle:10 |
| ovsam3d_ablation_hybrid_merge_person_nuscenes_mini | 193 | 87 | 0.451 | 87 | 106 | barrier:57, pedestrian:38, car:21, traffic cone:20, traffic light:15, trailer:15, truck:13, construction vehicle:10 |
| ovsam3d_ablation_owl_merge_person_nuscenes_mini | 193 | 0 | 0.000 | 0 | 193 | car:56, barrier:42, pedestrian:28, truck:25, traffic light:12, traffic cone:11, road sign:9, trailer:6 |
| ovsam3d_ablation_clip_merge_person_nuscenes_mini | 193 | 87 | 0.451 | 87 | 106 | barrier:57, pedestrian:38, car:21, traffic cone:20, traffic light:15, trailer:15, truck:13, construction vehicle:10 |
| ovsam3d_ablation_hybrid_clip030_merge_person_nuscenes_mini | 193 | 46 | 0.238 | 46 | 147 | barrier:47, car:46, pedestrian:34, traffic cone:17, truck:14, trailer:13, traffic light:11, road sign:5 |
| ovsam3d_ablation_hybrid_clip045_merge_person_nuscenes_mini | 193 | 24 | 0.124 | 24 | 169 | car:54, barrier:45, pedestrian:32, truck:15, traffic cone:13, traffic light:11, trailer:10, road sign:7 |
| ovsam3d_ablation_hybrid_clip060_merge_person_nuscenes_mini | 193 | 16 | 0.083 | 16 | 177 | car:56, barrier:43, pedestrian:31, truck:20, traffic cone:13, traffic light:12, road sign:7, trailer:6 |

CSV files:

- `run_level_metrics.csv`
- `sample_level_metrics.csv`
- `per_class_metrics.csv`
- `label_source_transitions.csv`
