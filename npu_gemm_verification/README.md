# NPU GEMM RTL Verification and Performance Analysis

PYNQ(Zynq-7020)에서 GPT-Neo 추론을 가속하는 8×8 INT16 systolic GEMM 가속기의 **RTL 검증과 성능 원인 분석** 기록입니다.
PS 측 통합과 보드 정합성 검증은 [zynq_ps_pl_gemm](../zynq_ps_pl_gemm/README.md)에 있습니다.

기반 GEMM RTL: [Buck008/Transformer-Accelerator-Based-on-FPGA](https://github.com/Buck008/Transformer-Accelerator-Based-on-FPGA) (이 저장소에는 포함하지 않음)

## Verification Environment

| 구성 | 내용 |
|---|---|
| Golden model | shift · saturation을 반영한 CPU INT16 GEMM (`golden_gemm`), RTL 출력과 원소 단위 정수 비교 |
| Stimulus | AXI4-Lite 설정 + AXI-Stream feature · weight 구동, 입력 공급률(TVALID duty) 조절 |
| Protocol checks | AXI-Stream 출력 순서, TLAST 위치, back-pressure 중 valid · data 유지 |
| Fault injection | weight 오류 주입 → scoreboard 검출 확인 → 정상 입력으로 복구 회귀 |
| Coverage | workload(QKV · OUT · FC · PROJ) × prefill/decode × 행렬 정렬 × 입력 공급률 bin, 미도달 조건은 directed test로 채움 |
| Metrics monitor | PE 활동, 구간(입력 적재 · weight 적재 · feature 공급 · drain · 제어 대기)별 cycle 계측 |

## Findings

### 1. 낮은 PE 이용률의 원인 분리

QKV (M=4 → 8 padding, K=64, N=192) 기준:

| 입력 공급률 | 총 cycle | compute 구간 PE 이용률 |
|---:|---:|---:|
| 100% | 10,190 | 18.62% |
| 80% | 10,573 | 18.62% |
| 60% | 11,212 | 18.62% |
| 40% | 12,491 | 18.62% |

- 공급률을 낮추면 입력 적재 cycle이 늘어 **총 cycle은 증가**하지만, compute 구간 이용률은 그대로였습니다.
- 구간별 계측에서 feature 공급 구간 4,984 cycle 중 실제 issue는 1,536 cycle, 대기가 3,448 cycle이었습니다. micro-tile 192개 기준 tile당 약 18 cycle입니다.
- 원인: 현재 tile의 출력 pipeline(약 2 × array 크기)이 모두 빠진 뒤에야 다음 weight를 적재하는 **직렬화**.

### 2. Next-weight prefetch와 검출된 결함

- 수정: pipeline drain 동안 다음 weight tile을 로컬 버퍼에 미리 받고, 이전 activation이 모두 빠진 뒤에만 PE weight를 교체(commit).
- **첫 구현에서 scheduled-MAC 검사가 98,304 중 4,096 MAC 누락을 검출**했습니다. 누락량은 K-block 8개 각각의 마지막 micro-tile 1개(8 feature issue)와 정확히 일치했습니다.
- 원인: 마지막 weight를 prefetch하는 순간 weight 종료 신호가 먼저 올라가, 마지막 tile 계산 전에 전체 완료로 판정됨.
- 수정: 완료 판정에 "feature 공급 상태" 조건을 추가한 뒤 연산량 · scoreboard · 프로토콜 회귀 전체 재통과.

### 3. 수정 전후 비교 (RTL 시뮬레이션, 모든 case scoreboard PASS)

| Kernel | Baseline cycles | Prefetch cycles | Speedup |
|---|---:|---:|---:|
| QKV | 10,190 | 8,534 | 1.194× |
| OUT | 3,406 | 2,902 | 1.174× |
| FC | 13,582 | 11,350 | 1.197× |
| PROJ | 13,414 | 11,398 | 1.177× |

- 평균 speedup 1.185×, QKV compute 구간 PE 이용률 18.62% → 23.30%
- 자원: DSP 69, BRAM 33.5 유지 (LUT · FF 차이는 ±4 수준)
- 타이밍 (Vivado OOC): 100 MHz에서 WNS +0.493 ns. 최고 timing-closed 제약은 9.0 ns → 9.1 ns로 소폭 악화

### 4. 배열 크기 판단

16×16 direct scaling도 합성해 비교했습니다. 합성은 되지만 DSP 220/220(100%), LUT 약 5.1배, decode(M=1) 유효 행 비율 12.5% → 6.25%로 기각하고, 8×8의 활용도를 높이는 방향을 택했습니다.

## Published Files

| 파일 | 내용 |
|---|---|
| `tb/test_mm_ultra.py` | golden model, AXI 드라이버, 출력 수집 · 프로토콜 검사, fault injection 옵션 |
| `tb/s5_utilization.py` | PE 활동 · 구간별 cycle monitor |
| `tb/s6_supply.py` | 입력 공급률 sweep |
| `tb/Makefile.verify` | cocotb · Verilator 실행 설정 (RTL은 기반 저장소에서 별도 준비 필요) |
| `results/s5_metrics.csv` | kernel별 이용률 · 구간별 cycle |
| `results/s6_supply_sweep.csv` | 공급률 sweep 결과 |
| `results/s9_prefetch_ab.csv` | prefetch 전후 비교 |

## Limitations

- 성능 수치는 RTL 시뮬레이션의 transaction cycle 기준이며, prefetch 수정본은 보드에서 다시 측정하지 않았습니다.
- 실제 DDR 대역폭 · contention은 측정하지 않았습니다.
- 공급률 실험은 testbench에서 TVALID duty를 조절한 것으로, 실제 메모리 대역폭 측정이 아닙니다.

No license is granted. All rights reserved.
