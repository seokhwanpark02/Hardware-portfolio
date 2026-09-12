`include "top_1.sv"
`include "top_2.sv"
`include "top_3.sv"
`include "top_4.sv"
`include "top_5.sv"
`include "top_6.sv"
`include "top_7.sv"
`include "top_8.sv"
`include "top_9.sv"

`include "if_1.sv"
`include "if_2.sv"
`include "if_3.sv"
`include "if_4.sv"
`include "if_5.sv"
`include "if_6.sv"
`include "if_7.sv"
`include "if_8.sv"
`include "if_9.sv"
`include "if_10.sv"
`include "if_11.sv"
`include "if_12.sv"

module system_top (
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

    output logic [7:0] new_image_data1,
    output logic [7:0] new_image_data2,
    output logic [7:0] new_image_data3,
    output logic [7:0] new_image_data4,
    output logic [7:0] new_image_data5,
    output logic [7:0] new_image_data6,
    output logic [7:0] new_image_data7,
    output logic [7:0] new_image_data8,
    output logic [7:0] new_image_data9,
    output logic [7:0] end_signal_total
);

    if_1 i1 ();  if_2 i2 ();  if_3 i3 ();  if_4 i4 ();
    if_5 i5 ();  if_6 i6 ();  if_7 i7 ();  if_8 i8 ();
    if_9 i9 ();  if_10 i10 ();  if_11 i11 ();  if_12 i12 ();

    top_1 u_cpu1 (
        .clk   (clk),
        .reset (reset),

        .if1   (i1),
        .if3   (i3),

        .image1 (image1),
        .image2 (image2),
        .image3 (image3),
        .image4 (image4),
        .image5 (image5),
        .image6 (image6),
        .image7 (image7),
        .image8 (image8),
        .image9 (image9)
    );

    top_2 u_cpu2 (
        .clk   (clk),
        .reset (reset),

        .if1   (i1),
        .if2   (i2),
        .if4   (i4)
    );

    top_3 u_cpu3 (
        .clk   (clk),
        .reset (reset),

        .if2   (i2),
        .if5   (i5)
    );

    top_4 u_cpu4 (
        .clk   (clk),
        .reset (reset),

        .if3   (i3),
        .if6   (i6),
        .if8   (i8)
    );

    top_5 u_cpu5 (
        .clk   (clk),
        .reset (reset),

        .if4   (i4),
        .if6   (i6),
        .if7   (i7),
        .if9   (i9)
    );

    top_6 u_cpu6 (
        .clk   (clk),
        .reset (reset),

        .if5   (i5),
        .if7   (i7),
        .if10  (i10)
    );

    top_7 u_cpu7 (
        .clk   (clk),
        .reset (reset),

        .if8   (i8),
        .if11  (i11)
    );

    top_8 u_cpu8 (
        .clk   (clk),
        .reset (reset),

        .if9   (i9),
        .if11  (i11),
        .if12  (i12)
    );

    top_9 u_cpu9 (
        .clk   (clk),
        .reset (reset),

        .if10  (i10),
        .if12  (i12),

        .new_image_data1 (new_image_data1),
        .new_image_data2 (new_image_data2),
        .new_image_data3 (new_image_data3),
        .new_image_data4 (new_image_data4),
        .new_image_data5 (new_image_data5),
        .new_image_data6 (new_image_data6),
        .new_image_data7 (new_image_data7),
        .new_image_data8 (new_image_data8),
        .new_image_data9 (new_image_data9),
        .end_signal_total (end_signal_total)
    );

endmodule