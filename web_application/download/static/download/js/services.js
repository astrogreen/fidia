// IIFE: Immediately invoked function expression: (function(){})() (where window == global scope)
// Create a download service
(function(angular){
   // Force variable declarations
    "use strict";

    // turn off for dev:
    // console.log = function() {};

    console.log('services.js');

    var app = angular.module('DCApp');

    // Inject in $cookieStore
    app.factory('DownloadService', function($cookieStore){

        // Private items object
        var items = {};

        function checkCookie(){
            console.log('- - CHECK - - - - ');
            if(items.length) {
                console.log('- - Items: ', items)
            }
            if (undefined != $cookieStore){
                    console.log('- - Cookie: ', $cookieStore.get('items'));
            } else {
                console.log('- - Cookie Empty!')
            }
        }

        // Update cookies
        function updateItemsCookie(){
            console.log('updateItemsCookie: ', items);
            // checkCookie();
            // Initialize an object that will be saved as a cookie
            var itemsCookie = {};
            // Loop through the items in the download
            angular.forEach(items, function(item, key){
                // Add each item to the items cookie,
                // using the id as the identifier
                itemsCookie[key] = item;
            });
            // Use the $cookieStore service to persist the itemsCookie object to the cookie named 'items'
            $cookieStore.put('items', itemsCookie);
            checkCookie();
        }

        function removeFromArray(array, elem){
            for(var i = array.length-1; i--;){
                if (array[i] === elem) array.splice(i, 1);
            }
        }

        function cleanArray(array){
            var remove_arr = [document.domain, document.domain+':'+location.port, location.protocol, 'asvo', "", ''];
            for(var j = 0; j < remove_arr.length; j++){
                removeFromArray(array,remove_arr[j]);
            }
        }

        var arr = [{ id: 1, username: 'fred' },
          { id: 2, username: 'bill'},
          { id: 3, username: 'ted' }];

        function objExists(arr, elem, property) {
          return arr.some(function(el) {
            return el[property] === elem;
          });
        }


        // Angular factories return service objects
        return {

            getItems: function() {
                // Initialize the itemsCookie variable
                var itemsCookie;

                // checkCookie();

                // Check if download is empty, if not - populate the current service with the cookie items
                if(!items.length) {
                    // Get the items cookie
                    itemsCookie = $cookieStore.get('items');
                    // Check if the item cookie exists
                    if(itemsCookie) {
                        // Loop through the items in the cookie
                        angular.forEach(itemsCookie, function(item, key) {
                            // Get the product details from the ProductService using the guid
                            items[item.id] = item;
                        });
                    }
                }
                // Returns items object
                return items;
            },

            checkItemInCookie: function(){
                // share data between directives
                if (undefined != $cookieStore){
                    var saved_items = [];
                    angular.forEach($cookieStore.get('items'), function(cookieitem){
                        // saved_items.push(cookieitem.url);
                        saved_items.push(cookieitem.id);
                    });
                    return saved_items;
                }
            },

            addItem: function(item){
                // Check if item already exists
                // If exists - don't add
                // Else, push the item onto the items array, at the relevant astronomical object key
                if (!items[item.id]){
                    // Add prettify property to item
                    item = this.prettifyCookie(item);
                    items[item.id] = item;
                } else {
                    // nothing - we don't need to update quantity - but this will need altering to cope with AO structure
                }
                // Update cookie
                updateItemsCookie();
                // Update angular summary obj
                this.getSummary();
            },

            removeItem: function(id){
                // Remove an item from the items object
                delete items[id];
                // Update cookie
                updateItemsCookie();
            },

            emptyDownload: function(){
                // items = {};
                // Can't re-initialize items object to an empty object, else break the reference and ng-repeat won't update
                // Instead, loop and clear the items object

                for (var prop in items){
                    delete items[prop]
                }
                // Remove items cookie using $cookieStore
                $cookieStore.remove('items');

                // updateItemsCookie();
                // checkCookie();
            },

            getItemCount: function(){
                // Initialize total counter
                var total = 0;
                // Loop through items and increment the total - also count by survey and unique objects
                // angular.forEach(items, function(item){
                //     // total += parseInt(item.quantity)
                //     total += 1;
                // })
                // console.log('getItemCount ', total)

                // NO! Best to use the updated cookie here - so the directive can use this method (directive doesn't have access to controller scope)
                if (undefined != $cookieStore){
                    angular.forEach($cookieStore.get('items'), function(item){
                        // total += parseInt(item.quantity)
                        total += 1;
                    })
                }
                return total;
            },

            getSummary: function(){

                var summary = {
                    "bySample": [
                            // {"sample": "GAMA", "count": 3},
                            // {"sample": "GALAH", "count": 6},
                        ],
                        "byObject": [
                            // {"id": 1, "name": "John Doe"},
                            // {"id": 2, "name": "Don Joeh"}
                        ],
                        "byData": [
                            // {"id": 1, "name": "John Doe"},
                            // {"id": 2, "name": "Don Joeh"}
                        ],
                };
                var itemsCookie = this.getItems();

                angular.forEach(itemsCookie, function(val, key){
                    // bySample
                    var sample_str = val.prettify.sample;

                    if (objExists(summary.bySample, sample_str, 'sample') == true){
                        // if the object exists in the sample structure already
                        // find it and boost the count.
                        for (var i=0;i<summary.bySample.length;i++){
                            if (summary.bySample[i].sample == sample_str){
                                summary.bySample[i]["count"] = summary.bySample[i]["count"]+1;
                            }
                        }
                    } else {
                        summary.bySample.push({"sample": sample_str, "count": 1})
                    }
                    // byObject
                    var object_str = val.prettify.ao;
                    if (objExists(summary.byObject, object_str, 'ao') == true){
                        // if the object exists in the ao structure already
                        // find it and boost the count.
                        for (var i=0;i<summary.byObject.length;i++){
                            if (summary.byObject[i].ao == object_str){
                                summary.byObject[i]["count"] = summary.byObject[i]["count"]+1;
                            }
                        }
                    } else {
                        summary.byObject.push({"ao": object_str, "count": 1})
                    }


                });
                // append to gama, sami etc (can this be modified for any sample)
                return summary;
            },

            prettifyCookie: function(item){
                var url_arr = item.id.split("/");
                cleanArray(url_arr);
                // Knowing that the 0 and 1 elements will always be sample and ao, we can
                // predefine these for the view.
                // Though this isn't actually asserted... it should be.

                var data_obj = {}, temp = [];

                data_obj['url'] = item.id.split('?format=')[0];
                data_obj['sample'] = url_arr[0].toUpperCase();
                data_obj['ao'] = url_arr[1];

                if (url_arr[url_arr.length-1].indexOf('?format=') > -1){
                    // If a format exists on the last element of the array, pop it off
                    // and prettify
                    data_obj['format'] = url_arr[url_arr.length-1].split('?format=')[1];
                    url_arr.pop();
                }

                for(var i = 2; i < url_arr.length; i++) {
                    if(url_arr[i]!=="" && url_arr[i]!==''){
                        temp.push(url_arr[i]);
                    }
                }
                data_obj['else'] = temp;
                item['prettify'] = data_obj;
                return item
            },

            download: function(){
                // TODO This function should create a valid json and save in user's download history
                // This will be easier to write once DataBrowser is completed, having a firm idea of the
                // allowed directives.

                // Create an object that contains the full data list
                // Format: unique url, options
                // /data/sami/gal1/redshift/value/
            },

            // user clicks button format appended to url.


        }
    })
})(window.angular);
