# Timing and Design Trade-offs

## Decision Criteria

최종안은 기능 simulation 결과만으로 선정하지 않았습니다. 다음 조건을 함께 적용했습니다.

1. Directed, random, CDC, reset 및 stress 검증 통과
2. 100 MHz memory clock의 post-route setup/hold 만족
3. FIFO depth와 burst limit의 성능 효과 분리
4. Resource와 power estimate 확인
5. 변경 후 동일 regression 반복

## Critical-path Improvement

초기 FIFO16 구현은 100 MHz에서 timing을 만족하지 못했습니다.

| Metric | Before | After |
|---|---:|---:|
| WNS | -2.847 ns | +0.113 ns |
| TNS | -411.156 ns | 0.000 ns |
| Setup failing endpoints | 243 | 0 |
| LUTs | 533 | 566 |
| FFs | 889 | 894 |

Burst planning과 요청 수락·상태 갱신 사이의 조합 경로를 분석한 뒤 request metadata에 pipeline boundary를 추가했습니다. 이 변경으로 WNS는 2.960 ns 개선되었고 LUT 33개와 FF 5개가 증가했습니다.

변경 전후 동일 seed와 A/B workload를 다시 실행했으며 측정된 cycle-level A/B 결과는 동일했습니다.

구체적인 address/burst-planning RTL과 내부 signal-level critical-path 구현은 이 저장소에 포함하지 않았습니다.

## FIFO16 versus FIFO32

| Metric | FIFO16 | FIFO32 |
|---|---:|---:|
| WNS | +0.113 ns | -1.253 ns |
| TNS | 0.000 ns | -5.361 ns |
| Setup failing endpoints | 0 | 5 |
| Total LUTs | 566 | 569 |
| FFs | 894 | 902 |
| LUTRAMs | 24 | 24 |
| Power estimate | 0.112 W | 0.112 W |

Power는 workload switching activity가 반영되지 않은 vectorless estimate이므로 보조 지표로만 사용했습니다.

## Performance Interpretation

FIFO32는 MAX_BURST16의 balanced-clock 조건에서 FIFO16 대비 다음 throughput 변화를 보였습니다.

| Condition | FIFO32 change |
|---|---:|
| MEM100/ACC100 steady | +9.62% |
| MEM100/ACC100 pressure | +18.90% |
| MEM100/ACC83 steady | +9.48% |
| MEM100/ACC83 pressure | +12.53% |
| MEM100/ACC33 | 0.00% |

Consumer가 지속 병목인 MEM100/ACC33에서는 깊은 FIFO가 transaction fragmentation을 줄여도 전체 throughput을 높이지 못했습니다.

## Final Selection

최종 구성은 FIFO_DEPTH=16, MAX_BURST=16입니다.

FIFO32는 일부 조건에서 simulation 성능이 높았지만 현재 구조에서 필수 100 MHz timing을 만족하지 못했습니다. FIFO16은 기능 검증과 post-route timing을 모두 통과했으므로 최종안으로 선정했습니다.

FIFO16의 +0.113 ns는 지정한 100 MHz 목표 통과를 의미합니다. 큰 timing margin이나 검증되지 않은 더 높은 Fmax를 주장하지 않습니다.
