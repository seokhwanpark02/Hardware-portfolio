import unittest

from model.reference_model import (
    Config,
    burst_crosses_4kb,
    choose_burst,
    expected_addresses,
    expected_data,
    memory_word,
    plan_bursts,
    validate_config,
)


class ReferenceModelTest(unittest.TestCase):
    def test_invalid_config(self):
        invalid_configs = [
            Config(0x1002, 64, 64, 1, 16),
            Config(0x1000, 0, 64, 1, 16),
            Config(0x1000, 6, 64, 1, 16),
            Config(0x1000, 64, 2, 1, 16),
            Config(0x1000, 64, 64, 0, 16),
            Config(0x1000, 64, 64, 1, 0),
            Config(0x1000, 64, 64, 1, 17),
        ]

        for config in invalid_configs:
            with self.subTest(config=config):
                with self.assertRaises(ValueError):
                    validate_config(config)

    def test_single_beat(self):
        config = Config(0x1000, 4, 4, 1, 16)
        bursts = plan_bursts(config)

        self.assertEqual(len(bursts), 1)
        self.assertEqual(bursts[0].addr, 0x1000)
        self.assertEqual(bursts[0].issued_beats, 1)
        self.assertEqual(bursts[0].arlen, 0)

    def test_exact_full_burst(self):
        config = Config(0x1000, 64, 64, 1, 16)
        bursts = plan_bursts(config)

        self.assertEqual(
            [burst.issued_beats for burst in bursts],
            [16],
        )

        self.assertEqual(
            [burst.arlen for burst in bursts],
            [15],
        )

    def test_row_tail_split(self):
        config = Config(0x1000, 80, 80, 1, 16)
        bursts = plan_bursts(config)

        self.assertEqual(
            [burst.issued_beats for burst in bursts],
            [16, 4],
        )

        self.assertEqual(
            [burst.addr for burst in bursts],
            [0x1000, 0x1040],
        )

        self.assertTrue(bursts[1].row_short)

    def test_4kb_split(self):
        config = Config(0x0FF0, 32, 32, 1, 16)
        bursts = plan_bursts(config)

        self.assertEqual(
            [burst.issued_beats for burst in bursts],
            [4, 4],
        )

        self.assertEqual(
            [burst.addr for burst in bursts],
            [0x0FF0, 0x1000],
        )

        self.assertTrue(bursts[0].boundary_short)

        for burst in bursts:
            self.assertFalse(burst_crosses_4kb(burst))

    def test_multi_row_stride(self):
        config = Config(0x2000, 32, 64, 3, 16)
        bursts = plan_bursts(config)

        self.assertEqual(
            [burst.addr for burst in bursts],
            [0x2000, 0x2040, 0x2080],
        )

        self.assertEqual(
            [burst.issued_beats for burst in bursts],
            [8, 8, 8],
        )

    def test_overlapping_rows(self):
        config = Config(0x3000, 32, 16, 3, 16)
        addresses = expected_addresses(config)

        self.assertEqual(len(addresses), 24)
        self.assertEqual(addresses[0], 0x3000)
        self.assertEqual(addresses[8], 0x3010)
        self.assertEqual(addresses[16], 0x3020)

        self.assertEqual(addresses[4:8], addresses[8:12])
        self.assertEqual(addresses[12:16], addresses[16:20])

    def test_shrink_to_fit(self):
        decision = choose_burst(
            row=0,
            addr=0x4000,
            row_remaining_beats=16,
            max_burst=16,
            fifo_free_slots=3,
        )

        self.assertIsNotNone(decision)
        self.assertEqual(decision.desired_beats, 16)
        self.assertEqual(decision.issued_beats, 3)
        self.assertEqual(decision.arlen, 2)
        self.assertTrue(decision.fifo_limited)

    def test_zero_free_slots_waits(self):
        decision = choose_burst(
            row=0,
            addr=0x4000,
            row_remaining_beats=16,
            max_burst=16,
            fifo_free_slots=0,
        )

        self.assertIsNone(decision)

    def test_deterministic_memory_data(self):
        self.assertEqual(memory_word(0x0000), 0xA5A55A5A)
        self.assertEqual(memory_word(0x0004), 0xC4B7960F)

        config = Config(0x0000, 8, 8, 1, 16)

        self.assertEqual(
            expected_data(config),
            [0xA5A55A5A, 0xC4B7960F],
        )

    def test_all_bursts_legal_and_complete(self):
        config = Config(
            base_addr=0x0FE0,
            length_bytes=320,
            stride_bytes=512,
            tile_h=3,
            max_burst=7,
        )

        bursts = plan_bursts(config)

        actual_addresses = []

        for burst in bursts:
            self.assertGreaterEqual(burst.issued_beats, 1)
            self.assertLessEqual(
                burst.issued_beats,
                config.max_burst,
            )
            self.assertEqual(
                burst.arlen,
                burst.issued_beats - 1,
            )
            self.assertFalse(burst_crosses_4kb(burst))

            actual_addresses.extend(
                burst.addr + 4 * beat
                for beat in range(burst.issued_beats)
            )

        self.assertEqual(
            actual_addresses,
            expected_addresses(config),
        )


if __name__ == "__main__":
    unittest.main()