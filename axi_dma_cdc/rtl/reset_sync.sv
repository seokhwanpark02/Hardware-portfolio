/* verilator lint_off SYNCASYNCNET */
module reset_sync (
    input  logic clk,
    input  logic arst_n,
    output logic srst_n
);

    (* ASYNC_REG = "TRUE" *)
    logic sync_ff1_q;

    (* ASYNC_REG = "TRUE" *)
    logic sync_ff2_q;

    always_ff @(posedge clk or negedge arst_n) begin
        if (!arst_n) begin
            sync_ff1_q <= 1'b0;
            sync_ff2_q <= 1'b0;
        end else begin
            sync_ff1_q <= 1'b1;
            sync_ff2_q <= sync_ff1_q;
        end
    end

    assign srst_n = sync_ff2_q;

/* verilator lint_on SYNCASYNCNET */
endmodule
