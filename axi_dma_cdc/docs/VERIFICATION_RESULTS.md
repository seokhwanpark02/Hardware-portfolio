# Verification Results

## Strategy

검증은 기능, protocol, CDC, reset, stress, physical implementation을 서로 다른 evidence로 분리했습니다.

| 방법 | 확인 대상 |
|---|---|
| Independent reference model | 주소와 burst 결정의 예상값 |
| Directed cocotb tests | 정상 동작 및 명시적 corner case |
| End-to-end scoreboard | 데이터 누락·중복·순서 변경 |
| SystemVerilog Assertions | temporal/protocol invariant |
| Fault injection | assertion 자체의 검출 능력 |
| Random regression | stall, clock, FIFO, 설정 조합 |
| Post-route STA | 목표 clock에서의 물리 timing |

## Result Summary

| 검증 항목 | 결과 |
|---|---:|
| Reference-model unit tests | 11/11 PASS |
| Directed CSR/address tests | PASS |
| AXI Read normal/error tests | PASS |
| FIFO16/32 unit tests | PASS |
| AXI4-Stream reader | PASS |
| End-to-end integration | PASS |
| Random regression | 120/120 PASS |
| SVA fault injection | 5/5 detected |
| Mid-transfer reset/restart | PASS |
| Runtime-error CDC | PASS |
| 500-cycle back-pressure | PASS |
| FIFO/Burst A/B matrix | 24/24 PASS |

## Random Regression Dimensions

- Base address, row length, stride and tile height
- Configured maximum burst length
- AXI ARREADY stalls
- AXI RVALID gaps
- AXI4-Stream TREADY back-pressure
- FIFO depth 16 and 32
- MEM100/ACC100, MEM100/ACC83 and MEM100/ACC33 clock conditions
- 4 KB boundary and row-tail cases

동일 seed 집합은 timing 개선 전후에 반복하여 기능적 회귀가 없는지 비교했습니다.

## Representative Assertions

공개된 `rtl/dma_sva.sv`에는 다음 검사가 포함됩니다.

| ID | Property |
|---|---|
| A1 | ARVALID && !ARREADY 동안 AR payload 안정성 |
| A2 | TVALID && !TREADY 동안 stream data 안정성 |
| A3 | FIFO full 상태에서 write 금지 |
| A4 | FIFO empty 상태에서 read 금지 |
| A5 | 최종 data handshake 이후에만 DONE 발생 |

`tb/dma_sva_fault_top.sv`와 `tb/test_sva_fault.py`는 각 위반을 의도적으로 주입하여 assertion이 실제로 반응하는지 확인하는 대표 harness입니다.

## Evidence Scope

전체 seed별 로그와 waveform은 크기, 로컬 경로 노출 및 가독성 문제로 공개하지 않습니다. A/B 실험의 숫자 데이터는 `results/fifo_burst_ab_metrics.csv`로 제공하며, 주요 결과와 한계는 README와 timing 문서에 요약했습니다.
