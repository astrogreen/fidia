console.log('availableproducts.controllers.js');
(function(angular){
    "use strict";

    var app = angular.module('DCApp');

    app.controller('AvailableProductsController', function($scope, AvailableProductsService){
        var ctrl = this; // create alias to this to avoid closure issues
        ctrl.surveys = {};

        // Set these on scope to allow two-way data binding
        $scope.availabledata = {};
        $scope.selection = [];

        try {
            ctrl.surveys = JSON.parse((ctrl.schemaurls).replace(/'/g, '"'));
            angular.forEach(ctrl.surveys, function(url, survey){
                $scope.availabledata[survey] = {};
                AvailableProductsService.getProducts(url).then(function (data) {

                    // Go through the data and add a selected property to each trait
                    angular.forEach(data.available_traits, function(v,k){
                        angular.forEach(v.traits, function(t,name){
                            t["selected"]= false;
                        })
                    });
                    $scope.availabledata[survey] = data;
                }).catch(function () {
                    ctrl.error = true;
                    ctrl.text = 'Unable to get schema at '+url;
                    ctrl.status = data.status;
                });
            });
        } catch (e) {
            ctrl.error = true;
            ctrl.text = "Incorrect input to available products component. Must be JSON string of survey: url "
        }

        ctrl.addProduct = function(trait_name){
            // iterate through the available data and for those with selected, take out into this array
            angular.forEach($scope.availabledata, function(schema,survey){
                angular.forEach(schema.available_traits, function(v, k){
                    angular.forEach(v.traits, function(t,name){
                        if (name == trait_name){
                            console.log('here')
                            t.selected = true;
                            if ($.inArray(name, ctrl.selection) < 0){
                                ctrl.selection.push(name)
                            }
                        }
                    })
                })
            })
            console.log(ctrl.selection);
        };




    });

    app.filter('isEmpty', [function(){
        return function(object){
            return angular.equals({}, object);
        }
    }])
    app.filter('isNotEmpty', [function(){
        return function(object){
            return ! angular.equals({}, object);
        }
    }])
})(window.angular);