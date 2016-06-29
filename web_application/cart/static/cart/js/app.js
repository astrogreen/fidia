var app = angular.module("CartApp", ['ngCookies'])
.config(['$cookiesProvider', function($cookiesProvider) {
    // Set $cookies defaults
    $cookiesProvider.defaults.path = '/';
    // $cookiesProvider.defaults.secure = true;
    // $cookiesProvider.defaults.expires = exp_date;
    // $cookiesProvider.defaults.domain = '/asvo/';
}]);
