CAT_G3CGALSINPAIR = 'G3CGalsInPair'
CAT_STELLARMASSES = 'StellarMasses'
CAT = (
    (CAT_G3CGALSINPAIR, 'G3CGalsInPair'),
    (CAT_STELLARMASSES, 'StellarMasses')
)

COLUMNS = {
    CAT_G3CGALSINPAIR: ['PairID', 'Gal1CATAID', 'Gal2CATAID', 'SepProjAng', 'SepVel'],
    CAT_STELLARMASSES: ['CATAID','Z','nQ','SURVEY_CODE','Z_TONRY','fluxscale','zmax_19p4','zmax_19p8','zmax_17p88','nbands','logmstar','dellogmstar','logmoverl_i','dellogmoverl_i','logage','dellogage','logtau','dellogtau','metal','delmetal','extBV','delextBV','logLWage','dellogLWage','gminusi','delgminusi','uminusr','deluminusr','gminusi_stars','uminusr_stars','C_logM_ur','C_logM_gi','C_logM_eBV','fitphot_u','delfitphot_u','absmag_u','delabsmag_u','absmag_u_stars','fitphot_g','delfitphot_g','absmag_g','delabsmag_g','absmag_g_stars','fitphot_r','delfitphot_r','absmag_r','delabsmag_r','absmag_r_stars','fitphot_i','delfitphot_i','absmag_i','delabsmag_i','absmag_i_stars','fitphot_z','delfitphot_z','absmag_z','delabsmag_z','absmag_z_stars']
}

