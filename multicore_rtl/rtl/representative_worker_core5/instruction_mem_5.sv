module instruction_mem_5 (/*AUTOARG*/
   // Outputs
   instr,
   // Inputs
   pc
   );
   input  logic [5:0] pc;
   output logic [17:0] instr;

   always_comb begin
      case (pc)
         6'd0 : instr = 18'b0001_0000_0000_000110; //LW  R0, DONE
         6'd1 : instr = 18'b0111_0000_0000_000000; //BEQi R0, 0, pc=0
	
         6'd2 : instr = 18'b0001_0001_0000_000001; //LW R1, image_data_2
         6'd3 : instr = 18'b0001_0010_0000_000010; //LW R2, image_data_5
         6'd4 : instr = 18'b0001_0011_0000_000011; //LW R3, image_data_4
         6'd5 : instr = 18'b0001_0100_0000_000100; //LW R4, image_data_6
         6'd6 : instr = 18'b0001_0101_0000_000101; //LW R5, image_data_8
         6'd7 : instr = 18'b0001_0110_0000_000010; //LW R6, image_data_5
         6'd8 : instr = 18'b0010_1111_1111_001001; //BEQ R15, R15, pc=9 stall
         
         6'd9 : instr = 18'b0101_0001_0010_001110; //SLT R1, R2, pc=14
         6'd10: instr = 18'b0010_0111_0010_000000; //MOV R7, R2
         6'd11: instr = 18'b0010_0010_0001_000000; //MOV R2, R1
         6'd12: instr = 18'b0010_0001_0111_000000; //MOV R1, R7
         6'd13: instr = 18'b0100_1111_1111_001110; //BEQ R15, R15, pc=14 stall 
         
         6'd14: instr = 18'b0101_0001_0011_010011; //SLT R1, R3, pc=19
         6'd15: instr = 18'b0010_0111_0011_000000; //MOV R7, R3
         6'd16: instr = 18'b0010_0011_0001_000000; //MOV R3, R1 
         6'd17: instr = 18'b0010_0001_0111_000000; //MOV R1, R7
         6'd18: instr = 18'b0100_1111_1111_010011; //BEQ R15, R15, pc=19 stall
         
         6'd19: instr = 18'b0101_0001_0100_011000; //SLT R1, R4, pc=24
         6'd20: instr = 18'b0010_0111_0100_000000; //MOV R7, R4 
         6'd21: instr = 18'b0010_0100_0001_000000; //MOV R4, R1
         6'd22: instr = 18'b0010_0001_0111_000000; //MOV R1, R7
	      6'd23: instr = 18'b0100_1111_1111_011000; //BEQ R15, R15, pc=24 stall
         
         6'd24: instr = 18'b0101_0001_0101_011101; //SLT R1, R5, pc=29
         6'd25: instr = 18'b0010_0111_0101_000000; //MOV R7, R5
         6'd26: instr = 18'b0010_0101_0001_000000; //MOV R5, R1
	      6'd27: instr = 18'b0010_0001_0111_000000; //MOV R1, R7
         6'd28: instr = 18'b0100_1111_1111_011101; //BEQ R15, R15, pc=29 stall 
         
         6'd29: instr = 18'b0101_0010_0011_100010; //SLT R2, R3, pc=34
         6'd30: instr = 18'b0010_0111_0011_000000; //MOV R7, R3
	      6'd31: instr = 18'b0010_0011_0010_000000; //MOV R3, R2
         6'd32: instr = 18'b0010_0010_0111_000000; //MOV R2, R7
	      6'd33: instr = 18'b0100_1111_1111_100010; //BEQ R15, R15, pc=34 stall
	      
         6'd34: instr = 18'b0101_0010_0100_100111; //SLT R2, R4, pc=39
         6'd35: instr = 18'b0010_0111_0100_000000; //MOV R7, R4
	      6'd36: instr = 18'b0010_0100_0010_000000; //MOV R4, R2
         6'd37: instr = 18'b0010_0010_0111_000000; //MOV R2, R7
         6'd38: instr = 18'b0100_1111_1111_100111; //BEQ R15, R15, pc=39 stall
	      
         6'd39: instr = 18'b0101_0010_0101_101100; //SLT R2, R5, pc=44
         6'd40: instr = 18'b0010_0111_0101_000000; //MOV R7, R5
         6'd41: instr = 18'b0010_0101_0010_000000; //MOV R5, R2
         6'd42: instr = 18'b0010_0010_0111_000000; //MOV R2, R7
         6'd43: instr = 18'b0100_1111_1111_101100; //BEQ R15, R15, pc=44 stall

         6'd44: instr = 18'b0101_0011_0100_110001; //SLT R3, R4, pc=49
         6'd45: instr = 18'b0010_0111_0100_000000; //MOV R7, R4
         6'd46: instr = 18'b0010_0100_0011_000000; //MOV R4, R3
         6'd47: instr = 18'b0010_0011_0111_000000; //MOV R3, R7
         6'd48: instr = 18'b0100_1111_1111_110001; //BEQ R15, R15, pc=49 stall

         6'd49: instr = 18'b0101_0011_0101_110110; //SLT R3, R5, pc=54
         6'd50: instr = 18'b0010_0111_0101_000000; //MOV R7, R5
         6'd51: instr = 18'b0010_0101_0011_000000; //MOV R5, R3
         6'd52: instr = 18'b0010_0011_0111_000000; //MOV R3, R7
         6'd53: instr = 18'b0100_1111_1111_110110; //BEQ R15, R15, pc=54 stall

         6'd54: instr = 18'b0110_1001_1001_000001; //ADDi R9, R9, 1
         6'd55: instr = 18'b0100_1111_1111_111000; //BEQ R15, R15, pc=56 stall
         
         6'd56: instr = 18'b0001_1010_0000_000111; //LW, R10 end_sig_total
         6'd57: instr = 18'b0111_1010_0000_111000; //BEQi R10, 0, pc=56
         
         6'd58: instr = 18'b0011_1000_0110_0011_00; //CIV R8, R6, R3

         6'd59: instr = 18'b0100_1011_1011_000000; //BEQ R11, R11, pc=0
         default: instr = 18'b0000_0000_0000_0000_00;
      endcase
   end

endmodule // instruction_mem
