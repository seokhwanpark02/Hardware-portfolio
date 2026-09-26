import json
import os
import sys
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ReadOnly

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

DIAG_MULT = [1, 2, 3, 4, 5, 6, 7, 8, 7, 6, 5, 4, 3, 2, 1]


def iv(sig):
    return int(sig.value)


def find_internal_handles(dut):
    """Resolve only RTL signals that have direct semantic meaning in the design."""
    try:
        axi = dut.U_MM_ultra_axi
        ultra = axi.u_MM_ultra
        mm_buf = ultra.u_MM_buffer
    except AttributeError as e:
        raise AssertionError(
            "[S5_HIER_FAIL] Could not resolve "
            "U_MM_ultra_axi.u_MM_ultra.u_MM_buffer. "
            "S5 Makefile must include --public-flat-rw."
        ) from e

    required = [
        "state",
        "input_weight_valid",
        "input_feature_valid",
    ]
    missing = [name for name in required if not hasattr(mm_buf, name)]
    if missing:
        raise AssertionError(
            f"[S5_HIER_FAIL] missing MM_buffer signals: {missing}"
        )

    return mm_buf


async def monitor_activity(dut, M, Mp, K, N, max_cycles=2_000_000):
    """Cycle-accurate activity monitor.

    The PE activity shadow follows the actual 8x8 systolic structure:
      - one FEATURE_FEED issue launches one 8-element K block,
      - every issue creates 64 valid PE MAC operations,
      - PE(i,j) becomes active after 1+i+j cycles.
    This counts valid scheduled work, not data-dependent non-zero switching.
    """
    mm_buf = find_internal_handles(dut)
    dut._log.info("[S5_HIER_PROBE_PASS] MM_buffer internal state/valid visible")

    hist = [0] * len(DIAG_MULT)

    started = False
    f_done = False
    w_done = False
    out_started = False

    tx_cycle = 0
    active_series = []

    phase = {
        "INPUT_LOAD": 0,
        "WEIGHT_LOAD": 0,
        "FEATURE_FEED": 0,
        "ARRAY_DRAIN": 0,
        "OUTPUT_DRAIN": 0,
        "CONTROL_IDLE": 0,
    }

    stalls = {
        "feature_source_starvation": 0,
        "weight_source_starvation": 0,
        "feature_input_backpressure": 0,
        "weight_input_backpressure": 0,
        "weight_load_wait": 0,
        "feature_feed_wait": 0,
        "output_backpressure": 0,
        "control_wait": 0,
    }

    counts = {
        "feature_top_accept_beats": 0,
        "weight_top_accept_beats": 0,
        "output_accept_beats": 0,
        "internal_weight_load_cycles": 0,
        "internal_feature_issue_cycles": 0,
        "full_pe_cycles": 0,
        "partial_pe_cycles": 0,
        "zero_pe_cycles_transaction": 0,
        "active_pe_ops": 0,
    }

    first_active_tx_cycle = None
    last_active_tx_cycle = None
    both_inputs_done_tx_cycle = None
    first_output_tx_cycle = None

    expected_feature_beats = Mp * K // A_SIZE
    expected_weight_beats = K * N // A_SIZE
    expected_output_beats = Mp * N // A_SIZE

    for _ in range(max_cycles):
        await FallingEdge(dut.aclk)
        await ReadOnly()

        f_valid = iv(dut.s0_axis_tvalid)
        f_ready = iv(dut.s0_axis_tready)
        f_last = iv(dut.s0_axis_tlast)
        w_valid = iv(dut.s1_axis_tvalid)
        w_ready = iv(dut.s1_axis_tready)
        w_last = iv(dut.s1_axis_tlast)
        o_valid = iv(dut.m0_axis_tvalid)
        o_ready = iv(dut.m0_axis_tready)
        o_last = iv(dut.m0_axis_tlast)

        f_hs = bool(f_valid and f_ready)
        w_hs = bool(w_valid and w_ready)
        o_hs = bool(o_valid and o_ready)

        state = iv(mm_buf.state)
        weight_internal_valid = iv(mm_buf.input_weight_valid)
        feature_internal_valid = iv(mm_buf.input_feature_valid)

        issue_now = bool(state == 3 and feature_internal_valid)
        weight_load_now = bool(state == 1 and weight_internal_valid)

        # Activity occurring at the upcoming rising edge comes from earlier
        # feature issues. Current issue enters the PE wavefront one cycle later.
        active_pe = sum(
            mult * hist[d] for d, mult in enumerate(DIAG_MULT)
        )

        if not started and (f_hs or w_hs):
            started = True

        if started:
            tx_cycle += 1

            if f_hs:
                counts["feature_top_accept_beats"] += 1
            if w_hs:
                counts["weight_top_accept_beats"] += 1
            if o_hs:
                counts["output_accept_beats"] += 1

            if weight_load_now:
                counts["internal_weight_load_cycles"] += 1
            if issue_now:
                counts["internal_feature_issue_cycles"] += 1

            counts["active_pe_ops"] += active_pe
            active_series.append(active_pe)

            if active_pe == 64:
                counts["full_pe_cycles"] += 1
            elif active_pe > 0:
                counts["partial_pe_cycles"] += 1
            else:
                counts["zero_pe_cycles_transaction"] += 1

            if active_pe > 0:
                if first_active_tx_cycle is None:
                    first_active_tx_cycle = tx_cycle
                last_active_tx_cycle = tx_cycle

            # Mutually-exclusive transaction phase classification.
            inputs_done_before = f_done and w_done
            if not inputs_done_before:
                phase["INPUT_LOAD"] += 1
            elif state == 1:
                phase["WEIGHT_LOAD"] += 1
            elif state == 3:
                phase["FEATURE_FEED"] += 1
            elif active_pe > 0:
                phase["ARRAY_DRAIN"] += 1
            elif o_valid or out_started:
                phase["OUTPUT_DRAIN"] += 1
            else:
                phase["CONTROL_IDLE"] += 1

            # Orthogonal stall/wait reasons. These are not additive phases.
            if not f_done:
                if f_ready and not f_valid:
                    stalls["feature_source_starvation"] += 1
                if f_valid and not f_ready:
                    stalls["feature_input_backpressure"] += 1

            if not w_done:
                if w_ready and not w_valid:
                    stalls["weight_source_starvation"] += 1
                if w_valid and not w_ready:
                    stalls["weight_input_backpressure"] += 1

            if state == 1 and not weight_internal_valid:
                stalls["weight_load_wait"] += 1
            if state == 3 and not feature_internal_valid:
                stalls["feature_feed_wait"] += 1
            if o_valid and not o_ready:
                stalls["output_backpressure"] += 1

            if (
                inputs_done_before
                and state not in (1, 3)
                and active_pe == 0
                and not o_valid
            ):
                stalls["control_wait"] += 1

            if o_valid and first_output_tx_cycle is None:
                first_output_tx_cycle = tx_cycle
            if o_valid:
                out_started = True

        # The sampled handshakes occur at this rising edge.
        await RisingEdge(dut.aclk)

        if started:
            hist = [1 if issue_now else 0] + hist[:-1]

        if f_hs and f_last:
            f_done = True
        if w_hs and w_last:
            w_done = True
        if started and f_done and w_done and both_inputs_done_tx_cycle is None:
            both_inputs_done_tx_cycle = tx_cycle

        if started and o_hs and o_last:
            break
    else:
        raise AssertionError("[S5_TIMEOUT] transaction did not finish")

    # Compute-window analysis from first to last shadow-active PE cycle.
    if first_active_tx_cycle is None or last_active_tx_cycle is None:
        raise AssertionError("[S5_ACTIVITY_FAIL] no active PE work observed")

    lo = first_active_tx_cycle - 1
    hi = last_active_tx_cycle
    win = active_series[lo:hi]
    compute_window_cycles = len(win)
    full_in_window = sum(v == 64 for v in win)
    partial_in_window = sum(0 < v < 64 for v in win)
    zero_in_window = sum(v == 0 for v in win)
    active_pe_ops_window = sum(win)

    scheduled_mac = Mp * K * N
    useful_mac = M * K * N
    shadow_from_issue = counts["internal_feature_issue_cycles"] * 64

    metrics = {
        "M": M,
        "Mp": Mp,
        "K": K,
        "N": N,
        "total_cycles": tx_cycle,
        "expected_feature_beats": expected_feature_beats,
        "expected_weight_beats": expected_weight_beats,
        "expected_output_beats": expected_output_beats,
        "both_inputs_done_cycle": both_inputs_done_tx_cycle,
        "first_active_cycle": first_active_tx_cycle,
        "last_active_cycle": last_active_tx_cycle,
        "first_output_cycle": first_output_tx_cycle,
        "compute_window_cycles": compute_window_cycles,
        "phase_cycles": phase,
        "stall_cycles": stalls,
        **counts,
        "full_pe_cycles_compute_window": full_in_window,
        "partial_pe_cycles_compute_window": partial_in_window,
        "zero_pe_cycles_compute_window": zero_in_window,
        "active_pe_ops_compute_window": active_pe_ops_window,
        "scheduled_mac": scheduled_mac,
        "useful_mac": useful_mac,
        "shadow_issue_mac": shadow_from_issue,
        "padding_efficiency_pct": 100.0 * useful_mac / scheduled_mac,
        "array_util_compute_window_pct": (
            100.0 * active_pe_ops_window / (64 * compute_window_cycles)
        ),
        "array_util_transaction_pct": (
            100.0 * counts["active_pe_ops"] / (64 * tx_cycle)
        ),
        "useful_capacity_transaction_pct": (
            100.0 * useful_mac / (64 * tx_cycle)
        ),
        "scheduled_capacity_transaction_pct": (
            100.0 * scheduled_mac / (64 * tx_cycle)
        ),
        "issue_vs_scheduled_mac_delta": shadow_from_issue - scheduled_mac,
        "active_vs_scheduled_mac_delta": counts["active_pe_ops"] - scheduled_mac,
    }

    # Hard consistency checks: if these fail, the metric interpretation is wrong.
    if counts["feature_top_accept_beats"] != expected_feature_beats:
        raise AssertionError(
            f"[S5_COUNT_FAIL] feature beats "
            f"{counts['feature_top_accept_beats']} != {expected_feature_beats}"
        )
    if counts["weight_top_accept_beats"] != expected_weight_beats:
        raise AssertionError(
            f"[S5_COUNT_FAIL] weight beats "
            f"{counts['weight_top_accept_beats']} != {expected_weight_beats}"
        )
    if counts["output_accept_beats"] != expected_output_beats:
        raise AssertionError(
            f"[S5_COUNT_FAIL] output beats "
            f"{counts['output_accept_beats']} != {expected_output_beats}"
        )
    if shadow_from_issue != scheduled_mac:
        raise AssertionError(
            f"[S5_SCHEDULE_FAIL] issue*64={shadow_from_issue} "
            f"scheduled_mac={scheduled_mac}"
        )
    if counts["active_pe_ops"] != scheduled_mac:
        raise AssertionError(
            f"[S5_SHADOW_FAIL] active_pe_ops={counts['active_pe_ops']} "
            f"scheduled_mac={scheduled_mac}"
        )
    if sum(phase.values()) != tx_cycle:
        raise AssertionError(
            f"[S5_PHASE_FAIL] phase_sum={sum(phase.values())} total={tx_cycle}"
        )

    return metrics


@cocotb.test()
async def measure_utilization(dut):
    kernel = os.getenv("KERNEL", "qkv").lower()
    M = int(os.getenv("M", "4"))
    shift = int(os.getenv("SHIFT", "4"))
    seed = int(os.getenv("SEED", "5101"))
    phase_name = os.getenv("PHASE", "prefill")
    run_id = os.getenv("RUN_ID", "s5_manual")

    if kernel not in SHAPES:
        raise ValueError(f"Unknown KERNEL={kernel}")

    K, N = SHAPES[kernel]

    cocotb.start_soon(Clock(dut.aclk, 10, units="ns").start())
    await reset_dut(dut)

    A, B, Mp = make_vectors(M, K, N, seed)
    expected = flatten(golden_gemm(A, B, shift))
    f_beats = to_beats(flatten(A))
    w_beats = to_beats(flatten(B))
    expected_beats = Mp * N // A_SIZE

    dut._log.info(
        f"[S5_CASE] run_id={run_id} phase={phase_name} "
        f"kernel={kernel} M={M} Mp={Mp} K={K} N={N}"
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
        drive_axis(
            dut, "s0", f_beats, 100, done_flags, "feature"
        )
    )
    w_task = cocotb.start_soon(
        drive_axis(
            dut, "s1", w_beats, 100, done_flags, "weight"
        )
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
            f"[S5_SCOREBOARD_FAIL] first_idx={first} "
            f"actual={actual[first]} expected={expected[first]}"
        )

    dut._log.info(
        f"[S5_SCOREBOARD_PASS] elements={len(actual)}"
    )
    dut._log.info(
        "[S5_METRICS] " + json.dumps(metrics, sort_keys=True)
    )
