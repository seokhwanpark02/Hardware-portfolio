module async_fifo_gray #(
    parameter integer DATA_WIDTH = 33,
    parameter integer DEPTH = 16
) (
    input  logic                  wr_clk,
    input  logic                  wr_rst_n,

    input  logic                  wr_en_i,
    input  logic [DATA_WIDTH-1:0] wr_data_i,

    output logic                  wr_full_o,
    output logic                  wr_accept_o,

    output logic [$clog2(DEPTH):0]
                                  wr_level_o,

    output logic [$clog2(DEPTH):0]
                                  wr_free_slots_o,

    input  logic                  rd_clk,
    input  logic                  rd_rst_n,

    input  logic                  rd_en_i,
    output logic [DATA_WIDTH-1:0] rd_data_o,

    output logic                  rd_empty_o,
    output logic                  rd_accept_o
);

    localparam integer ADDR_WIDTH = $clog2(DEPTH);
    localparam integer PTR_WIDTH  = ADDR_WIDTH + 1;

    localparam logic [PTR_WIDTH-1:0]
        DEPTH_COUNT = PTR_WIDTH'(DEPTH);

    logic [DATA_WIDTH-1:0] mem [0:DEPTH-1];

    logic [PTR_WIDTH-1:0] wr_bin_q;
    logic [PTR_WIDTH-1:0] wr_bin_next;

    logic [PTR_WIDTH-1:0] wr_gray_q;
    logic [PTR_WIDTH-1:0] wr_gray_next;

    logic [PTR_WIDTH-1:0] rd_bin_q;
    logic [PTR_WIDTH-1:0] rd_bin_next;

    logic [PTR_WIDTH-1:0] rd_gray_q;
    logic [PTR_WIDTH-1:0] rd_gray_next;

    (* ASYNC_REG = "TRUE" *)
    logic [PTR_WIDTH-1:0] rd_gray_sync1_wr_q;

    (* ASYNC_REG = "TRUE" *)
    logic [PTR_WIDTH-1:0] rd_gray_sync2_wr_q;

    (* ASYNC_REG = "TRUE" *)
    logic [PTR_WIDTH-1:0] wr_gray_sync1_rd_q;

    (* ASYNC_REG = "TRUE" *)
    logic [PTR_WIDTH-1:0] wr_gray_sync2_rd_q;

    logic [PTR_WIDTH-1:0] rd_bin_sync_wr;

    logic [PTR_WIDTH-1:0]
        wr_full_compare_gray;

    logic wr_full_next;
    logic rd_empty_next;

    function automatic logic [PTR_WIDTH-1:0]
        binary_to_gray (
            input logic [PTR_WIDTH-1:0] binary
        );

        binary_to_gray =
            (binary >> 1) ^ binary;
    endfunction

    function automatic logic [PTR_WIDTH-1:0]
        gray_to_binary (
            input logic [PTR_WIDTH-1:0] gray
        );

        logic [PTR_WIDTH-1:0] binary;
        integer index;

        begin
            binary[PTR_WIDTH-1]
                = gray[PTR_WIDTH-1];

            for (
                index = PTR_WIDTH - 2;
                index >= 0;
                index = index - 1
            ) begin
                binary[index]
                    = binary[index + 1]
                    ^ gray[index];
            end

            gray_to_binary = binary;
        end
    endfunction

    always_comb begin
        wr_accept_o =
            wr_en_i
            && !wr_full_o;

        wr_bin_next = wr_bin_q;

        if (wr_accept_o) begin
            wr_bin_next =
                wr_bin_q
                + {{(PTR_WIDTH-1){1'b0}}, 1'b1};
        end

        wr_gray_next =
            binary_to_gray(wr_bin_next);

        wr_full_compare_gray = {
            ~rd_gray_sync2_wr_q[
                PTR_WIDTH-1:PTR_WIDTH-2
            ],
            rd_gray_sync2_wr_q[
                PTR_WIDTH-3:0
            ]
        };

        wr_full_next =
            (
                wr_gray_next
                == wr_full_compare_gray
            );

        rd_accept_o =
            rd_en_i
            && !rd_empty_o;

        rd_bin_next = rd_bin_q;

        if (rd_accept_o) begin
            rd_bin_next =
                rd_bin_q
                + {{(PTR_WIDTH-1){1'b0}}, 1'b1};
        end

        rd_gray_next =
            binary_to_gray(rd_bin_next);

        rd_empty_next =
            (
                rd_gray_next
                == wr_gray_sync2_rd_q
            );

        rd_bin_sync_wr =
            gray_to_binary(
                rd_gray_sync2_wr_q
            );

        wr_level_o =
            wr_bin_q
            - rd_bin_sync_wr;

        wr_free_slots_o =
            DEPTH_COUNT
            - wr_level_o;
    end

    always_ff @(posedge wr_clk or negedge wr_rst_n) begin
        if (!wr_rst_n) begin
            wr_bin_q             <= '0;
            wr_gray_q            <= '0;
            wr_full_o            <= 1'b0;

            rd_gray_sync1_wr_q   <= '0;
            rd_gray_sync2_wr_q   <= '0;
        end else begin
            wr_bin_q  <= wr_bin_next;
            wr_gray_q <= wr_gray_next;
            wr_full_o <= wr_full_next;

            rd_gray_sync1_wr_q
                <= rd_gray_q;

            rd_gray_sync2_wr_q
                <= rd_gray_sync1_wr_q;

            
        end
    end

       /*
     * FIFO storage intentionally has no reset.
     * Resetting pointers and empty/full state prevents stale
     * memory contents from becoming architecturally visible.
     * Keeping RAM write outside the async-reset process allows
     * Vivado RAM inference.
     */
    always_ff @(posedge wr_clk) begin
        if (wr_accept_o) begin
            mem[
                wr_bin_q[ADDR_WIDTH-1:0]
            ] <= wr_data_i;
        end
    end

    always_ff @(posedge rd_clk or negedge rd_rst_n) begin
        if (!rd_rst_n) begin
            rd_bin_q             <= '0;
            rd_gray_q            <= '0;
            rd_empty_o           <= 1'b1;

            wr_gray_sync1_rd_q   <= '0;
            wr_gray_sync2_rd_q   <= '0;
        end else begin
            rd_bin_q   <= rd_bin_next;
            rd_gray_q  <= rd_gray_next;
            rd_empty_o <= rd_empty_next;

            wr_gray_sync1_rd_q
                <= wr_gray_q;

            wr_gray_sync2_rd_q
                <= wr_gray_sync1_rd_q;
        end
    end

    assign rd_data_o =
        mem[rd_bin_q[ADDR_WIDTH-1:0]];

endmodule
