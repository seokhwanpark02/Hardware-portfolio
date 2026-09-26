import os
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import (
    ClockCycles,
    FallingEdge,
    RisingEdge,
    Timer,
    with_timeout,
)

import test_s5_e2e as e2e

from model.reference_model import (
    Config,
    expected_addresses,
    expected_data,
    memory_word,
)


def value(signal):
    return int(signal.value)


def make_random_config(rng):
    page_base = (
        rng.randint(1, 31) * 0x1000
    )

    if rng.random() < 0.35:
        page_offset = rng.choice(
            (
                0xFC0,
                0xFD0,
                0xFE0,
                0xFF0,
            )
        )
    else:
        page_offset = (
            rng.randint(0, 1023) * 4
        )

    length_beats = rng.randint(1, 48)
    stride_beats = rng.randint(0, 64)

    return Config(
        base_addr=page_base + page_offset,
        length_bytes=length_beats * 4,
        stride_bytes=stride_beats * 4,
        tile_h=rng.randint(1, 4),
        max_burst=rng.randint(1, 16),
    )


async def program_config(dut, config):
    register_values = (
        (0x08, config.base_addr),
        (0x0C, config.length_bytes),
        (0x10, config.stride_bytes),
        (0x14, config.tile_h),
        (0x18, config.max_burst),
    )

    for address, data in register_values:
        await e2e.axi_lite_write(
            dut,
            address,
            data,
        )


async def accept_random_ar(
    dut,
    config,
    rng,
):
    dut.m_axi_arready.value = 0

    while True:
        await FallingEdge(dut.clk_mem)

        if value(dut.m_axi_arvalid):
            break

    address = value(dut.m_axi_araddr)
    arlen = value(dut.m_axi_arlen)
    beats = arlen + 1

    assert value(dut.m_axi_arsize) == 2
    assert value(dut.m_axi_arburst) == 1
    assert 1 <= beats <= config.max_burst

    assert (
        (address & 0xFFF)
        + beats * 4
        <= 4096
    )

    stall_cycles = rng.randint(0, 5)

    for _ in range(stall_cycles):
        assert value(dut.m_axi_arvalid) == 1
        assert value(dut.m_axi_araddr) == address
        assert value(dut.m_axi_arlen) == arlen

        await RisingEdge(dut.clk_mem)
        await FallingEdge(dut.clk_mem)

    assert value(dut.m_axi_arvalid) == 1
    assert value(dut.m_axi_araddr) == address
    assert value(dut.m_axi_arlen) == arlen

    dut.m_axi_arready.value = 1

    await Timer(1, unit="ns")
    await RisingEdge(dut.clk_mem)
    await Timer(1, unit="ns")

    dut.m_axi_arready.value = 0

    return address, beats, stall_cycles


async def random_memory_model(
    dut,
    config,
    total_beats,
    rng,
    ar_records,
    observed_addresses,
    statistics,
):
    while len(observed_addresses) < total_beats:
        (
            address,
            beats,
            ar_stall,
        ) = await accept_random_ar(
            dut,
            config,
            rng,
        )

        ar_records.append(
            {
                "addr": address,
                "beats": beats,
            }
        )

        statistics["ar_stall_cycles"] += (
            ar_stall
        )

        for beat_index in range(beats):
            beat_address = (
                address + beat_index * 4
            )

            gap_cycles = rng.randint(0, 3)

            statistics["r_gap_cycles"] += (
                gap_cycles
            )

            dut.m_axi_rvalid.value = 0

            if gap_cycles:
                await ClockCycles(
                    dut.clk_mem,
                    gap_cycles,
                )

            await e2e.send_r_beat(
                dut,
                memory_word(beat_address),
                beat_index == beats - 1,
            )

            observed_addresses.append(
                beat_address
            )


async def random_axis_consumer(
    dut,
    expected_count,
    rng,
    observed_words,
    statistics,
):
    while not value(dut.busy_o):
        await RisingEdge(dut.clk_acc)
        await Timer(1, unit="ns")

    initial_delay = rng.randint(0, 40)

    statistics["initial_tready_delay"] = (
        initial_delay
    )

    dut.m_axis_tready.value = 0

    if initial_delay:
        await ClockCycles(
            dut.clk_acc,
            initial_delay,
        )

    stall_remaining = 0
    cycle_count = 0

    while len(observed_words) < expected_count:
        await FallingEdge(dut.clk_acc)

        if stall_remaining > 0:
            ready = False
            stall_remaining -= 1
        elif rng.random() < 0.08:
            stall_remaining = (
                rng.randint(1, 15) - 1
            )
            ready = False
        else:
            ready = rng.random() < 0.75

        dut.m_axis_tready.value = int(ready)

        if not ready:
            statistics["tready_low_cycles"] += 1

        await Timer(1, unit="ns")

        valid = value(dut.m_axis_tvalid)
        data = value(dut.m_axis_tdata)

        if len(observed_words) < expected_count:
            assert value(dut.done_o) == 0

        await RisingEdge(dut.clk_acc)
        await Timer(1, unit="ns")

        if valid and ready:
            observed_words.append(data)

        cycle_count += 1

        assert cycle_count < 20000, (
            "random AXIS timeout"
        )

    dut.m_axis_tready.value = 0

    assert value(dut.done_o) == 1
    assert value(dut.busy_o) == 0
    assert value(dut.error_o) == 0


@cocotb.test()
async def test_random_transfer(dut):
    seed = int(
        os.environ.get("TEST_SEED", "1")
    )

    fifo_depth = int(
        os.environ.get("FIFO_DEPTH", "16")
    )

    clock_tag = os.environ.get(
        "CLOCK_TAG",
        "C1",
    )

    clk_acc_ns = float(
        os.environ.get("CLK_ACC_NS", "10")
    )

    clk_mem_ns = float(
        os.environ.get("CLK_MEM_NS", "12")
    )

    config_rng = random.Random(seed)
    memory_rng = random.Random(
        seed ^ 0x1357_2468
    )
    axis_rng = random.Random(
        seed ^ 0xA5A5_5A5A
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

    await e2e.initialize(dut)

    config = make_random_config(
        config_rng
    )

    reference_addresses = expected_addresses(
        config
    )

    reference_words = expected_data(
        config
    )

    await program_config(
        dut,
        config,
    )

    ar_records = []
    observed_addresses = []
    observed_words = []

    statistics = {
        "ar_stall_cycles": 0,
        "r_gap_cycles": 0,
        "initial_tready_delay": 0,
        "tready_low_cycles": 0,
    }

    memory_task = cocotb.start_soon(
        random_memory_model(
            dut,
            config,
            len(reference_addresses),
            memory_rng,
            ar_records,
            observed_addresses,
            statistics,
        )
    )

    consumer_task = cocotb.start_soon(
        random_axis_consumer(
            dut,
            len(reference_words),
            axis_rng,
            observed_words,
            statistics,
        )
    )

    await e2e.axi_lite_write(
        dut,
        0x00,
        0x0000_0001,
    )

    await with_timeout(
        memory_task,
        500,
        "us",
    )

    await with_timeout(
        consumer_task,
        500,
        "us",
    )

    assert observed_addresses == reference_addresses
    assert observed_words == reference_words

    assert statistics["tready_low_cycles"] > 0

    assert value(dut.done_o) == 1
    assert value(dut.busy_o) == 0
    assert value(dut.error_o) == 0
    assert value(dut.fifo_empty_o) == 1

    dut._log.info(
        f"RANDOM_PASS seed={seed} "
        f"clock={clock_tag} "
        f"fifo={fifo_depth} "
        f"base=0x{config.base_addr:08X} "
        f"length={config.length_bytes} "
        f"stride={config.stride_bytes} "
        f"tile_h={config.tile_h} "
        f"max_burst={config.max_burst} "
        f"beats={len(reference_words)} "
        f"AR={len(ar_records)} "
        f"AR_stall={statistics['ar_stall_cycles']} "
        f"R_gap={statistics['r_gap_cycles']} "
        f"TREADY_low="
        f"{statistics['tready_low_cycles']}"
    )
