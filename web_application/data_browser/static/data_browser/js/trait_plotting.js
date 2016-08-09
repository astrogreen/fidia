function trait_plot(trait_url, trait_name, map_selector, options_selector) {
    function changePlotData(data, array_index) {
        // If single component
        var trait_data = data;
        if (array_index != null) {
            // If multi-component
            trait_data = data[array_index];
        }
        if (getdim(trait_data) !== false) {
            // Everything's good, clear the element
            $(map_selector).html('');
            // Call plotly
            plot_map(trait_name, trait_data, map_selector);
        }
        else {
            return $(map_selector).html('Validation Fail: value array is irregular. Contact support. ');
        }
    };

    $.ajax({
        url: trait_url,
        // here, don't let ajax parse as json, NANs are a problem. set type to string and parse with parseMore
        dataType: 'text',
        type: 'GET',
        success: function (data) {
            // Parse NANs here
            var trait_value = JSON.parseMore(data);

            // Does value have multiple extensions? If so, add in plot options.
            if (typeof(trait_value.value[0][0][0]) != 'undefined') {
                for (var a = 0; a < trait_value.value.length; a++) {
                    var checked = "";
                    if (a == 0) {
                        checked = 'checked'
                    }
                    $(options_selector).append('<div class="radio"> <label> <input type="radio" name="optionsRadios" id="optionsRadios' + a + '" value="' + a + '" ' + checked + '> ' + a + ' </label> </div>')
                }
                changePlotData(trait_value.value, 0);

                $("input[name=optionsRadios]").click(function () {
                    console.log($("input[name=optionsRadios]:checked").val());
                    var array_index = Number($("input[name=optionsRadios]:checked").val());
                    changePlotData(trait_value.value, array_index);
                });
            } else {
                changePlotData(trait_value.value);
            }
        },
        error: function (jqXHR, exception) {
            alert("Error");
            if (jqXHR.status === 0) {
                console.log('Not connect.\n Verify Network.');
            } else if (jqXHR.status == 404) {
                console.log('Requested page not found. [404]');
            } else if (jqXHR.status == 500) {
                console.log('Internal Server Error [500].');
            } else if (exception === 'parsererror') {
                console.log('Requested JSON parse failed.');
            } else if (exception === 'timeout') {
                console.log('Time out error.');
            } else if (exception === 'abort') {
                console.log('Ajax request aborted.');
            } else {
                console.log('Uncaught Error.\n' + jqXHR.responseText);
            }
        }
    });
}