console.log('availableproducts.controllers.js');
(function(angular){
    "use strict";

    var app = angular.module('DCApp');

    app.controller('AvailableProductsController', function($scope, AvailableProductsService, SessionService, $window, $q){

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

        try {

            ctrl.surveys = JSON.parse((ctrl.schemaurls).replace(/'/g, '"'));

            angular.forEach(ctrl.surveys, function(url, survey){
                $scope.availabledata[survey] = {};
                AvailableProductsService.getProducts(url).then(function (data) {
                    // Go through the data and add a selected property to each trait

                    angular.forEach(data.schema.trait_types, function(trait_type_value, trait_type_key){

                        // console.log('---'+trait_type_key+'---');

                        angular.forEach(trait_type_value.trait_qualifiers, function(trait_qualifier_value, trait_qualifier_key){
                            // console.log('-'+trait_qualifier_key+'-');

                            angular.forEach(trait_qualifier_value.branches, function(trait_branch_value,trait_branch_key){

                                angular.forEach(trait_branch_value.versions, function(trait_version_value,trait_version_key){
                                    trait_version_value['selected'] = false;

                                    // If the trait qualifier can be collapsed, do so
                                    var trait_key = '';
                                    if (trait_qualifier_key != "null"){
                                        trait_key = trait_type_key+'-'+trait_qualifier_key+':'+trait_branch_key+'('+trait_version_key+')';
                                    } else {
                                        trait_key = trait_type_key+':'+trait_branch_key+'('+trait_version_key+')';
                                    }
                                    trait_version_value['url'] = trait_key;
                                    trait_version_value['trait_key'] = trait_key;
                                });


                            });
                        });
                    });
                    // availabledata["sami"] = object containing schema with :selected: attribute on branch + version
                    $scope.availabledata[survey] = data.schema.trait_types;

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
                angular.forEach(schema, function (trait_type_value, trait_type_key) {
                    angular.forEach(trait_type_value.trait_qualifiers, function (trait_qualifier_value, trait_qualifier_key) {
                        angular.forEach(trait_qualifier_value.branches, function (trait_branch_value, trait_branch_key) {
                            angular.forEach(trait_branch_value.versions, function (trait_version_value, trait_version_key) {

                                if (trait_version_value.selected == true) {
                                    if (typeof $scope.selection[survey] == "undefined") {
                                        $scope.selection[survey] = [];
                                        $scope.download[survey] = [];
                                    }
                                    $scope.selection[survey].push({
                                        trait_key: trait_version_value.trait_key,
                                        pretty_names:{
                                            'trait_type':trait_type_value.pretty_name,
                                            'trait_qualifier':trait_qualifier_value.pretty_name,
                                            'branch':trait_branch_value.pretty_name,
                                            'version':trait_version_value.pretty_name
                                        }
                                    });

                                    $scope.download[survey].push({
                                        // pretty_name: t.pretty_name,
                                        // trait_name: trait_name,
                                        // trait_key: trait_name + ':' + branch.name,
                                        // trait_type: k,
                                        // branch: branch.name
                                    })
                                }

                            });


                        });
                    });
                });

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


            var deferred = $q.defer();

            SessionService.getStorageContents().then(function (storage_data) {

                // Go through the cookie items and get the trait_type, trait_name and branches that have been previously selected.
                // Switch their selected property to 'true'
                angular.forEach(storage_data, function (data, id) {
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
                deferred.resolve();
            }).catch(function () {
                deferred.reject(data);
                ctrl.error = true;
                ctrl.text = 'Unable to get stored data';
                ctrl.status = data.status;
            });


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