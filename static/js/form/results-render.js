
$( document ).ready(function() {
    //TODO CALLBACK FOR JSON
    $('#results').hide();

//    $('#getAJAX').on('click',function(){
//
//        var jqxhr = $.getJSON( '/asvo/testground/', function(results) {
//            console.log( "success");
//            $('#results').show();
////            $('#waiting').hide();
//
//            console.log(results);
//
//            //data is nested obj (see view):
//            //results = { "progress" : {'progress':0.5}, "data" : data }
//
//            //queryData is a nested array
//            var queryData = results.data;
//            //queryColumns is nested obj
//            var queryColumns = [];
//
//            var thead = '';
//            $('#returnTableResults').find('thead > tr').empty();
//
//            $.each(queryData.columns, function(i,k){
//                b = { title: k };
//                th = '<th>'+k+'</th>';
//                queryColumns.push(b);
//                $('#returnTableResults').find('thead > tr').append(th);
//            });
//
//            var table = $('#returnTableResults').DataTable( {
//                data : queryData.data,
//                columns : queryColumns,
//                'deferRender':true
//             });
//
//          })
//          .done(function() {
////            console.log( "second success" );
//          })
//          .fail(function() {
//            console.log( "error- cannot retrieve data" );
//          })
//
//
//
//
//    });




    var refreshIntervalId = setInterval(function(){
        $.ajax({type: "GET",url: '/asvo/testground/', dataType:'json', success: function(results){
            console.log(results);

            updateProgress(results.progress.progress);

            if (typeof results.data !== 'undefined'){

                clearInterval(refreshIntervalId);
                $('#results').show();$('#waiting').hide();

                var queryData = results.data;
                var queryColumns = [];

                var thead = '';
                $('#returnTableResults').find('thead > tr').empty();

                $.each(queryData.columns, function(i,k){
                    b = { title: k };
                    th = '<th>'+k+'</th>';
                    queryColumns.push(b);
                    $('#returnTableResults').find('thead > tr').append(th);
                });

                var table = $('#returnTableResults').DataTable( {
                    data : queryData.data,
                    columns : queryColumns,
                    'deferRender':true
                 });
            } else {

                console.log('waiting');
            }


        }, cache: false}); //adds timestamp to ensure that .progress isn't read from cache and subsequently not updated

    }, 1000);



    function updateProgress(data) {
        result = data;	// if no coverage of source (zero files) 1/1=>100, else 0/0 = NAN
        console.log(result);
        if (result>=100 && error ==0){
            clearInterval(refreshIntervalId);   //stop ajax calls
            //build data tables


        } else {
            $('div.progress-bar').attr('aria-valuetransitiongoal',result);
            $(window).ready(function (e) {
                $.each($('div.progress-bar'), function () {
                    $(this).css('width', $(this).attr('aria-valuetransitiongoal') + '%').text(Math.round($(this).attr('aria-valuetransitiongoal')) + '%');
                });
            });

        }
    };



//OLD ARRAY RENDER

    if ((typeof json_data !== 'undefined')){
         //convert  into array DataTables can read
    var querydata=json_data;
        var dataSet = [];
        for (var i = 0; i < querydata.length; i++) {
                var row = $.parseJSON(querydata[i])
                var rowArr=[];
                for (var property in row) {
                    if (row.hasOwnProperty(property) && (typeof property !== "undefined")) {
                        rowArr.push(row[property]);
                    }
                }
                dataSet.push(rowArr);
        }
        //pull out thead column names
        var columns = [];
        var row0=$.parseJSON(querydata[0])
        for (var property in row0) {
            if (row0.hasOwnProperty(property) && (typeof property !== "undefined")) {
                b = { title: property }
    //            console.log(b);
                columns.push(b);
            }
        }
    //    console.log(columns);

        //build dataTable
        $('#returnTableResults').DataTable( {
            data: dataSet,
            columns: columns,
            "deferRender": true
        } );

    } else {
        console.log('no data')
        };





});