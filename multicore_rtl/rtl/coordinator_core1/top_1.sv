module top_1 (
    input  logic       clk,
    input  logic       reset,

    input  logic [7:0] image1,
    input  logic [7:0] image2,
    input  logic [7:0] image3,
    input  logic [7:0] image4,
    input  logic [7:0] image5,
    input  logic [7:0] image6,
    input  logic [7:0] image7,
    input  logic [7:0] image8,
    input  logic [7:0] image9,

    if_1.cpu1_side     if1, // CPU1 - CPU2
    if_3.cpu1_side     if3  // CPU1 - CPU4
);

    //from interface1
    wire [7:0] end_signal2 = if1.end_signal2;
    wire [7:0] end_signal3 = if1.end_signal3;
    wire [7:0] end_signal5 = if1.end_signal5;
    wire [7:0] end_signal6 = if1.end_signal6;
    wire [7:0] end_signal8 = if1.end_signal8;
    wire [7:0] end_signal9 = if1.end_signal9;

    wire [7:0] end_signal4 = if3.end_signal4;
    wire [7:0] end_signal7 = if3.end_signal7;

    logic [5:0]  pc;
    logic [17:0] instr;
    logic [3:0]  opcode, rd, rs1, rs2, imm;
    logic [5:0]  branch_target;
    logic        we;
    logic [7:0]  rs1_data, rs2_data, result;
    logic        branch_taken;

    logic [7:0] done;
    logic [7:0] image_data1;
    logic [7:0] image_data2;
    logic [7:0] image_data3;
    logic [7:0] image_data4;
    logic [7:0] image_data5;
    logic [7:0] image_data6;
    logic [7:0] image_data7;
    logic [7:0] image_data8;
    logic [7:0] image_data9;

    logic [7:0] end_signal_total;
    logic [7:0] new_image_data1;

    pc_counter_1 u_pc_counter1 (
        .clk          (clk),
        .reset        (reset),
        .branch_taken (branch_taken),
        .branch_target(branch_target),
        .pc           (pc)
    );

    instruction_mem_1 u_instruction_mem1 (
        .pc    (pc),
        .instr (instr)
    );

    control_1 u_control1 (
        .instr         (instr),
        .opcode        (opcode),
        .rd            (rd),
        .rs1           (rs1),
        .rs2           (rs2),
        .imm           (imm),
        .branch_target (branch_target),
        .we            (we)
    );

    regfile_1 u_regfile1 (
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
        .done            (done),
        .image_data1     (image_data1),
        .image_data2     (image_data2),
        .image_data3     (image_data3),
        .image_data4     (image_data4),
        .image_data5     (image_data5),
        .image_data6     (image_data6),
        .image_data7     (image_data7),
        .image_data8     (image_data8),
        .image_data9     (image_data9),
        .new_image_data1 (new_image_data1)
    );

    alu_1 u_alu1 (
        .opcode           (opcode),
        .rs1_data         (rs1_data),
        .rs2_data         (rs2_data),
        .imm              (imm),
        .image1           (image1),
        .image2           (image2),
        .image3           (image3),
        .image4           (image4),
        .image5           (image5),
        .image6           (image6),
        .image7           (image7),
        .image8           (image8),
        .image9           (image9),
        .end_signal_total (end_signal_total),
        .result           (result),
        .branch_taken     (branch_taken)
    );

    // end_signal
    assign end_signal_total = {8{
        (end_signal2 == 8'd1) &&
        (end_signal3 == 8'd1) &&
        (end_signal4 == 8'd1) &&
        (end_signal5 == 8'd1) &&
        (end_signal6 == 8'd1) &&
        (end_signal7 == 8'd1) &&
        (end_signal8 == 8'd1) &&
        (end_signal9 == 8'd1)
    }};

    // ---- CPU2 ----
    assign if1.done             = done;
    assign if1.image_data1      = image_data1;
    assign if1.image_data2      = image_data2;
    assign if1.image_data3      = image_data3;
    assign if1.image_data5      = image_data5;
    assign if1.image_data6      = image_data6;
    assign if1.new_image_data1  = new_image_data1;
    assign if1.end_signal_total = end_signal_total;

    // ---- CPU4 ----
    assign if3.done             = done;
    assign if3.image_data1      = image_data1;
    assign if3.image_data4      = image_data4;
    assign if3.image_data7      = image_data7;
    assign if3.image_data8      = image_data8;
    assign if3.image_data9      = image_data9;
    assign if3.end_signal_total = end_signal_total;

`ifdef ENABLE_SVA

    // ---------------------------------------------------------
    // SVA: 9-core barrier synchronization checks
    // ---------------------------------------------------------

    wire all_done_sva;

    assign all_done_sva =
        (end_signal2 == 8'd1) &&
        (end_signal3 == 8'd1) &&
        (end_signal4 == 8'd1) &&
        (end_signal5 == 8'd1) &&
        (end_signal6 == 8'd1) &&
        (end_signal7 == 8'd1) &&
        (end_signal8 == 8'd1) &&
        (end_signal9 == 8'd1);


    // A1.
    // global completion이 올라왔으면 모든 worker core가 완료된 상태여야 한다.
    A_TOTAL_REQUIRES_ALL_DONE:
    assert property (
        @(posedge clk)
        disable iff (reset)
        (end_signal_total == 8'hFF) |-> all_done_sva
    )
    else $error("SVA_FAIL: end_signal_total asserted before all cores completed");


    // A2.
    // 모든 worker core가 완료되면 global completion이 반드시 발생해야 한다.
    A_ALL_DONE_RAISES_TOTAL:
    assert property (
        @(posedge clk)
        disable iff (reset)
        all_done_sva |-> (end_signal_total == 8'hFF)
    )
    else $error("SVA_FAIL: all cores completed but end_signal_total not asserted");


    // A3.
    // 각 completion signal은 0 또는 1만 가져야 한다.
    // ADDI가 중복 실행되어 2 이상이 되는 control-flow 오류 등을 검출한다.
    A_END_SIGNAL_LEGAL_VALUE:
    assert property (
        @(posedge clk)
        disable iff (reset)

        ((end_signal2 == 8'd0) || (end_signal2 == 8'd1)) &&
        ((end_signal3 == 8'd0) || (end_signal3 == 8'd1)) &&
        ((end_signal4 == 8'd0) || (end_signal4 == 8'd1)) &&
        ((end_signal5 == 8'd0) || (end_signal5 == 8'd1)) &&
        ((end_signal6 == 8'd0) || (end_signal6 == 8'd1)) &&
        ((end_signal7 == 8'd0) || (end_signal7 == 8'd1)) &&
        ((end_signal8 == 8'd0) || (end_signal8 == 8'd1)) &&
        ((end_signal9 == 8'd0) || (end_signal9 == 8'd1))
    )
    else $error("SVA_FAIL: core completion signal has illegal value");


    // A4.
    // reset이 걸리면 다음 cycle에는 global completion이 clear되어야 한다.
    A_RESET_CLEARS_TOTAL:
    assert property (
        @(posedge clk)
        reset |=> (end_signal_total == 8'd0)
    )
    else $error("SVA_FAIL: end_signal_total was not cleared after reset");

`endif

endmodule
