module top_5 (
   input logic clk,
   input logic reset,

   if_4.cpu5_side if4,
   if_6.cpu5_side if6,
   if_7.cpu5_side if7,
   if_9.cpu5_side if9
   );

   logic [7:0] image_data2;
   logic [7:0] image_data4;
   logic [7:0] image_data5;
   logic [7:0] image_data6;
   logic [7:0] image_data8;
   logic [7:0] done;
   logic [7:0] end_signal_total;
   logic [7:0] end_signal5;
   logic [7:0] new_image_data5;
   logic [7:0] end_signal8;

   assign done             = if4.done;
   assign image_data2      = if4.image_data2;
   assign image_data5      = if4.image_data5;
   assign end_signal_total = if4.end_signal_total;

   // from if6 (from CPU4)
   assign image_data4 = if6.image_data4;

   // from if7 (from CPU6)
   assign image_data6 = if7.image_data6;

   // from if9 (from CPU8)
   assign end_signal8 = if9.end_signal8;
   assign image_data8 = if9.image_data8;

   // to if4 (CPU2)
   assign if4.end_signal5 = end_signal5;
   assign if4.end_signal8 = end_signal8;

   // to if6 (CPU4)
   assign if6.image_data5 = image_data5;

   // to if7 (CPU6)
   assign if7.image_data5 = image_data5;

   // to if9 (CPU8)
   assign if9.done             = done;
   assign if9.image_data5      = image_data5;
   assign if9.new_image_data5  = new_image_data5;
   assign if9.end_signal_total = end_signal_total;

   logic [5:0] pc;
   logic [17:0] instr;

   logic [3:0] opcode;
   logic [3:0] rd, rs1, rs2;
   logic [3:0] imm;
   logic [5:0] branch_target;
   logic we;

   logic [7:0] rs1_data, rs2_data;
   logic [7:0] result;
   logic branch_taken;

   pc_counter_5 u_pc_counter_5 (
      .pc            (pc[5:0]),
      .clk           (clk),
      .reset         (reset),
      .branch_taken  (branch_taken),
      .branch_target (branch_target[5:0])
      );

   instruction_mem_5 u_instruction_mem_5 (
      .instr (instr[17:0]),
      .pc    (pc[5:0])
      );

   regfile_5 u_regfile_5 (
      .clk             (clk),
      .reset           (reset),
      .rd              (rd),
      .rs1             (rs1),
      .rs2             (rs2),
      .result          (result),
      .we              (we),
      .pc              (pc),
      .rs1_data        (rs1_data),
      .rs2_data        (rs2_data),
      .new_image_data5 (new_image_data5),
      .end_signal5     (end_signal5)
      );

   alu_5 u_alu_5 (
      .opcode           (opcode),
      .rs1_data         (rs1_data),
      .rs2_data         (rs2_data),
      .imm              (imm),
      .image_data2      (image_data2),
      .image_data4      (image_data4),
      .image_data5      (image_data5),
      .image_data6      (image_data6),
      .image_data8      (image_data8),
      .done             (done),
      .end_signal_total (end_signal_total),
      .result           (result),
      .branch_taken     (branch_taken)
      );

   control_5 u_control_5 (
      .instr         (instr),
      .opcode        (opcode),
      .rd            (rd),
      .rs1           (rs1),
      .rs2           (rs2),
      .imm           (imm),
      .branch_target (branch_target),
      .we            (we)
      );

endmodule
