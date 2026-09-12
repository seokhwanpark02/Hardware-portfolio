import cocotb
from cocotb.triggers import Timer


def value(signal):
    return int(signal.value)


async def settle():
    await Timer(1, unit="ns")


@cocotb.test()
async def test_axis_fifo_reader(dut):
    dut.fifo_rd_data_i.value = 0
    dut.fifo_empty_i.value = 1
    dut.m_axis_tready.value = 0

    await settle()

    # Empty FIFO
    assert value(dut.m_axis_tvalid) == 0
    assert value(dut.fifo_rd_en_o) == 0
    assert value(dut.final_handshake_o) == 0

    # Empty 상태에서는 TREADY가 있어도 read 금지
    dut.m_axis_tready.value = 1
    await settle()

    assert value(dut.m_axis_tvalid) == 0
    assert value(dut.fifo_rd_en_o) == 0
    assert value(dut.final_handshake_o) == 0

    # 일반 데이터가 있지만 downstream stall
    normal_data = 0x1234_5678

    dut.fifo_rd_data_i.value = normal_data
    dut.fifo_empty_i.value = 0
    dut.m_axis_tready.value = 0

    await settle()

    assert value(dut.m_axis_tvalid) == 1
    assert value(dut.m_axis_tdata) == normal_data
    assert value(dut.fifo_rd_en_o) == 0
    assert value(dut.final_handshake_o) == 0

    # stall을 여러 사이클 상당 시간 유지
    for _ in range(10):
        await settle()

        assert value(dut.m_axis_tvalid) == 1
        assert value(dut.m_axis_tdata) == normal_data
        assert value(dut.fifo_rd_en_o) == 0
        assert value(dut.final_handshake_o) == 0

    # 일반 데이터 handshake
    dut.m_axis_tready.value = 1
    await settle()

    assert value(dut.m_axis_tvalid) == 1
    assert value(dut.m_axis_tdata) == normal_data
    assert value(dut.fifo_rd_en_o) == 1
    assert value(dut.final_handshake_o) == 0

    # 마지막 데이터지만 아직 downstream stall
    final_data = 0xCAFE_BABE

    dut.fifo_rd_data_i.value = (
        (1 << 32) | final_data
    )
    dut.m_axis_tready.value = 0

    await settle()

    assert value(dut.m_axis_tvalid) == 1
    assert value(dut.m_axis_tdata) == final_data
    assert value(dut.fifo_rd_en_o) == 0
    assert value(dut.final_handshake_o) == 0

    # 마지막 데이터가 실제 전달되는 순간
    dut.m_axis_tready.value = 1
    await settle()

    assert value(dut.m_axis_tvalid) == 1
    assert value(dut.m_axis_tdata) == final_data
    assert value(dut.fifo_rd_en_o) == 1
    assert value(dut.final_handshake_o) == 1

    # final metadata가 없는 다음 데이터에서는 즉시 해제
    dut.fifo_rd_data_i.value = 0x0BAD_F00D
    await settle()

    assert value(dut.final_handshake_o) == 0

    dut._log.info(
        "AXIS empty/stall/handshake/final: PASS"
    )
    dut._log.info(
        "AXI4-Stream FIFO reader: ALL PASS"
    )
