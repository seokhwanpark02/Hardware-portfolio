interface if_3;
   /* -------- CPU-1 → CPU-4 -------- */
   logic [7:0] done, image_data1, image_data4,
               image_data7, image_data8, image_data9,
               end_signal_total;

   /* -------- CPU-4 → CPU-1 -------- */
   logic [7:0] end_signal4, end_signal7;

   /*--- modport ---*/
   modport cpu1_side (
      output done, image_data1, image_data4,
             image_data7, image_data8, image_data9,
             end_signal_total,
      input  end_signal4, end_signal7
   );

   modport cpu4_side (
      input  done, image_data1, image_data4,
             image_data7, image_data8, image_data9,
             end_signal_total,
      output end_signal4, end_signal7
   );
endinterface
