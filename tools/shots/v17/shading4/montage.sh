#!/bin/sh
# Shading phase 4 montages from run_all.sh output (cd here first): before | after rows; zooms are native-pixel crops (NEAREST).
G="python3 grid.py"
pairs() { b=$1; a=$2; shift 2; for n in "$@"; do printf '%s/%s.png %s/%s.png ' "$b" "$n" "$a" "$n"; done; }
P="before_proto after_proto"
$G before_after_reflections.png --cols 2 --w 640 $(pairs $P rf_CF5 rf_CF5b rf_CF10 rf_DB15 rf_M14 rf_M7)
$G before_after_reflections_2.png --cols 2 --w 640 $(pairs $P rf_HF8 rf_HF13 rf_SP8 fx_holy)
$G before_after_reflections_zoom.png --cols 2 --crop 300,280,900,600 --z 1.2 $(pairs $P rf_CF5 rf_CF10 rf_M7 rf_HF8)
$G before_after_particles.png --cols 2 --w 640 $(pairs $P pt_C10m pt_K7m pt_C10d pt_HF14s pt_M14s pt_SP8)
$G before_after_particles_zoom.png --cols 2 --crop 250,150,850,500 --z 1.2 $(pairs $P pt_C10m pt_K7m pt_SP8)
$G before_after_shafts.png --cols 2 --w 640 $(pairs $P sh_K7 sh_K7b sh_K11 sh_C10 sh_CF5)
$G before_after_shafts_zoom.png --cols 2 --crop 100,40,800,500 --z 1.2 $(pairs $P sh_K7 sh_K11 sh_C10)
$G before_after_haze.png --cols 2 --w 640 $(pairs $P hz_X11 hz_LF1 hz_R11 hz_DU10 hz_C8)
$G before_after_effects.png --cols 2 --w 640 $(pairs $P fx_shock fx_nova fx_flame fx_holy fx_slam fx_parry)
$G before_after_regions_1.png --cols 2 --w 576 $(pairs before after r_ramparts r_catacombs r_cathedral r_mire r_crown r_archives r_hoarfrost r_spire)
$G before_after_regions_2.png --cols 2 --w 576 $(pairs before after r_deep r_hermit r_ember r_thornveil r_barrows r_crimson r_necropolis)
$G before_after_regions_3.png --cols 2 --w 576 $(pairs before after r_dunes r_starfall r_neohallow r_lastfield r_forge r_threshold r_training)
$G before_after_vistas.png --cols 2 --w 576 $(pairs before after v_R11 v_K11 v_HF14 v_SP15 v_DU15 v_LF1 v_X11)
$G before_after_dark_hot.png --cols 2 --w 576 $(pairs before after d_catacombs d_crimson d_hermit d_lightsout h_deep h_ember h_forge_hearth h_neon)
$G before_after_boss.png --cols 2 --w 640 $(pairs before_boss after_boss hk_a hk_b hk_c hk_d hk_p3)
$G before_after_boss_zoom.png --cols 2 --crop 330,150,830,560 --z 1.5 $(pairs before_boss after_boss hk_b hk_c hk_p3)
$G before_after_orbit.png --cols 2 --crop 180,320,1152,560 --z 0.9 $(pairs before_orbit after_orbit orb_none orb_left orb_right orb_above orb_hk_left)
$G lightning_sequence.png --cols 2 --w 640 $(pairs before_storm after_storm sp8_0calm sp8_1sky_f01 sp8_1sky_f04 sp8_2strike_f16 sp3_1sky_f01)
$G before_after_stress.png --cols 2 --w 576 $(pairs before_stress after_stress r_ramparts d_catacombs r_lastfield h_forge_hearth r_cathedral)
$G before_after_classic.png --cols 2 --w 576 $(pairs before_off after_off r_ramparts d_catacombs r_mire) $(pairs before_classic after_classic r_ramparts r_barrows)
$G before_after_hard_smooth.png --cols 2 --w 576 $(pairs before_hard after_hard r_dunes d_catacombs r_cathedral) $(pairs before_smooth after_smooth d_catacombs d_hermit)
T=after_toggle
$G toggle_reflections.png --cols 2 --crop 250,250,950,600 --z 0.9 $T/rf_CF5_refloff.png $T/rf_CF5.png $T/rf_M7_refloff.png $T/rf_M7.png $T/rf_HF8_refloff.png $T/rf_HF8.png
$G toggle_lit_particles.png --cols 2 --w 640 $T/pt_C10m_partoff.png $T/pt_C10m.png $T/pt_K7m_partoff.png $T/pt_K7m.png
$G toggle_light_shafts.png --cols 3 --w 480 $T/sh_K7_raysoff.png $T/sh_K7.png $T/sh_K7_raysstrong.png $T/sh_K11_raysoff.png $T/sh_K11.png $T/sh_K11_raysstrong.png $T/sh_C10_raysoff.png $T/sh_C10.png $T/sh_C10_raysstrong.png
$G toggle_depth_haze.png --cols 2 --w 640 $T/hz_R11_hazeoff.png $T/hz_R11.png
$G toggle_all_off.png --cols 2 --w 640 $T/rf_M7_alloff.png $T/rf_M7.png $T/fx_flame_alloff.png $T/fx_flame.png
for d in "" _proto _stress _off _classic _hard; do echo "### before$d -> after$d"; python3 ../shading/stats.py before$d after$d; echo; done > luminance.md
