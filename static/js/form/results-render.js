$( document ).ready(function() {
//TODO CALLBACK FOR JSON

    //For getting CSRF token
    function getCookie(name) {
              var cookieValue = null;
              if (document.cookie && document.cookie != '') {
                    var cookies = document.cookie.split(';');
              for (var i = 0; i < cookies.length; i++) {
                   var cookie = jQuery.trim(cookies[i]);
              // Does this cookie string begin with the name we want?
              if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                  break;
                 }
              }
          }
     return cookieValue;
    }
    var csrftoken = getCookie('csrftoken');


    if (typeof json_data !== 'undefined'){

        var queryData = json_data;
        var queryColumns = [];

        var thead = '';
        $('#returnTableResults').find('thead > tr').empty();

        $.each(json_data.columns, function(i,k){
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
        console.log('json_data undefined');
    }


});