#include "Vsystem_top.h"
#include <verilated.h>
#include <verilated_vcd_c.h>
#include <array>
#include <vector>
#include <algorithm>
#include <numeric>
#include <iostream>
#include <iomanip>
#include <fstream>
#include <sstream>
#include <string>
#include <stdexcept>
#include <set>

/* -- util -- */
static constexpr int NBR[9][6]={
    {0,1,3,-1},{0,1,2,4,-1},{1,2,5,-1},
    {0,3,4,6,-1},{1,3,4,5,7,-1},{2,4,5,8,-1},
    {3,6,7,-1},{4,6,7,8,-1},{5,7,8,-1}};
static uint8_t median_any(std::vector<uint8_t>& v){
    std::sort(v.begin(), v.end());
    return (v.size()&1)? v[v.size()/2]
        : uint8_t((v[v.size()/2-1]>>1)+(v[v.size()/2]>>1));
}

/* -- Txn & Vector Loader -- */
struct Txn {
    std::array<uint8_t,9> pix;
};

static std::vector<Txn> load_vectors(const std::string& path)
{
    std::ifstream fin(path);

    if (!fin) {
        throw std::runtime_error(
            "Cannot open vector file: " + path
        );
    }

    std::vector<Txn> txns;
    std::string line;
    int line_no = 0;

    while (std::getline(fin, line)) {
        ++line_no;

        if (line.empty())
            continue;

        std::istringstream iss(line);
        Txn t{};

        for (int i = 0; i < 9; ++i) {
            int value;

            if (!(iss >> value)) {
                throw std::runtime_error(
                    "Not enough values at line " +
                    std::to_string(line_no)
                );
            }

            if (value < 0 || value > 255) {
                throw std::runtime_error(
                    "Value out of range at line " +
                    std::to_string(line_no)
                );
            }

            t.pix[i] = static_cast<uint8_t>(value);
        }

        int extra;

        if (iss >> extra) {
            throw std::runtime_error(
                "Too many values at line " +
                std::to_string(line_no)
            );
        }

        txns.push_back(t);
    }

    if (txns.empty()) {
        throw std::runtime_error(
            "Vector file contains no transactions"
        );
    }

    return txns;
}

/* -- Driver -- */
struct Driver{
    Vsystem_top* d;
    explicit Driver(Vsystem_top* dut): d(dut){}
    void drive(const Txn& t){
        d->image1=t.pix[0]; d->image2=t.pix[1]; d->image3=t.pix[2];
        d->image4=t.pix[3]; d->image5=t.pix[4]; d->image6=t.pix[5];
        d->image7=t.pix[6]; d->image8=t.pix[7]; d->image9=t.pix[8];
    }
};

/* -- Monitor -- */
struct Monitor{
    Vsystem_top* d;
    explicit Monitor(Vsystem_top* dut): d(dut){}
    bool capture(std::array<uint8_t,9>& out, vluint64_t& time, VerilatedVcdC* tfp){
        if(!d->end_signal_total) return false;
        for(int e=0;e<8;++e){ d->clk^=1; d->eval(); ++time; tfp->dump(time); }
        out = { d->new_image_data1,d->new_image_data2,d->new_image_data3,
                d->new_image_data4,d->new_image_data5,d->new_image_data6,
                d->new_image_data7,d->new_image_data8,d->new_image_data9 };
        return true;
    }
};

/* -- Scoreboard (표 + mismatch 집계) -- */
struct Scoreboard {
    uint64_t errors = 0;
    uint64_t checks = 0;

    bool check(
        const Txn& in,
        const std::array<uint8_t,9>& out,
        int txn
    ) {
        uint64_t txn_errors = 0;

        std::cout
            << "\n[TXN " << txn << "]\n"
            << " idx | in | exp | out | OK?\n"
            << "--------------------------------\n";

        for (int i = 0; i < 9; ++i) {
            std::vector<uint8_t> buf;

            for (int k = 0; NBR[i][k] != -1; ++k)
                buf.push_back(in.pix[NBR[i][k]]);

            uint8_t exp =
                uint8_t(
                    (in.pix[i] >> 1) +
                    (median_any(buf) >> 1)
                );

            bool ok = (exp == out[i]);

            ++checks;

            if (!ok) {
                ++errors;
                ++txn_errors;
            }

            std::cout
                << std::setw(3) << i << " | "
                << std::setw(3) << (int)in.pix[i] << " | "
                << std::setw(3) << (int)exp << " | "
                << std::setw(3) << (int)out[i] << " | "
                << (ok ? "OK" : "ERR")
                << "\n";
        }

        bool pass = (txn_errors == 0);

        std::cout
            << (pass ? "PASS" : "FAIL")
            << " (errors=" << txn_errors << ")\n";

        return pass;
    }
};

/* ---------------------------------------------------------
 * Functional Coverage
 *
 * This is C++ functional coverage, not SystemVerilog covergroup.
 *
 * Coverpoints:
 *   1) Core type x relation(self, mathematical median)
 *   2) Transaction input patterns
 *   3) Edge-core middle-pair parity
 * --------------------------------------------------------- */
struct Coverage {

    enum CoreType {
        CORNER = 0,
        EDGE   = 1,
        CENTER = 2
    };

    enum Relation {
        SELF_LT_MED = 0,
        SELF_EQ_MED = 1,
        SELF_GT_MED = 2
    };

    enum PairParity {
        PAIR_EE = 0,   // even-even
        PAIR_EO = 1,   // even-odd / odd-even
        PAIR_OO = 2    // odd-odd
    };

    enum Pattern {
        P_ALL_EQUAL = 0,
        P_HAS_ZERO,
        P_HAS_255,
        P_DUPLICATE,
        P_ASCENDING,
        P_DESCENDING,
        P_CENTER_HIGH,
        P_CENTER_LOW,
        P_COUNT
    };

    uint64_t transactions = 0;

    // [corner/edge/center][self<median / = / >]
    uint64_t relation_cross[3][3] = {};

    // edge cores only
    uint64_t pair_parity[3] = {};

    // transaction-level patterns
    uint64_t pattern[P_COUNT] = {};


    static int local_value_count(int core)
    {
        int n = 0;

        while (NBR[core][n] != -1)
            ++n;

        return n;
    }


    static CoreType get_core_type(int core)
    {
        int n = local_value_count(core);

        if (n == 3)
            return CORNER;

        if (n == 4)
            return EDGE;

        return CENTER;
    }


    // IMPORTANT:
    // Coverage의 median은 RTL 구현을 복사하지 않고
    // 수학적 floor((a+b)/2)를 사용한다.
    static uint16_t mathematical_median(std::vector<uint8_t> v)
    {
        std::sort(v.begin(), v.end());

        const size_t n = v.size();

        if (n & 1)
            return v[n / 2];

        return (
            static_cast<uint16_t>(v[n/2 - 1]) +
            static_cast<uint16_t>(v[n/2])
        ) / 2;
    }


    static bool all_equal(const Txn& tx)
    {
        for (int i = 1; i < 9; ++i)
            if (tx.pix[i] != tx.pix[0])
                return false;

        return true;
    }


    static bool has_value(const Txn& tx, uint8_t value)
    {
        for (auto v : tx.pix)
            if (v == value)
                return true;

        return false;
    }


    static bool has_duplicate(const Txn& tx)
    {
        std::set<uint8_t> s;

        for (auto v : tx.pix) {
            if (!s.insert(v).second)
                return true;
        }

        return false;
    }


    static bool strictly_ascending(const Txn& tx)
    {
        for (int i = 1; i < 9; ++i)
            if (tx.pix[i] <= tx.pix[i-1])
                return false;

        return true;
    }


    static bool strictly_descending(const Txn& tx)
    {
        for (int i = 1; i < 9; ++i)
            if (tx.pix[i] >= tx.pix[i-1])
                return false;

        return true;
    }


    static bool center_strict_high(const Txn& tx)
    {
        const uint8_t c = tx.pix[4];

        for (int i = 0; i < 9; ++i) {
            if (i == 4)
                continue;

            if (c <= tx.pix[i])
                return false;
        }

        return true;
    }


    static bool center_strict_low(const Txn& tx)
    {
        const uint8_t c = tx.pix[4];

        for (int i = 0; i < 9; ++i) {
            if (i == 4)
                continue;

            if (c >= tx.pix[i])
                return false;
        }

        return true;
    }


    void sample(const Txn& tx)
    {
        ++transactions;

        // -----------------------------
        // Transaction pattern coverage
        // -----------------------------

        if (all_equal(tx))
            ++pattern[P_ALL_EQUAL];

        if (has_value(tx, 0))
            ++pattern[P_HAS_ZERO];

        if (has_value(tx, 255))
            ++pattern[P_HAS_255];

        if (has_duplicate(tx))
            ++pattern[P_DUPLICATE];

        if (strictly_ascending(tx))
            ++pattern[P_ASCENDING];

        if (strictly_descending(tx))
            ++pattern[P_DESCENDING];

        if (center_strict_high(tx))
            ++pattern[P_CENTER_HIGH];

        if (center_strict_low(tx))
            ++pattern[P_CENTER_LOW];


        // -----------------------------
        // Per-core coverage
        // -----------------------------

        for (int core = 0; core < 9; ++core) {

            std::vector<uint8_t> values;

            for (int k = 0; NBR[core][k] != -1; ++k)
                values.push_back(
                    tx.pix[NBR[core][k]]
                );

            CoreType type = get_core_type(core);

            uint16_t med =
                mathematical_median(values);

            uint16_t self =
                tx.pix[core];

            Relation rel;

            if (self < med)
                rel = SELF_LT_MED;
            else if (self > med)
                rel = SELF_GT_MED;
            else
                rel = SELF_EQ_MED;

            ++relation_cross[type][rel];


            // -------------------------
            // Edge core:
            // middle-pair parity
            // -------------------------

            if (type == EDGE) {

                std::sort(
                    values.begin(),
                    values.end()
                );

                uint8_t a = values[1];
                uint8_t b = values[2];

                const bool a_odd = (a & 1);
                const bool b_odd = (b & 1);

                if (!a_odd && !b_odd)
                    ++pair_parity[PAIR_EE];

                else if (a_odd && b_odd)
                    ++pair_parity[PAIR_OO];

                else
                    ++pair_parity[PAIR_EO];
            }
        }
    }


    static const char* hit(uint64_t n)
    {
        return n ? "HIT" : "MISS";
    }


    void report() const
    {
        std::cout
            << "\n================================\n"
            << "[FUNCTIONAL COVERAGE]\n"
            << "================================\n";


        // ---------------------------------
        // 1. Core type x relation
        // ---------------------------------

        const char* core_name[3] = {
            "CORNER",
            "EDGE",
            "CENTER"
        };

        const char* rel_name[3] = {
            "SELF_LT_MED",
            "SELF_EQ_MED",
            "SELF_GT_MED"
        };

        int hit_bins = 0;
        int total_bins = 0;

        std::cout
            << "\n[CORE_TYPE x SELF_MEDIAN_RELATION]\n";

        for (int c = 0; c < 3; ++c) {
            for (int r = 0; r < 3; ++r) {

                ++total_bins;

                if (relation_cross[c][r])
                    ++hit_bins;

                std::cout
                    << "  "
                    << core_name[c]
                    << " x "
                    << rel_name[r]
                    << " : "
                    << relation_cross[c][r]
                    << "  "
                    << hit(relation_cross[c][r])
                    << "\n";
            }
        }


        // ---------------------------------
        // 2. Input patterns
        // ---------------------------------

        const char* pattern_name[P_COUNT] = {
            "ALL_EQUAL",
            "HAS_ZERO",
            "HAS_255",
            "DUPLICATE",
            "ASCENDING",
            "DESCENDING",
            "CENTER_HIGH",
            "CENTER_LOW"
        };

        std::cout
            << "\n[INPUT PATTERN]\n";

        for (int i = 0; i < P_COUNT; ++i) {

            ++total_bins;

            if (pattern[i])
                ++hit_bins;

            std::cout
                << "  "
                << pattern_name[i]
                << " : "
                << pattern[i]
                << "  "
                << hit(pattern[i])
                << "\n";
        }


        // ---------------------------------
        // 3. Edge middle-pair parity
        // ---------------------------------

        const char* parity_name[3] = {
            "EVEN_EVEN",
            "EVEN_ODD",
            "ODD_ODD"
        };

        std::cout
            << "\n[EDGE MEDIAN MIDDLE-PAIR PARITY]\n";

        for (int i = 0; i < 3; ++i) {

            ++total_bins;

            if (pair_parity[i])
                ++hit_bins;

            std::cout
                << "  "
                << parity_name[i]
                << " : "
                << pair_parity[i]
                << "  "
                << hit(pair_parity[i])
                << "\n";
        }


        double coverage =
            total_bins
            ? 100.0 * hit_bins / total_bins
            : 0.0;

        std::cout
            << "\n--------------------------------\n"
            << "Functional bins : "
            << hit_bins
            << "/"
            << total_bins
            << "\n"

            << std::fixed
            << std::setprecision(1)

            << "Functional Coverage : "
            << coverage
            << "%\n"

            << "FCOV_SUMMARY "
            << hit_bins << " "
            << total_bins << " "
            << coverage
            << "\n"

            << "================================\n";
    }
};

int main(int argc,char** argv){
    Verilated::commandArgs(argc, argv);

    std::string vector_path =
        (argc >= 2) ? argv[1] : "vectors.txt";

    std::vector<Txn> txns;

    try {
        txns = load_vectors(vector_path);
    }
    catch (const std::exception& e) {
        std::cerr << "[VECTOR ERROR] "
                  << e.what() << "\n";
        return 2;
    }

    std::cout << "VECTOR_FILE = "
              << vector_path << "\n";

    std::cout << "VECTORS = "
              << txns.size() << "\n";

    Vsystem_top dut;
    Verilated::traceEverOn(true);
    VerilatedVcdC tfp; dut.trace(&tfp, 99); tfp.open("wave.vcd");
    std::cout<<"VCD - wave.vcd\n";

    Driver drv(&dut); Monitor mon(&dut);
    Scoreboard scb; Coverage cov;

    vluint64_t t = 0;

    /* -- reset HIGH 2 clk, 입력 0 -- */
    dut.reset = 1; dut.clk = 0;
    dut.image1 = 0;
    dut.image2 = 0;
    dut.image3 = 0;
    dut.image4 = 0;
    dut.image5 = 0;
    dut.image6 = 0;
    dut.image7 = 0;
    dut.image8 = 0;
    dut.image9 = 0;
    dut.eval();                         // dump X (선택)
    dut.clk = 1; dut.eval();            // posedge #1 : 레지스터 클리어
    dut.clk = 0; dut.eval();            // negedge
    dut.clk = 1; dut.eval();            // posedge #2

    /* reset LOW & dump 시작 */
    dut.reset = 0;
    tfp.dump(t++);

    /* -- 트랜잭션 진행 -- */
    const unsigned MAX_WAIT_CYCLES = 1000;
    uint64_t failed_txns = 0;

    for (size_t n = 0; n < txns.size(); ++n) {
        const Txn& tx = txns[n];
        cov.sample(tx);
        drv.drive(tx);

        unsigned waitCycles = 0;
        while(!dut.end_signal_total){
            for(int edge=0;edge<2;++edge){ dut.clk^=1; dut.eval(); ++t; tfp.dump(t); }
            if(++waitCycles >= MAX_WAIT_CYCLES){
                std::cerr << "\nTIMEOUT\n"
                          << "transaction = " << n << "\n"
                          << "inputs =";
                for(auto value : tx.pix) std::cerr << ' ' << static_cast<unsigned>(value);
                std::cerr << "\ncurrent cycle = " << (t / 2)
                          << "\nend_signal_total = " << static_cast<unsigned>(dut.end_signal_total)
                          << "\n";
                dut.final(); tfp.close();
                return 2;
            }
        }

        std::array<uint8_t,9> out;
        if(!mon.capture(out,t,&tfp)){
            std::cerr << "Monitor capture failed after end_signal_total rising\n";
            dut.final(); tfp.close();
            return 2;
        }
        if (!scb.check(tx, out, static_cast<int>(n)))
            ++failed_txns;

        waitCycles = 0;
        while(dut.end_signal_total){
            for(int edge=0;edge<2;++edge){ dut.clk^=1; dut.eval(); ++t; tfp.dump(t); }
            if(++waitCycles >= MAX_WAIT_CYCLES){
                std::cerr << "\nTIMEOUT\n"
                          << "transaction = " << n << "\n"
                          << "inputs =";
                for(auto value : tx.pix) std::cerr << ' ' << static_cast<unsigned>(value);
                std::cerr << "\ncurrent cycle = " << (t / 2)
                          << "\nend_signal_total = " << static_cast<unsigned>(dut.end_signal_total)
                          << "\n";
                dut.final(); tfp.close();
                return 2;
            }
        }
    }

    cov.report();

    const uint64_t total_outputs = scb.checks;
    const uint64_t passed_outputs =
        total_outputs - scb.errors;

    std::cout
        << "\n================================\n"
        << "[REGRESSION SUMMARY]\n"
        << "================================\n"
        << "Vectors       : " << txns.size() << "\n"
        << "Outputs       : " << total_outputs << "\n"
        << "Passed        : " << passed_outputs << "\n"
        << "Failed        : " << scb.errors << "\n"
        << "Failed Txns   : " << failed_txns << "\n"
        << "Timeouts      : 0\n"
        << "RESULT        : "
        << (scb.errors ? "FAIL" : "PASS")
        << "\n"
        << "================================\n";

    dut.final(); tfp.close();
    return scb.errors ? 1 : 0;
}
