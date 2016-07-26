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
    app.controller('DownloadController', function($scope, DownloadService){
        // console.log('-------DownloadController------');

        var ctrl3 = this; // create alias to this to avoid closure issues
        // Here, we've registered properties on $scope.ctrl rather than on $scope (all modules have global access
        // to $scope - which may result in unwanted cross-talk


        // Set the items on the scope to the items in the DownloadService using the getItems method
        ctrl3.items = {};

        ctrl3.items = DownloadService.getItems();

        ctrl3.addItem = function(item){
            // Pass the item into the addItem method of the DownloadService
            DownloadService.addItem(item);
        };

        ctrl3.getItemCount = function(){
            // Return the item count from the DownloadService
            return DownloadService.getItemCount();
        };

        ctrl3.getAstronomicalObjectsCount = function(){
            DownloadService.getAstronomicalObjectsCount()
        };

        ctrl3.getItemPerSurvey = function (){
            DownloadService.getItemPerSurvey()
        };

        ctrl3.removeItem = function(id){
            // Pass item id into the removeItem method of DownloadService
            DownloadService.removeItem(id);
        };
        
        ctrl3.emptyDownload = function(items){
            DownloadService.emptyDownload($scope.items);
        };

        ctrl3.parseDownloadCookie = function(){
            // var cookie_arr = DownloadService.prettifyCookie();
            // console.log(cookie_arr);
            // var prettydownload = [];
            // for (var i = 0; i < cookie_arr.length; i++){
            //     // var temp = InspectorService.nestedData(cookie_arr[i]);
            //     prettydownload.push(temp);
            // }
            // console.log(prettydownload);
            // DownloadService.parseDownloadCookie();
        };

        ctrl3.download = function(){
            // Invoke the download method of the DownloadService
            DownloadService.download();
        };

        ctrl3.parseDownloadCookie();
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