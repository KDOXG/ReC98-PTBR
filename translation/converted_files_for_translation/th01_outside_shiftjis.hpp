// rank.h

#define RANKS_CAPS { \
    "EASY", "NORMAL", "HARD", "LUNATIC" \
}

#define RANKS_CAPS_CENTERED { \
    " EASY ", \
    "NORMAL", \
    " HARD ", \
    "LUNATIC" \
}

// resident.hpp

#define BGM_MODES_CENTERED { \
    "  OFF ", \
    "  FM  ", \
}

// main_01.cpp

void stage_num_animate(unsigned int stage_num)
{
    TRAMCursor tram_cursor;
    REGS in;
    font_glyph_ank_8x16_t glyphs[7];

    font_read(glyphs[0], 'S');
    font_read(glyphs[1], 'T');
    font_read(glyphs[2], 'A');
    font_read(glyphs[3], 'G');
    font_read(glyphs[4], 'E');
    font_read(glyphs[5], ('0' + (stage_num / 10)));
    font_read(glyphs[6], ('0' + (stage_num % 10)));
}

// main/stage/timer.cpp

void harryup_animate(void)
{
    TRAMCursor tram_cursor;
    REGS in;
    font_glyph_ank_8x16_t glyphs[7];

    mdrv2_se_play(17);

    font_read(glyphs[0], 'H');
    font_read(glyphs[1], 'A');
    font_read(glyphs[2], 'R');
    font_read(glyphs[3], 'R');
    font_read(glyphs[4], 'Y');
    font_read(glyphs[5], 'U');
    font_read(glyphs[6], 'P');
}