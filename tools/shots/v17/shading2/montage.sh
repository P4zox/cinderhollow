#!/bin/sh
# before/after montages + luminance tables from run_all.sh output (cd here first). Zooms are native-pixel crops (NEAREST).
P="python3 ../shading/pairs.py"; W="--w 576"
$P before_after_regions_1.png before after r_ramparts r_catacombs r_cathedral r_mire r_crown r_archives r_hoarfrost r_spire $W
$P before_after_regions_2.png before after r_deep r_hermit r_ember r_thornveil r_barrows r_crimson r_necropolis $W
$P before_after_regions_3.png before after r_dunes r_starfall r_neohallow r_lastfield r_forge r_threshold r_training $W
$P before_after_vistas.png before after v_R11 v_K11 v_HF14 v_SP15 v_DU15 v_LF1 v_X11 $W
$P before_after_dark.png before after d_catacombs d_crimson d_hermit d_lightsout $W
$P before_after_hot.png before after h_deep h_ember h_forge_hearth h_flue h_neon $W
$P before_after_backdrop.png before after s_X11 r_hermit d_hermit r_crown s_LF1 s_crown_snow $W
$P before_after_backdrop_zoom.png before after s_X11 r_hermit --crop 0,0,1152,420 --w 864
$P before_after_foes.png before_foes after_foes p_cat_lamp p_ramparts p_C8 p_forge p_deep $W
$P before_after_foes_zoom.png before_foes after_foes p_ramparts p_C8 p_deep --crop 330,330,830,560 --w 864
$P before_after_boss.png before_boss after_boss hk_a hk_b hk_c hk_d hk_p3 $W
$P before_after_boss_zoom.png before_boss after_boss hk_b hk_c hk_p3 --crop 330,150,830,520 --w 750
$P before_after_orbit.png before_orbit after_orbit orb_none orb_left orb_right orb_above orb_hk_left orb_hk_right --crop 250,330,1152,545 --w 864
$P before_after_orbit_zoom.png before_orbit after_orbit orb_left orb_right orb_hk_left --crop 440,410,640,545 --w 600
$P before_after_stress.png before_stress after_stress r_ramparts r_crown d_catacombs h_forge_hearth $W
$P before_after_classic.png before_off after_off r_ramparts d_catacombs d_lightsout $W
$P before_after_classic_light.png before_classic after_classic r_ramparts d_catacombs r_lastfield $W
$P before_after_hard.png before_hard after_hard r_dunes d_catacombs r_ramparts $W
$P before_after_bands_smooth.png before_smooth after_smooth d_catacombs d_hermit r_ramparts $W
$P before_after_bands_dithered.png before_dith after_dith d_catacombs d_hermit r_ramparts $W
$P before_after_brightness_dark.png before_bright0 after_bright0 d_catacombs r_lastfield r_crimson $W
$P before_after_brightness_bright.png before_bright2 after_bright2 d_catacombs r_lastfield r_crimson $W
python3 rows.py toggle_surface_off_on.png after_toggle p_cat_lamp_surfoff p_cat_lamp p_ramparts_surfoff p_ramparts p_deep_surfoff p_deep --crop 250,250,900,560 --w 700
python3 rows.py toggle_rim_off_on.png after_toggle p_ramparts_rimoff p_ramparts p_C8_rimoff p_C8 p_deep_rimoff p_deep --crop 330,330,830,560 --w 700
for d in "" _stress _off _classic _hard _bright0 _bright2; do echo "### before$d -> after$d"; python3 ../shading/stats.py before$d after$d; echo; done > luminance.md
