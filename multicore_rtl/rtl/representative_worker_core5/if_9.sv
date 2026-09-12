interface if_9;
   /* -------- CPU-5 → CPU-8 -------- */
   logic [7:0] done, image_data5;
   logic [7:0] new_image_data5;
   logic [7:0] end_signal_total;

   /* -------- CPU-8 → CPU-5 -------- */
   logic [7:0] end_signal8, image_data8;

   /*--- modport ---*/
   modport cpu5_side (
      output done, image_data5,
             new_image_data5,
             end_signal_total,
      input  end_signal8, image_data8
   );

   modport cpu8_side (
      input  done, image_data5,
             new_image_data5,
             end_signal_total,
      output end_signal8, image_data8
   );
endinterface
