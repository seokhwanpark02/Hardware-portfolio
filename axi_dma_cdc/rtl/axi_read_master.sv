module axi_read_master (
    input  logic        clk,
    input  logic        rst_n,

    input  logic        req_valid_i,
    output logic        req_ready_o,

    input  logic [31:0] req_addr_i,
    input  logic [4:0]  req_desired_beats_i,
    input  logic        req_desired_final_i,

    output logic [4:0]  req_accepted_beats_o,
    output logic        req_fifo_limited_o,

    input  logic [5:0]  fifo_free_slots_i,
    input  logic        fifo_full_i,

    output logic        fifo_wr_en_o,
    output logic [32:0] fifo_wr_data_o,

    output logic [31:0] m_axi_araddr_o,
    output logic [7:0]  m_axi_arlen_o,
    output logic [2:0]  m_axi_arsize_o,
    output logic [1:0]  m_axi_arburst_o,
    output logic        m_axi_arvalid_o,
    input  logic        m_axi_arready_i,

    input  logic [31:0] m_axi_rdata_i,
    input  logic [1:0]  m_axi_rresp_i,
    input  logic        m_axi_rlast_i,
    input  logic        m_axi_rvalid_i,
    output logic        m_axi_rready_o,

    output logic        ar_handshake_o,
    output logic        r_handshake_o,

    output logic        read_active_o,
    output logic        error_o
);

    typedef enum logic [1:0] {
        STATE_IDLE,
        STATE_SEND_AR,
        STATE_RECV_R,
        STATE_ERROR
    } state_t;

    localparam logic [1:0] AXI_RESP_OKAY = 2'b00;
    localparam logic [2:0] AXI_SIZE_4B   = 3'b010;
    localparam logic [1:0] AXI_BURST_INCR = 2'b01;

    state_t state_q;

    logic [4:0] burst_beats_q;
    logic [4:0] beats_received_q;
    logic       burst_final_q;

    logic       expected_last_beat;
    logic       r_protocol_ok;

    always_comb begin
        req_accepted_beats_o =
            req_desired_beats_i;

        if (
            fifo_free_slots_i
            < {1'b0, req_desired_beats_i}
        ) begin
            req_accepted_beats_o =
                fifo_free_slots_i[4:0];
        end

        req_ready_o =
            (state_q == STATE_IDLE)
            && !error_o
            && (req_desired_beats_i != 5'd0)
            && (fifo_free_slots_i != 6'd0);

        req_fifo_limited_o =
            req_valid_i
            && req_ready_o
            && (
                fifo_free_slots_i
                < {1'b0, req_desired_beats_i}
            );

        m_axi_arsize_o  = AXI_SIZE_4B;
        m_axi_arburst_o = AXI_BURST_INCR;

        m_axi_arvalid_o =
            (state_q == STATE_SEND_AR);

        m_axi_rready_o =
            (state_q == STATE_RECV_R)
            && !fifo_full_i
            && !error_o;

        ar_handshake_o =
            m_axi_arvalid_o
            && m_axi_arready_i;

        r_handshake_o =
            m_axi_rvalid_i
            && m_axi_rready_o;

        expected_last_beat =
            (
                beats_received_q + 5'd1
                == burst_beats_q
            );

        r_protocol_ok =
            (m_axi_rresp_i == AXI_RESP_OKAY)
            && (
                m_axi_rlast_i
                == expected_last_beat
            );

        fifo_wr_en_o =
            r_handshake_o
            && r_protocol_ok;

        fifo_wr_data_o = {
            burst_final_q
            && expected_last_beat,
            m_axi_rdata_i
        };

        read_active_o =
            (state_q == STATE_SEND_AR)
            || (state_q == STATE_RECV_R);
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state_q            <= STATE_IDLE;

            burst_beats_q      <= 5'd0;
            beats_received_q   <= 5'd0;
            burst_final_q      <= 1'b0;

            m_axi_araddr_o     <= 32'd0;
            m_axi_arlen_o      <= 8'd0;

            error_o            <= 1'b0;
        end else begin
            case (state_q)
                STATE_IDLE: begin
                    beats_received_q <= 5'd0;

                    if (
                        req_valid_i
                        && req_ready_o
                    ) begin
                        m_axi_araddr_o
                            <= req_addr_i;

                        m_axi_arlen_o
                            <= {
                                3'd0,
                                req_accepted_beats_o
                            } - 8'd1;

                        burst_beats_q
                            <= req_accepted_beats_o;

                        burst_final_q
                            <= req_desired_final_i
                            && (
                                req_accepted_beats_o
                                == req_desired_beats_i
                            );

                        state_q
                            <= STATE_SEND_AR;
                    end
                end

                STATE_SEND_AR: begin
                    if (ar_handshake_o) begin
                        beats_received_q
                            <= 5'd0;

                        state_q
                            <= STATE_RECV_R;
                    end
                end

                STATE_RECV_R: begin
                    if (r_handshake_o) begin
                        if (!r_protocol_ok) begin
                            error_o
                                <= 1'b1;

                            state_q
                                <= STATE_ERROR;
                        end else if (
                            expected_last_beat
                        ) begin
                            beats_received_q
                                <= 5'd0;

                            state_q
                                <= STATE_IDLE;
                        end else begin
                            beats_received_q
                                <= beats_received_q
                                + 5'd1;
                        end
                    end
                end

                STATE_ERROR: begin
                    state_q <= STATE_ERROR;
                end

                default: begin
                    state_q <= STATE_ERROR;
                    error_o <= 1'b1;
                end
            endcase
        end
    end

endmodule
