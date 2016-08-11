// IIFE: Immediately invoked function expression: (function(){})() (where window == global scope)
(function(angular, AvailableProducts){
    // This service provides a Schema Inspector for the download data.
    "use strict";
    console.log('availableproducts.service.js');

    var app = angular.module('DCApp');

    // Get Available trait data from json endpoint
    app.factory('AvailableProductsService', function($http){

        var getProducts = function() {
            // then() returns a new promise. We return that new promise.
            // that new promise is resolved via response.data, i.e. the ponies

            return $http.get(GLOBAL_URL).then(function (response) {
                return response.data;
            });
        };

        return {
            getProducts: getProducts
        };



        // console.log("GLOBAL_URL", GLOBAL_URL);
        //
        // return {
        //
        //     getProducts: function() {
        //         var config = {headers:  {
        //                 'Accept': 'application/json'
        //             }
        //         };
        //         $http.get(GLOBAL_URL, config)
        //           .then(function success(response) {
        //               console.log(response);
        //               return response.data.available_traits;
        //           }, function error(response) {
        //               return response.status
        //           });
        //     }
        // }
    })
})(window.angular, window.AvailableProducts);
