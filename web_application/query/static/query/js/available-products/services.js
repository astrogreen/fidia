// IIFE: Immediately invoked function expression: (function(){})() (where window == global scope)
(function(angular, AvailableProducts){
    // This service provides a Schema Inspector for the download data.
    "use strict";
    console.log('availableproducts.service.js');

    var app = angular.module('DCApp');

    // Get Available trait data from json endpoint
    app.factory('AvailableProductsService', function($http){

        // var getProducts = function() {
        //     // then() returns a new promise. We return that new promise.
        //     // that new promise is resolved via response.data, i.e. the ponies
        //
        //     return $http.get(url).then(function (response) {
        //         return response.data;
        //     });
        // };

        return {
            // getProducts: getProducts
            getProducts: function(url) {
                // then() returns a new promise. We return that new promise.
                // that new promise is resolved via response.data, i.e. the ponies

                return $http.get(url).then(function (response) {
                    return response.data;
                });
            }
        }
    })
})(window.angular, window.AvailableProducts);
