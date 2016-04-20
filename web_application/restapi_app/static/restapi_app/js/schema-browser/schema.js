(function() {
    // var app = angular.module('queryBuilder', [ "isteven-multi-select", 'ngSanitize' ]);

    //console.log = function() {};                      // TURN OFF/ON CONSOLE STATEMENTS FOR PRODUCTION

    app.controller('SchemaController', ['$scope', '$timeout', function($scope, $timeout) {
        console.log('test')
    } ]); //end controller

})();





// if ($('#schema-browser').length) {
//     var nodeCataloguesGlobal = (function () {
//         var json = null;
//         // urlCataloguesGlobal='test/'
//         $.ajax({
//             'async': false,
//             'global': false,
//             'url': urlCataloguesGlobal,
//             'dataType': "json",
//             'success': function (data) {
//                 json = data;
//                 fBuildSchemaBrowser(json);
//             },
//             'error': function (xhr, status) {
//                 alert(status);
//             }
//         });
//         return json;
//     })();
//
//     // ENSURE FUNCTION DECLARATION (not expression fBuildSchemaBrowser = function(data)) SO HOISTED
//     function fBuildSchemaBrowser(data) {
//      //yeah nah angular.
//
//
//     };
// };