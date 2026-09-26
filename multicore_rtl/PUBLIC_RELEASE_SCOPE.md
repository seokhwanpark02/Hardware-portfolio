# Repository Contents

## Included

- `system_top.sv`: 3×3 topology
- Core 1 coordinator/barrier RTL and SVA
- Core 5 representative worker RTL
- Interfaces directly connected to the two cores
- C++ driver, monitor, scoreboard and functional coverage
- 30 verification vectors

## Not Included

- Core 2–4 and Core 6–9 internal RTL
- Full point-to-point interface network and remaining instruction programs
- Analysis automation scripts
- Vivado projects, build outputs, waveforms and executables

`system_top.sv`는 전체 구조를 보여 주기 위해 포함했으며, 이 저장소만으로는 빌드되지 않습니다.

No license is granted. All rights reserved.
