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



function fAstroMap(k,v){
    var map_name = k;
    var map_val = JSON.parse(v.value);
    var map_title = ftoTitleCase(map_name.split("_").join(" "));

    //test = [[ 0.75362986,  0.85060664,  0.81329006,  0.52951276,  0.29646403],
    //         [ 0.87069105,  0.67854957,  0.72128648,  0.07452028,  0.14661033],
    //         [ 0.17558352,  0.34659373,  0.78048335,  0.34665987,  0.48257683],
    //         [ 0.87636844,  0.43451588,  0.28513813,  0.77172319,  0.26592765],
    //         [ 0.19636954,  0.75303641,  0.53733789,  0.92042435,  0.23448685]];

    // Get number of pixels
    var row_pixel_count = map_val.length;
    var col_pixel_count = map_val[0].length;
    console.log("rows, cols: ",row_pixel_count,col_pixel_count);
    var rows = range(1,row_pixel_count);
    var cols = range(1,col_pixel_count);

    // - note that position is at center of pixel (rather than at origin left bottom)
    // - no normalization applied

    var colors=['rgb(165,0,38)','rgb(215,48,39)','rgb(244,109,67)','rgb(253,174,97)','rgb(254,224,144)','rgb(224,243,248)','rgb(171,217,233)','rgb(116,173,209)','rgb(69,117,180)','rgb(49,54,149)'];

    var colorscale = [];
    var numcolors = colors.length;


    var Zmin = fNthArrayMin(map_val);
    var Zmax = fNthArrayMax(map_val);
    console.log("Zmin,Zmax: ",Zmin, Zmax);

    var Zscale = Zmax-Zmin;
    var tickvalues = [];

    for (i=0; i<numcolors; i++){
        colorscale[i] = [String((i/(numcolors-1))*Zscale+Zmin), colors[i]];
        tickvalues[i] = (i/(numcolors-1))*Zscale+Zmin;
    };

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
                //tickvals:tickvalues
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
        paper_bgcolor: '#7f7f7f',
        title: map_title,
    };

    Plotly.newPlot(map_name, map_data, layout, {modeBarButtonsToRemove: ['sendDataToCloud'], displaylogo:false, showLink: false});


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

function fLogScale(key){
    console.log(key)

}