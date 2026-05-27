#include "game/forkbann.hpp"
#include "obj/fork.h"
#include "th01/hardware/grppsafx.h"

static const shiftjis_t near *STRS[] = {
	"Anniversary Edition", FORK_TAG, FORK_DATE, FORK_CREDIT,
};
static const unsigned int ROW_COUNT = (sizeof(STRS) / sizeof(STRS[0]));
static const pixel_t ROW_H = (GLYPH_HALF_H + 2);

void pascal forkbanner_put(
	screen_x_t x, screen_y_t y, uint16_t align, int16_t col_and_fx
)
{
	return;
}
