interface if_6;
   /* -------- CPU-4 → CPU-5 -------- */
   logic [7:0] image_data4;
   /* -------- CPU-5 → CPU-4 -------- */
   logic [7:0] image_data5;
   /*--- modport ---*/
   modport cpu4_side (
      input image_data5,
      output image_data4
   );
   modport cpu5_side (
      output image_data5,
      input image_data4
   );
endinterface
