console.log('availableproducts.components.js');
(function(angular){
    "use strict";

    var app = angular.module('DCApp');

    app.component("availableProducts", {
        templateUrl:'/static/query/js/available-products/templates/availableProductsSingleSurvey.html',
        bindings:{surveys:'@', schemaurls:'@', single:'@'},
        controller: 'AvailableProductsController',
        controllerAs: 'apctrl'
    });


})(window.angular);