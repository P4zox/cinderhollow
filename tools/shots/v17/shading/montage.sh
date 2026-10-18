#!/bin/sh
# before/after montages + luminance tables from run_all.sh output (cd here first)
P="python3 pairs.py"; W="--w 576"
$P before_after_regions_1.png before after r_ramparts r_catacombs r_cathedral r_mire r_crown r_archives r_hoarfrost r_spire $W
$P before_after_regions_2.png before after r_deep r_hermit r_ember r_thornveil r_barrows r_crimson r_necropolis $W
$P before_after_regions_3.png before after r_dunes r_starfall r_neohallow r_lastfield r_forge r_threshold r_training $W
$P before_after_vistas.png before after v_R11 v_K11 v_HF14 v_SP15 v_DU15 $W
$P before_after_dark.png before after d_catacombs d_crimson d_hermit d_lightsout $W
$P before_after_hot.png before after h_deep h_ember h_forge_hearth h_flue h_neon $W
$P before_after_boss.png before after hk_p1_flash0 hk_p1_flash1 hk_p1_flash2 hk_p3_flash hk_flash55 hk_flash55_screen $W
$P before_after_boss_zoom.png before after hk_p1_flash1 hk_flash55 --crop 420,180,820,560 $W
$P before_after_buffers.png buffers_before buffers_after du_dbg2 du_dbg3 cat_dbg3 her_dbg3 $W
$P before_after_fill_zoom.png before after r_threshold s_threshold_nofill s_threshold_read s_crown_snow s_dunes_sand --crop 380,250,880,560 --w 500
$P before_after_fill_bright.png before after r_crown r_dunes s_LF1 s_X11 v_LF1 v_X11 $W
$P before_after_bands_zoom.png before after d_catacombs d_hermit r_threshold --crop 380,150,880,450 $W
$P before_after_stress.png before_stress after_stress r_ramparts r_crown d_catacombs h_forge_hearth $W
$P before_after_classic.png before_off after_off r_ramparts d_catacombs d_lightsout $W
$P before_after_brightness_dark.png before_bright0 after_bright0 d_catacombs r_lastfield $W
$P before_after_brightness_bright.png before_bright2 after_bright2 d_catacombs r_lastfield $W
for d in "" _stress _off _classic _hard _bright0 _bright2; do echo "### before$d -> after$d"; python3 stats.py before$d after$d; echo; done > luminance.md
