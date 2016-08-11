console.log('availableproducts.controllers.js');
(function(angular){
    "use strict";

    var app = angular.module('DCApp');

    app.controller('AvailableProductsController', function($scope, AvailableProductsService){
        var ctrl = this; // create alias to this to avoid closure issues
        ctrl.surveys = {};
        ctrl.availabledata = {};

        // // Get survey string from component input and parse as arr
        // var surveys = ctrl.surveys.split(',');
        // ctrl.surveys = [];
        // for (var s in surveys){
        //     ctrl.surveys[s] = surveys[s].replace(/ /g,'');
        // }

        // Get url string from component input and parse as arr
        // var urls = ctrl.schemaurls.split(',');
        // ctrl.urls = [];
        // for (var u in urls){
        //     ctrl.urls[u] = surveys[u].replace(/ /g,'');
        // }
        // if (ctrl.urls.length != ctrl.surveys.length){
        //     ctrl.statuserror = true;
        //     ctrl.statustext = "Incorrect inputs to available products component. Must be comma separated strings of surveys and urls. "
        // }

        // // if arrays are same length, great, if not - error
        // for (var s in ctrl.surveys){
        //     ctrl.availabledata[ctrl.surveys[s]] = ctrl.urls[s]
        // }


        try {
            ctrl.surveys = JSON.parse((ctrl.schemaurls).replace(/'/g, '"'));
            angular.forEach(ctrl.surveys, function(url, survey){
                AvailableProductsService.getProducts(url).then(function (data) {
                    ctrl.availabledata[survey] = data;
                    console.log(ctrl.availabledata)
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



        // console.log(JSON.parse((ctrl.schemaurls).replace(/'/g,'"')));



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