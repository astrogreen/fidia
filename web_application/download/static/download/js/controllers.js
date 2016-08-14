console.log('controllers.js');
(function(angular){
    "use strict";

    var app = angular.module('DCApp');
    
    // Create 'fixtures'
    var dummy_data_url = "/static/download/js/dummy-data.json";
    app.controller('DummyData', function($scope, $http){
       $http.get(dummy_data_url).then(function(response){
           $scope.data = response.data;
           console.log('success - dummy data in $scope.data')
       })
    });

    // Inject in the DownloadService
    app.controller('DownloadController', function($scope, DownloadService, StorageService, $q){
        // console.log('-------DownloadController------');

        var ctrl = this; // create alias to this to avoid closure issues
        // Here, we've registered properties on $scope.ctrl rather than on $scope (all modules have global access
        // to $scope - which may result in unwanted cross-talk

        // Set the items on the scope to the items in the DownloadService using the getItems method
        ctrl.items = {};

        // ctrl.items = DownloadService.getItems();
        //
        // ctrl.summary = DownloadService.getSummary();
        //
        // ctrl.prettyCookie = DownloadService.prettifyCookie(ctrl.items);
        //
        // ctrl.download = DownloadService.download();
        //
        // ctrl.addItem = function(item){
        //     // Pass the item into the addItem method of the DownloadService
        //     DownloadService.addItem(item);
        // };
        //
        // ctrl.getItemCount = function(){
        //     // Return the item count from the DownloadService
        //     return DownloadService.getItemCount();
        // };
        //
        // ctrl.removeItem = function(id){
        //     // Pass item id into the removeItem method of DownloadService
        //     DownloadService.removeItem(id);
        //     ctrl.summary = DownloadService.getSummary();
        //     ctrl.prettyCookie = DownloadService.prettifyCookie(ctrl.items);
        //     ctrl.download = DownloadService.download();
        // };
        //
        // ctrl.emptyDownload = function(){
        //     DownloadService.emptyDownload($scope.items);
        //     ctrl.summary = DownloadService.getSummary();
        // };


        // NEW STORAGE METHOD - - - - - - - - -
        var ctrl = this; // create alias to this to avoid closure issues
        // Here, we've registered properties on $scope.ctrl rather than on $scope (all modules have global access
        // to $scope - which may result in unwanted cross-talk

        // Set the items on the scope to the items in the DownloadService using the getItems method
        ctrl.items = {};
        ctrl.pretty_data = {}, ctrl.summary = {}, ctrl.item_count = {}

        ctrl.getItems = function(){
            /**
             * Get the data from storage/ and update the local items object.
             * ctrl.items is used as local representation of the data so only one request is made.
             */

            var deferred = $q.defer();
            var url = '/asvo/storage/1/';

            StorageService.getStorageContents().then(function (data) {
                // Set the local items object
                ctrl.items = data
                deferred.resolve(data);
            }).catch(function () {
                deferred.reject(data);
                ctrl.error = true;
                ctrl.text = 'Unable to get stored data at ' + url;
                ctrl.status = data.status;
            });
            return deferred.promise;
        };

        ctrl.getItems();

        ctrl.addItemToStorage = function(item){
            // Pass the item into the addItem method of the DownloadService
            StorageService.addItemToStorage(item);
        };

        ctrl.removeItem = function(id){
            // Pass item id into the removeItem method of DownloadService
            StorageService.removeItem(id);
        };

        // ctrl.getStorageItemCount = function(){
        //     /**
        //      * Resolves a promise from the getItems Service for the data from /storage/
        //      * then provides the count of objects
        //      */
        //     ctrl.getItems().then(function(data){
        //         StorageService.getItemCount(data);
        //     }).catch(function(){
        //         console.log('Data could not be counted.')
        //     })
        // };

        ctrl.emptyDownload = function(){
            StorageService.emptyDownload();
        };

        $scope.$watch('ctrl.items', function(newVal, oldVal) {
            /**
             * Watch the local items object - if it changes, prettify and update template
             * then provides a summarized version for the template
             */
            ctrl.pretty_data = StorageService.prettifyData(ctrl.items);
            ctrl.summary = StorageService.getSummary(ctrl.items);
            ctrl.item_count = StorageService.getItemCount(ctrl.items);
            ctrl.download = StorageService.prepareDownload(ctrl.items);

        }, true);

        $scope.$on('storageUpdated', function (event) {
            ctrl.getItems();
        });

        // ctrl.PrepareDownload = function(){
        //     /**
        //      * Resolves a promise from the getItems Service for the data from /storage/
        //      * then provides a summarized version for the template
        //      */
        //     ctrl.getItems().then(function(data){
        //         return StorageService.prepareDownload(data);
        //     }).catch(function(){
        //         console.log('Data could not be prepared for Download.')
        //     })
        // };



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