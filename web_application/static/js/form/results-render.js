$( document ).ready(function() {

    if(typeof json_data !== 'undefined'){

        var queryData = json_data;
        var queryColumns = [];

        var thead = '';
        $('#returnTableResults').find('thead > tr').empty();
        //APPEND COLUMN VALUES TO TABLE HEAD
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

        var data = queryData.data;

        if (typeof data == 'undefined'){data=[];}

        var table = $('#returnTableResults').DataTable( {
            data : data,
            columns : queryColumns,
            "orderClasses": false,
            "scrollX": true,
            "language": {
                 "loadingRecords": "Please wait - loading..."
              }
         });
         if (json_size[2]!==0){$('#warning').append('<p class="bg-info"><strong>Displaying '+json_size[2]+' out of '+json_size[0]+' rows</strong>. Please download the CSV for the full data set.</p>')};
    } else {
        $('#returnTableResults').find('thead > tr').empty();
        $('#warning').append('<p class="bg-info"><strong>Over 100,000 elements ('+json_size[0]+' rows, '+json_size[1]+' colums).</strong> Please download the CSV for the full data set.</p>')

    }


});