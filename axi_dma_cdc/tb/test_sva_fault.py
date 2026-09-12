import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import (
    ClockCycles,
    FallingEdge,
    RisingEdge,
    Timer,
)


async def initialize(dut):
    dut.rst_mem_n.value = 0
    dut.rst_acc_n.value = 0

    dut.m_axi_araddr.value = 0
    dut.m_axi_arlen.value = 0
    dut.m_axi_arsize.value = 2
    dut.m_axi_arburst.value = 1
    dut.m_axi_arvalid.value = 0
    dut.m_axi_arready.value = 0

    dut.m_axis_tdata.value = 0
    dut.m_axis_tvalid.value = 0
    dut.m_axis_tready.value = 0

    dut.fifo_full.value = 0
    dut.fifo_wr_en.value = 0

    dut.fifo_empty.value = 1
    dut.fifo_rd_en.value = 0

    dut.final_handshake.value = 0
    dut.done.value = 0

    await ClockCycles(dut.clk_mem, 3)
    await ClockCycles(dut.clk_acc, 3)

    dut.rst_mem_n.value = 1
    dut.rst_acc_n.value = 1

    await ClockCycles(dut.clk_mem, 3)
    await ClockCycles(dut.clk_acc, 3)


@cocotb.test()
async def inject_sva_fault(dut):
    fault_id = os.environ.get(
        "FAULT_ID",
        "A1",
    )

    cocotb.start_soon(
        Clock(
            dut.clk_mem,
            12,
            unit="ns",
        ).start()
    )

    cocotb.start_soon(
        Clock(
            dut.clk_acc,
            10,
            unit="ns",
        ).start()
    )

    await initialize(dut)

    if fault_id == "A1":
        # ARVALID stall 중 ARADDR 변경
        await FallingEdge(dut.clk_mem)

        dut.m_axi_arvalid.value = 1
        dut.m_axi_arready.value = 0
        dut.m_axi_araddr.value = 0x1000
        dut.m_axi_arlen.value = 7

        await RisingEdge(dut.clk_mem)
        await FallingEdge(dut.clk_mem)

        dut.m_axi_araddr.value = 0x2000

        await RisingEdge(dut.clk_mem)

    elif fault_id == "A2":
        # TVALID stall 중 TDATA 변경
        await FallingEdge(dut.clk_acc)

        dut.m_axis_tvalid.value = 1
        dut.m_axis_tready.value = 0
        dut.m_axis_tdata.value = 0x1111_2222

        await RisingEdge(dut.clk_acc)
        await FallingEdge(dut.clk_acc)

        dut.m_axis_tdata.value = 0x3333_4444

        await RisingEdge(dut.clk_acc)

    elif fault_id == "A3":
        # FIFO full 상태에서 write
        await FallingEdge(dut.clk_mem)

        dut.fifo_full.value = 1
        dut.fifo_wr_en.value = 1

        await RisingEdge(dut.clk_mem)

    elif fault_id == "A4":
        # FIFO empty 상태에서 read
        await FallingEdge(dut.clk_acc)

        dut.fifo_empty.value = 1
        dut.fifo_rd_en.value = 1

        await RisingEdge(dut.clk_acc)

    elif fault_id == "A5":
        # Final handshake 없이 DONE 상승
        await FallingEdge(dut.clk_acc)

        dut.final_handshake.value = 0
        dut.done.value = 1

        await RisingEdge(dut.clk_acc)

    else:
        raise ValueError(
            f"Unknown FAULT_ID={fault_id}"
        )

    # 여기까지 도달하면 checker가 오류를 놓친 것이다.
    await Timer(50, unit="ns")

    raise AssertionError(
        "Injected violation was not detected"
    )
