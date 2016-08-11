console.log('availableproducts.components.js');
(function(angular){
    "use strict";

    var app = angular.module('DCApp');

    app.component("availableProducts", {
        templateUrl:'/static/query/js/available-products/templates/availableProducts.html',
        bindings:{surveys:'@', schemaurls:'@'},
        controller: 'AvailableProductsController',
        controllerAs: 'apctrl'
    });

})(window.angular);