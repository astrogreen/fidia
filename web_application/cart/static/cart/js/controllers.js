console.log('controllers.js');

(function(angular){
    "use strict";

    var app = angular.module('CartApp');

    // Create 'fixtures'
    app.controller('DummyData', function($scope, $http){
       $http.get('/static/js/cart/dummy-data.json').then(function(response){
           $scope.data = response.data;
           console.log('success - dummy data in $scope.data')
       })
    });

    // Inject in the CartService
    app.controller('CartController', function($scope, CartService){
        console.log('-------CartController------');
        // Set the items on the scope to the items in the CartService using the getItems method
        $scope.items = {};

        $scope.items = CartService.getItems();

        $scope.addItem = function(item){
            // Pass the item into the addItem method of the CartService
            CartService.addItem(item);
        };

        $scope.getItemCount = function(){
            // Return the item count from the CartService
            CartService.getItemCount();
        };

        $scope.getAstronomicalObjectsCount = function(){
            CartService.getAstronomicalObjectsCount()
        }

        $scope.getItemPerSurvey = function (){
            CartService.getItemPerSurvey()
        };

        $scope.removeItem = function(id){
            // Pass item id into the removeItem method of CartService
            CartService.removeItem(id);
        }
        
        $scope.emptyCart = function(){
            CartService.emptyCart();
        }
        
        $scope.download = function(){
            // Invoke the download method of the CartService
            CartService.download();
        };
    });
})(window.angular);