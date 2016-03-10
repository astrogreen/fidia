console.log(AstroObjectJson);

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

function getMinMaxOf2DIndex (arr, idx) {
    var arrayMap = arr.map(function (e) { return e[idx]});
    return {
        min: Math.min.apply(null, arrayMap),
        max: Math.max.apply(null, arrayMap)
    }
}

function fNthArrayMin(arr){
    // Get minimum value in 2D array
    return arr.reduce(function(min, arr) {
        return Math.min(min, arr[0]);
    }, +Infinity);
};

function fNthArrayMax(arr){
    // Get minimum value in 2D array
    return arr.reduce(function(max, arr) {
        return Math.max(max, arr[0]);
    }, -Infinity);
};

function fGenerateColourScale(map_name, map_val){

    var colors=['rgb(165,0,38)','rgb(215,48,39)','rgb(244,109,67)','rgb(253,174,97)','rgb(254,224,144)','rgb(224,243,248)','rgb(171,217,233)','rgb(116,173,209)','rgb(69,117,180)','rgb(49,54,149)'];
    // red to white to blue -->

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

    var Zmin = fNthArrayMin(map_val);
    var Zmax = fNthArrayMax(map_val);
    //console.log("Zmin,Zmax: ",Zmin, Zmax);

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
        //console.log(colorscale[i],tickvals[i]);
    };

    return {
        colorscale:colorscale,
        tickvals:tickvals
    };
};

function fGetTraitPropertyValue(key){
    return JSON.parse(AstroObjectJson[key].value);
}

function fAstroMap(k,v){
    var map_name = k;
    var map_val = fGetTraitPropertyValue(k);
    var map_title = ftoTitleCase(map_name.split("_").join(" "));

    // Get number of pixels
    var row_pixel_count = map_val.length;
    var col_pixel_count = map_val[0].length;
    //console.log("rows, cols: ",row_pixel_count,col_pixel_count);
    var rows = range(1,row_pixel_count);
    var cols = range(1,col_pixel_count);

    // - note that position is at center of pixel (rather than at origin left bottom)
    // - no normalization applied
    var temp = fGenerateColourScale(map_name, map_val);
    var colorscale = temp.colorscale;
    var tickvals = temp.tickvals;

    var map_data = [
        {
            x:cols,
            y:rows,
            z: map_val,
            colorscale:colorscale,
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


$.each(AstroObjectJson, function(k,v){
    // k == trait name
    // v == trait value
    // value == trait property name

    // If element exists (defined in django template sov.html)
    if ($('#'+k).length){
        fAstroMap(k,v);
    };
});


// UPDATES # TODO refactor as bindings



