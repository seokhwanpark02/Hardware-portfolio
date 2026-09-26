# RTL Verification Portfolio


RTL 구조를 이해하고, 그에 맞는 검증환경을 직접 구축해 온 프로젝트를 모았습니다. 각 폴더는 채용 검토용 **선별 공개본**입니다. 설계 핵심 일부와 대용량 산출물은 제외하고, 검증 코드와 결과를 중심으로 공개했습니다.

## Projects

| 프로젝트 | 범위 | 핵심 검증 결과 | 폴더 |
|---|---|---|---|
| **AXI4 Read DMA·CDC 설계 및 검증** | 개인 · 2026.08 | 랜덤 회귀 120/120 PASS · SVA fault injection 5/5 검출 · post-route WNS −2.847 → +0.113 ns | [axi_dma_cdc](axi_dma_cdc/README.md) |
| **PYNQ 기반 LLM 추론 가속 NPU — GEMM RTL 검증** | 3인 졸업작품 · 2026.08 개인 재분석 | scheduled-MAC 검사로 4,096 MAC 누락 검출 · prefetch 후 평균 speedup 1.185× (RTL cycle 기준) | [npu_gemm_verification](npu_gemm_verification/README.md) · [zynq_ps_pl_gemm](zynq_ps_pl_gemm/README.md) |
| **3×3 분산 멀티코어 이미지 필터 RTL 검증** | 4인 팀 과제 · 2026.08 개인 재분석 | 270/270 출력 PASS · functional coverage 20/20 bins · barrier SVA fault 검출 | [multicore_rtl](multicore_rtl/README.md) |

## Verification Approach

| 확인 대상 | 방법 |
|---|---|
| 출력 값 | 독립 레퍼런스 모델 기반 scoreboard 자동 대조 |
| 시간 관계 | SVA + fault injection으로 검사기 자체의 검출 능력 확인 |
| 검증 범위 | functional coverage 정의 → 미도달 조건에 directed test 추가 |
| 설계 변경 | 동일 seed 회귀 재실행으로 변경 전후 비교 |

## Tools

SystemVerilog · SVA · cocotb · Verilator · Python · C++ · Vivado

## Scope and Rights

각 폴더의 `PUBLIC_RELEASE_SCOPE.md`에 공개·비공개 범위를 적었습니다. 오픈소스 라이선스를 부여하지 않으며, 기술 검토 목적으로만 공개합니다.
