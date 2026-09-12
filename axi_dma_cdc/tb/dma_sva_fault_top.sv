module dma_sva_fault_top (
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

    dma_sva u_dma_sva (
        .clk_mem          (clk_mem),
        .rst_mem_n        (rst_mem_n),

        .clk_acc          (clk_acc),
        .rst_acc_n        (rst_acc_n),

        .m_axi_araddr     (m_axi_araddr),
        .m_axi_arlen      (m_axi_arlen),
        .m_axi_arsize     (m_axi_arsize),
        .m_axi_arburst    (m_axi_arburst),
        .m_axi_arvalid    (m_axi_arvalid),
        .m_axi_arready    (m_axi_arready),

        .m_axis_tdata     (m_axis_tdata),
        .m_axis_tvalid    (m_axis_tvalid),
        .m_axis_tready    (m_axis_tready),

        .fifo_full        (fifo_full),
        .fifo_wr_en       (fifo_wr_en),

        .fifo_empty       (fifo_empty),
        .fifo_rd_en       (fifo_rd_en),

        .final_handshake  (final_handshake),
        .done             (done)
    );

endmodule
