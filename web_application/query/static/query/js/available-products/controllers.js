console.log('availableproducts.controllers.js');
(function(angular){
    "use strict";

    var app = angular.module('DCApp');

    app.controller('AvailableProductsController', function($scope, AvailableProductsService, DownloadService, $window){

        var ctrl = this; // create alias to this to avoid closure issues

        // Constants on ctrl scope
        ctrl.surveys = {};
        ctrl.sample_url = $window.location.pathname;
        ctrl.download_url = DOWNLOAD_URL;
        ctrl.temporary = {};

        // Set these on scope to allow two-way data binding
        $scope.availabledata = {};
        $scope.selection = {};
        $scope.download = {};

        $scope.isDisabled={};
        $scope.isDisabled.state=false;
        $scope.isSubmitted={};
        $scope.isSubmitted.state=false;
        console.log('controller')

        try {
            ctrl.surveys = JSON.parse((ctrl.schemaurls).replace(/'/g, '"'));
            angular.forEach(ctrl.surveys, function(url, survey){
                $scope.availabledata[survey] = {};
                AvailableProductsService.getProducts(url).then(function (data) {

                    // Go through the data and add a selected property to each trait
                    angular.forEach(data.available_traits, function(v,k){
                        angular.forEach(v.traits, function(t,name){
                            t['branch_list'] = {};
                            angular.forEach(t.branches, function(branch_url,branch_name){
                                var temp = {name:branch_name, selected:false, url:branch_url};
                                t['branch_list'][branch_name]=temp;
                            });
                            t['branches'] = t['branch_list'];
                            delete t['branch_list'];
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

        // watch the availabledata to see if any have been selected
        $scope.$watch('availabledata', function(newVal, oldVal) {
            $scope.selection={};
            $scope.download={};
            angular.forEach(newVal, function(schema,survey){
                angular.forEach(schema.available_traits, function(v, k){
                    angular.forEach(v.traits, function(t,trait_name){
                        angular.forEach(t.branches, function(branch) {
                            if (branch.selected == true) {
                                if (typeof $scope.selection[survey] == "undefined") {
                                    $scope.selection[survey] = [];
                                    $scope.download[survey] = [];
                                }
                                //adds: {trait_key: "line_map-HALPHA:1_comp", pretty_name: "Line Map — Hα:1_comp"}
                                $scope.selection[survey].push({
                                    pretty_name: t.pretty_name,
                                    trait_name: trait_name,
                                    trait_key: trait_name + ':' + branch.name,
                                    trait_type: k,
                                    branch: branch.name
                                });

                                $scope.download[survey].push({
                                    pretty_name: t.pretty_name,
                                    trait_name: trait_name,
                                    trait_key: trait_name + ':' + branch.name,
                                    trait_type: k,
                                    branch: branch.name
                                })
                            };
                        });
                    })
                })
            });
        }, true);

        ctrl.uncheckProduct = function(survey, trait_type, trait_name, trait_key, branch) {
            // console.log(survey, trait_type, trait_name, trait_key, branch);

            // console.log($scope.availabledata[survey]['available_traits'][trait_type]['traits'][trait_name]['branches'][branch]['selected']);
            $scope.availabledata[survey]['available_traits'][trait_type]['traits'][trait_name]['branches'][branch]['selected'] = false;
        };
        ctrl.emptyList = function(){
            $scope.download = {};
        };

        ctrl.reapplyState = function(){
            var items = DownloadService.getItems();

            // Go through the cookie items and get the trait_type, trait_name and branches that have been previously selected.
            // Switch their selected property to 'true'
            angular.forEach(items, function (data, id) {
                if (id == ctrl.sample_url) {
                    angular.forEach(data.options, function (product, survey) {
                        angular.forEach(product, function (value, key) {
                            var trait_type = value.trait_type;
                            var trait_name = value.trait_name;
                            var branch = value.branch;
                            // console.log($scope.availabledata[survey]['available_traits'][trait_type]['traits'][trait_name]['branches'][branch]['selected'])
                            $scope.availabledata[survey]['available_traits'][trait_type]['traits'][trait_name]['branches'][branch]['selected'] = true;
                        });
                    });
                }
            });

            // Allow submitting again
            $scope.isDisabled.state=false;
            $scope.isSubmitted.state=false;

            $('#available-products').html('<i class="fa fa-download"></i> Update Download');

        }

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