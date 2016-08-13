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

        ctrl.items = DownloadService.getItems();

        ctrl.summary = DownloadService.getSummary();

        ctrl.prettyCookie = DownloadService.prettifyCookie(ctrl.items);

        ctrl.download = DownloadService.download();

        ctrl.addItem = function(item){
            // Pass the item into the addItem method of the DownloadService
            DownloadService.addItem(item);
        };

        ctrl.getItemCount = function(){
            // Return the item count from the DownloadService
            return DownloadService.getItemCount();
        };

        ctrl.removeItem = function(id){
            // Pass item id into the removeItem method of DownloadService
            DownloadService.removeItem(id);
            ctrl.summary = DownloadService.getSummary();
            ctrl.prettyCookie = DownloadService.prettifyCookie(ctrl.items);
            ctrl.download = DownloadService.download();
        };
        
        ctrl.emptyDownload = function(){
            DownloadService.emptyDownload($scope.items);
            ctrl.summary = DownloadService.getSummary();
        };

        // NEW STORAGE METHOD
        // ctrl.items ==>
        ctrl.getItems = function(){
            var deferred = $q.defer();
            var url = '/asvo/storage/1/'

            StorageService.getStorageContents(url).then(function (data) {
                deferred.resolve(data);
            }).catch(function () {
                deferred.reject(data);
                ctrl.error = true;
                ctrl.text = 'Unable to get stored data at ' + url;
                ctrl.status = data.status;
            });

            return deferred.promise;
        };

        ctrl.getSummary = function(){
            StorageService.getSummary();
        }

        ctrl.prettyData = function(){
            ctrl.getItems().then(function(data){
                console.log(data)
                StorageService.prettifyData(data);
            }).catch(function(){
                console.log('Data could not be prettified.')
            })
        };

        ctrl.getSummary = function(){
            ctrl.getItems().then(function(data){
                console.log('Resolved Promise')
                console.log(data);
                StorageService.getSummary(data);
            }).catch(function(){
                console.log('Data could not be summarized.')
            })
        };

        ctrl.getSummary();


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