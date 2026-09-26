import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import (
    ClockCycles,
    FallingEdge,
    RisingEdge,
    Timer,
    with_timeout,
)

from model.reference_model import (
    Config,
    expected_addresses,
    expected_data,
    memory_word,
)


def value(signal):
    return int(signal.value)


async def initialize(dut):
    dut.arst_n.value = 0

    dut.s_axi_awaddr.value = 0
    dut.s_axi_awvalid.value = 0

    dut.s_axi_wdata.value = 0
    dut.s_axi_wstrb.value = 0
    dut.s_axi_wvalid.value = 0

    dut.s_axi_bready.value = 0

    dut.s_axi_araddr.value = 0
    dut.s_axi_arvalid.value = 0
    dut.s_axi_rready.value = 0

    dut.m_axi_arready.value = 0

    dut.m_axi_rdata.value = 0
    dut.m_axi_rresp.value = 0
    dut.m_axi_rlast.value = 0
    dut.m_axi_rvalid.value = 0

    dut.m_axis_tready.value = 0

    await ClockCycles(dut.clk_acc, 5)
    await ClockCycles(dut.clk_mem, 5)

    dut.arst_n.value = 1

    await ClockCycles(dut.clk_acc, 6)
    await ClockCycles(dut.clk_mem, 6)

    assert value(dut.busy_o) == 0
    assert value(dut.done_o) == 0
    assert value(dut.error_o) == 0


async def axi_lite_write(
    dut,
    address,
    data,
):
    await FallingEdge(dut.clk_acc)

    dut.s_axi_awaddr.value = address
    dut.s_axi_awvalid.value = 1

    dut.s_axi_wdata.value = data
    dut.s_axi_wstrb.value = 0xF
    dut.s_axi_wvalid.value = 1

    dut.s_axi_bready.value = 1

    response_seen = False

    for _ in range(30):
        await RisingEdge(dut.clk_acc)
        await Timer(1, unit="ns")

        if value(dut.s_axi_bvalid):
            assert value(dut.s_axi_bresp) == 0
            response_seen = True
            break

    assert response_seen, (
        f"AXI-Lite write timeout: "
        f"address=0x{address:08X}"
    )

    await FallingEdge(dut.clk_acc)

    dut.s_axi_awvalid.value = 0
    dut.s_axi_wvalid.value = 0

    for _ in range(10):
        await RisingEdge(dut.clk_acc)
        await Timer(1, unit="ns")

        if not value(dut.s_axi_bvalid):
            break
    else:
        raise AssertionError(
            "AXI-Lite BVALID did not clear"
        )

    dut.s_axi_bready.value = 0


async def accept_ar(
    dut,
    transaction_index,
    config,
):
    dut.m_axi_arready.value = 0

    while True:
        await FallingEdge(dut.clk_mem)

        if value(dut.m_axi_arvalid):
            break

    address = value(dut.m_axi_araddr)
    beats = value(dut.m_axi_arlen) + 1

    arsize = value(dut.m_axi_arsize)
    arburst = value(dut.m_axi_arburst)

    assert arsize == 2
    assert arburst == 1
    assert 1 <= beats <= config.max_burst

    assert (
        (address & 0xFFF)
        + beats * 4
        <= 4096
    ), (
        f"4KB violation: "
        f"addr=0x{address:08X}, beats={beats}"
    )

    held_address = address
    held_arlen = value(dut.m_axi_arlen)

    # ARVALID stall과 payload stability를 함께 확인한다.
    stall_cycles = (
        transaction_index % 3
    ) + 1

    for _ in range(stall_cycles):
        assert value(dut.m_axi_arvalid) == 1
        assert value(dut.m_axi_araddr) == held_address
        assert value(dut.m_axi_arlen) == held_arlen

        await RisingEdge(dut.clk_mem)
        await FallingEdge(dut.clk_mem)

    assert value(dut.m_axi_arvalid) == 1
    assert value(dut.m_axi_araddr) == held_address
    assert value(dut.m_axi_arlen) == held_arlen

    dut.m_axi_arready.value = 1

    await Timer(1, unit="ns")
    await RisingEdge(dut.clk_mem)
    await Timer(1, unit="ns")

    dut.m_axi_arready.value = 0

    return address, beats


async def send_r_beat(
    dut,
    data,
    last,
):
    await FallingEdge(dut.clk_mem)

    dut.m_axi_rdata.value = data
    dut.m_axi_rresp.value = 0
    dut.m_axi_rlast.value = int(last)
    dut.m_axi_rvalid.value = 1

    held_data = data
    held_last = int(last)

    for _ in range(500):
        await Timer(1, unit="ns")

        ready_before_edge = value(
            dut.m_axi_rready
        )

        assert value(dut.m_axi_rdata) == held_data
        assert value(dut.m_axi_rlast) == held_last

        await RisingEdge(dut.clk_mem)

        if ready_before_edge:
            await Timer(1, unit="ns")
            dut.m_axi_rvalid.value = 0
            dut.m_axi_rlast.value = 0
            return

        await FallingEdge(dut.clk_mem)

    raise AssertionError(
        "AXI R channel timeout"
    )


async def memory_model(
    dut,
    config,
    total_beats,
    ar_records,
    observed_addresses,
):
    transaction_index = 0

    while len(observed_addresses) < total_beats:
        address, beats = await accept_ar(
            dut,
            transaction_index,
            config,
        )

        ar_records.append(
            {
                "addr": address,
                "beats": beats,
            }
        )

        for beat_index in range(beats):
            beat_address = (
                address + beat_index * 4
            )

            # RVALID gap 삽입
            gap_cycles = (
                transaction_index
                + beat_index
            ) % 3

            dut.m_axi_rvalid.value = 0

            if gap_cycles:
                await ClockCycles(
                    dut.clk_mem,
                    gap_cycles,
                )

            await send_r_beat(
                dut,
                memory_word(beat_address),
                beat_index == beats - 1,
            )

            observed_addresses.append(
                beat_address
            )

        transaction_index += 1

    dut.m_axi_rvalid.value = 0
    dut.m_axi_rlast.value = 0


async def axis_consumer(
    dut,
    expected_words,
    observed_words,
    statistics,
    initial_stall_cycles,
):
    # START가 받아들여질 때까지 기다린다.
    for _ in range(100):
        await RisingEdge(dut.clk_acc)
        await Timer(1, unit="ns")

        if value(dut.busy_o):
            break
    else:
        raise AssertionError(
            "BUSY did not assert"
        )

    assert value(dut.done_o) == 0
    assert value(dut.error_o) == 0

    # FIFO16/32 모두 실제 full을 경험하도록
    # downstream을 먼저 정지시킨다.
    dut.m_axis_tready.value = 0

    for _ in range(initial_stall_cycles):
        await RisingEdge(dut.clk_acc)
        await Timer(1, unit="ns")

        if value(dut.fifo_full_o):
            statistics["fifo_full_seen"] = True

        assert value(dut.done_o) == 0
        assert value(dut.busy_o) == 1

    assert statistics["fifo_full_seen"], (
        "FIFO full was not exercised"
    )

    cycle_index = 0

    while len(observed_words) < len(expected_words):
        await FallingEdge(dut.clk_acc)

        # 마지막 AXIS 데이터는 별도로 길게 stall한다.
        if (
            len(observed_words)
            == len(expected_words) - 1
            and value(dut.m_axis_tvalid)
        ):
            final_data = value(
                dut.m_axis_tdata
            )

            assert final_data == expected_words[-1]

            dut.m_axis_tready.value = 0

            for _ in range(20):
                await Timer(1, unit="ns")

                assert value(dut.m_axis_tvalid) == 1
                assert value(dut.m_axis_tdata) == final_data
                assert value(dut.done_o) == 0
                assert value(dut.busy_o) == 1

                await RisingEdge(dut.clk_acc)
                await FallingEdge(dut.clk_acc)

            # 마지막 consumer handshake
            dut.m_axis_tready.value = 1

            await Timer(1, unit="ns")

            assert value(dut.m_axis_tvalid) == 1
            assert value(dut.m_axis_tdata) == final_data
            assert value(dut.done_o) == 0
            assert value(dut.busy_o) == 1

            await RisingEdge(dut.clk_acc)
            await Timer(1, unit="ns")

            observed_words.append(final_data)

            assert value(dut.done_o) == 1
            assert value(dut.busy_o) == 0
            assert value(dut.error_o) == 0

            dut.m_axis_tready.value = 0
            return

        # 일반 데이터에는 주기적 back-pressure를 준다.
        ready = (
            cycle_index % 5
        ) not in (0, 1)

        dut.m_axis_tready.value = int(ready)

        await Timer(1, unit="ns")

        valid = value(dut.m_axis_tvalid)
        data = value(dut.m_axis_tdata)

        await RisingEdge(dut.clk_acc)

        if valid and ready:
            observed_words.append(data)

        cycle_index += 1

        assert cycle_index < 10000, (
            "AXI4-Stream consumer timeout"
        )


@cocotb.test()
async def test_s5_e2e(dut):
    fifo_depth = int(
        os.environ.get("FIFO_DEPTH", "16")
    )
    clk_acc_ns = float(
        os.environ.get("CLK_ACC_NS", "10")
    )

    clk_mem_ns = float(
        os.environ.get("CLK_MEM_NS", "12")
    )

    initial_stall_cycles = int(
        os.environ.get(
            "INITIAL_STALL_CYCLES",
            "160",
        )
    )
    cocotb.start_soon(
        Clock(
            dut.clk_acc,
            clk_acc_ns,
            unit="ns",
        ).start()
    )

    cocotb.start_soon(
        Clock(
            dut.clk_mem,
            clk_mem_ns,
            unit="ns",
        ).start()
    )

    await initialize(dut)

    config = Config(
        base_addr=0x0000_0FF0,
        length_bytes=80,
        stride_bytes=128,
        tile_h=3,
        max_burst=16,
    )

    reference_addresses = expected_addresses(
        config
    )

    reference_words = expected_data(
        config
    )

    assert len(reference_addresses) == 60
    assert len(reference_words) == 60

    # Programming CSR
    await axi_lite_write(
        dut,
        0x08,
        config.base_addr,
    )

    await axi_lite_write(
        dut,
        0x0C,
        config.length_bytes,
    )

    await axi_lite_write(
        dut,
        0x10,
        config.stride_bytes,
    )

    await axi_lite_write(
        dut,
        0x14,
        config.tile_h,
    )

    await axi_lite_write(
        dut,
        0x18,
        config.max_burst,
    )

    ar_records = []
    observed_addresses = []
    observed_words = []

    statistics = {
        "fifo_full_seen": False,
    }

    memory_task = cocotb.start_soon(
        memory_model(
            dut,
            config,
            len(reference_addresses),
            ar_records,
            observed_addresses,
        )
    )

    consumer_task = cocotb.start_soon(
        axis_consumer(
            dut,
            reference_words,
            observed_words,
            statistics,
            initial_stall_cycles,
        )
    )

    # CONTROL.START
    await axi_lite_write(
        dut,
        0x00,
        0x0000_0001,
    )

    await with_timeout(
        memory_task,
        200,
        "us",
    )

    await with_timeout(
        consumer_task,
        200,
        "us",
    )

    assert observed_addresses == reference_addresses, (
        "AXI read address coverage mismatch"
    )

    assert observed_words == reference_words, (
        "AXI4-Stream data scoreboard mismatch"
    )

    assert value(dut.done_o) == 1
    assert value(dut.busy_o) == 0
    assert value(dut.error_o) == 0
    assert value(dut.fifo_empty_o) == 1

    # DONE sticky 확인
    await ClockCycles(dut.clk_acc, 5)

    assert value(dut.done_o) == 1
    dut._log.info(
        f"Clock acc={clk_acc_ns}ns, "
        f"mem={clk_mem_ns}ns, "
        f"initial_stall="
        f"{initial_stall_cycles} cycles"
    )
    dut._log.info(
        f"FIFO_DEPTH={fifo_depth}: "
        f"{len(observed_words)} data beats, "
        f"{len(ar_records)} AR transactions PASS"
    )

    dut._log.info(
        "AXI-Lite -> CDC -> AXI Read -> "
        "Async FIFO -> AXIS -> DONE: ALL PASS"
    )
