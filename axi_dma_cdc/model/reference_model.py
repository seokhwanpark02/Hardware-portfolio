from dataclasses import asdict, dataclass
from typing import Optional

BEAT_BYTES = 4
PAGE_BYTES = 4096
HW_MAX_BURST = 16
MASK32 = 0xFFFFFFFF


@dataclass(frozen=True)
class Config:
    base_addr: int
    length_bytes: int
    stride_bytes: int
    tile_h: int
    max_burst: int


@dataclass(frozen=True)
class BurstDecision:
    row: int
    addr: int
    row_remaining_before: int
    beats_until_4kb: int
    desired_beats: int
    issued_beats: int
    arlen: int
    row_short: bool
    boundary_short: bool
    fifo_limited: bool


def validate_config(config: Config) -> None:
    errors = []

    if config.base_addr % BEAT_BYTES != 0:
        errors.append("BASE_ADDR is not 4-byte aligned")

    if config.length_bytes == 0:
        errors.append("LENGTH is zero")
    elif config.length_bytes % BEAT_BYTES != 0:
        errors.append("LENGTH is not 4-byte aligned")

    if config.stride_bytes % BEAT_BYTES != 0:
        errors.append("STRIDE is not 4-byte aligned")

    if config.tile_h == 0:
        errors.append("TILE_H is zero")

    if not 1 <= config.max_burst <= HW_MAX_BURST:
        errors.append("MAX_BURST is outside 1..16")

    if errors:
        raise ValueError("; ".join(errors))


def beats_until_4kb(addr: int) -> int:
    if addr % BEAT_BYTES != 0:
        raise ValueError("Address is not 4-byte aligned")

    bytes_remaining = PAGE_BYTES - (addr & (PAGE_BYTES - 1))
    return bytes_remaining // BEAT_BYTES


def choose_burst(
    *,
    row: int,
    addr: int,
    row_remaining_beats: int,
    max_burst: int,
    fifo_free_slots: int,
) -> Optional[BurstDecision]:
    if addr % BEAT_BYTES != 0:
        raise ValueError("Address is not 4-byte aligned")

    if row_remaining_beats <= 0:
        raise ValueError("row_remaining_beats must be positive")

    if not 1 <= max_burst <= HW_MAX_BURST:
        raise ValueError("max_burst must be inside 1..16")

    if fifo_free_slots < 0:
        raise ValueError("fifo_free_slots cannot be negative")

    if fifo_free_slots == 0:
        return None

    boundary_beats = beats_until_4kb(addr)

    desired_beats = min(
        row_remaining_beats,
        boundary_beats,
        max_burst,
    )

    issued_beats = min(
        desired_beats,
        fifo_free_slots,
    )

    return BurstDecision(
        row=row,
        addr=addr,
        row_remaining_before=row_remaining_beats,
        beats_until_4kb=boundary_beats,
        desired_beats=desired_beats,
        issued_beats=issued_beats,
        arlen=issued_beats - 1,
        row_short=(
            desired_beats < max_burst
            and desired_beats == row_remaining_beats
        ),
        boundary_short=(
            desired_beats < max_burst
            and desired_beats == boundary_beats
            and boundary_beats < row_remaining_beats
        ),
        fifo_limited=(issued_beats < desired_beats),
    )


def plan_bursts(config: Config) -> list[BurstDecision]:
    validate_config(config)

    bursts = []
    beats_per_row = config.length_bytes // BEAT_BYTES

    for row in range(config.tile_h):
        addr = config.base_addr + row * config.stride_bytes
        remaining = beats_per_row

        while remaining > 0:
            decision = choose_burst(
                row=row,
                addr=addr,
                row_remaining_beats=remaining,
                max_burst=config.max_burst,
                fifo_free_slots=config.max_burst,
            )

            if decision is None:
                raise RuntimeError("Static planning unexpectedly stalled")

            bursts.append(decision)
            addr += decision.issued_beats * BEAT_BYTES
            remaining -= decision.issued_beats

    return bursts


def expected_addresses(config: Config) -> list[int]:
    validate_config(config)

    addresses = []
    beats_per_row = config.length_bytes // BEAT_BYTES

    for row in range(config.tile_h):
        row_addr = config.base_addr + row * config.stride_bytes

        for beat in range(beats_per_row):
            addresses.append(row_addr + beat * BEAT_BYTES)

    return addresses


def memory_word(addr: int) -> int:
    if addr % BEAT_BYTES != 0:
        raise ValueError("Address is not 4-byte aligned")

    word_index = addr >> 2

    return (
        word_index * 0x1F123BB5
        + 0xA5A55A5A
    ) & MASK32


def expected_data(config: Config) -> list[int]:
    return [
        memory_word(addr)
        for addr in expected_addresses(config)
    ]


def burst_crosses_4kb(burst: BurstDecision) -> bool:
    last_byte_addr = (
        burst.addr
        + burst.issued_beats * BEAT_BYTES
        - 1
    )

    return (burst.addr >> 12) != (last_byte_addr >> 12)


def config_to_dict(config: Config) -> dict:
    return asdict(config)


def burst_to_dict(burst: BurstDecision) -> dict:
    return asdict(burst)