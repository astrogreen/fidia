$( document ).ready(function() {
//TODO CALLBACK FOR JSON


//    //For getting CSRF token
//    function getCookie(name) {
//              var cookieValue = null;
//              if (document.cookie && document.cookie != '') {
//                    var cookies = document.cookie.split(';');
//              for (var i = 0; i < cookies.length; i++) {
//                   var cookie = jQuery.trim(cookies[i]);
//              // Does this cookie string begin with the name we want?
//              if (cookie.substring(0, name.length + 1) == (name + '=')) {
//                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
//                  break;
//                 }
//              }
//          }
//     return cookieValue;
//    }
//    var csrftoken = getCookie('csrftoken');
//
//    $.ajax({type: "POST",url: '/asvo/query-builder/', data: {csrfmiddlewaretoken : csrftoken}, dataType:'json', success: function(results){ 
//            console.log(results); 
//            }
//        });


    if(typeof json_data !== 'undefined'){

        var queryData = json_data;
        var queryColumns = [];

        var thead = '';
        $('#returnTableResults').find('thead > tr').empty();

        $.each(json_data.columns, function(i,k){
            var b = { title: k };

            if (k.indexOf("url_img") > -1){
                b = {
                "title":k,
                "render": function(data, type, row) {
                        return '<img class="img-responsive" style="max-width:70px" src="'+data+'" />';
                    }
                }
            }
            th = '<th>'+k+'</th>';
            queryColumns.push(b);
            $('#returnTableResults').find('thead > tr').append(th);
        });

        var numRows = queryData.data.length;
        var numCols = queryColumns.length;

//        console.log(numRows+'*'+numCols+'='+numRows*numCols);

        var cap = 100000;
        var capRows=(cap/numCols).toPrecision(2);

//        console.log(capRows+' '+cap);

        //CAP THE NUMBER OF ROWS RENDERED TO THE
        if (numRows*numCols>cap){
            var data = queryData.data.slice(0,capRows);
            $('#warning').append('<p class="bg-info"><strong>Displaying '+data.length+' out of '+numRows+' rows</strong> Please download the CSV for the full data set</p>')
        } else {
            var data = queryData.data;
        }

        var table = $('#returnTableResults').DataTable( {
            data : data,
            columns : queryColumns,
            "orderClasses": false,
            "scrollX": true,
            "language": {
                 "loadingRecords": "Please wait - loading..."
              }
         });
         console.log('loaded table');
    } else {
        console.log('json_data undefined');
    }


});