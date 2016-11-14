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
    app.controller('DownloadController', function($scope, DownloadService, SessionService, $q){
        // console.log('-------DownloadController------');

        var ctrl = this; // create alias to this to avoid closure issues
        // Here, we've registered properties on $scope.ctrl rather than on $scope (all modules have global access
        // to $scope - which may result in unwanted cross-talk

        // Set the items on the scope to the items in the DownloadService using the getItems method
        ctrl.items = {};

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

            SessionService.getStorageContents().then(function (data) {
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
            SessionService.addItemToStorage(item);
        };

        ctrl.removeItem = function(id){
            // Pass item id into the removeItem method of DownloadService
            SessionService.removeItem(id);
        };

        // ctrl.getStorageItemCount = function(){
        //     /**
        //      * Resolves a promise from the getItems Service for the data from /storage/
        //      * then provides the count of objects
        //      */
        //     ctrl.getItems().then(function(data){
        //         SessionService.getItemCount(data);
        //     }).catch(function(){
        //         console.log('Data could not be counted.')
        //     })
        // };

        ctrl.emptyDownload = function(){
            SessionService.emptyDownload();

            // Resolve bootstrap jQuery modal issue - conflict with angular methodology, which updates rather
            // than injects
            // $('#empty-modal-sm').modal('hide');
            // $('body').removeClass('modal-open');
            // $('.modal-backdrop').remove();
        };

        $scope.$watch('ctrl.items', function(newVal, oldVal) {
            /**
             * Watch the local items object - if it changes, prettify and update template
             * then provides a summarized version for the template
             */
            ctrl.pretty_data = SessionService.prettifyData(ctrl.items);
            ctrl.summary = SessionService.getSummary(ctrl.items);
            ctrl.item_count = SessionService.getItemCount(ctrl.items);
            ctrl.download = SessionService.prepareDownload(ctrl.items);

        }, true);

        $scope.$on('storageUpdated', function (event) {
            ctrl.getItems();
        });

        ctrl.pretty_resource = function(data){
            /** Allows an existing resource to benefit from the prettification of
             * data products in the session data.
             */
            console.log(data);
            // console.log(SessionService.prettifyData(data));
            // return SessionService.prettifyData(data);
        };

        // ctrl.PrepareDownload = function(){
        //     /**
        //      * Resolves a promise from the getItems Service for the data from /storage/
        //      * then provides a summarized version for the template
        //      */
        //     ctrl.getItems().then(function(data){
        //         return SessionService.prepareDownload(data);
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