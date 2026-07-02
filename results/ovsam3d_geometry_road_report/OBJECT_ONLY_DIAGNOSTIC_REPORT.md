# Object-Only SAM Diagnostic Report

This report intentionally removes stuff/background classes from the main reading. It is a diagnostic for the current object-mask route, not a full-scene semantic segmentation benchmark. When present, `superpoint` is an official-like 3D overlap-voting post-process over SAM point labels. `road_fused` also adds a geometry road prior, so its object rows should be read together with full/stuff metrics.

## Object Groups

| Run | Label mode | Stage | Group | Assigned acc | Micro R | Micro IoU | Macro IoU | Classes | Class list |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| owl | owl | sam | object | 0.464 | 0.692 | 0.385 | 0.194 | 9 | barrier, bicycle, bus, car, construction vehicle, pedestrian, traffic cone, trailer, truck |
| owl | owl | sam | frequent_object | 0.506 | 0.694 | 0.413 | 0.350 | 5 | barrier, car, pedestrian, traffic cone, truck |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | owl | sam | object | 0.464 | 0.692 | 0.385 | 0.194 | 9 | barrier, bicycle, bus, car, construction vehicle, pedestrian, traffic cone, trailer, truck |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | owl | sam | frequent_object | 0.506 | 0.694 | 0.413 | 0.350 | 5 | barrier, car, pedestrian, traffic cone, truck |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | owl | superpoint | object | 0.464 | 0.743 | 0.400 | 0.208 | 9 | barrier, bicycle, bus, car, construction vehicle, pedestrian, traffic cone, trailer, truck |
| ovsam3d_official_like_superpoint_owl_nuscenes_mini | owl | superpoint | frequent_object | 0.512 | 0.744 | 0.436 | 0.375 | 5 | barrier, car, pedestrian, traffic cone, truck |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | owl | sam | object | 0.464 | 0.692 | 0.385 | 0.194 | 9 | barrier, bicycle, bus, car, construction vehicle, pedestrian, traffic cone, trailer, truck |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | owl | sam | frequent_object | 0.506 | 0.694 | 0.413 | 0.350 | 5 | barrier, car, pedestrian, traffic cone, truck |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | owl | superpoint | object | 0.464 | 0.743 | 0.400 | 0.208 | 9 | barrier, bicycle, bus, car, construction vehicle, pedestrian, traffic cone, trailer, truck |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | owl | superpoint | frequent_object | 0.512 | 0.744 | 0.436 | 0.375 | 5 | barrier, car, pedestrian, traffic cone, truck |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | owl | road_fused | object | 0.464 | 0.743 | 0.400 | 0.208 | 9 | barrier, bicycle, bus, car, construction vehicle, pedestrian, traffic cone, trailer, truck |
| ovsam3d_geometry_road_superpoint_owl_nuscenes_mini | owl | road_fused | frequent_object | 0.512 | 0.744 | 0.436 | 0.375 | 5 | barrier, car, pedestrian, traffic cone, truck |

## Best Object-Only Route

- Best object-only run: `ovsam3d_official_like_superpoint_owl_nuscenes_mini`.
- Best object-only stage: `superpoint`.
- Object assigned accuracy: `0.464`.
- Object micro IoU: `0.400`.
- Object macro IoU: `0.208`.

## Frequent-Object Reading

`frequent_object` keeps object classes with enough ground-truth support in this mini split. It is useful for checking whether the object-mask chain works before long-tail classes dominate the macro average.

- Best frequent-object run: `ovsam3d_official_like_superpoint_owl_nuscenes_mini`.
- Best frequent-object stage: `superpoint`.
- Frequent-object assigned accuracy: `0.512`.
- Frequent-object micro IoU: `0.436`.
- Frequent-object macro IoU: `0.375`.
- Frequent-object classes: `barrier, car, pedestrian, traffic cone, truck`.

## Best Run Per-Object Classes

| Class | TP | Pred | GT | Precision | Recall | IoU |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| truck | 11677 | 13539 | 16239 | 0.862 | 0.719 | 0.645 |
| pedestrian | 1042 | 1411 | 1558 | 0.738 | 0.669 | 0.541 |
| traffic cone | 49 | 82 | 104 | 0.598 | 0.471 | 0.358 |
| barrier | 4460 | 13366 | 5072 | 0.334 | 0.879 | 0.319 |
| car | 75 | 5378 | 271 | 0.014 | 0.277 | 0.013 |
| bicycle | 0 | 0 | 10 | n/a | 0.000 | 0.000 |
| bus | 0 | 8 | 8 | 0.000 | 0.000 | 0.000 |
| construction vehicle | 0 | 0 | 32 | n/a | 0.000 | 0.000 |
| trailer | 0 | 3480 | 0 | 0.000 | n/a | 0.000 |

## Reading Rule

- Use `object` to evaluate the object-mask route without background classes.
- Use `frequent_object` to inspect classes with enough support in the current mini split.
- Keep `full` and `stuff` metrics visible elsewhere so the report does not claim full-scene segmentation.
