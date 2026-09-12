interface if_1;
   /* -------- CPU-1 → CPU-2 -------- */
   logic [7:0] done, image_data2, end_signal_total;
   logic [7:0] image_data1;
   logic [7:0] image_data3, image_data6;
   logic [7:0] image_data5;
   logic [7:0] new_image_data1;

   /* -------- CPU-2 → CPU-1 -------- */
   logic [7:0] end_signal3, end_signal6, end_signal9;
   logic [7:0] end_signal5, end_signal8;
   logic [7:0] end_signal2;

   /*--- modport ---*/
   modport cpu1_side (
      output done, image_data1, image_data2, image_data3,
             image_data5, image_data6, new_image_data1, end_signal_total,
      input  end_signal2, end_signal3, end_signal5,
             end_signal6, end_signal8, end_signal9
   );

   modport cpu2_side (
      input  done, image_data1, image_data2, image_data3,
             image_data5, image_data6, new_image_data1, end_signal_total,
      output end_signal2, end_signal3, end_signal5,
             end_signal6, end_signal8, end_signal9
   );
endinterface
