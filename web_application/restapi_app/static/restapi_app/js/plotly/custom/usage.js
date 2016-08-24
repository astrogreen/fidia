var trace1 = {
    x: [30],
    y: [1],
    name: 'query',
    orientation: 'h',
    marker: {
        color: '#f1cb76',
        width: 1
    },
    type: 'bar',
    hoverinfo: 'none',
};

var trace2 = {
    x: [10],
    y: [1],
    name: 'downloads',
    orientation: 'h',
    type: 'bar',
    marker: {
        color: '#a94442',
        width: 1
    }, hoverinfo: 'none',
};
var trace3 = {
    x: [60],
    y: [1],
    name: 'free',
    orientation: 'h',
    type: 'bar',
    marker: {
        color: '#4078C0',
        width: 1
    }, hoverinfo: 'none',
};
var data = [trace1, trace2, trace3];

var annotationContent = [];
var x_pos = 0;
for (var i = 0; i < data.length; i++) {
    x_pos += data[i]['x'][0];
    var result = {
        x: x_pos-data[i]['x'][0]/2,
        y: 1,
        text: data[i]['x'][0]+'%',
        xanchor: 'center',
        yanchor: 'center',
        showarrow: false
    };
    annotationContent.push(result);
}

var layout = {
    annotations: annotationContent,
    margin: {
        l: 0,
        r: 0,
        b: 0,
        t: 0,
        pad: 0
    },
    xaxis: {
        autorange: false,
        showgrid: false,
        zeroline: false,
        showline: false,
        autotick: true,
        ticks: '',
        fixedrange: true,
        showticklabels: false,
        range: [0,100],

    },
    yaxis: {
        autorange: true,
        showgrid: false,
        zeroline: false,
        showline: false,
        autotick: true,
        ticks: '',
        showticklabels: false,
        fixedrange: true
    },
    height: 36,
    width: document.getElementById('statistics').offsetWidth,
    barmode: 'stack',
    showlegend: false
};

Plotly.newPlot('statistics', data, layout, {displayModeBar: false});