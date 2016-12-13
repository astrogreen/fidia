// IIFE: Immediately invoked function expression: (function(){})() (where window == global scope)
(function(angular, AvailableProducts){
    // This service provides a Schema Inspector for the download data.
    "use strict";
    console.log('availableproducts.service.js');

    var app = angular.module('DCApp');

    // Get Available trait data from json endpoint
    app.factory('AvailableProductsService', function($http){

        return {
            getProducts: function(url) {
                // then returns a new promise, which we return - the new promise is resolved
                // via response.data

                return $http.get(url).then(function (response) {
                    return response.data;
                });
            }

        }
    })
})(window.angular, window.AvailableProducts);
