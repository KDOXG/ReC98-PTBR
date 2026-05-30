#include "pc98.h"
#include "shiftjis.hpp"

#define STAGEBONUS_TITLE_PREFIX "ＳＴＡＧＥ　"

// The fullwidth stage number is directly inserted into the single static copy
// of this string.
#define stagebonus_title STAGEBONUS_TITLE_PREFIX "　　　ＣＯＭＰＬＥＴＥ"

struct stagebonus_title_t {
	ShiftJISKanji prefix[(sizeof(STAGEBONUS_TITLE_PREFIX) - 1) / 2];
	ShiftJISKanji stage[2];
	ShiftJISKanji suffix[];
};

// ZUN bloat: Same here for all rendered fullwidth numbers. This constant seems
// to do us a favor by pre-filling the constant ones digit and the trailing
// space, but the game overwrites it anyway, making it entirely pointless.
#define stagebonus_digit_buf "　　　　０　"

#define STAGEBONUS_SUBTITLE     	"　　ＢＯＮＵＳ"
#define STAGEBONUS_TIME         	"   　Ｔｉｍｅ　"
#define STAGEBONUS_CARDCOMBO_MAX	"Ｃｏｎｔｉｎｕｏｕｓ"
#define STAGEBONUS_RESOURCES    	"Ｂｏｍｂ＆Ｐｌａｙｅｒ"
#define STAGEBONUS_STAGE_NUMBER 	"　　ＳＴＡＧＥ"
#define STAGEBONUS_TOTAL        	"ＢＯＮＵＳ　Ｐｏｉｎｔ"
#define STAGEBONUS_HIT_KEY      	"Ｈｉｔ　Ｚ　Ｋｅｙ"

static const pixel_t STAGEBONUS_TITLE_W = shiftjis_w(stagebonus_title);

// TRANSLATORS: Replace with your longest string.
static const pixel_t STAGEBONUS_LABEL_W = shiftjis_w(STAGEBONUS_TOTAL);

static const pixel_t STAGEBONUS_METRIC_ROW_W = (
	STAGEBONUS_LABEL_W + GLYPH_FULL_W + shiftjis_w(stagebonus_digit_buf)
);

static const pixel_t STAGEBONUS_W = (
	(STAGEBONUS_TITLE_W > STAGEBONUS_METRIC_ROW_W)
		? STAGEBONUS_TITLE_W
		: STAGEBONUS_METRIC_ROW_W
);
