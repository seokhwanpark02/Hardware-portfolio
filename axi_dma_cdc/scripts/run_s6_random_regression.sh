#!/usr/bin/env bash

set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$HOME/.venvs/axi_dma_cdc"

cd "$PROJECT_ROOT" || exit 1
[ -f "$VENV_PATH/bin/activate" ] && source "$VENV_PATH/bin/activate"

LOG_DIR="$PROJECT_ROOT/results/random"
SUMMARY_FILE="$PROJECT_ROOT/results/s6_random_summary.log"

mkdir -p "$LOG_DIR"
: > "$SUMMARY_FILE"

PASS_COUNT=0
TOTAL_COUNT=0
EXPECTED_COUNT=120

run_case() {
    local clock_tag="$1"
    local clk_acc_ns="$2"
    local clk_mem_ns="$3"
    local fifo_depth="$4"
    local seed="$5"

    local log_file
    local pass_line

    log_file="$LOG_DIR/${clock_tag}_f${fifo_depth}_s${seed}.log"

    TOTAL_COUNT=$((TOTAL_COUNT + 1))

    if make -f tb/Makefile.s6_random \
        FIFO_DEPTH="$fifo_depth" \
        TEST_SEED="$seed" \
        CLOCK_TAG="$clock_tag" \
        CLK_ACC_NS="$clk_acc_ns" \
        CLK_MEM_NS="$clk_mem_ns" \
        > "$log_file" 2>&1
    then
        pass_line=$(
            grep "RANDOM_PASS" "$log_file" \
                | tail -n 1
        )

        if [[ -z "$pass_line" ]]; then
            echo "[FAIL] Missing RANDOM_PASS: ${clock_tag} FIFO=${fifo_depth} SEED=${seed}"
            tail -n 80 "$log_file"
            exit 1
        fi

        PASS_COUNT=$((PASS_COUNT + 1))

        echo "[PASS ${PASS_COUNT}/${EXPECTED_COUNT}] ${clock_tag} FIFO=${fifo_depth} SEED=${seed}"
        echo "$pass_line" >> "$SUMMARY_FILE"
    else
        echo "[FAIL] ${clock_tag} FIFO=${fifo_depth} SEED=${seed}"
        echo "Log: $log_file"
        tail -n 120 "$log_file"
        exit 1
    fi
}

for clock_spec in \
    "C1_100_83 10 12" \
    "C2_100_33 10 30"
do
    read -r clock_tag clk_acc_ns clk_mem_ns \
        <<< "$clock_spec"

    for fifo_depth in 16 32
    do
        for seed in $(seq 1 30)
        do
            run_case \
                "$clock_tag" \
                "$clk_acc_ns" \
                "$clk_mem_ns" \
                "$fifo_depth" \
                "$seed"
        done
    done
done

echo
echo "Random regression result: ${PASS_COUNT}/${TOTAL_COUNT} PASS"

if [[ "$PASS_COUNT" -ne "$EXPECTED_COUNT" ]]; then
    echo "Expected ${EXPECTED_COUNT} passes."
    exit 1
fi

SUMMARY_COUNT=$(
    grep -c "RANDOM_PASS" "$SUMMARY_FILE"
)

if [[ "$SUMMARY_COUNT" -ne "$EXPECTED_COUNT" ]]; then
    echo "Summary count mismatch: ${SUMMARY_COUNT}"
    exit 1
fi

echo "Summary: $SUMMARY_FILE"
echo "S6 random regression: PASS"
