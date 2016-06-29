console.log('services.js');
// IIFE: Immediately invoked function expression: (function(){})() (where window == global scope)
// Create a cart service
(function(angular){
   // Force variable declarations
    "use strict"

    var app = angular.module('CartApp');

    // Inject in $cookieStore
    app.factory('CartService', function($cookieStore){

        // Private items object
        var items = {};

        function checkCookie(){
            if (undefined != $cookieStore){
                    console.log('Check the cookie: ', $cookieStore.get('items'));
            } else {
                console.log('Cookie Empty!')
            }
        }

        // Update cookies
        function updateItemsCookie(){
            console.log('updateItemsCookie: ', items);
            // Initialize an object that will be saved as a cookie
            var itemsCookie = {};
            // Loop through the items in the cart
            angular.forEach(items, function(item, key){
                // Add each item to the items cookie,
                // using the id as the identifier
                itemsCookie[key] = item;
            });
            // Use the $cookieStore service to persist the itemsCookie object to the cookie named 'items'
            $cookieStore.put('items', itemsCookie);

            checkCookie();
            console.log('updateItemsCookie: - - - END');
        }

        // Angular factories return service objects
        return {

            getItems: function() {
                console.log('- - - getItems - - -')

                // Initialize the itemsCookie variable
                var itemsCookie;

                checkCookie();

                // Check if cart is empty, if not - populate the current service with the cookie items
                if(!items.length) {
                    // Get the items cookie
                    itemsCookie = $cookieStore.get('items');
                    // Check if the item cookie exists
                    if(itemsCookie) {
                        // Loop through the items in the cookie
                        angular.forEach(itemsCookie, function(item, key) {
                            console.log('item ',item)
                            console.log('key ',key)
                            // Get the product details from the ProductService using the guid
                            items[item.id] = item;
                        });
                    }
                }
                // Returns items object
                return items;
            },

            addItem: function(item){
                console.log('addItem: ', item);
                // Check if item already exists
                // If exists - don't add
                // Else, push the item onto the items array, at the relevant astronomical object key

                if (!items[item.id]){
                    items[item.id] = item;
                } else {
                    // nothing - we don't need to update quantity - but this will need altering to cope with AO structure
                }
                // Update cookie
                updateItemsCookie();
            },

            removeItem: function(id){
                // Remove an item from the items object
                delete items[id];
                // Update cookie
                updateItemsCookie();
            },

            emptyCart: function(){
                // Re-initialize items object to an empty object
                items = {};
                // Remove items cookie using $cookieStore
                $cookieStore.remove('items');

                checkCookie();
            },

            getItemCount: function(){
                // Initialize total counter
                var total = 0;
                // Loop through items and increment the total - also count by survey and unique objects
                angular.forEach(items, function(item){
                    // total += parseInt(item.quantity)
                    total += 1;
                })
                console.log('getItemCount ', total)
                return total;
            },

            getAstronomicalObjectsCount: function(){
                var total_astronomical_objects = 0;
                // Loop through items array and increment the total number of unique AOs
                return total_astronomical_objects;
            },

            getItemPerSurvey: function(){
                var total_per_survey = {};
                // append to gama, sami etc (can this be modified for any sample)
                return total_per_survey;
            },

            download: function(){
                // Implement the download
            }

        }
    })
})(window.angular);
