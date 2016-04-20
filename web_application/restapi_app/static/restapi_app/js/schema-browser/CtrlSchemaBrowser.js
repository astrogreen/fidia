app.controller('Ctrl2', ['$scope', '$http', function ($scope, $http) {
    /* -- INITIALIZATION -- */
    //
    // I/O CATALOGUES (ng-repeat loops over this to create select elements)
    $scope.inputSchema = [];
    $scope.outputSchema = [];
    // here, each 'row' will contain the next dropdown.


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

    getData().done(fBuildSchema);


    $scope.fDropClick = function () {
        var restricted_arr = ['ticked', 'columns', 'description'];

        angular.forEach($scope.outputSchema, function (value, key) {
            // current dropdown == key
            console.log('depth');
            angular.forEach($scope.outputSchema[key], function (valuea, keya) {
                $('#schema-browser .information dl').html('')
                $('#schema-browser .description').html('')
                angular.forEach($scope.outputSchema[key][keya], function (valueb, keyb) {
                    // Sort alphabetically
                    if (restricted_arr.indexOf(keyb) < 0) {
                        $('#schema-browser .information dl').append("<dt>"+ String(keyb) + "</dt><dd>" + String(valueb) + " </dd>");
                    }
                    if (keyb == 'description'){
                        $('#schema-browser p.description').append(String(valueb));
                    }
                });
            })
        })
        // Populate HTML info panels

        // Populate next dropdown
    };
    // var nodeCataloguesGlobal = (function () {
    //     var json = null;
    //     $.ajax({
    //         'async': false,
    //         'global': false,
    //         'url': urlCataloguesGlobal,
    //         'dataType': "json",
    //         'success': function (data) {
    //             fBuildSchema(data);
    //         },
    //         'error': function(err){
    //             // Fail silently
    //         }
    //     });
    //     return json;
    // })();

    //
    //
    // var fBuildSchema = function(data){
    //     // RUN once, populate the schema browser dropdowns
    //     $scope.inputSchema.push([]);
    //
    //     $scope.inputSchema[0]=data;
    //     console.log($scope.inputSchema)
    //     angular.forEach($scope.inputSchema, function(value,key){
    //         console.log(value)
    //         console.log(key);
    //     });
    // };
    //
    // function fPopulateNext(data){
    //
    // }
}]);