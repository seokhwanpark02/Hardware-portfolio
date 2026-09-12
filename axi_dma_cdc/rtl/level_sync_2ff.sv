module level_sync_2ff (
    input  logic dst_clk,
    input  logic dst_rst_n,

    input  logic async_level_i,
    output logic sync_level_o
);

    (* ASYNC_REG = "TRUE" *)
    logic sync_ff1_q;

    (* ASYNC_REG = "TRUE" *)
    logic sync_ff2_q;

    always_ff @(posedge dst_clk or negedge dst_rst_n) begin
        if (!dst_rst_n) begin
            sync_ff1_q <= 1'b0;
            sync_ff2_q <= 1'b0;
        end else begin
            sync_ff1_q <= async_level_i;
            sync_ff2_q <= sync_ff1_q;
        end
    end

    assign sync_level_o = sync_ff2_q;

endmodule
