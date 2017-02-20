function range(start, count) {
    if(arguments.length == 1) {
        count = start;
        start = 0;
    }
    var temp = [];
    for (var i = 0; i < count; i++) {
        temp.push(start + i);
    }
    return temp;
};


function removeNan(arr) {
    // should only remove NaN values from array.
    // previously:
    // return arr.filter(Boolean);
    // which also removes zeros - which we don't want!!

    return arr.filter(function(value) {
        // console.log(value, typeof value == "number", value >= 0, isNaN(value));
        // this effectively replicates isNaN(value) but will
        // also filter for 'true' and 'null' values, which isNaN
        // says is false (ie. they are a number).
        return (typeof value == "string" && parseFloat(value)) || (typeof value == "number" && value >= 0);
    });
}

function standardDeviation(values){
  var avg = average(values);

  var squareDiffs = values.map(function(value){
    var diff = value - avg;
    var sqrDiff = diff * diff;
    return sqrDiff;
  });

  var avgSquareDiff = average(squareDiffs);

  var stdDev = Math.sqrt(avgSquareDiff);
  return stdDev;
}

function average(data){
  var sum = data.reduce(function(sum, value){
    return sum + value;
  }, 0);

  var avg = sum / data.length;
  return avg;
}

function fGenerateColourScale(map_val, zmin_user, zmax_user){

    var colors=['rgb(165,0,38)','rgb(215,48,39)','rgb(244,109,67)','rgb(253,174,97)','rgb(254,224,144)','rgb(224,243,248)','rgb(171,217,233)','rgb(116,173,209)','rgb(69,117,180)','rgb(49,54,149)'];
    // red to white to blue -->

    colors = colors.reverse();
    // red higher value

    //var colorscale_old= [
    //    ['0.0', 'rgb(165,0,38)'],
    //    ['0.111111111111', 'rgb(215,48,39)'],
    //    ['0.222222222222', 'rgb(244,109,67)'],
    //    ['0.333333333333', 'rgb(253,174,97)'],
    //    ['0.444444444444', 'rgb(254,224,144)'],
    //    ['0.555555555556', 'rgb(224,243,248)'],
    //    ['0.666666666667', 'rgb(171,217,233)'],
    //    ['0.777777777778', 'rgb(116,173,209)'],
    //    ['0.888888888889', 'rgb(69,117,180)'],
    //    ['1.0', 'rgb(49,54,149)']
    //];

    var colorscale = [];
    var numcolors = colors.length;

    // Flatten n x n array to 1D (in order to sort and get min/max values).
    var FlatArr = map_val.reduce(function (p, c) {
        // type c == 1 x 50 arr
      return p.concat(c);
    });

    // Remove NaN
    var NumArr = removeNan(FlatArr);

    //ZMIN ZMAX (without sigma clip)
    // var Zmax_old = Math.max.apply(null, removeNan(FlatArr));
    // var Zmin_old = Math.min.apply(null, removeNan(FlatArr));

    // sort Num arr ascending
    NumArr.sort(function(a,b){return a - b});

    // X percentile clip, i.e. 0.01 to 0.99 of the actual values.

    // get closest indices to the 1% and 99% elements (-1 as array starts at 0)
    var _min_index = Math.floor(NumArr.length * zmin_user);
    var _max_index = ((Math.floor(NumArr.length * zmax_user) - 1) < 0 ?  0: (Math.floor(NumArr.length * zmax_user) - 1) );

    // console.log(NumArr.length * zmax_user);
    // console.log(_max_index);
    // console.log(_min_index);

    var _Zmin = NumArr[_min_index];
    var _Zmax = NumArr[_max_index];

    // console.log(_Zmax, _Zmin)

    if ($('#data-range').length>0){

        // $("#data-range").html( _Zmin.toPrecision(8) + "  - " + _Zmax.toPrecision(8));
        if (_Zmin != 0.0 || undefined == _Zmin){
            $("#lv").html( _Zmin.toPrecision(6));
        } else {
            $("#lv").html( _Zmin);
        }
        if (_Zmax != 0.0 || undefined == _Zmax){
            $("#uv").html( _Zmax.toPrecision(6));
        } else {
            $("#uv").html( _Zmax);
        }


        $('#data-range button').click(function(){
            // console.log('clip')
            // figure out percentile clip of values
            // _Zmin = $("#lv").val();
            // _Zmax = $("#uv").val();

        })

    }

    var Zscale = _Zmax-_Zmin;

    var tickvals = [];

    // Generate mapping between colours and colorbar, log or linear
    for (var i=0; i<numcolors; i++){
        colorscale[i] = [i/(numcolors-1), colors[i]];
        tickvals[i] = Number((Zscale*i)/(numcolors-1)+_Zmin).toPrecision(2);
        // console.log(colorscale[i],tickvals[i]);
    }

    return {
        colorscale:colorscale,
        tickvals:tickvals,
        Zmin:_Zmin,
        Zmax:_Zmax
    };
};


function plot_map(name, data, selector, zmin, zmax){

    var map_title = name;
    var map_selector = selector;
    var map_val = data;
    // if (getdim(data.value) !== false) {
    //     // Everything's good, clear the element
    //     $(map_selector).html('');
    //     var map_val = data.value;
    // }
    // else {
    //     return $(map_selector).html('Validation Fail: value array is irregular. Contact support. ');
    // }

    // Get number of pixels
    var row_pixel_count = map_val.length;
    var col_pixel_count = map_val[0].length;
    var rows = range(1,row_pixel_count);
    var cols = range(1,col_pixel_count);

    // - note that position is at center of pixel (rather than at origin left bottom)
    // - no normalization applied
    var temp = fGenerateColourScale(map_val, zmin, zmax);
    var colorscale = temp.colorscale;
    var tickvals = temp.tickvals;
    var Zmin = temp.Zmin;
    var Zmax = temp.Zmax;

    //test_map_val = [
    //    [[1,2],[3,4],[5550]],
    //    [[5,6],[7,8],[3232]],
    //]
    //map_val = [test_map_val[0][0], test_map_val[0][1]]

    var map_data = [
        {
            x:cols,
            y:rows,
            z: map_val,
            colorscale:colorscale,
            zmin: Zmin,
            zmax: Zmax,
            type: 'heatmap',
            colorbar:{
                lenmode:'fraction',
                tickformat:'.2e',
                leng:1,
                thicknessmode: 'fraction',
                thickness: 0.02,
                outlinewidth: 0,
                xpad:0, ypad:0,
                x: 1.02
            }
        }
    ];

    // Force responsive layout
    var elementWidth=$('#'+map_selector).parent().width();
    var layout = {
        autosize:true,
        width:elementWidth,
        height:elementWidth,
        margin: {
            l: 0.08*elementWidth,
            r: 0.00*elementWidth,
            b: 0.08*elementWidth,
            t: 0.06*elementWidth
        },
        // title: map_title
    };

    var raw_id = map_selector.replace("#","");
    var plotDiv = document.getElementById(raw_id);

    Plotly.newPlot(plotDiv, map_data, layout, {
        modeBarButtonsToRemove: ['sendDataToCloud', 'zoom2d', 'pan2d', 'select2d',
            'lasso2d', 'zoomIn2d', 'zoomOut2d', 'hoverCompareCartesian', 'hoverClosestCartesian', 'resetScale2d'],
        displaylogo: false,
        showLink: false,
        displayModeBar: true,
        scrollZoom: false
    });


    // RESPONSIVE TO CHANGING WINDOW SIZE
    $(window).on("resize",function(e){
        var elementWidth=$('#'+map_selector).parent().width();
        var update = {
          width: elementWidth,
          height:elementWidth
        };

        Plotly.relayout(map_selector, update);
    });

};


// VALIDATION
// Assumes a valid matrix and returns its dimension array.
// Won't work for irregular matrices, but is cheap.
function dim(mat) {
    if (mat instanceof Array) {
        return [mat.length].concat(dim(mat[0]));
    } else {
        return [];
    }
}

// Makes a validator function for a given matrix structure d.
function validator(d) {
    return function (mat) {
        if (mat instanceof Array) {
            return d.length > 0
                && d[0] === mat.length
                && every(mat, validator(d.slice(1)));
        } else {
            return d.length === 0;
        }
    };
}

// Combines dim and validator to get the required function.
function getdim(mat) {
    var d = dim(mat);
    return validator(d)(mat) ? d : false;
}

// Checks whether predicate applies to every element of array arr.
// This ought to be built into JS some day!
function every(arr, predicate) {
    var i, N;
    for (i = 0, N = arr.length; i < N; ++i) {
        if (!predicate(arr[i])) {
            return false;
        }
    }

    return true;
}


// UPDATES # TODO refactor as bindings - necessary for interactive plots