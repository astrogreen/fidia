
$( document ).ready(function() {
    //TODO CALLBACK FOR JSON

    //console.log()

    //  $.ajax({
    //    url: "/asvo/query-builder/",
    //    type:"POST",
    //    dataType: 'json',
    //    data: {data}
    //  }).done(function(data){
    //     console.log(data);//do what you want to do with response
    //  });


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
            console.log(b);
            columns.push(b);
        }
    }
    console.log(columns);

    //build dataTable
    $('#returnTableResults').DataTable( {
        data: dataSet,
        columns: columns
    } );



//
//    //DATA TABLES
//
////    for(var i = 0; i < json_data.length; i++) {
////        var object = json_data[i];
////        for (var property in object) {
////            if (object.hasOwnProperty(property)) {
////                console.log(property);
////            }
////        }
////    }
//
////        var obj = json_data[0];
////        console.log(json_data[0]);
////        var columns = [];
////        for (var property in obj) {
////            if (obj.hasOwnProperty(property) && (typeof property !== "undefined")) {
////                console.log(property);
//////                var newObj = { mData: property };
//////                columns.push(newObj);
////
////            }
////        }
//
////    var columns = [];
////    $.each(json_data.COLUMNS, function(i, value){
////        var obj = { mData: value };
////         columns.push(obj);
////    });
//
////    $('#returnTableResults').DataTable( {
////        "ajax": json_data,
//////        data : json_data,
////        "columns": [
////            { "mData": "cataid" },
////            { "mData": "ra" },
////            { "mData": "dec" },
////            { "mData": "z" },
////        ]
////    } );

//test

// Assign handlers immediately after making the request,
//// and remember the jqxhr object for this request
//var jqxhr = $.getJSON( "/static/js/form/payload.js", function( data ) {
//  console.log( data );
//  var t = data;
//  $('#returnTableResults').DataTable( {
//    "processing": true,
//    "deferRender": true,
//    "ajax": '/static/js/form/payload.js',
//    "columns": [
//        { "data": "name" },
//        { "data": "hr.position" },
//        { "data": "contact.0" },
//        { "data": "contact.1" },
//        { "data": "hr.start_date" },
//        { "data": "hr.salary" }
//    ]
//    });
//})



//$.getJSON( "/static/js/form/payload.js", function( data ) {
// var test = data;
// console.log(data)
//
// $('#returnTableResults').DataTable( {
//        "processing": true,
//        data: test,
//        "columns": [
//            { "data": "name" },
//            { "data": "hr.position" },
//            { "data": "contact.0" },
//            { "data": "contact.1" },
//            { "data": "hr.start_date" },
//            { "data": "hr.salary" }
//        ]
//});
//
//});






});