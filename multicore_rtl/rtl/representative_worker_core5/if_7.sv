interface if_7;
   /* -------- CPU-5 → CPU-6 -------- */
   logic [7:0] image_data5;
   /*-------- CPU-6 → CPU-5 -------- */
   logic [7:0] image_data6;
   /*--- modport ---*/
   modport cpu5_side (
      input image_data6,
      output image_data5
   );
   modport cpu6_side (
      output image_data6,
      input image_data5
   );
endinterface
