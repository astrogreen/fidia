app.controller('Ctrl2', ['$scope', '$http', function ($scope, $http) {
    /* -- INITIALIZATION -- */
    //
    // I/O CATALOGUES (ng-repeat loops over this to create select elements)
    $scope.inputSchema = [];
    $scope.outputSchema = [];
    // here, each 'row' will contain the next dropdown.
    var dummy = [
        {
            "columns": [
                {
                    "ucd": "obs.param",
                    "tableid": 156,
                    "description": "SDSS run number",
                    "units": "-",
                    "name": "RUN",
                    "columnid": 5085
                },
                {
                    "ucd": "meta.code.status",
                    "tableid": 156,
                    "description": "See SDSS photoobj table",
                    "units": "-",
                    "name": "STATUS",
                    "columnid": 5084
                },
                {
                    "ucd": "phot.mag;em.opt",
                    "tableid": 156,
                    "description": "DR6 mag",
                    "units": "mag",
                    "name": "MODELMAG_Z",
                    "columnid": 5083
                },
                {
                    "ucd": "phot.mag;em.opt.I",
                    "tableid": 156,
                    "description": "DR6 mag",
                    "units": "mag",
                    "name": "MODELMAG_I",
                    "columnid": 5082
                },
                {
                    "ucd": "phot.mag;em.opt.R",
                    "tableid": 156,
                    "description": "DR6 mag",
                    "units": "mag",
                    "name": "MODELMAG_R",
                    "columnid": 5081
                },
                {
                    "ucd": "phot.mag;em.opt",
                    "tableid": 156,
                    "description": "DR6 mag",
                    "units": "mag",
                    "name": "MODELMAG_G",
                    "columnid": 5080
                },
                {
                    "ucd": "phot.mag;em.opt.U",
                    "tableid": 156,
                    "description": "DR6 mag",
                    "units": "mag",
                    "name": "MODELMAG_U",
                    "columnid": 5079
                },
                {
                    "ucd": "phot.mag;em.opt",
                    "tableid": 156,
                    "description": "DR6 mag",
                    "units": "mag",
                    "name": "PETROMAG_Z",
                    "columnid": 5078
                },
                {
                    "ucd": "phot.mag;em.opt.I",
                    "tableid": 156,
                    "description": "DR6 mag",
                    "units": "mag",
                    "name": "PETROMAG_I",
                    "columnid": 5077
                },
                {
                    "ucd": "phot.mag;em.opt.R",
                    "tableid": 156,
                    "description": "DR6 mag",
                    "units": "mag",
                    "name": "PETROMAG_R",
                    "columnid": 5076
                },
                {
                    "ucd": "phot.mag;em.opt",
                    "tableid": 156,
                    "description": "DR6 mag",
                    "units": "mag",
                    "name": "PETROMAG_G",
                    "columnid": 5075
                },
                {
                    "ucd": "phot.mag;em.opt.U",
                    "tableid": 156,
                    "description": "DR6 mag",
                    "units": "mag",
                    "name": "PETROMAG_U",
                    "columnid": 5074
                },
                {
                    "ucd": "phys.angSize;em.opt.R",
                    "tableid": 156,
                    "description": "Radius containing 50% of Petrosian flux",
                    "units": "arcsec",
                    "name": "PETROR50_R",
                    "columnid": 5073
                },
                {
                    "ucd": "phys.angSize;em.opt.R",
                    "tableid": 156,
                    "description": "Radius containing 90% of Petrosian flux",
                    "units": "arcsec",
                    "name": "PETROR90_R",
                    "columnid": 5072
                },
                {
                    "ucd": "phys.absorption.gal;em.opt.R",
                    "tableid": 156,
                    "description": "r-band Galactic extinction",
                    "units": "mag",
                    "name": "EXTINCTION_R",
                    "columnid": 5071
                },
                {
                    "ucd": "meta.code.qual;phot;em.opt.R",
                    "tableid": 156,
                    "description": "See SDSS photoobj table",
                    "units": "-",
                    "name": "FLAGS_R",
                    "columnid": 5070
                },
                {
                    "ucd": "phot.mag;em.opt.R",
                    "tableid": 156,
                    "description": "3-arcsec fiber magnitude",
                    "units": "mag",
                    "name": "FIBERMAG_R",
                    "columnid": 5069
                },
                {
                    "ucd": "phot.mag;em.opt.R",
                    "tableid": 156,
                    "description": "PSF magnitude",
                    "units": "mag",
                    "name": "PSFMAG_R",
                    "columnid": 5068
                },
                {
                    "ucd": "phys.angSize;em.opt.R",
                    "tableid": 156,
                    "description": "Petrosian radius",
                    "units": "arcsec",
                    "name": "PETRORAD_R",
                    "columnid": 5067
                },
                {
                    "ucd": "meta.code.class",
                    "tableid": 156,
                    "description": "See SDSS photoobj table",
                    "units": "-",
                    "name": "PRIMTARGET",
                    "columnid": 5066
                },
                {
                    "ucd": "meta.code.qual;phot",
                    "tableid": 156,
                    "description": "See SDSS photoobj table",
                    "units": "-",
                    "name": "FLAGS",
                    "columnid": 5065
                },
                {
                    "ucd": "pos.eq.dec",
                    "tableid": 156,
                    "description": "J2000 coordinate",
                    "units": "deg",
                    "name": "DEC",
                    "columnid": 5064
                },
                {
                    "ucd": "pos.eq.ra",
                    "tableid": 156,
                    "description": "J2000 coordinate",
                    "units": "deg",
                    "name": "RA",
                    "columnid": 5063
                },
                {
                    "ucd": "meta.id",
                    "tableid": 156,
                    "description": "SDSS objid",
                    "units": "-",
                    "name": "OBJID",
                    "columnid": 5062
                },
                {
                    "ucd": "meta.id;meta.main",
                    "tableid": 156,
                    "description": "Unique GAMA ID of object",
                    "units": "-",
                    "name": "CATAID",
                    "columnid": 5061
                }
            ],
            "contact": "Ivan Baldry <ikb@astro.livjm.ac.uk>",
            "DMU": "InputCat",
            "version": "v05",
            "catalogId": 156,
            "description": "This DMU provides various input catalogues for the spectroscopy.",
            "name": "InputCatA"
        },
    ];

    struccounter = 0;
    function objStruct(obj, struccounter) {
        for (var k in obj) {
            // console.log('Function call ' + struccounter + ' key ' + k);
            if (typeof obj[k] == "object" && obj[k] !== null) {
                // console.log('typeof obj[' + k + '] == "object"');
                // console.log('RECURSE - - - - - - - - - - - - -  obj[' + k + ']');
                struccounter++;
                objStruct(obj[k], struccounter);

            } else {
                //console.log('typeof obj[' + k + '] ==  ' + typeof obj[k]);
            }
            // if (!foo.hasOwnProperty(key)){
            //     continue;
            // }
        }
    };

    // objStruct(dummy, struccounter)

    function getData() {
        return $.ajax({
            'async': false,
            'global': false,
            'url': urlCataloguesGlobal,
            'dataType': "json"
        });
    }

    function fBuildSchema(data) {
        // RUN once, populate the schema browser dropdowns
        $scope.inputSchema.push([]);
        $scope.inputSchema[0] = data;
    };

    function fMapColumnNames(data){
        var description = ["name", "contact", "columns", "DMU", "description", "version", "catalogId", "dmu_description", "ticked", "columnid", "units", "tableid", "ucd" ];
        var description_formatted = ["Name", "Contact", "Columns", "DMU", "Description", "Version", "Catalog ID", "DMU Description", "ticked", "Column ID", "Units", "Table ID", "UCD" ];
        var description_string = data;
        description.forEach(function(val, i){
           // Update the description string if a value is found in the array above
           if (data == val){
               description_string = description_formatted[i];
           };
        });
        return description_string;
    };


    getData().done(fBuildSchema);

    // the dropdown needs to take the data from output schema... here is always taking row 0.
    // dropdown should just populate the immediate thingy, remove the looping over outputshema, pass index
    $scope.fDropClick = function (key) {

        var restricted_arr = ['ticked', 'columns', 'contact'];

        // angular.forEach($scope.outputSchema, function (value, key) {
        // current dropdown (row) == key
        var key = key;
        angular.forEach($scope.outputSchema[key], function (valuea, keya) {
            // keya == 0 (each in arr)
            $('#schema-element-' + key + '  .information dl').html('')
            $('#schema-element-' + key + '  .description').html('')
            var descriptions = [];
            angular.forEach($scope.outputSchema[key][keya], function (valueb, keyb) {
                descriptions.push(keyb);
                // Negotiate output by type
                // console.log('typeof obj['+keyb+'] ==  '+typeof valueb);
                // Reminder: Javascript spec typeof(null) == obj (legacy standard)
                if ((typeof valueb == 'object') && (valueb !== null)) {
                    var temp = Object.keys($scope.inputSchema).length;
                    //delete inputschema beyond this click.
                    // iterate baackwardds over arr and stop deleting at this point.
                    for (var i = temp; i>0; i--){
                        //console.log('i'+i);console.log('key'+key)
                        // never remove the first dropdown
                        if(i>0 && i > key){
                            //console.log(angular.toJson($scope.inputSchema))
                            $scope.inputSchema.splice(i,1);
                            //clear previous rows
                            $('#schema-element-' + i + '  .information dl').html('')
                            $('#schema-element-' + i + '  .description').html('')
                        };
                    };

                    //populate another dropdown
                    $scope.inputSchema.push([]);
                    // here - don't add to last object, but next object and clear the rest.

                    // Add data to last key in object (not arr so need to be careful here)
                    var k = Object.keys($scope.inputSchema).length - 1;
                    $scope.inputSchema[k] = valueb;
                }
                // Sort alphabetically...

                if (restricted_arr.indexOf(keyb) < 0) {
                    $('#schema-element-' + key + ' .information dl').append("<dt>" + fMapColumnNames(String(keyb)) + "</dt><dd>" + String(valueb) + " </dd>");
                }
                // if (keyb == 'description') {
                //     $('#schema-element-' + key + ' p.description').append(String(valueb));
                // }
                if (keyb == 'contact') {
                    var email = valueb.match("<(.*)>")[1];
                    $('#schema-element-' + key + ' .information dl').append("<dt>" + fMapColumnNames(String(keyb)) + " </dt><dd><a href='mailto:" + email + "'>" + String(valueb) + "</a></dd>");
                    if (null != email) {

                    } else {
                        // TODO depends on other support detail types - may need helper function here
                    }
                }
            });
        });
    };
}]);