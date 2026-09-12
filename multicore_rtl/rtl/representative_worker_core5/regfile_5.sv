module regfile_5 (/*AUTARG*/
   // Outputs
   rs1_data, rs2_data, new_image_data5, end_signal5,
   // Inputs
   clk, reset, rd, rs1, rs2, result, we, pc
   );
   input logic              clk;
   input logic              reset;
   input logic [3:0]        rd, rs1, rs2;
   input logic [7:0]        result;
   input logic              we;
   input logic [5:0]        pc;

   output logic [7:0]       rs1_data, rs2_data;
   output logic [7:0]       new_image_data5;
   output logic [7:0]       end_signal5;

   logic [7:0]              regs[0:15];
   integer                  i;

   //write register
   always_ff@(posedge clk) begin
      if (reset || pc == 59) begin
         for (i = 0; i < 16; i = i + 1)
            regs[i] <= 8'd0;
      end
      else if (we) begin
         regs[rd] <= result;
      end

   end

   //read register
   assign rs1_data = regs[rs1];
   assign rs2_data = regs[rs2];

   //output imagedata
   assign end_signal5 = regs[9];
   assign new_image_data5 = regs[8];

endmodule // regfile
