$( document ).ready(function() {
//TODO CALLBACK FOR JSON
//    $('#results').hide();

//Prepare csrf token
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
//    console.log(csrftoken);

//    var refreshIntervalId = setInterval(function(){

//        $.ajax({type: "POST",url: '/asvo/testground/', data: {csrfmiddlewaretoken : csrftoken}, dataType:'json', success: function(results){
//            console.log(results);
//
//            updateProgress(results.progress.progress);

            if (typeof json_data !== 'undefined'){

//                clearInterval(refreshIntervalId);
//                $('#results').show();$('#waiting').hide();

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

                console.log('waiting');
            }


//        }, cache: false}); //adds timestamp to ensure that .progress isn't read from cache and subsequently not updated

//    }, 1000);



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

});