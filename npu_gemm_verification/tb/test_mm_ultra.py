import os
import random
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ReadOnly

A_SIZE = 8
DW = 16

SHAPES = {
    "qkv":  (64, 192),
    "out":  (64, 64),
    "fc":   (64, 256),
    "proj": (256, 64),
}


def s16(v: int) -> int:
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


def clip_s16(v: int) -> int:
    return max(-32768, min(32767, int(v)))


def pack8(vals):
    assert len(vals) == 8
    word = 0
    for i, v in enumerate(vals):
        word |= (int(v) & 0xFFFF) << (16 * i)
    return word


def unpack8(word: int):
    return [s16((word >> (16 * i)) & 0xFFFF) for i in range(8)]


def flatten(mat):
    return [x for row in mat for x in row]


def to_beats(flat_vals):
    assert len(flat_vals) % A_SIZE == 0
    return [pack8(flat_vals[i:i + A_SIZE]) for i in range(0, len(flat_vals), A_SIZE)]


def golden_gemm(A, B, shift):
    """Bit-exact CPU INT16 reference used by the old notebook.

    z = A @ B using signed integer arithmetic.
    Rounding rule is identical to right_shifter.v/notebook:
      (z >> shift) + bit(shift-1), then saturate to INT16.
    Test vectors are bounded so the 40-bit inter-block accumulator does not overflow.
    """
    M = len(A)
    K = len(B)
    N = len(B[0])
    out = [[0] * N for _ in range(M)]
    for r in range(M):
        for c in range(N):
            z = 0
            for k in range(K):
                z += int(A[r][k]) * int(B[k][c])
            if shift > 0:
                z = (z >> shift) + ((z >> (shift - 1)) & 1)
            out[r][c] = clip_s16(z)
    return out


def make_vectors(M, K, N, seed):
    rng = random.Random(seed)
    Mp = ((M + A_SIZE - 1) // A_SIZE) * A_SIZE

    # Moderate magnitude keeps PE(35b) and output accumulation(40b) away from overflow,
    # while still exercising signed arithmetic and right-shift rounding.
    A = [[rng.randint(-256, 255) for _ in range(K)] for _ in range(Mp)]
    for r in range(M, Mp):
        A[r] = [0] * K
    B = [[rng.randint(-256, 255) for _ in range(N)] for _ in range(K)]

    # Deterministic non-zero point for fault injection sensitivity.
    A[0][0] = 123
    B[0][0] = -77
    return A, B, Mp


def duty_pattern(duty):
    table = {
        100: [1],
        80:  [1, 1, 1, 1, 0],
        60:  [1, 1, 1, 0, 0],
        40:  [1, 1, 0, 0, 0],
    }
    if duty not in table:
        raise ValueError(f"unsupported DUTY={duty}")
    return table[duty]


async def reset_dut(dut):
    dut.aresetn.value = 0

    dut.s0_axis_tdata.value = 0
    dut.s0_axis_tvalid.value = 0
    dut.s0_axis_tlast.value = 0
    dut.s1_axis_tdata.value = 0
    dut.s1_axis_tvalid.value = 0
    dut.s1_axis_tlast.value = 0
    dut.m0_axis_tready.value = 0

    dut.s00_axi_awaddr.value = 0
    dut.s00_axi_awprot.value = 0
    dut.s00_axi_awvalid.value = 0
    dut.s00_axi_wdata.value = 0
    dut.s00_axi_wstrb.value = 0
    dut.s00_axi_wvalid.value = 0
    dut.s00_axi_bready.value = 0
    dut.s00_axi_araddr.value = 0
    dut.s00_axi_arprot.value = 0
    dut.s00_axi_arvalid.value = 0
    dut.s00_axi_rready.value = 0

    for _ in range(8):
        await RisingEdge(dut.aclk)
    dut.aresetn.value = 1
    for _ in range(5):
        await RisingEdge(dut.aclk)


async def axi_write(dut, addr, data):
    """AXI-Lite write matched to this RTL's registered READY/BVALID behavior."""
    await FallingEdge(dut.aclk)

    dut.s00_axi_awaddr.value = addr
    dut.s00_axi_awprot.value = 0
    dut.s00_axi_awvalid.value = 1

    dut.s00_axi_wdata.value = data
    dut.s00_axi_wstrb.value = 0xF
    dut.s00_axi_wvalid.value = 1

    # Do not consume BVALID before the testbench observes it.
    dut.s00_axi_bready.value = 0

    saw_ready = False

    for _ in range(100):
        await RisingEdge(dut.aclk)
        await FallingEdge(dut.aclk)

        if int(dut.s00_axi_awready.value) and int(dut.s00_axi_wready.value):
            saw_ready = True

        if int(dut.s00_axi_bvalid.value):
            if int(dut.s00_axi_bresp.value) != 0:
                raise AssertionError(
                    f"[AXIL_FAIL] BRESP={int(dut.s00_axi_bresp.value)} "
                    f"addr=0x{addr:x}"
                )
            break
    else:
        raise AssertionError(
            f"[AXIL_FAIL] response timeout addr=0x{addr:x} "
            f"saw_ready={int(saw_ready)}"
        )

    if not saw_ready:
        raise AssertionError(
            f"[AXIL_FAIL] BVALID observed without AW/W ready addr=0x{addr:x}"
        )

    # Request is complete. Accept the held BVALID response.
    dut.s00_axi_awvalid.value = 0
    dut.s00_axi_wvalid.value = 0
    dut.s00_axi_bready.value = 1

    await RisingEdge(dut.aclk)
    await FallingEdge(dut.aclk)

    dut.s00_axi_bready.value = 0

    dut._log.info(
        f"[CHK_AXIL_WRITE_PASS] addr=0x{addr:x} data={data}"
    )


async def drive_axis(dut, prefix, beats, duty, done_flags, done_key):
    """Drive input AXI-Stream using READY sampled before the rising edge."""
    tdata = getattr(dut, f"{prefix}_axis_tdata")
    tvalid = getattr(dut, f"{prefix}_axis_tvalid")
    tready = getattr(dut, f"{prefix}_axis_tready")
    tlast = getattr(dut, f"{prefix}_axis_tlast")

    pat = duty_pattern(duty)
    phase = 0
    idx = 0

    tvalid.value = 0
    tlast.value = 0
    tdata.value = 0

    await FallingEdge(dut.aclk)

    while idx < len(beats):
        # Controlled source-valid bubble.
        if not pat[phase % len(pat)]:
            tvalid.value = 0
            tlast.value = 0

            await RisingEdge(dut.aclk)
            phase += 1
            await FallingEdge(dut.aclk)
            continue

        # Present one beat. Once VALID is asserted, hold it until accepted.
        tdata.value = beats[idx]
        tlast.value = 1 if idx == len(beats) - 1 else 0
        tvalid.value = 1

        while True:
            # READY here is stable for the upcoming rising-edge handshake.
            ready_before_edge = int(tready.value)

            await RisingEdge(dut.aclk)
            phase += 1

            if ready_before_edge:
                idx += 1
                break

            await FallingEdge(dut.aclk)

        await FallingEdge(dut.aclk)
        tvalid.value = 0
        tlast.value = 0

    done_flags[done_key] = True


async def output_ready_driver(dut, stall_enable):
    pat = [1, 1, 0, 0, 1, 0] if stall_enable else [1]
    idx = 0
    dut.m0_axis_tready.value = pat[0]
    while True:
        await FallingEdge(dut.aclk)
        idx += 1
        dut.m0_axis_tready.value = pat[idx % len(pat)]


async def collect_output(dut, expected_beats, done_flags, max_cycles=250000):
    """Collect output using VALID/READY values stable before each rising edge."""
    beats = []
    hold_checks = 0
    early_output_seen = False

    prev_blocked = False
    prev_data = 0
    prev_last = 0

    for _ in range(max_cycles):
        await FallingEdge(dut.aclk)
        await ReadOnly()

        valid = int(dut.m0_axis_tvalid.value)
        ready = int(dut.m0_axis_tready.value)
        data = int(dut.m0_axis_tdata.value)
        last = int(dut.m0_axis_tlast.value)

        # If VALID was blocked by READY=0, payload must remain stable.
        if prev_blocked:
            if not valid or data != prev_data or last != prev_last:
                raise AssertionError(
                    "[CHK_STREAM_STABLE_FAIL] "
                    "output changed while TVALID=1 and TREADY=0"
                )
            hold_checks += 1

        # MM_in_buffer enters CAL only after both complete input buffers
        # have been filled, so this is an RTL-grounded contract.
        if valid and not (
            done_flags["feature"] and done_flags["weight"]
        ):
            early_output_seen = True
            raise AssertionError(
                "[CHK_OUTPUT_AFTER_INPUTS_FAIL] "
                "output became valid before both input streams completed"
            )

        will_accept = bool(valid and ready)

        if will_accept:
            beat_idx = len(beats)
            expected_last = 1 if beat_idx == expected_beats - 1 else 0

            if last != expected_last:
                raise AssertionError(
                    f"[CHK_OUTPUT_ORDER_FAIL] "
                    f"TLAST={last} at beat={beat_idx}, "
                    f"expected={expected_last}"
                )

        prev_blocked = bool(valid and not ready)
        prev_data = data
        prev_last = last

        # Actual transfer occurs here.
        await RisingEdge(dut.aclk)

        if will_accept:
            beats.append(data)

            if len(beats) == expected_beats:
                break

    else:
        raise AssertionError(
            f"[OUTPUT_TIMEOUT] got {len(beats)}/{expected_beats} "
            f"beats after {max_cycles} cycles"
        )

    return beats, hold_checks, early_output_seen


@cocotb.test()
async def verify_gemm(dut):
    kernel = os.getenv("KERNEL", "qkv").lower()
    M = int(os.getenv("M", "8"))
    duty = int(os.getenv("DUTY", "100"))
    shift = int(os.getenv("SHIFT", "4"))
    seed = int(os.getenv("SEED", "1234"))
    phase = os.getenv("PHASE", "prefill")
    out_stall = os.getenv("OUT_STALL", "0") == "1"
    fault = os.getenv("FAULT", "0") == "1"
    run_id = os.getenv("RUN_ID", "manual")

    if kernel not in SHAPES:
        raise ValueError(f"Unknown KERNEL={kernel}")
    K, N = SHAPES[kernel]

    cocotb.start_soon(Clock(dut.aclk, 10, units="ns").start())
    await reset_dut(dut)

    A, B_ref, Mp = make_vectors(M, K, N, seed)
    B_dut = [row[:] for row in B_ref]
    if fault:
        B_dut[0][0] = clip_s16(B_dut[0][0] + 2048)
        dut._log.info(
            f"[FAULT_INJECTED] B[0][0] golden={B_ref[0][0]} dut={B_dut[0][0]}"
        )

    expected = flatten(golden_gemm(A, B_ref, shift))
    f_beats = to_beats(flatten(A))
    w_beats = to_beats(flatten(B_dut))
    expected_beats = (Mp * N) // A_SIZE

    dut._log.info(
        f"[CASE] run_id={run_id} phase={phase} kernel={kernel} M={M} Mp={Mp} "
        f"K={K} N={N} duty={duty} shift={shift} out_stall={int(out_stall)} fault={int(fault)}"
    )

    # Same register programming used by linear_hw() in the notebook.
    await axi_write(dut, 0x0, shift)
    await axi_write(dut, 0x4, Mp)
    await axi_write(dut, 0x8, K // A_SIZE)
    await axi_write(dut, 0xC, N // A_SIZE)

    # MM_in_buffer derives block sizes through registered arithmetic.
    for _ in range(8):
        await RisingEdge(dut.aclk)

    done_flags = {"feature": False, "weight": False}
    ready_task = cocotb.start_soon(output_ready_driver(dut, out_stall))
    out_task = cocotb.start_soon(collect_output(dut, expected_beats, done_flags))
    f_task = cocotb.start_soon(drive_axis(dut, "s0", f_beats, duty, done_flags, "feature"))
    w_task = cocotb.start_soon(drive_axis(dut, "s1", w_beats, duty, done_flags, "weight"))

    await f_task
    await w_task
    out_beats, hold_checks, _ = await out_task
    ready_task.kill()

    actual = []
    for beat in out_beats:
        actual.extend(unpack8(beat))

    dut._log.info("[CHK_OUTPUT_AFTER_INPUTS_PASS]")
    dut._log.info(f"[CHK_STREAM_STABLE_PASS] hold_checks={hold_checks}")
    dut._log.info(f"[CHK_OUTPUT_ORDER_PASS] beats={len(out_beats)}")

    if out_stall and hold_checks == 0:
        raise AssertionError(
            "[CHK_STREAM_STABLE_FAIL] OUT_STALL requested but no blocked-valid cycle was observed"
        )

    if actual != expected:
        first = next(i for i, (a, e) in enumerate(zip(actual, expected)) if a != e)
        raise AssertionError(
            f"[SCOREBOARD_FAIL] first_idx={first} actual={actual[first]} expected={expected[first]} "
            f"mismatch_count={sum(a != e for a, e in zip(actual, expected))}"
        )

    dut._log.info(f"[SCOREBOARD_PASS] elements={len(actual)}")
