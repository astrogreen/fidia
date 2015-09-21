$('.form-group > button').addClass('pull-right');

testTree={
    "GAMA": {
        "TABLE": {
            G3CGALSINPAIR: ['PairID', 'Gal1CATAID', 'Gal2CATAID', 'SepProjAng', 'SepVel'],
            STELLARMASSES: ['CATAID','Z','nQ','SURVEY_CODE','Z_TONRY','fluxscale','zmax_19p4','zmax_19p8','zmax_17p88','nbands','logmstar','dellogmstar','logmoverl_i','dellogmoverl_i','logage','dellogage','logtau','dellogtau','metal','delmetal','extBV','delextBV','logLWage','dellogLWage','gminusi','delgminusi','uminusr','deluminusr','gminusi_stars','uminusr_stars','C_logM_ur','C_logM_gi','C_logM_eBV','fitphot_u','delfitphot_u','absmag_u','delabsmag_u','absmag_u_stars','fitphot_g','delfitphot_g','absmag_g','delabsmag_g','absmag_g_stars','fitphot_r','delfitphot_r','absmag_r','delabsmag_r','absmag_r_stars','fitphot_i','delfitphot_i','absmag_i','delabsmag_i','absmag_i_stars','fitphot_z','delfitphot_z','absmag_z','delabsmag_z','absmag_z_stars'],
        },
        "DATA": {}
    },
    "SAMI": {
        "TABLE": {
            SAMICAT1: ['PairID', 'Gal1CATAID', 'Gal2CATAID', 'SepProjAng', 'SepVel'],
            SAMICAT2: ['CATAID','Z','nQ','SURVEY_CODE','Z_TONRY','fluxscale','zmax_19p4','zmax_19p8','zmax_17p88','nbands','logmstar','dellogmstar','logmoverl_i','dellogmoverl_i','logage','dellogage','logtau','dellogtau','metal','delmetal','extBV','delextBV','logLWage','dellogLWage','gminusi','delgminusi','uminusr','deluminusr','gminusi_stars','uminusr_stars','C_logM_ur','C_logM_gi','C_logM_eBV','fitphot_u','delfitphot_u','absmag_u','delabsmag_u','absmag_u_stars','fitphot_g','delfitphot_g','absmag_g','delabsmag_g','absmag_g_stars','fitphot_r','delfitphot_r','absmag_r','delabsmag_r','absmag_r_stars','fitphot_i','delfitphot_i','absmag_i','delabsmag_i','absmag_i_stars','fitphot_z','delfitphot_z','absmag_z','delabsmag_z','absmag_z_stars'],
        },
        "DATA": {}
    },
};
var my_json;
$.getJSON('/static/js/table_tree.json', function(json) {
      my_json = json;
      console.log(my_json);
      console.log(testTree['GAMA']['TABLE']);
      testTree['GAMA']['TABLE']=my_json;
}).done(function(){
    updateForm();
});
function updateForm(){
    $.each(testTree,function(key, value)
    {
    //KEY=={GAMA, SAMI...}
    //VALUE=={OBJECT{{TABLE:...}, {DATA:...}}, OBJECT{{TABLE:...}, {DATA:...}...}
        $('#id_testSurvey').append('<option value=' + key + '>' + key + '</option>');
        $.each(value, function(surveykey,surveyvalue){
        //SURVEYKEY=={TABLE, DATA}, {TABLE, DATA}
            if (surveykey == 'TABLE'){
            //SURVEYVALUE==Object {G3CGALSINPAIR: Array[5], STELLARMASSES: Array[58]...}
                $.each(surveyvalue, function(tablekey,tablevalue){
//                    TABLEKEY=G3CGalsInPair, StellarMasses...
                    $('#id_testCat').append('<option class='+key+' value="' + tablekey + '">' + tablekey + '</option>');
//                    TABLEVALUE=all columns within catalogue tablekey["PairID", "Gal1CATAID", "Gal2CATAID", "SepProjAng", "SepVel"]
                    $.each(tablevalue,function(columnkey,columnvalue){
//                    COLUMNVALUES==separate column names
                        $('#id_testColumns').append('<option class='+tablekey+' value="' + columnvalue + '">' + columnvalue + '</option>');
                    })
                });
            }
        });
    //COLUMNS
    });
    $("#id_testCat").chainedTo("#id_testSurvey");
    $("#id_testColumns").chainedTo("#id_testCat");
}

$( document ).ready(function() {





});