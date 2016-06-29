console.log('services.js');

// Create a cart service
(function(angular){
   // Force variable declarations
    "use strict"

    var app = angular.module('CartApp');

    // Inject in $cookieStore
    app.factory('CartService', function(){

        // Private items object
        var items = {};

        // Update cookies
        function updateItemsCookie(){}

        // Angular factories return service objects
        return {

            getItems: function(){
                // Initialize itemsCookie variable
                var itemsCookie;

                // Check if items object has been populated
                if (!items.length){
                    // Populate items object from cookie

                    // Check if cookie exists
                    if(itemsCookie){
                        // Loop through each cookie and get the item by its ID
                        // Add each item ot the items object
                    }
                }
                // Return the items object
                return items;
            },

            addItem: function(item){
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
            },

            getItemCount: function(){
                // Initialize total counter
                var total = 0;
                // Loop through items and increment the total - also count by survey and unique objects
                angular.forEach(items, function(item){
                    // total += parseInt(item.quantity)
                    total += 1;
                })
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
