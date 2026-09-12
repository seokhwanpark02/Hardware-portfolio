module control_1(/*AUTARG*/
   // Outputs
   opcode, rd, rs1, rs2, imm, branch_target, we,
   // Inputs
   instr
   );
   input logic [17:0] instr;

   output logic [3:0] opcode;
   output logic [3:0] rd, rs1, rs2;
   output logic [3:0] imm;
   output logic [5:0] branch_target;
   output logic       we;

   always_comb begin
      opcode = instr[17:14];
      rd = 4'b0;
      rs1 = 4'b0;
      rs2 = 4'b0;
      imm = 4'b0;
      branch_target = 6'b0;
      we = 0;

      case (opcode)
         4'b0001: begin // L-type (lw)
            rd = instr[13:10];
            imm = instr[3:0];
            we = 1;
         end

         4'b0011: begin // R1-type (DIV)
            rd = instr[13:10];
            rs1 = instr[9:6];
            rs2 = instr[5:2];
            we = 1;
         end

         4'b0110: begin // R2-type (ADDI)
            rd = instr[13:10];
            rs1 = instr[9:6];
            imm = instr[3:0];
            we = 1;
         end

         4'b0010: begin // I 1-type (MOV)
            rd = instr[13:10];
            rs1 = instr[9:6];
            we = 1;
         end

         4'b0100, 4'b0101: begin // I 2-type (beq, slt)
            rs1 = instr[13:10];
            rs2 = instr[9:6];
            branch_target = instr[5:0];
            we = 0;
         end

         4'b0111: begin // I 3-type (beqi)
            rs1 = instr[13:10];
            imm = instr[9:6];
            branch_target = instr[5:0];
            we = 0;
         end

         default:
            we = 0;
      endcase
   end
endmodule
