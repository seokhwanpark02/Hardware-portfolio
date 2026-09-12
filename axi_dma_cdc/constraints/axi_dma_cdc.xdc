# clk_mem: AXI Read Master + Async FIFO write
# Target: 100 MHz
create_clock \
    -name clk_mem \
    -period 10.000 \
    -waveform {0.000 5.000} \
    [get_ports clk_mem]

# clk_acc: AXI4-Lite + Async FIFO read + AXI4-Stream
# Target: approximately 83 MHz
create_clock \
    -name clk_acc \
    -period 12.048 \
    -waveform {0.000 6.024} \
    [get_ports clk_acc]

# clk_mem and clk_acc have no fixed phase relationship.
set_clock_groups \
    -asynchronous \
    -group [get_clocks clk_mem] \
    -group [get_clocks clk_acc]