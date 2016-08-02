console.log('controllers.js');

(function(angular){
    "use strict";

    var app = angular.module('DCApp');
    
    // Create 'fixtures'
    // var dummy_data_url = "/static/cart/js/dummy-data.json";
    // app.controller('DummyData', function($scope, $http){
    //    $http.get(dummy_data_url).then(function(response){
    //        $scope.data = response.data;
    //        console.log('success - dummy data in $scope.data')
    //    })
    // });

    // Inject in the CartService
    app.controller('CartController', function($scope, CartService){
        // console.log('-------CartController------');

        var ctrl3 = this; // create alias to this to avoid closure issues
        // Here, we've registered properties on $scope.ctrl rather than on $scope (all modules have global access
        // to $scope - which may result in unwanted cross-talk


        // Set the items on the scope to the items in the CartService using the getItems method
        ctrl3.items = {};

        ctrl3.items = CartService.getItems();

        ctrl3.addItem = function(item){
            // Pass the item into the addItem method of the CartService
            CartService.addItem(item);
        };

        ctrl3.getItemCount = function(){
            // Return the item count from the CartService
            return CartService.getItemCount();
        };

        ctrl3.getAstronomicalObjectsCount = function(){
            CartService.getAstronomicalObjectsCount()
        }

        ctrl3.getItemPerSurvey = function (){
            CartService.getItemPerSurvey()
        };

        ctrl3.removeItem = function(id){
            // Pass item id into the removeItem method of CartService
            CartService.removeItem(id);
        }
        
        ctrl3.emptyCart = function(items){
            CartService.emptyCart($scope.items);
        }
        
        ctrl3.download = function(){
            // Invoke the download method of the CartService
            CartService.download();
        };
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