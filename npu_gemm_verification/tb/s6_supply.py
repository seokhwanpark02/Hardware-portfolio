import json
import os
import sys
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_mm_ultra import (  # noqa: E402
    A_SIZE,
    SHAPES,
    axi_write,
    collect_output,
    drive_axis,
    flatten,
    golden_gemm,
    make_vectors,
    output_ready_driver,
    reset_dut,
    to_beats,
    unpack8,
)
from s5_utilization import monitor_activity  # noqa: E402


@cocotb.test()
async def supply_sensitivity(dut):
    kernel = os.getenv("KERNEL", "qkv").lower()
    M = int(os.getenv("M", "4"))
    duty = int(os.getenv("DUTY", "100"))
    shift = int(os.getenv("SHIFT", "4"))
    seed = int(os.getenv("SEED", "6101"))
    phase_name = os.getenv("PHASE", "prefill")
    run_id = os.getenv("RUN_ID", "s6_manual")

    if kernel not in SHAPES:
        raise ValueError(f"Unknown KERNEL={kernel}")
    if duty not in (100, 80, 60, 40):
        raise ValueError(f"Unsupported DUTY={duty}")

    K, N = SHAPES[kernel]

    cocotb.start_soon(Clock(dut.aclk, 10, units="ns").start())
    await reset_dut(dut)

    A, B, Mp = make_vectors(M, K, N, seed)
    expected = flatten(golden_gemm(A, B, shift))
    f_beats = to_beats(flatten(A))
    w_beats = to_beats(flatten(B))
    expected_beats = Mp * N // A_SIZE

    dut._log.info(
        f"[S6_CASE] run_id={run_id} phase={phase_name} "
        f"kernel={kernel} M={M} Mp={Mp} K={K} N={N} duty={duty}"
    )

    await axi_write(dut, 0x0, shift)
    await axi_write(dut, 0x4, Mp)
    await axi_write(dut, 0x8, K // A_SIZE)
    await axi_write(dut, 0xC, N // A_SIZE)

    for _ in range(8):
        await RisingEdge(dut.aclk)

    done_flags = {"feature": False, "weight": False}

    ready_task = cocotb.start_soon(output_ready_driver(dut, False))
    monitor_task = cocotb.start_soon(
        monitor_activity(dut, M=M, Mp=Mp, K=K, N=N)
    )
    out_task = cocotb.start_soon(
        collect_output(dut, expected_beats, done_flags)
    )
    f_task = cocotb.start_soon(
        drive_axis(dut, "s0", f_beats, duty, done_flags, "feature")
    )
    w_task = cocotb.start_soon(
        drive_axis(dut, "s1", w_beats, duty, done_flags, "weight")
    )

    await f_task
    await w_task
    out_beats, _, _ = await out_task
    metrics = await monitor_task
    ready_task.kill()

    actual = []
    for beat in out_beats:
        actual.extend(unpack8(beat))

    if actual != expected:
        first = next(
            i for i, (a, e) in enumerate(zip(actual, expected))
            if a != e
        )
        raise AssertionError(
            f"[S6_SCOREBOARD_FAIL] first_idx={first} "
            f"actual={actual[first]} expected={expected[first]}"
        )

    metrics["duty"] = duty
    metrics["phase_name"] = phase_name
    metrics["kernel_name"] = kernel

    dut._log.info(f"[S6_SCOREBOARD_PASS] elements={len(actual)}")
    dut._log.info("[S6_METRICS] " + json.dumps(metrics, sort_keys=True))
