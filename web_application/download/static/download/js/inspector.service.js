// IIFE: Immediately invoked function expression: (function(){})() (where window == global scope)
// Create an inspector service
(function(angular, SchemaInspector){
    // This service provides a Schema Inspector for the download data.
    "use strict";
    console.log('inspector.service.js');

    //organise data into nested structure
    // sample
    //  -- ao
    //      -- trait
    //           -- subtrait
    //           -- traitproperty

    // Provide a service for each level - validation and sanitization from array into obj

    var app = angular.module('DCApp');

    // Inject in $cookieStore
    app.factory('InspectorService', function($cookieStore){

        // Angular factories return service objects
        return {

            nestedData: function(data){
                // data will be a single array input (["sami", "221375", "line_map-OIII5007", ""])
                var validation = {
                    type: 'array',
                    splitWith: ','
                };
                SchemaInspector.validate(validation, data, function (err, result) {
                    if (!result.valid)
                        return console.log(result.format());
                });

                var data_obj = {}, o = data_obj;
                for(var i = 0; i < data.length; i++) {
                    if(data[i]!=="" && data[i]!==''){
                        o = o[data[i]] = {};
                    }
                }

                return data_obj;
            }

        }
    })
})(window.angular, window.SchemaInspector);
