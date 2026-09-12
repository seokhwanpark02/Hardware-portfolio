module regfile_1 (/*AUTARG*/
   // Outputs
   rs1_data, rs2_data, done, image_data1, image_data2, image_data3,
   image_data4, image_data5, image_data6, image_data7, image_data8,
   image_data9, new_image_data1,
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
   output logic [7:0]       done;
   output logic [7:0]       image_data1;
   output logic [7:0]       image_data2;
   output logic [7:0]       image_data3;
   output logic [7:0]       image_data4;
   output logic [7:0]       image_data5;
   output logic [7:0]       image_data6;
   output logic [7:0]       image_data7;
   output logic [7:0]       image_data8;
   output logic [7:0]       image_data9;
   output logic [7:0]       new_image_data1;

   logic [7:0]              regs[0:15];
   integer                  i;

   //write register
   always_ff@(posedge clk) begin
      if (reset || pc == 31) begin
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
   assign done            = regs[0];
   assign image_data1     = regs[1];
   assign image_data2     = regs[2];
   assign image_data3     = regs[3];
   assign image_data4     = regs[4];
   assign image_data5     = regs[5];
   assign image_data6     = regs[6];
   assign image_data7     = regs[7];
   assign image_data8     = regs[8];
   assign image_data9     = regs[9];
   assign new_image_data1 = regs[14];

endmodule // regfile
