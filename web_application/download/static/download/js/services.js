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
            var remove_arr = [document.domain, document.domain+':'+location.port, location.protocol, 'asvo', "", '', ];
            for(var j = 0; j < remove_arr.length; j++){
                removeFromArray(array,remove_arr[j]);
            }
        }

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
                // share data between services
                if (undefined != $cookieStore){
                    var saved_items = [];
                    angular.forEach($cookieStore.get('items'), function(cookieitem){
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
                    // TODO strip the item.id field once added as already present in key - this might affect other services
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

            prettifyCookie: function(items){

                var prettyCookie = {};
                prettyCookie["objects"] = {}, prettyCookie["samples"] = {};
                // object, id: prettified array
                angular.forEach(items, function(v, url){
                    // Clean the url, removing all excess info (protocol, domain etc) and split into arr
                    var url_arr = url.split("/");
                    cleanArray(url_arr);
                    var data_obj = {}, temp = [];

                    // If the url has come from the data browser, this will be a single object.
                    if (url.indexOf("data-browser") !== -1){

                        // Knowing that the 1 and 2 elements will always be sample and ao, we can
                        // predefine these for the view.
                        // Though this isn't actually asserted... it should be.
                        data_obj['url'] = url.split('?format=')[0];

                        data_obj['sample'] = url_arr[1].toUpperCase();
                        data_obj['ao'] = url_arr[2];
                        data_obj['id'] = url;
                        data_obj['options'] = v.options;

                        if (url_arr[url_arr.length-1].indexOf('?format=') > -1){
                        // If a format exists on the last element of the array, pop it off
                        // and prettify
                            data_obj['format'] = url_arr[url_arr.length-1].split('?format=')[1];
                            url_arr.pop();
                        }
                        // Collect the remaining data pieces below trait into one line
                        for(var i = 3; i < url_arr.length; i++) {
                            if(url_arr[i]!=="" && url_arr[i]!==''){
                                temp.push(url_arr[i]);
                            }
                        }
                        data_obj['trait'] = temp;
                        prettyCookie["objects"][url] = data_obj;

                    } else if (url.indexOf("query-history") !== -1){
                        // If the url has come from the query builder - this will have options
                        data_obj['url'] = url;
                        data_obj['id'] = url;
                        data_obj['sample_id'] = url.split("query-history/")[1].split("/")[0];
                        // data_obj['options'] = JSON.parse(v.options);
                        data_obj['options'] = v.options;
                        prettyCookie["samples"][url] = data_obj;
                    }


                });
                return prettyCookie;
            },

            getSummary: function(prettifiedCookie){

                var summary = {
                    "bySample": [
                            // {"sample": "GAMA", "count": 3},
                        ],
                        "byObject": [
                            // {"id": 1, "name": "John Doe"},
                        ],
                        "byData": [
                            // {"id": 1, "name": "John Doe"},
                        ],
                };
                var itemsCookie = this.prettifyCookie(this.getItems());

                angular.forEach(itemsCookie.objects, function(val, key){
                    // bySample
                    var sample_str = val.sample;

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
                    var object_str = val.ao;
                    if (objExists(summary.byObject, object_str, 'ao') == true){
                        // if the object exists in the ao structure already
                        // find it and boost the count.
                        for (var j=0;j<summary.byObject.length;j++){
                            if (summary.byObject[j].ao == object_str){
                                summary.byObject[j]["count"] = summary.byObject[j]["count"]+1;
                            }
                        }
                    } else {
                        summary.byObject.push({"ao": object_str, "count": 1})
                    }
                });

                return summary;
            },

            download: function(){
                // TODO This function should create a valid json and save in user's download history
                // Wrap up (pretty==more info attached) cookie and return a string of valid JSON
                var download_arr = this.prettifyCookie(this.getItems());
                // console.log(download_arr);
                return JSON.stringify(download_arr);
            }

            // user clicks button format appended to url.


        }
    })

    app.factory('StorageService', function($http, $q, $rootScope){

        // Private items object
        var items = {};

        function removeFromArray(array, elem){
            for(var i = array.length-1; i--;){
                if (array[i] === elem) array.splice(i, 1);
            }
        }

        function cleanArray(array){
            var remove_arr = [document.domain, document.domain+':'+location.port, location.protocol, 'asvo', "", '', ];
            for(var j = 0; j < remove_arr.length; j++){
                removeFromArray(array,remove_arr[j]);
            }
        }

        function objExists(arr, elem, property) {
          return arr.some(function(el) {
            return el[property] === elem;
          });
        }

        // Define service methods

        return {

            storageURL:function(){
                return '/asvo/storage/1/'
            },

            getStorageContents: function() {
                /**
                 * Populate the current service with the storage data
                 * then returns a new promise, which we return - the new promise is resolved via response.data
                 * @param {String} url
                 * @return {Object} items - this is the main object containing all current data.
                 */
                // if(!items.length) {
                //
                //
                // }
                // then returns a new promise, which we return - the new promise is resolved
                // via response.data
                var url = this.storageURL();

                return $http.get(url).then(function (response) {

                    if(response.data.storage_data) {
                        var storage_data = response.data.storage_data;
                        // Loop through the items in the storage and get into local items object
                        angular.forEach(storage_data, function(item, key) {
                            // everything is stored by unique ID
                            items[item.id] = item;
                        });
                    }
                    return items;
                    // return response.data;
                });
                return items;
            },

            addItemToStorage: function(item, overwrite){
                /**
                 * Update storage at url. DOES NOT update the local items obj
                 */
                var url = this.storageURL();
                if (typeof overwrite === 'undefined') { overwrite = false; }

                return this.getStorageContents(url).then(function(data){

                    // the items object has been updated with the server version.
                    // Check if this ID is already present
                    // If storage data doesn't contain this id:

                    if (!data[item.id] || overwrite == true){

                        // Initialize request data
                        var items_for_storage = {};

                        // Loop through the storage data
                        angular.forEach(data, function(temp_item, temp_id){
                            // Add each item to the items to be stored
                            // using the id as the identifier
                            items_for_storage[temp_id] = temp_item;
                        });

                        // Add the new item
                        items_for_storage[item.id] = item;

                        var data_to_be_patched = {
                            "storage_data": items_for_storage
                        };

                        // then returns a new promise, which we return - the new promise is resolved
                        // via response.data
                        return $http.patch(url, data_to_be_patched).then(function () {

                            // Broadcast the event to rootScope such that all directives can access
                            $rootScope.$broadcast('storageUpdated', [1,2,3])

                            // this.getItemCount(response.data.storage_data);
                        })
                        .catch(function (response) {
                            console.log('Hmmm something went wrong: ' + angular.toJson(response.data))
                        });

                    } else {
                        // nothing - we don't need to update quantity
                        console.log(item.id + ' already in basket and overwrite is set to false in StorageService:addItemToStorage().')
                    }


                }).catch(function(){
                    console.log('Data could not be updated: ' + item)
                });
                // this.getSummary(items);
            },

            removeItem: function(id){
                /**
                 * Remove item from storage and local items object
                 */

                var url = this.storageURL();

                return this.getStorageContents(url).then(function(data){

                    // if storage data contains this id:
                    if (data[id]){

                        // Initialize request data variable
                        var items_for_storage = {};

                        // Loop through the storage data
                        angular.forEach(data, function(item, key){
                            // Add each item to the items cookie,
                            // using the id as the identifier
                            // Ignore if it's the id we're removing
                            if (key !== id){
                                items_for_storage[key] = item;
                            }
                        });

                        if (items[id]){
                            delete items[id];
                        }

                        var data_to_be_patched = {
                            "storage_data": items_for_storage
                        };

                        // then returns a new promise, which we return - the new promise is resolved
                        // via response.data
                        return $http.patch(url, data_to_be_patched).then(function () {

                            // Broadcast the event to rootScope such that all directives can access
                            $rootScope.$broadcast('storageUpdated');

                        })
                        .catch(function (response) {
                            console.log('Hmmm something went wrong, data removal failed: ' + angular.toJson(response.data))
                        });

                    } else {
                        console.log('Could not remove: '+ id + ', was not found in storage')
                    }

                }).catch(function(){
                    console.log('Data could not be updated: ' + item)
                });
            },

            emptyDownload: function(){
                /**
                 * Set storage to blank
                 */
                var url = this.storageURL();

                return this.getStorageContents(url).then(function(data){

                    if (items) {
                        // items = {}
                        // Can't re-initialize items object to an empty object, else break the reference and ng-repeat won't update
                        // Instead, loop and clear the items object

                        for (var prop in items){
                            delete items[prop]
                        }
                    }

                    var data_to_be_patched = {
                        "storage_data": ""
                    };

                    return $http.patch(url, data_to_be_patched).then(function () {
                            // Broadcast the event to rootScope such that all directives can access
                            $rootScope.$broadcast('storageUpdated');
                        })
                        .catch(function (response) {
                            console.log('Hmmm something went wrong, data removal failed: ' + angular.toJson(response.data))
                        });

                }).catch(function(){
                    console.log('Data could not be updated: ' + item)
                });
            },

            getItemCount: function(data){
                /**
                 * Returns the count of items in storage
                 * @type {number} total
                 */

                // Initialize total counter
                var total = 0;

                if (Object.keys(data).length === 0 && data.constructor === Object){
                    // Empty object - no need to tally
                } else {
                    angular.forEach(data, function (item) {
                        total += 1;
                    });
                }
                return total;
            },

            prettifyData: function(items){
                /**
                 * Takes an object and returns the pretty version for the template rendering
                 * @param {Object} items
                 * @return {Object} prettyData
                 */

                var prettyData = {};
                prettyData["objects"] = {}, prettyData["samples"] = {};
                // object, id: prettified array
                angular.forEach(items, function(v, url){
                    // Clean the url, removing all excess info (protocol, domain etc) and split into arr
                    var url_arr = url.split("/");
                    cleanArray(url_arr);
                    var data_obj = {}, temp = [];

                    // If the url has come from the data browser, this will be a single object.
                    if (url.indexOf("data-browser") !== -1){

                        // Knowing that the 1 and 2 elements will always be sample and ao, we can
                        // predefine these for the view.
                        // Though this isn't actually asserted... it should be.
                        data_obj['url'] = url.split('?format=')[0];

                        data_obj['sample'] = url_arr[1].toUpperCase();
                        data_obj['ao'] = url_arr[2];
                        data_obj['id'] = url;

                        if (v.options){
                            data_obj['options'] = v.options;
                        }

                        if (v.prettyname){
                            data_obj['prettyname'] = v.prettyname;
                        }

                        if (url_arr[url_arr.length-1].indexOf('?format=') > -1){
                        // If a format exists on the last element of the array, pop it off
                        // and prettify
                            data_obj['format'] = url_arr[url_arr.length-1].split('?format=')[1];
                            url_arr.pop();
                        }

                        // Collect the remaining data pieces below trait into one line
                        for(var i = 3; i < url_arr.length; i++) {
                            if(url_arr[i]!=="" && url_arr[i]!==''){
                                temp.push(url_arr[i]);
                            }
                        }
                        data_obj['trait'] = temp;
                        prettyData["objects"][url] = data_obj;

                    } else if (url.indexOf("query-history") !== -1){
                        // If the url has come from the query builder - this will have options
                        data_obj['url'] = url;
                        data_obj['id'] = url;
                        data_obj['sample_id'] = url.split("query-history/")[1].split("/")[0];
                        // data_obj['options'] = JSON.parse(v.options);

                        if (v.options){
                            if (!(Object.keys(v.options).length === 0 && v.options.constructor === Object)) {
                                // Check not empty
                                data_obj['options'] = v.options;
                            }
                        }

                        if (url_arr[url_arr.length-1].indexOf('?format=') > -1){
                        // If a format exists on the last element of the array, pop it off
                        // and prettify
                            data_obj['format'] = url_arr[url_arr.length-1].split('?format=')[1];
                            url_arr.pop();
                        }
                        prettyData["samples"][url] = data_obj;
                    }
                });
                return prettyData;
            },

            getSummary: function(items){

                /**
                 * Takes items object and returns the summary for download template render
                 * @param {Object} items
                 * @return {Object} summary
                 */

                var summary = {
                    "bySample": [
                            // {"sample": "GAMA", "count": 3},
                        ],
                        "byObject": [
                            // {"id": 1, "name": "John Doe"},
                        ],
                        "byData": [
                            // {"id": 1, "name": "John Doe"},
                        ],
                };

                var pretty_data = this.prettifyData(items);

                angular.forEach(pretty_data.objects, function(val, key){
                    // bySample
                    var sample_str = val.sample;

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
                    var object_str = val.ao;
                    if (objExists(summary.byObject, object_str, 'ao') == true){
                        // if the object exists in the ao structure already
                        // find it and boost the count.
                        for (var j=0;j<summary.byObject.length;j++){
                            if (summary.byObject[j].ao == object_str){
                                summary.byObject[j]["count"] = summary.byObject[j]["count"]+1;
                            }
                        }
                    } else {
                        summary.byObject.push({"ao": object_str, "count": 1})
                    }
                });
                return summary;
            },

            prepareDownload: function(items){
                /**
                 * Wrap up (prettified==more info attached) data and return a string of valid JSON to submit
                 * to the download/ route
                 * @param {Object} items
                 * @return {String} JSON stringified prettified items
                 */
                var download_arr = this.prettifyData(items);
                return JSON.stringify(download_arr);
            }

        }
    })

})(window.angular);
