#include "th01/hardware/frmdelay.h"
#include "th01/hardware/tram_x16.hpp"
#include "th01/snd/mdrv2.h"
#include "shiftjis.hpp"

inline void touhou_reiiden_animate_char(shiftjis_kanji_t shiftjis) {
	mdrv2_se_play(14);
	tram_x16_kanji_center_reverse(shiftjis_to_jis(shiftjis));
	frame_delay(8);
}

inline void touhou_reiiden_animate(void) {
	touhou_reiiden_animate_char('東');
	touhou_reiiden_animate_char('方');
	touhou_reiiden_animate_char('★');
	touhou_reiiden_animate_char('靈');
	touhou_reiiden_animate_char('異');
	touhou_reiiden_animate_char('伝');
}
