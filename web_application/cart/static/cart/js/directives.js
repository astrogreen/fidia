console.log('directives.js');
(function(angular){
    "use strict"

    var app = angular.module('DCApp');

    // CartDirective
    app.directive('miniCart', function(CartService){
        return{
            // Create in an isolated scope
            scope:{
            },
            restrict: 'AE',
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
                },
                elem.bind('click', function(e){
                    // e.currentTarget is element that event is hooked on (target is the one that received the click)
                    angular.element(e.currentTarget).addClass('btn-added-to-cart')
                        .html('<i class="fa fa-check"></i> <small>added to cart</small>').removeClass('btn-primary')
                        .addClass('btn-default').attr('disabled', true);

                        $('#mini-cart').addClass('bounce')
                            .one('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function(){
                                $('#mini-cart').removeClass('bounce');
                            });
                })
            }
        }
    });

})(window.angular)