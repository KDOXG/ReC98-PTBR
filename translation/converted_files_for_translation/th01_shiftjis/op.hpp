#include "pc98.h"

#define HIT_KEY " ＨＩＴ　ＫＥＹ"

#define MAIN_CHOICES { \
	"   ＳＴＡＲＴ   ", \
	"ＣＯＮＴＩＮＵＥ", \
	"　ＯＰＴＩＯＮ　", \
	"　　ＱＵＩＴ　　", \
}

static const pixel_t MAIN_CHOICE_W = (9 * GLYPH_FULL_W);

#define OPTION_CHOICES { \
	"　ＲＡＮＫ　 ", \
	" ＭＵＳＩＣ  ", \
	"ＰＬＡＹＥＲ ", \
	"Ｍ．ＴＥＳＴ ", \
	"　ＱＵＩＴ　 ", \
}

#define MUSIC_CHOICES { \
	"ＭＵＳＩＣ　Ｎｏ．", \
	"　　Ｑｕｉｔ      ", \
}

#define MUSIC_TITLES { \
	"    A Sacret Lot", \
	"      風の神社     ", \
	"     永遠の巫女    ", \
	"  Highly Responsive", \
	"     東方怪奇談    ", \
	"  Oriental Magician", \
	"　  破邪の小太刀　 ", \
	" The Legend of KAGE", \
	"Positive and Negative", \
	"　　  天使伝説　　 ", \
	"　　　  魔鏡　　　 ", \
	"いざ倒れ逝くその時まで", \
	"　　死なばもろとも　　", \
	"　　  星幽剣士", \
	"　　　アイリス", \
}

#define GOODBYE "おつかれさまでした！！\n"
