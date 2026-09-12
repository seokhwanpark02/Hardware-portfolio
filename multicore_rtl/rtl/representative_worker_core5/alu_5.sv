module alu_5 (/*AUTARG*/
   // Outputs
   result, branch_taken,
   // Inputs
   opcode, rs1_data, rs2_data, imm, image_data2, image_data4, image_data5, image_data6, image_data8, done, end_signal_total
   );
   input logic [3:0] opcode;
   input logic [7:0] rs1_data;
   input logic [7:0] rs2_data;
   input logic [3:0] imm;

   input logic [7:0] image_data2;
   input logic [7:0] image_data4;
   input logic [7:0] image_data5;
   input logic [7:0] image_data6;
   input logic [7:0] image_data8;
   input logic [7:0] done;
   input logic [7:0] end_signal_total;

   output logic [7:0] result;
   output logic       branch_taken;

   always_comb begin
      result = 8'b0;
      branch_taken = 1'b0;
      case (opcode)
         4'b0001: begin // lw
            case (imm)
            4'd1: result = image_data2;
            4'd2: result = image_data5;
            4'd3: result = image_data4;
            4'd4: result = image_data6;
            4'd5: result = image_data8;
            4'd6: result = done;
            4'd7: result = end_signal_total;
               default: result = 8'd0;
            endcase
         end

         4'b0010: begin // mov
            result = rs1_data;
         end

         4'b0011: begin // div
            result = rs1_data/2 + rs2_data/2;
         end

         4'b0100: begin // beq
            if (rs1_data == rs2_data)
               branch_taken = 1'b1;
            else
               branch_taken = 1'b0;
         end

         4'b0101: begin // slt
            if (rs1_data > rs2_data)
               branch_taken = 1'b1;
            else
               branch_taken = 1'b0;
         end

         4'b0110: begin // ADDI
            result = rs1_data + {4'b0000, imm};
         end

         4'b0111: begin // beqi
            if (rs1_data == {4'b0000, imm})
               branch_taken = 1'b1;
            else
               branch_taken = 1'b0;
         end

         default: result = 8'd0;
      endcase
   end // always_comb

endmodule // alu
