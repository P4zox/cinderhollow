#!/bin/sh
# Shading phase 3 montages from run_all.sh output (cd here first): before | after rows; zooms are native-pixel crops (NEAREST).
G="python3 grid.py"
pairs() { b=$1; a=$2; shift 2; for n in "$@"; do printf '%s/%s.png %s/%s.png ' "$b" "$n" "$a" "$n"; done; }
$G before_after_proto.png --cols 2 --w 640 $(pairs before_proto after_proto p_cat_lamp p_cat_torch p_cat_jump p_ramparts p_C8 p_forge)
$G before_after_proto_2.png --cols 2 --w 640 $(pairs before_proto after_proto p_deep p_hoar p_mire p_spire p_X11 p_hermit)
$G before_after_proto_zoom.png --cols 2 --crop 330,330,830,560 --z 1.6 $(pairs before_proto after_proto p_cat_lamp p_cat_jump p_ramparts p_C8 p_deep)
$G before_after_boss.png --cols 2 --w 640 $(pairs before_boss after_boss hk_a hk_b hk_c hk_d hk_p3)
$G before_after_boss_zoom.png --cols 2 --crop 330,150,830,560 --z 1.5 $(pairs before_boss after_boss hk_b hk_c hk_p3)
$G before_after_orbit.png --cols 2 --crop 180,320,1152,560 --z 0.9 $(pairs before_orbit after_orbit orb_none orb_left orb_right orb_above orb_low_left orb_hk_left orb_hk_right)
$G before_after_orbit_zoom.png --cols 2 --crop 180,330,720,545 --z 1.6 $(pairs before_orbit after_orbit orb_left orb_right orb_low_left)
$G before_after_regions_1.png --cols 2 --w 576 $(pairs before after r_ramparts r_catacombs r_cathedral r_mire r_crown r_archives r_hoarfrost r_spire)
$G before_after_regions_2.png --cols 2 --w 576 $(pairs before after r_deep r_hermit r_ember r_thornveil r_barrows r_crimson r_necropolis)
$G before_after_regions_3.png --cols 2 --w 576 $(pairs before after r_dunes r_starfall r_neohallow r_lastfield r_forge r_threshold r_training)
$G before_after_vistas.png --cols 2 --w 576 $(pairs before after v_R11 v_K11 v_HF14 v_SP15 v_DU15 v_LF1 v_X11)
$G before_after_dark_hot.png --cols 2 --w 576 $(pairs before after d_catacombs d_crimson d_hermit d_lightsout h_deep h_ember h_forge_hearth h_neon)
$G before_after_stress.png --cols 2 --w 576 $(pairs before_stress after_stress r_ramparts d_catacombs r_lastfield h_forge_hearth)
$G before_after_classic.png --cols 2 --w 576 $(pairs before_off after_off r_ramparts d_catacombs d_lightsout) $(pairs before_classic after_classic r_ramparts d_catacombs)
$G before_after_hard_smooth.png --cols 2 --w 576 $(pairs before_hard after_hard r_dunes d_catacombs r_ramparts) $(pairs before_smooth after_smooth d_catacombs d_hermit)
# lightning: before (the old unshadowed flash) | after (sky light with shadows), the flash decaying; then a strike
$G lightning_sequence.png --cols 2 --w 640 $(pairs before_storm after_storm sp8_0calm sp8_1sky_f01 sp8_1sky_f04 sp8_1sky_f08 sp8_1sky_f14 sp8_2strike_f16 sp8_2strike_f19)
$G lightning_sequence_2.png --cols 2 --w 640 $(pairs before_storm after_storm sp3_0calm sp3_1sky_f01 sp3_1sky_f08 sp3_2strike_f16)
$G lightning_zoom.png --cols 2 --crop 300,150,900,560 --z 1.4 $(pairs before_storm after_storm sp8_1sky_f01 sp8_2strike_f16)
# eye adaptation: frames 3..63 after the teleport (top row bright -> dark, then dark -> bright, then the Crown -> Crimson)
for t in b2d d2b b2d2; do $G expo_$t.png --cols 4 --w 400 $(for f in 03 09 15 21 30 39 51 63; do printf 'after_expo/%s_f%s.png ' $t $f; done); done
$G exposure_transition_strip.png --cols 1 expo_b2d.png expo_d2b.png expo_b2d2.png
# the new options: the same frame with the option off / partly on (left) and on (right)
$G toggle_character_shadows.png --cols 3 --crop 250,250,900,560 --z 0.9 $(for n in p_cat_lamp p_ramparts p_C8 p_deep; do printf 'after_toggle/%s_cshoff.png after_toggle/%s_cshcon.png after_toggle/%s.png ' $n $n $n; done)
$G toggle_materials.png --cols 2 --crop 330,330,830,560 --z 1.4 $(for n in p_cat_lamp p_ramparts p_forge p_deep; do printf 'after_toggle/%s_matoff.png after_toggle/%s.png ' $n $n; done)
for d in "" _stress _off _classic _hard; do echo "### before$d -> after$d"; python3 ../shading/stats.py before$d after$d; echo; done > luminance.md
