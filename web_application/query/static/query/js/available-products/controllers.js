console.log('availableproducts.controllers.js');
(function(angular){
    "use strict";

    var app = angular.module('DCApp');

    app.controller('AvailableProductsController', function($scope, AvailableProductsService){
        var ctrl = this; // create alias to this to avoid closure issues
        // Here, we've registered properties on $scope.ctrl rather than on $scope (all modules have global access
        // to $scope - which may result in unwanted cross-talk
        ctrl.myName = 'brian';
        ctrl.surveyName="SAMI";

        AvailableProductsService.getProducts().then(function (data) {
            ctrl.dataproducts = data;
        }).catch(function () {
            $scope.error = 'unable to get the ponies';
        });
        
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