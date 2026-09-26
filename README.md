# Hardware-portfolio

RTL 설계와 검증, CDC, 타이밍 분석을 다룬 하드웨어 프로젝트 모음입니다.

## Projects

| 프로젝트 | 핵심 검증 결과 | 폴더 |
|---|---|---|
| **AXI4 Read DMA·CDC** | 랜덤 회귀 120/120 PASS · SVA fault injection 5/5 검출 · post-route WNS −2.847 → +0.113 ns | [axi_dma_cdc](axi_dma_cdc/README.md) |
| **LLM 추론 가속 NPU GEMM RTL 검증** | scheduled-MAC 검사로 4,096 MAC 누락 검출 · prefetch 후 평균 speedup 1.185× (RTL cycle 기준) | [npu_gemm_verification](npu_gemm_verification/README.md) |
| **Zynq PS–PL INT16 GEMM 통합** | CPU INT16 reference 대비 prefill·decode 예측 토큰 일치 | [zynq_ps_pl_gemm](zynq_ps_pl_gemm/README.md) |
| **3×3 분산 멀티코어 이미지 필터 RTL** | 270/270 출력 PASS · functional coverage 20/20 bins · barrier SVA fault 검출 | [multicore_rtl](multicore_rtl/README.md) |

## Verification Approach

| 확인 대상 | 방법 |
|---|---|
| 출력 값 | 독립 레퍼런스 모델 기반 scoreboard 자동 대조 |
| 시간 관계 | SVA + fault injection으로 검사기 자체의 검출 능력 확인 |
| 검증 범위 | functional coverage 정의 → 미도달 조건에 directed test 추가 |
| 설계 변경 | 동일 seed 회귀 재실행으로 변경 전후 비교 |

## Tools

SystemVerilog · SVA · cocotb · Verilator · Python · C++ · Vivado

No license is granted. All rights reserved.
