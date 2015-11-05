
$( document ).ready(function() {

    var json_data = JSON.parse($('#jsonTblData').html());
    console.log(json_data)
    //DATA TABLES
    if ($('#returnTableResults > table > thead > tr:nth-child(2) > th:nth-child(1)').length){
    //get text and remove dummy thead tr - problem with data structure in panda
        $('table > thead > tr:nth-child(1) > th:nth-child(1)').append($('table > thead > tr:nth-child(2) > th:nth-child(1)').html());
        $('#returnTableResults > table > thead > tr:nth-child(2)').remove();
        $('#returnTableResults > table').css( 'border', '1px solid #ddd' );
        $('#returnTableResults > table').DataTable(
        {
            data: json_data,
            columns: [
                { data: "cataid"},
                { data: "z"},
                { data: "nq"}
            ]
        }
        );
    };
console.log('results');
});