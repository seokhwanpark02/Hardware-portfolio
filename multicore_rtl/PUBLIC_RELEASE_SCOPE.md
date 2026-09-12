# Public Release Scope

이 폴더는 `9core_recovery`에서 선별한 채용 검토용 코드 샘플입니다.

## Included

- 3x3 topology를 확인할 수 있는 `system_top.sv`
- Core 1 coordinator/barrier RTL과 SVA
- 중앙 Core 5 representative worker RTL
- 위 두 코어에 직접 연결되는 interface 정의
- C++ driver, monitor, scoreboard, functional coverage
- 30개 verification vector

## Intentionally Withheld

- Core 2-4 및 Core 6-9의 내부 RTL
- 전체 point-to-point interface network
- 나머지 코어별 instruction program
- Vivado project, generated runs, checkpoint, bitstream
- Verilator build output, waveform, cache, executable
- 개인 경로 및 개발 환경 설정
- 타인이 작성했거나 공개 권한이 불명확한 자료

`system_top.sv`는 전체 구조를 설명하기 위해 포함했지만, 비공개 모듈이 있으므로 이 공개 샘플만으로 전체 시스템을 빌드할 수는 없습니다.

## Rights

오픈소스 라이선스를 부여하지 않습니다. 별도 허가 없이 재배포하거나 상업적으로 사용할 수 없습니다.
