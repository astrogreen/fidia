console.log('directives.js');
(function(angular){
    "use strict";

    var app = angular.module('DCApp');

    function caretToTick(elem){
        // Switch caret for green tick
        elem.html('<i class="fa fa-check text-success"></i>');
    }

    function disableFormat(elem, format){
        elem.html(format + '<small class="sub-heading"> ADDED</small>')
            .attr('disabled', true)
            .addClass('disabled')
            .parent('li').addClass('disabled');
    }
    if (!Date.now) {
        Date.now = function() { return new Date().getTime(); }
    }
    // DownloadDirective
    app.directive('miniDownload', function(DownloadService, StorageService, $q){
        return{
            // Create in an isolated scope
            scope:{},
            restrict: 'AE',
            replace: true,
            template: '<span class="badge animated">{{ item_count }}</span>',
            // templateUrl: '/static/download/js/templates/mini-download.html',
            link: function(scope, elem, attr){
                scope.item_count = 0;

                scope.$on('storageUpdated', function (event) {
                    getItemCount();
                });

                function getItemCount(){
                    var deferred = $q.defer();
                    StorageService.getStorageContents().then(function (data) {
                        scope.item_count = StorageService.getItemCount(data)
                        deferred.resolve(data);
                    }).catch(function () {
                        deferred.reject();
                    });
                };
                getItemCount();

            }
        };
    });

    app.directive('addDownloadButton', function(DownloadService, StorageService, $q){
        return {
            // E for Element
            // A for Attribute
            // C for Class
            // e.g., by adding a restrict property with the value "A", the directive can only be invoked by attributes.
            restrict: 'E',
            scope: {
                // 3 types of bindings for scope properties
                // @ == string
                // & == one-way binding
                // = == two-way binding
                formats: "="
            },
            replace: true,
            templateUrl: '/static/download/js/templates/add-download-button.html',
            link: function(scope, elem, attr){

                // define targets on scope.
                scope.caret_button = angular.element(elem[0].querySelector('.add-to-download-caret'));

                // populate the dropdown
                scope.populateDropdown = function(){
                    if (typeof attr.formats !== 'undefined' && attr.formats.length > 0){
                        // Parse the valid json string (after replacing ' for ") as a valid JS object
                        scope.formats = JSON.parse(attr.formats.replace(/'/g, '"'));
                    };
                };

                scope.constructItem = function() {
                    // DO THIS ONLY ONCE

                    // Construct an item per format (on the local scope) from the element attributes
                    // items = {format: item, format: item}
                    if (typeof attr.url !== 'undefined' && typeof scope.formats !== 'undefined') {
                        scope.items = {};

                        var lastChar = attr.url.substr(-1);     // Selects the last character
                        if (lastChar != '/') {                  // If the last character is not a slash
                           attr.url = attr.url + '/';           // Append a slash to it.
                        }
                        for (var f = 0; f< scope.formats.length; f++){
                            // Create temp item, append the format type
                            var item ={};
                            var temp = attr.url;
                            // ?format=type

                            item['id']=temp+'?format='+scope.formats[f];
                            item['format'] = scope.formats[f];

                            if (attr.options){item['options'] = attr.options;};
                            if (attr.prettyname){item['prettyname'] = attr.prettyname;};

                            // Shape of objects is as: scope.items ["json"] = item == {id: "http://127.0.0.1:8000/asvo/data-browser/sami/9352/spectral_map-red/?format=json", options: "", format: "json"}
                            scope.items[scope.formats[f]] = item;
                        }

                    } else if (typeof attr.url !== 'undefined' && typeof attr.options !== 'undefined' && typeof scope.formats == 'undefined') {
                        console.log(attr.url);
                        console.log(attr.options);
                            // scope.items['SAMPLE'] = item;
                    } else {
                        console.log('Error. Cannot find id (url) has been set for this add-to-download-' +
                            'directive. Please contact the site administrator. ');
                    }
                };

                angular.element(document).ready(function() {
                    scope.populateDropdown();
                    scope.constructItem();

                    var deferred = $q.defer();

                    StorageService.getStorageContents().then(function (storage_data) {

                        // CHECK for this in stored data already and disable the button.
                        angular.forEach(storage_data, function(storage_value, id){
                            if (undefined != scope.formats){
                                angular.forEach(scope.items, function(v, k){
                                    var temp = v['id'];
                                    if (id == temp){
                                        // Already in cart, disable this element
                                        var format = v['format'];
                                        caretToTick(scope.caret_button);
                                        scope.format_dropdown = angular.element(elem[0].querySelector("ul.dropdown-menu li ."+format));
                                        disableFormat(scope.format_dropdown, format);
                                    } else {

                                    }
                                });
                            }
                        });
                        deferred.resolve();
                    }).catch(function () {
                        deferred.reject();
                    });

                });

                scope.addItem = function(f){
                    // Get clicked item from scope.items by format
                    scope.item = scope.items[f];

                    var deferred = $q.defer();

                    StorageService.addItemToStorage(scope.item).then(function () {
                        // Update local items object with that from storage
                        StorageService.getStorageContents()

                        $('#mini-download').addClass('bounce')
                        .one('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function(){
                            $('#mini-download').removeClass('bounce');
                        });

                        // Change button states
                        caretToTick(scope.caret_button);

                        scope.format_dropdown = angular.element(elem[0].querySelector("ul.dropdown-menu li ."+f));

                        disableFormat(scope.format_dropdown, f);

                        angular.element(elem[0].querySelector(".dropdown-menu ul li ."+f))
                            .html('added')

                        deferred.resolve();
                    }).catch(function () {
                        deferred.reject();
                    });

                    return deferred.promise;

                };

                scope.chooseFormat = function(f){
                    scope.item['format'] = f;
                };


            }
        }
    });

    // DownloadDirective
    app.directive('sampleDownload', function(StorageService, $q){
        return{
            // Create in an isolated scope
            scope:{},
            // scope:{bind:"=isDisabled"},
            // transclude:true,
            restrict: 'AE',
            replace: true,
            template: '<button class="btn btn-default" id="available-products" ng-click="addItem()"><i class="fa fa-download"></i> Add to Download</button>',
            // templateUrl: '/static/download/js/templates/add-sample-data-products-to-download-button.html',
            link: function(scope, elem, attr){
                scope.isDisabled = {};

                scope.constructItem = function() {
                    // DO THIS ONLY ONCE ON DOWNLOAD

                    // Construct an item per format (on the local scope) from the element attributes

                    if (typeof attr.url !== 'undefined') {
                        scope.item = {};

                        var lastChar = attr.url.substr(-1);     // Selects the last character
                        if (lastChar != '/') {                  // If the last character is not a slash
                           attr.url = attr.url + '/';           // Append a slash to it.
                        }

                        scope.item['id'] = attr.url;
                        // scope.item['id'] = attr.url+Date.now();
                        // Here, we have to create a fake time-stamped id to track by, so that multiple samples at the same url can be downloaded

                        scope.item['url'] = attr.url;

                        if (typeof attr.options !== 'undefined'){
                            scope.item['options'] = JSON.parse(attr.options);
                        }
                        // Shape of object is as: scope.item = {id: "http://127.0.0.1:8000/asvo/query-history/2", options: "blah"}

                    } else {
                        console.log('Error. Cannot find id (url) has been set for this sample-download-' +
                            'directive. Please contact the site administrator. ');
                    }
                };

                angular.element(document).ready(function() {

                    var deferred = $q.defer();

                    StorageService.getStorageContents().then(function (storage_data) {

                        // CHECK for this in stored data already and disable the button.
                        angular.forEach(storage_data, function(storage_value, id){
                            if (id == attr.url){
                                $('#available-products').html('<i class="fa fa-check text-success"></i> Added');
                                scope.$parent.isDisabled.state = true;
                            }
                        });
                        deferred.resolve();
                    }).catch(function () {
                        deferred.reject();
                    });

                });

                // scope.addItem = function(){
                //
                //     scope.constructItem();
                //
                //     var items = DownloadService.getItems();
                //
                //     // If pre-existing sample item, copy into temporary variable
                //     angular.forEach(items, function (data, id) {
                //         if (id == scope.item.id) {
                //             var temporary = items[scope.item.id];
                //             // Now remove the previous item from the cookie
                //             DownloadService.removeItem(scope.item.id);
                //         }
                //     });
                //
                //
                //     // Pass the item into the addItem method of DownloadService
                //     // populate the items obj for this particular view before start writing in to the cookie
                //     DownloadService.getItems();
                //     DownloadService.addItem(scope.item);
                //     DownloadService.getItemCount();
                //
                //     $('#mini-download').addClass('bounce')
                //         .one('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function(){
                //             $('#mini-download').removeClass('bounce');
                //         });
                //     $('#available-products').html('<i class="fa fa-check text-success"></i> Added');
                //     // Parent scope has access to the state of this directive should it wish to change states after submit
                //     scope.$parent.isSubmitted.state = true;
                //     scope.$parent.isDisabled.state = true;
                // };

                scope.addItem = function(){
                    /**
                     *  Add the sample to the storage/ route
                     *  If this id already exists, remove it from the storage array and re-submit
                     *  This function is unique, as it allows data to be written
                     */

                    scope.constructItem();
                    var deferred = $q.defer();

                    StorageService.addItemToStorage(scope.item, true).then(function () {
                        // Update local items object with that from storage
                        StorageService.getStorageContents()

                        $('#mini-download').addClass('bounce')
                            .one('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function(){
                                $('#mini-download').removeClass('bounce');
                            });
                        $('#available-products').html('<i class="fa fa-check text-success"></i> Added');
                        // Parent scope has access to the state of this directive should it wish to change states after submit
                        scope.$parent.isSubmitted.state = true;
                        scope.$parent.isDisabled.state = true;

                        deferred.resolve();
                    }).catch(function () {
                        deferred.reject();
                    });

                    return deferred.promise;

                };

                scope.updateItem = function(){

                };

            }
        };
    });

})(window.angular);