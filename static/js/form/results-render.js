$( document ).ready(function() {

//PROGRESS BAR
//update value as ajax callback updated with query progress
//can do stages: successful sql build, parse, run, conversion etc.
    var newvalue=70;
    $(".progress-bar").animate({
        width: newvalue+"%"
    }, 2500);


////    //DATA TABLES
//    if ($('#returnTableResults > table > thead > tr:nth-child(2) > th:nth-child(1)').length){
//    //get text and remove dummy thead tr - problem with data structure in panda
//        $('table > thead > tr:nth-child(1) > th:nth-child(1)').append($('table > thead > tr:nth-child(2) > th:nth-child(1)').html());
//        $('#returnTableResults > table > thead > tr:nth-child(2)').remove();
//        $('#returnTableResults > table').css( 'border', '1px solid #ddd' );
//        $('#returnTableResults > table').DataTable();
//    };


//HERE GET JSON OBJECT AND UPDATE CSV DOWNLOAD BUTTON? CAN PASS THAT IMMEDIATELY AS KNOW NAME
    //$('#returnTableResults').DataTable( {
    //    serverSide: true,
    //    ajax: {
    //        url: '/data-source',
    //        type: 'POST'
    //    }
    //} );

});