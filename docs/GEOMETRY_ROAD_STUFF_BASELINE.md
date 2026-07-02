# Geometry Road Stuff Baseline

This experiment adds a simple LiDAR geometry prior for the `road` class on top
of the OWL-only + SAM + superpoint route. It is not a mature dense stuff model;
it is a low-cost check of whether covering a major background class moves the
full benchmark metrics.

## Setup

- Dataset: `nuScenes-mini` with lidarseg mini labels.
- Samples: `0-4`.
- Base route: `OWL-only -> SAM -> superpoint voting`.
- Added route: fill unassigned low local-ground points as `road`.
- Remote output:
  - `outputs/ovsam3d_geometry_road_superpoint_owl_nuscenes_mini`
  - `outputs/ovsam3d_geometry_road_report`
- Local result copy:
  - `results/ovsam3d_geometry_road_superpoint_owl_nuscenes_mini`
  - `results/ovsam3d_geometry_road_report`

Geometry-road settings:

```text
road_voxel_size = 1.0 m
road_max_height_above_min = 0.20 m
road_max_height_above_global_ground = 0.65 m
road_min_cell_points = 3
road_score = 0.35
```

## Main Result

| Stage | Coverage | Mapped acc | Full micro IoU | Full macro IoU | Stuff micro IoU | Stuff macro IoU |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SAM point labels | 0.201 | 0.464 | 0.116 | 0.134 | 0.000 | 0.000 |
| Superpoint voting | 0.215 | 0.464 | 0.123 | 0.144 | 0.000 | 0.000 |
| Geometry-road fused | 0.548 | 0.685 | 0.433 | 0.198 | 0.446 | 0.174 |

The result confirms that the full benchmark bottleneck is strongly tied to
background coverage. A single geometry prior for road raises full micro IoU from
`0.123` to `0.433`. Full macro IoU only reaches `0.198` because
`building`, `sidewalk`, and `vegetation` are still not predicted.

## Per-Class Result

| Class | Precision | Recall | IoU |
| --- | ---: | ---: | ---: |
| road | 0.828 | 0.811 | 0.694 |
| truck | 0.862 | 0.719 | 0.645 |
| pedestrian | 0.738 | 0.669 | 0.541 |
| traffic cone | 0.598 | 0.471 | 0.358 |
| barrier | 0.334 | 0.879 | 0.319 |
| car | 0.014 | 0.277 | 0.013 |
| bicycle | n/a | 0.000 | 0.000 |
| building | n/a | 0.000 | 0.000 |
| bus | 0.000 | 0.000 | 0.000 |
| construction vehicle | n/a | 0.000 | 0.000 |
| sidewalk | n/a | 0.000 | 0.000 |
| trailer | 0.000 | n/a | 0.000 |
| vegetation | n/a | 0.000 | 0.000 |

## Interpretation

- `road` is now a strong class: IoU `0.694`.
- The object route is unchanged by design: road filling only applies to
  previously unassigned points.
- Full micro IoU jumps because road is a large fraction of nuScenes-mini points.
- Full macro IoU remains low because macro averaging still gives equal weight to
  `building`, `sidewalk`, `vegetation`, long-tail vehicles, and the noisy
  `car/trailer` classes.

## Next Step

This result changes the priority: road can be covered cheaply with geometry, so
the next benchmark gap is dense non-road stuff:

- `building`
- `vegetation`
- `sidewalk`

The next official-like route should add a dense 2D stuff segmentation model or
VLM mask source for those classes, then fuse it with the current object route and
geometry-road prior.
