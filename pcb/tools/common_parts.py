"""Part data shared by the board generators of both variants: footprint names of the parts every variant uses,
datasheet references, the silkscreen logos and the project URL."""

FP_ROCKER = "Rocker_DPST_Marquardt_1802.2504_E-Switch_RA412C1100"
FP_MOV = "Varistor_TDK_CU4032"
FP_FUSE = "Fuse_Schurter_UMT250"
FP_ANT, FP_KICAD = "Ant_Logo_8mm_SilkScreen", "KiCad-Logo2_5mm_SilkScreen"
ANT_LOGO_H = 8.0                            # height the ant logo is scaled to (pcb/art/Ant_Logo_SilkScreen.kicad_mod)
URL = "github.com/antevens/sladdseg"

ROCKER_DS = "Marquardt drawing 1802.2504 rev g, 2003-09-16 (K-drawing 18022504.03)"
UMT_DS = "https://us.schurter.com/bundles/snceschurter/epim/_ProdPool_/newDS/en/typ_UMT_250.pdf"
CU_DS = "https://www.farnell.com/datasheets/2921094.pdf"
SMSI_DS = "https://www.we-online.com/catalog/datasheet/9774070243R.pdf"

# WA-SMSI M2 land pattern (DATASHEET 9774070243R, the same as the L6 9774060243R): stencil ring, body
POST_PASTE = (3.1, 5.2, 0.6)                # stencil ring inner / outer diameter, web width
SMSI_BODY_D = 4.35                          # spacer body diameter (Fab outline)
