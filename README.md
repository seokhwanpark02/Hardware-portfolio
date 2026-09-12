# fpga-hw-integration-portfolio

RTL design, verification, CDC, and timing analysis portfolio



\## Projects



\### 1. AXI4 DMA + CDC Data Transfer Engine



AXI4-Lite, AXI4 Read, AXI4-Stream 기반 DMA와 Clock Domain Crossing 구조를 설계하고 검증했습니다.



\[프로젝트 README 보기](axi\_dma\_cdc/README.md)



\### 2. 3×3 Multicore RTL



9개의 8-bit processor를 3×3으로 연결하고, barrier synchronization과 scoreboard/SVA 기반 검증을 수행했습니다.



\[프로젝트 README 보기](multicore\_rtl/README.md)



\### 3. Zynq PS–PL INT16 GEMM Integration



Zynq PS에서 PL GEMM accelerator를 제어하고, CPU quantized reference와 결과를 비교하는 PS-side 검증 구조를 정리했습니다.



\[프로젝트 README 보기](zynq\_ps\_pl\_gemm/README.md)



\## Focus Areas



\- RTL architecture

\- Interface and DMA integration

\- Clock/reset and synchronization

\- Self-checking verification

\- Timing and design trade-off analysis

\- Zynq PS–PL hardware integration

