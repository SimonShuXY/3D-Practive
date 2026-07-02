# Official-Like Superpoint Experiment

This note records the first step away from point-wise projection toward an
OV-SAM3D-like pipeline. The change is intentionally small: keep the same
OWL-only + SAM masks, then add a 3D superpoint overlap-voting stage after point
projection.

## Setup

- Dataset: `nuScenes-mini` with lidarseg mini labels.
- Samples: `0-4`.
- Base route: `OWL-ViT label -> SAM mask -> person/pedestrian merge -> point projection`.
- New route: base route plus voxel superpoints and label voting.
- Remote output:
  - `outputs/ovsam3d_official_like_superpoint_owl_nuscenes_mini`
  - `outputs/ovsam3d_official_like_superpoint_report`

Default superpoint settings:

```text
voxel_size = 0.75 m
min_points = 4
min_purity = 0.55
min_score = 0.02
```

## Result

| Stage | Object assigned acc | Object micro IoU | Object macro IoU | Frequent-object assigned acc | Frequent-object micro IoU | Frequent-object macro IoU |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SAM point labels | 0.464 | 0.385 | 0.194 | 0.506 | 0.413 | 0.350 |
| Superpoint voting | 0.464 | 0.400 | 0.208 | 0.512 | 0.436 | 0.375 |

The official-like post-process improves the object-only diagnostic, but only
modestly. It increases object micro IoU from `0.385` to `0.400`, and
frequent-object macro IoU from `0.350` to `0.375`.

## Per-Class Reading

Best superpoint run:

| Class | Precision | Recall | IoU |
| --- | ---: | ---: | ---: |
| truck | 0.862 | 0.719 | 0.645 |
| pedestrian | 0.738 | 0.669 | 0.541 |
| traffic cone | 0.598 | 0.471 | 0.358 |
| barrier | 0.334 | 0.879 | 0.319 |
| car | 0.014 | 0.277 | 0.013 |
| bicycle | n/a | 0.000 | 0.000 |
| bus | 0.000 | 0.000 | 0.000 |
| construction vehicle | n/a | 0.000 | 0.000 |
| trailer | 0.000 | n/a | 0.000 |

Superpoint voting helps `truck` and `pedestrian` clearly, but it does not solve
the biggest remaining failure: `car` and `trailer` are still noisy. That means
the bottleneck is not just point-level fragmentation; it is also proposal/label
quality from OWL-ViT and the lack of a stronger 3D grouping prior.

## Threshold Ablation

The remote run also evaluated a small offline threshold sweep using the saved
SAM point-label PLY files, without rerunning OWL/SAM/CLIP.

Best frequent-object macro IoU:

```text
voxel=0.75, min_points=4, purity=0.55
frequent-object macro IoU = 0.375
frequent-object micro IoU = 0.436
```

Best object micro IoU:

```text
voxel=0.75, min_points=12, purity=0.55
object micro IoU = 0.426
frequent-object micro IoU = 0.460
frequent-object assigned acc = 0.610
```

The stricter `min_points=12` setting is more precision-oriented, but it lowers
coverage and macro IoU. This is useful as an ablation, not yet the default.

## Conclusion

The official-like direction is helpful but not sufficient. Superpoint overlap
voting confirms that 3D grouping can improve the object-mask route, but the gain
is too small to close the gap to SOTA. The next meaningful step is to replace
simple voxel superpoints with stronger 3D segments and label assignment:

- geometry-aware superpoints or connected components instead of fixed voxels,
- multi-view overlap score tables instead of single-label point overwrite,
- RAM/dense open-vocabulary tags instead of CLIP crop retagging,
- explicit confusion handling for `car` and `trailer`.
