module instruction_mem_1 (/*AUTOARG*/
   // Outputs
   instr,
   // Inputs
   pc
   );
   input  logic [5:0] pc;
   output logic [17:0] instr;

   always_comb begin
      case (pc)
         6'd0 : instr = 18'b0001_0001_0000_000001; //LW R1, image_data_1
         6'd1 : instr = 18'b0001_0010_0000_000010; //LW R2, image_data_2
         6'd2 : instr = 18'b0001_0011_0000_000011; //LW R3, image_data_3
         6'd3 : instr = 18'b0001_0100_0000_000100; //LW R4, image_data_4
         6'd4 : instr = 18'b0001_0101_0000_000101; //LW R5, image_data_5
         6'd5 : instr = 18'b0001_0110_0000_000110; //LW R6, image_data_6
         6'd6 : instr = 18'b0001_0111_0000_000111; //LW R7, image_data_7
         6'd7 : instr = 18'b0001_1000_0000_001000; //LW R8, image_data_8
         6'd8 : instr = 18'b0001_1001_0000_001001; //LW R9, image_data_9
         6'd9 : instr = 18'b0110_0000_0000_000001; //ADDI R0, R0, 1
         
         6'd10: instr = 18'b0001_1010_0000_000001; //LW R10, image_data_1
         6'd11: instr = 18'b0001_1011_0000_000010; //LW R11, image_data_2
         6'd12: instr = 18'b0001_1100_0000_000100; //LW R12, image_data_4
         
         6'd13: instr = 18'b0101_1010_1011_010010; //SLT R10, R11, pc=18
         6'd14: instr = 18'b0010_1101_1011_000000; //MOV R13, R11 
         6'd15: instr = 18'b0010_1011_1010_000000; //MOV R11, R10
         6'd16: instr = 18'b0010_1010_1101_000000; //MOV R10, R13
         6'd17: instr = 18'b0100_1111_1111_010010; //BEQ R15, R15, pc=18 stall
         
         6'd18: instr = 18'b0101_1010_1100_010111; //SLT R10, R12, pc=23 
         6'd19: instr = 18'b0010_1101_1100_000000; //MOV R13, R12
         6'd20: instr = 18'b0010_1100_1010_000000; //MOV R12, R10
         6'd21: instr = 18'b0010_1010_1101_000000; //SLT R10, R13
         6'd22: instr = 18'b0100_1111_1111_010111; //BEQ R15, R15, pc=23 stall 
         
         6'd23: instr = 18'b0101_1011_1100_011100; //SLT R11, R12, pc=28
         6'd24: instr = 18'b0010_1101_1100_000000; //MOV R13, R12
	      6'd25: instr = 18'b0010_1100_1011_000000; //MOV R12, R11
	      6'd26: instr = 18'b0010_1011_1101_000000; //MOV R11. R13
         6'd27: instr = 18'b0100_1111_1111_011100; //BEQ R15, R15, pc=28 stall
	      
         6'd28: instr = 18'b0001_1111_0000_001010; //LW R15, END
         6'd29: instr = 18'b0111_1111_0000_011100; //BEQI R15, 0, pc=28

         6'd30: instr = 18'b0011_1110_1011_0001_00; //DIV R14, R11, R1
         6'd31: instr = 18'b0100_1111_1111_000000; //BEQ R15, R15, pc=0
         default: instr = 18'b0000_0000_0000_0000_00;
      endcase
   end

endmodule // instruction_mem


