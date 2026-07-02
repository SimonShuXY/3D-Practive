# Object-Only SAM Diagnostic Report

This report intentionally removes stuff/background classes from the main reading. It is a diagnostic for the current object-mask route, not a full-scene semantic segmentation benchmark. When present, `superpoint` is an official-like 3D overlap-voting post-process over SAM point labels. `road_fused` also adds a geometry road prior, so its object rows should be read together with full/stuff metrics.

## Object Groups

| Run | Label mode | Stage | Group | Assigned acc | Micro R | Micro IoU | Macro IoU | Classes | Class list |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| baseline | unknown | sam | object | 0.269 | 0.368 | 0.184 | 0.125 | 10 | barrier, bicycle, bus, car, construction vehicle, motorcycle, pedestrian, traffic cone, trailer, truck |
| baseline | unknown | sam | frequent_object | 0.331 | 0.369 | 0.211 | 0.250 | 5 | barrier, car, pedestrian, traffic cone, truck |
| hybrid | hybrid | sam | object | 0.269 | 0.368 | 0.184 | 0.125 | 10 | barrier, bicycle, bus, car, construction vehicle, motorcycle, pedestrian, traffic cone, trailer, truck |
| hybrid | hybrid | sam | frequent_object | 0.331 | 0.369 | 0.211 | 0.250 | 5 | barrier, car, pedestrian, traffic cone, truck |
| owl | owl | sam | object | 0.464 | 0.692 | 0.385 | 0.194 | 9 | barrier, bicycle, bus, car, construction vehicle, pedestrian, traffic cone, trailer, truck |
| owl | owl | sam | frequent_object | 0.506 | 0.694 | 0.413 | 0.350 | 5 | barrier, car, pedestrian, traffic cone, truck |
| clip | clip | sam | object | 0.262 | 0.359 | 0.179 | 0.124 | 10 | barrier, bicycle, bus, car, construction vehicle, motorcycle, pedestrian, traffic cone, trailer, truck |
| clip | clip | sam | frequent_object | 0.325 | 0.360 | 0.206 | 0.248 | 5 | barrier, car, pedestrian, traffic cone, truck |
| hybrid_clip030 | hybrid | sam | object | 0.271 | 0.371 | 0.186 | 0.141 | 9 | barrier, bicycle, bus, car, construction vehicle, pedestrian, traffic cone, trailer, truck |
| hybrid_clip030 | hybrid | sam | frequent_object | 0.372 | 0.372 | 0.228 | 0.255 | 5 | barrier, car, pedestrian, traffic cone, truck |
| hybrid_clip045 | hybrid | sam | object | 0.297 | 0.406 | 0.207 | 0.178 | 9 | barrier, bicycle, bus, car, construction vehicle, pedestrian, traffic cone, trailer, truck |
| hybrid_clip045 | hybrid | sam | frequent_object | 0.407 | 0.407 | 0.256 | 0.320 | 5 | barrier, car, pedestrian, traffic cone, truck |
| hybrid_clip060 | hybrid | sam | object | 0.356 | 0.531 | 0.271 | 0.142 | 9 | barrier, bicycle, bus, car, construction vehicle, pedestrian, traffic cone, trailer, truck |
| hybrid_clip060 | hybrid | sam | frequent_object | 0.421 | 0.533 | 0.307 | 0.255 | 5 | barrier, car, pedestrian, traffic cone, truck |

## Best Object-Only Route

- Best object-only run: `ovsam3d_ablation_owl_merge_person_nuscenes_mini`.
- Best object-only stage: `sam`.
- Object assigned accuracy: `0.464`.
- Object micro IoU: `0.385`.
- Object macro IoU: `0.194`.

## Frequent-Object Reading

`frequent_object` keeps object classes with enough ground-truth support in this mini split. It is useful for checking whether the object-mask chain works before long-tail classes dominate the macro average.

- Best frequent-object run: `ovsam3d_ablation_owl_merge_person_nuscenes_mini`.
- Best frequent-object stage: `sam`.
- Frequent-object assigned accuracy: `0.506`.
- Frequent-object micro IoU: `0.413`.
- Frequent-object macro IoU: `0.350`.
- Frequent-object classes: `barrier, car, pedestrian, traffic cone, truck`.

## Best Run Per-Object Classes

| Class | TP | Pred | GT | Precision | Recall | IoU |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| truck | 10471 | 12801 | 16239 | 0.818 | 0.645 | 0.564 |
| pedestrian | 780 | 1130 | 1558 | 0.690 | 0.501 | 0.409 |
| barrier | 4629 | 11778 | 5072 | 0.393 | 0.913 | 0.379 |
| traffic cone | 57 | 109 | 104 | 0.523 | 0.548 | 0.365 |
| car | 189 | 6065 | 271 | 0.031 | 0.697 | 0.031 |
| bicycle | 0 | 8 | 10 | 0.000 | 0.000 | 0.000 |
| bus | 0 | 53 | 8 | 0.000 | 0.000 | 0.000 |
| construction vehicle | 0 | 0 | 32 | n/a | 0.000 | 0.000 |
| trailer | 0 | 2782 | 0 | 0.000 | n/a | 0.000 |

## Reading Rule

- Use `object` to evaluate the object-mask route without background classes.
- Use `frequent_object` to inspect classes with enough support in the current mini split.
- Keep `full` and `stuff` metrics visible elsewhere so the report does not claim full-scene segmentation.
