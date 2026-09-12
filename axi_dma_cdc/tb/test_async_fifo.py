import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import (
    ClockCycles,
    FallingEdge,
    RisingEdge,
    Timer,
)


def value(signal):
    return int(signal.value)


def make_entry(index):
    final = index & 1
    data = (
        0x1357_9BDF
        ^ (index * 0x1020_3041)
    ) & 0xFFFF_FFFF

    return (final << 32) | data


async def reset_fifo(dut):
    dut.wr_rst_n.value = 0
    dut.rd_rst_n.value = 0

    dut.wr_en_i.value = 0
    dut.wr_data_i.value = 0
    dut.rd_en_i.value = 0

    await ClockCycles(dut.wr_clk, 4)
    await ClockCycles(dut.rd_clk, 4)

    dut.wr_rst_n.value = 1
    dut.rd_rst_n.value = 1

    await ClockCycles(dut.wr_clk, 4)
    await ClockCycles(dut.rd_clk, 4)


async def push_once(
    dut,
    entry,
    expected_accept=True,
):
    await FallingEdge(dut.wr_clk)

    dut.wr_data_i.value = entry
    dut.wr_en_i.value = 1

    await Timer(1, unit="ns")

    accepted = value(dut.wr_accept_o)

    assert accepted == int(expected_accept), (
        f"write acceptance mismatch: "
        f"expected={expected_accept} "
        f"actual={accepted} "
        f"full={value(dut.wr_full_o)}"
    )

    await RisingEdge(dut.wr_clk)
    await FallingEdge(dut.wr_clk)

    dut.wr_en_i.value = 0

    return accepted


async def pop_once(
    dut,
    expected_accept=True,
):
    await FallingEdge(dut.rd_clk)

    dut.rd_en_i.value = 1

    await Timer(1, unit="ns")

    accepted = value(dut.rd_accept_o)
    entry = value(dut.rd_data_o)

    assert accepted == int(expected_accept), (
        f"read acceptance mismatch: "
        f"expected={expected_accept} "
        f"actual={accepted} "
        f"empty={value(dut.rd_empty_o)}"
    )

    await RisingEdge(dut.rd_clk)
    await FallingEdge(dut.rd_clk)

    dut.rd_en_i.value = 0

    return accepted, entry


async def wait_for_write_free(
    dut,
    expected_free,
):
    for _ in range(12):
        await RisingEdge(dut.wr_clk)
        await Timer(1, unit="ns")

        if value(dut.wr_free_slots_o) == expected_free:
            return

    raise AssertionError(
        "write-domain free-space did not converge: "
        f"expected={expected_free} "
        f"actual={value(dut.wr_free_slots_o)}"
    )


async def concurrent_producer(
    dut,
    entries,
    statistics,
):
    index = 0
    attempts = 0
    maximum_attempts = len(entries) * 20

    while index < len(entries):
        await FallingEdge(dut.wr_clk)

        dut.wr_en_i.value = 1
        dut.wr_data_i.value = entries[index]

        await Timer(1, unit="ns")

        accepted = value(dut.wr_accept_o)

        if accepted:
            index += 1
        else:
            statistics["write_stalls"] += 1

        await RisingEdge(dut.wr_clk)

        attempts += 1

        assert attempts < maximum_attempts, (
            "producer timeout"
        )

    await FallingEdge(dut.wr_clk)
    dut.wr_en_i.value = 0


async def concurrent_consumer(
    dut,
    expected_count,
    observed,
    statistics,
):
    await ClockCycles(dut.rd_clk, 4)

    attempts = 0
    maximum_attempts = expected_count * 30

    while len(observed) < expected_count:
        await FallingEdge(dut.rd_clk)

        dut.rd_en_i.value = 1

        await Timer(1, unit="ns")

        accepted = value(dut.rd_accept_o)

        if accepted:
            observed.append(
                value(dut.rd_data_o)
            )
        else:
            statistics["read_stalls"] += 1

        await RisingEdge(dut.rd_clk)

        attempts += 1

        assert attempts < maximum_attempts, (
            "consumer timeout"
        )

    await FallingEdge(dut.rd_clk)
    dut.rd_en_i.value = 0


@cocotb.test()
async def test_async_fifo(dut):
    depth = int(
        os.environ.get("FIFO_DEPTH", "16")
    )

    cocotb.start_soon(
        Clock(
            dut.wr_clk,
            10,
            unit="ns",
        ).start()
    )

    cocotb.start_soon(
        Clock(
            dut.rd_clk,
            12,
            unit="ns",
        ).start()
    )

    await reset_fifo(dut)

    assert value(dut.rd_empty_o) == 1
    assert value(dut.wr_full_o) == 0
    assert value(dut.wr_level_o) == 0
    assert value(dut.wr_free_slots_o) == depth

    # Empty 상태의 read는 수락되지 않아야 한다.
    _, _ = await pop_once(
        dut,
        expected_accept=False,
    )

    assert value(dut.rd_empty_o) == 1

    # FIFO를 정확히 DEPTH개 채운다.
    fill_entries = [
        make_entry(index)
        for index in range(depth)
    ]

    for entry in fill_entries:
        await push_once(dut, entry)

    assert value(dut.wr_full_o) == 1
    assert value(dut.wr_level_o) == depth
    assert value(dut.wr_free_slots_o) == 0

    # Full 상태의 추가 write는 차단되어야 한다.
    await push_once(
        dut,
        make_entry(0x1000),
        expected_accept=False,
    )

    # 기존 데이터가 손상되지 않았는지 확인한다.
    observed_fill = []

    for expected in fill_entries:
        accepted, received = await pop_once(dut)

        assert accepted == 1
        observed_fill.append(received)

        assert received == expected, (
            f"FIFO order/data mismatch: "
            f"expected=0x{expected:09X} "
            f"actual=0x{received:09X}"
        )

    assert observed_fill == fill_entries
    assert value(dut.rd_empty_o) == 1

    # Empty 상태의 추가 read는 차단되어야 한다.
    await pop_once(
        dut,
        expected_accept=False,
    )

    await wait_for_write_free(
        dut,
        depth,
    )

    assert value(dut.wr_level_o) == 0
    assert value(dut.wr_free_slots_o) == depth

    dut._log.info(
        f"DEPTH={depth} full/empty/"
        "overflow/underflow: PASS"
    )

    # 여러 번 pointer wrap이 발생하도록 충분한 수를
    # 두 비동기 clock에서 동시에 전송한다.
    stream_count = depth * 8

    stream_entries = [
        make_entry(0x2000 + index)
        for index in range(stream_count)
    ]

    observed_stream = []

    statistics = {
        "write_stalls": 0,
        "read_stalls": 0,
    }

    producer_task = cocotb.start_soon(
        concurrent_producer(
            dut,
            stream_entries,
            statistics,
        )
    )

    await concurrent_consumer(
        dut,
        stream_count,
        observed_stream,
        statistics,
    )

    await producer_task

    assert observed_stream == stream_entries, (
        "asynchronous stream order/data mismatch"
    )

    assert statistics["write_stalls"] > 0, (
        "full back-pressure was not exercised"
    )

    assert value(dut.rd_empty_o) == 1

    await wait_for_write_free(
        dut,
        depth,
    )

    assert value(dut.wr_level_o) == 0
    assert value(dut.wr_free_slots_o) == depth

    dut._log.info(
        f"DEPTH={depth} asynchronous order/wrap: "
        f"{stream_count} entries, "
        f"write_stalls="
        f"{statistics['write_stalls']} PASS"
    )

    dut._log.info(
        f"Async FIFO DEPTH={depth}: ALL PASS"
    )
