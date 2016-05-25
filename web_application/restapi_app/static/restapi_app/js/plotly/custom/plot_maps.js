function ftoTitleCase(str)
{
    return str.replace(/\w\S*/g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();});
};

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

// Remove NaN
function bouncer(arr) {
  var filteredArray = arr.filter(Boolean);
  return filteredArray;
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


function fGenerateColourScale(map_name, map_val){

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

    // Flatten array
    var FlatArr = map_val.reduce(function (p, c) {
      return p.concat(c);
    });

    // Remove NaN
    var NumArr = bouncer(FlatArr);

    //ZMIN ZMAX (without sigma clip)
    var Zmax_old = Math.max.apply(null, bouncer(FlatArr));
    var Zmin_old = Math.min.apply(null, bouncer(FlatArr));

    // 98 percentile clip, i.e. 0.01 to 0.99 of the actual values.
    var NumArrSort = NumArr.sort(function(a,b){return a - b});
    var Zmin = NumArrSort[Math.floor(NumArr.length * 0.01) + 1];
    var Zmax = NumArrSort[Math.floor(NumArr.length * 0.99)];

    var Zscale = Zmax-Zmin;
    var tickvals = [];

    // Generate mapping between colours and colorbar, log or linear
    //var colorbarlog = fLogScale(map_name);
    var colorbarlog = $('#'+map_name+"-log").is(':checked');

    for (i=0; i<numcolors; i++){
        if (colorbarlog==false){
            colorscale[i] = [i/(numcolors-1), colors[i]];
            //if (i % 2 ==0){
                tickvals[i] = ((Zscale*i)/(numcolors-1)+Zmin).toPrecision(2);
            //}
        } else {
            colorscale[i] = [parseFloat(1/(Math.pow(10,(numcolors-(i+1))))), colors[i]];
            if (i==0){colorscale[i] = [i, colors[i]];}
            //if (i % 2 ==1) {
                tickvals[i] = (Math.pow(10, (numcolors - (i + 1)))).toPrecision(2);
            //}
        }
        // console.log(colorscale[i],tickvals[i]);
    };

    return {
        colorscale:colorscale,
        tickvals:tickvals,
        Zmin:Zmin,
        Zmax:Zmax
    };
};


function fGetTraitPropertyValue(data){
    if (getdim(data.value) !== false) {
        return data.value;
    }
    else {console.log('value array irregular ')};
}

function fAstroMap(k,v){
    var map_name = k;
    var map_val = fGetTraitPropertyValue(v);
    var map_title = ftoTitleCase(map_name.split("_").join(" "));


    // Get number of pixels
    var row_pixel_count = map_val.length;
    var col_pixel_count = map_val[0].length;
    // console.log("rows, cols: ",row_pixel_count,col_pixel_count);
    // console.log(getdim(map_val));
    // console.log((map_val));
    var rows = range(1,row_pixel_count);
    var cols = range(1,col_pixel_count);

    // - note that position is at center of pixel (rather than at origin left bottom)
    // - no normalization applied
    var temp = fGenerateColourScale(map_name, map_val);
    var colorscale = temp.colorscale;
    var tickvals = temp.tickvals;
    var Zmin = temp.Zmin;
    var Zmax = temp.Zmax;

    // might look as (where last is wavelength)
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
                leng:1,
                thicknessmode: 'fraction',
                thickness: 0.02,
                outlinewidth: 0,
                xpad:0, ypad:0,
                x: 1.02,
                //tickmode: 'array',
                //tickvals: tickvals,
            },
        }
    ];

    var elementWidth=$('#'+map_name).parent().width();
    var layout = {
        autosize:true,
        width:elementWidth,
        height:elementWidth,
        margin: {
            l: 0.08*elementWidth,
            r: 0.10*elementWidth,
            b:0.09*elementWidth,
            t: 0.09*elementWidth,
        },
        //paper_bgcolor: '#7f7f7f',
        title: map_title,
    };
    var plotDiv = document.getElementById(map_name);
    Plotly.newPlot(plotDiv, map_data, layout, {modeBarButtonsToRemove: ['sendDataToCloud'], displaylogo:false, showLink: false});


    // RESPONSIVE TO CHANGING WINDOW SIZE
    $(window).on("resize",function(e){
        var elementWidth=$('#'+map_name).parent().width();
        var update = {
          width: elementWidth,
          height:elementWidth
        };

        Plotly.relayout(map_name, update);
    });
};

function plot_map(k,v){
    // k == trait name
    // v == trait data
    // value == trait property name (AO/k/v.value/)
    $('#'+k).html('');
    fAstroMap(k,v);
}


// UPDATES # TODO refactor as bindings - necessary for interactive plots

// TESTING
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