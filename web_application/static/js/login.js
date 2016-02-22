
/**
 * Function that gets the data of the profile if saved in localstorage.
 * !exists key in localstorage return null
 */
function getLocalProfile(callback){
  //profile name is set by registration
    var profileName        = localStorage.getItem("PROFILE_NAME");
    var profileReAuthEmail = localStorage.getItem("PROFILE_REAUTH_EMAIL");

    if(profileName !== null
            && profileReAuthEmail !== null) {
        callback(profileName, profileReAuthEmail);
    }
}

/**
 * Load the profile if exists in localstorage
 */
function loadProfile() {
    if(!supportsHTML5Storage()) { return false; }
    getLocalProfile(function(profileName, profileReAuthEmail) {
        //changes in the UI
        $("#profile-name").html(profileName);
        $("#reauth-email").html(profileReAuthEmail);
        $("#inputEmail").hide();
        $("#inputEmail-addon").hide();
        $("#remember").hide();
    });
}

/**
 * function that checks if the browser supports HTML5 local storage
 * @returns {boolean}
 */
function supportsHTML5Storage() {
    try {
        return 'localStorage' in window && window['localStorage'] !== null;
    } catch (e) {
        return false;
    }
}
