module toggle_pulse_cdc (
    input  logic src_clk,
    input  logic src_rst_n,
    input  logic src_pulse_i,

    input  logic dst_clk,
    input  logic dst_rst_n,
    output logic dst_pulse_o
);

    logic src_toggle_q;

    (* ASYNC_REG = "TRUE" *)
    logic dst_sync_ff1_q;

    (* ASYNC_REG = "TRUE" *)
    logic dst_sync_ff2_q;

    logic dst_sync_delay_q;

    always_ff @(posedge src_clk or negedge src_rst_n) begin
        if (!src_rst_n) begin
            src_toggle_q <= 1'b0;
        end else if (src_pulse_i) begin
            src_toggle_q <= ~src_toggle_q;
        end
    end

    always_ff @(posedge dst_clk or negedge dst_rst_n) begin
        if (!dst_rst_n) begin
            dst_sync_ff1_q  <= 1'b0;
            dst_sync_ff2_q  <= 1'b0;
            dst_sync_delay_q <= 1'b0;
        end else begin
            dst_sync_ff1_q
                <= src_toggle_q;

            dst_sync_ff2_q
                <= dst_sync_ff1_q;

            dst_sync_delay_q
                <= dst_sync_ff2_q;
        end
    end

    assign dst_pulse_o =
        dst_sync_ff2_q
        ^ dst_sync_delay_q;

endmodule
