module pc_counter_1 (/*AUTARG*/
   // Outputs
   pc,
   // Inputs
   clk, reset, branch_taken, branch_target
   );
   input logic          clk;
   input logic          reset;
   input logic          branch_taken;
   input logic [5:0]    branch_target;

   output logic [5:0]   pc;

   always_ff @(posedge clk) begin
      if (reset) begin
         pc <= 6'd0;
      end else if (branch_taken) begin
         pc <= branch_target;
      end else begin
         pc <= pc + 6'd1;
      end
   end

endmodule // pc
