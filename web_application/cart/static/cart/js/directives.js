console.log('directives.js');
(function(angular){
    "use strict"

    var app = angular.module('CartApp');

    // CartDirective
    app.directive('miniCart', function(CartService){
        return{
            // Create in an isolated scope
            scope:{
            },
            restrict: 'A',
            replace: true,
            templateUrl: '/static/templates/cart/mini-cart.html',
            link: function(scope, elem, attr){
                scope.getItemCount = function(){
                    // Returns the item count from the Cart Service
                    return CartService.getItemCount();
                }
            }
        };
    });

    app.directive('addCartButton', function(CartService){
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
                item: "="

            },
            replace: true,
            templateUrl: '/static/templates/cart/add-cart-button.html',
            link: function(scope, elem, attr){
                scope.addItem = function(item){
                    // Pass the item into the addItem method of CartService
                    CartService.addItem(item);
                    CartService.getItemCount();
                }
            }
        }
    });

})(window.angular)