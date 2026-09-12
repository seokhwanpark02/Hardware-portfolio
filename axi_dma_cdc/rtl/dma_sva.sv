module dma_sva (
    input logic        clk_mem,
    input logic        rst_mem_n,

    input logic        clk_acc,
    input logic        rst_acc_n,

    input logic [31:0] m_axi_araddr,
    input logic [7:0]  m_axi_arlen,
    input logic [2:0]  m_axi_arsize,
    input logic [1:0]  m_axi_arburst,
    input logic        m_axi_arvalid,
    input logic        m_axi_arready,

    input logic [31:0] m_axis_tdata,
    input logic        m_axis_tvalid,
    input logic        m_axis_tready,

    input logic        fifo_full,
    input logic        fifo_wr_en,

    input logic        fifo_empty,
    input logic        fifo_rd_en,

    input logic        final_handshake,
    input logic        done
);

    property p_ar_stable_while_stalled;
        @(posedge clk_mem)
        disable iff (!rst_mem_n)

        m_axi_arvalid && !m_axi_arready
        |=>
        m_axi_arvalid
        && $stable(m_axi_araddr)
        && $stable(m_axi_arlen)
        && $stable(m_axi_arsize)
        && $stable(m_axi_arburst);
    endproperty

    A1_AR_STABLE:
        assert property (
            p_ar_stable_while_stalled
        )
        else $error(
            "A1: AXI AR changed while stalled"
        );


    property p_axis_stable_while_stalled;
        @(posedge clk_acc)
        disable iff (!rst_acc_n)

        m_axis_tvalid && !m_axis_tready
        |=>
        m_axis_tvalid
        && $stable(m_axis_tdata);
    endproperty

    A2_AXIS_STABLE:
        assert property (
            p_axis_stable_while_stalled
        )
        else $error(
            "A2: AXIS data changed while stalled"
        );


    property p_no_fifo_write_when_full;
        @(posedge clk_mem)
        disable iff (!rst_mem_n)

        fifo_full
        |->
        !fifo_wr_en;
    endproperty

    A3_NO_WRITE_WHEN_FULL:
        assert property (
            p_no_fifo_write_when_full
        )
        else $error(
            "A3: FIFO write attempted while full"
        );


    property p_no_fifo_read_when_empty;
        @(posedge clk_acc)
        disable iff (!rst_acc_n)

        fifo_empty
        |->
        !fifo_rd_en;
    endproperty

    A4_NO_READ_WHEN_EMPTY:
        assert property (
            p_no_fifo_read_when_empty
        )
        else $error(
            "A4: FIFO read attempted while empty"
        );


    property p_done_after_final_handshake;
        @(posedge clk_acc)
        disable iff (!rst_acc_n)

        $rose(done)
        |->
        $past(final_handshake);
    endproperty

    A5_DONE_AFTER_FINAL:
        assert property (
            p_done_after_final_handshake
        )
        else $error(
            "A5: DONE rose without final handshake"
        );

endmodule
