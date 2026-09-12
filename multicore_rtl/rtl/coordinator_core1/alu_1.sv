module alu_1 (/*AUTARG*/
   // Outputs
   result, branch_taken,
   // Inputs
   opcode, rs1_data, rs2_data, imm, image1, image2, image3, image4, image5, image6, image7, image8, image9, end_signal_total
   );
   input logic [3:0] opcode;
   input logic [7:0] rs1_data;
   input logic [7:0] rs2_data;
   input logic [3:0] imm;

   input logic [7:0] image1;
   input logic [7:0] image2;
   input logic [7:0] image3;
   input logic [7:0] image4;
   input logic [7:0] image5;
   input logic [7:0] image6;
   input logic [7:0] image7;
   input logic [7:0] image8;
   input logic [7:0] image9;
   input logic [7:0] end_signal_total;

   output logic [7:0] result;
   output logic       branch_taken;

   always_comb begin
      result = 8'b0;
      branch_taken = 1'b0;
      case (opcode)
         4'b0001: begin // lw
            case (imm)
            4'd1: result = image1;
            4'd2: result = image2;
            4'd3: result = image3;
            4'd4: result = image4;
            4'd5: result = image5;
            4'd6: result = image6;
            4'd7: result = image7;
            4'd8: result = image8;
            4'd9: result = image9;
            4'd10: result = end_signal_total;
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
