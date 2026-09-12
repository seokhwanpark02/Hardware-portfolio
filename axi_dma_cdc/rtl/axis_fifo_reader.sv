module axis_fifo_reader (
    input  logic [32:0] fifo_rd_data_i,
    input  logic        fifo_empty_i,

    output logic        fifo_rd_en_o,

    output logic [31:0] m_axis_tdata,
    output logic        m_axis_tvalid,
    input  logic        m_axis_tready,

    output logic        final_handshake_o
);

    always_comb begin
        m_axis_tdata =
            fifo_rd_data_i[31:0];

        m_axis_tvalid =
            !fifo_empty_i;

        fifo_rd_en_o =
            m_axis_tvalid
            && m_axis_tready;

        final_handshake_o =
            fifo_rd_en_o
            && fifo_rd_data_i[32];
    end

endmodule
