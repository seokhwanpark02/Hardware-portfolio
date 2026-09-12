interface if_4;
   /* -------- CPU-2 → CPU-5 -------- */
   logic [7:0] done, image_data2, end_signal_total;
   logic [7:0] image_data5;

   /* -------- CPU-5 → CPU-2 -------- */
   logic [7:0] end_signal5, end_signal8;

   /*--- modport ---*/
   modport cpu2_side (
      output done, image_data2, end_signal_total,
             image_data5,
      input  end_signal5, end_signal8
   );

   modport cpu5_side (
      input  done, image_data2, end_signal_total,
             image_data5,
      output end_signal5, end_signal8
   );
endinterface
