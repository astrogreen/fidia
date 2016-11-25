function trait_plot(trait_url, trait_name, map_selector, options_selector, trait_description_url, trait_key) {
    var zmin = 0.01;
    var zmax = 0.99;
    var options_selector = 'extensions-select';

    function changePlotData(data, array_index, zmin, zmax) {
        // If single component
        var trait_data = data;
        if (array_index != null) {
            // If multi-component
            trait_data = data[array_index];
        }
        if (getdim(trait_data) !== false) {
            // Everything's good, clear the element
            $('#'+map_selector).html('');
            // Call plotly
            plot_map(trait_name, trait_data, map_selector, zmin, zmax);

            return trait_data;
        }
        else {
            return $('#'+map_selector).html('Validation Fail: value array is irregular. Contact support. ');
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

            // flatten array
            var FlatArr = trait_value.value.reduce(function (p, c) {
                return p.concat(c);
            });
            // remove NANs
            var NumArr = bouncer(FlatArr);

            // can min/max exist?
            var NumArrSort = NumArr.sort(function(a,b){return a - b});

            var _Zmin = NumArrSort[Math.floor(NumArr.length * zmin)];
            var _Zmax = NumArrSort[Math.floor(NumArr.length * zmax) - 1];

            // if z_min == z_max
            if ((NumArrSort[Math.floor(NumArr.length)] == NumArrSort[Math.floor(NumArr.length) - 1] )) {
                // exit
                $('#visualization_status').html('<span class="text-error"><strong>Error:</strong> max/min values cannot be defined (likely: value object contains only NaN)</span>');
                return
            };

            // EXTENSIONS
            // Does value have multiple extensions? If so, add in plot options.
            if (typeof(trait_value.value[0][0][0]) != 'undefined') {
                for (var a = 0; a < trait_value.value.length; a++) {
                    var checked = "";
                    if (a == 0) {
                        checked = 'checked'
                    }
                    $('#'+options_selector).append('<div class="radio"> <label> <input type="radio" name="optionsRadios" id="optionsRadios' + a + '" value="' + a + '" ' + checked + '> ' + a + ' </label> </div>')
                }
                changePlotData(trait_value.value, 0, zmin, zmax);

                if ($("input[name=optionsRadios]").length > 0){
                    $("input[name=optionsRadios]").click(function () {
                        // console.log($("input[name=optionsRadios]:checked").val());
                        var array_index = Number($("input[name=optionsRadios]:checked").val());
                        changePlotData(trait_value.value, array_index, zmin, zmax);
                    });
                }
            } else {
                changePlotData(trait_value.value, null, zmin, zmax);
                $('.extensions').hide();

            }

            // SLIDER
            if ($("#slider-range").length > 0){
                if (typeof $("#slider-range").slider === "function"){
                    $("#slider-range").slider({
                        range: true,
                        min: 0.0,
                        max: 1.0,
                        step: 0.01,
                        values: [zmin, zmax],
                        slide: function (event, ui) {
                            $("#amount").html( (ui.values[0]*100).toPrecision(2) + "% - " + (ui.values[1]*100).toPrecision(2)+"% ");
                            // $("#uv").attr('value', ui.values[1]);
                            // $("#lv").attr('value', ui.values[0]);
                        },
                        stop: function(event, ui) {
                            var array_index = null;
                            // if multiple extensions, get the currently selected option.
                            if ($("input[name=optionsRadios]").length > 0){
                                array_index = Number($("input[name=optionsRadios]:checked").val());
                            }
                            changePlotData(trait_value.value, array_index, ui.values[0], ui.values[1]);
                        }
                    });

                    updateHtml = function(){
                        $("#amount").html( ($("#slider-range").slider("values", 0)*100).toPrecision(2) +
                            "% - " + ($("#slider-range").slider("values", 1)*100).toPrecision(2) +'% ');
                    };
                    updateHtml();

                    // $("#uv").val($("#slider-range").slider("values", 0));
                    // $("#lv").val($("#slider-range").slider("values", 1));

                    // RESET
                    $('#reset_2d_plot').click(function () {
                        // move slider back
                        var $slider = $("#slider-range");
                        $slider.slider("values", 0, zmin);
                        $slider.slider("values", 1, zmax);
                        // replot
                        var array_index = null;
                            // if multiple extensions, get the currently selected option.
                            if ($("input[name=optionsRadios]").length > 0){
                                array_index = Number($("input[name=optionsRadios]:checked").val());
                            }
                        changePlotData(trait_value.value, array_index, zmin, zmax);
                        // update html
                        updateHtml();
                    });
                };
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
    if (trait_description_url != undefined){
        $.ajax({
        url: trait_description_url,
        // here, don't let ajax parse as json, NANs are a problem. set type to string and parse with parseMore
        dataType: 'text',
        type: 'GET',
        success: function (data) {
            var trait = JSON.parseMore(data);
            console.log('#'+trait_key+'_trait_description')
            console.log(trait.description);
            $('#'+trait_key+'_trait_description').html(trait.description)
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


}