(function() {
    var app = angular.module('queryBuilder', [ "isteven-multi-select", 'ngSanitize' ]);

    //console.log = function() {};                      // TURN OFF/ON CONSOLE STATEMENTS FOR PRODUCTION

    app.controller('CatalogueController', ['$scope', '$timeout', function($scope, $timeout) {

        /* -- INITIALIZATION -- */

        // ERRORS
        $scope.error={errorFlag: false};
        $scope.warning={warningFlag: false};

        // I/O CATALOGUES (ng-repeat loops over this to create select elements)
        $scope.inputCatalogues = [];
        $scope.outputCatalogues = [];
        $scope.outputColumns = [];

        // I/O JOINS
        $scope.inputJoins=[];
        $scope.inputJoinsB=[];
        $scope.inputJoinOperators = [];
        $scope.outputJoinOperator=[];
        $scope.outputJoins=[];
        $scope.outputJoinsB=[]

        // I/O WHERES
        $scope.inputWheres = [];
        $scope.outputWheres = [];
        $scope.inputWhereOperators = [];
        $scope.outputWhereOperator=[];
        $scope.outputWhereValue=[];
        $scope.outputLowerWhereValue=[];
        $scope.queryCheckbox=[];

        // AVAILABLE CATALOGUES                                                     TODO: is this really needed here? TEST
        var nodeCatalogues = [
    {
        name: "InputCatA",
        catalogueId: 1,
        survey: "GAMA",
        version: "v05",
        DMU: "InputCat",
        Date: "2010-05-21",
        description: "SS DR6 data of GAMA I survey regions. This is GAMA`s master input catalogue.",
        dimension: "960510 rows × 25 columns",
        contact: "Ivan Baldry",
        columns: [
        {
            cid: "1",
            name: "CATAID",
            units: "-",
            UCD: "meta.id;meta.main",
            description: "Unique GAMA ID of object"
        }, {
            cid: "2",
            name: "OBJID",
            units: "-",
            UCD: "meta.id;",
            description: "SDSS objid"
        }, {
            cid: "3",
            name: "RA",
            units: "deg",
            UCD: "pos.eq.ra",
            description: "J2000 coordinate"
        }, {
            cid: "4",
            name: "DEC",
            units: "deg",
            UCD: "pos.eq.dec",
            description: "J2000 coordinate"
        }, ]
    }, {
        name: "ExternalSpecAll",
        catalogueId: 2,
        survey: "GAMA",
        version: "v01",
        DMU: "ExternalSpec",
        Date: "2011-03-03",
        description: "This table lists all spectra of GAMA DR2 objects that are available from previous spectroscopic surveys (such as the SDSS), including duplicate observations. Every spectrum listed in this table is available in the GAMA DR2 database.",
        contact: "Joe Liske",
        columns: [{
            cid: "1",
            name: "SPECID",
            units: "-",
            UCD: "meta.id;meta.main",
            description: "Unique ID of spectrum"
        }, {
            cid: "2",
            name: "SURVEY",
            units: "-",
            UCD: "meta.dataset",
            description: "Survey this spectrum originated from"
        }, {
            cid: "3",
            name: "RA",
            units: "deg",
            UCD: "pos.eq.ra",
            description: "J2000 coordinate"
        }, {
            cid: "4",
            name: "DEC",
            units: "deg",
            UCD: "pos.eq.dec",
            description: "J2000 coordinate"
        }, ]
    },{
        name: "Test",
        catalogueId: 2,

        columns: [{
            name: "a",
        }, {
            name: "NEW",
        }, {
            name: "COLUMNS",
        }, {
            name: "HERE",
        }, ]
    },{
        name: "Test2Cat",
        catalogueId: 2,

        columns: [{
            name: "aasda",
        }, {
            name: "NEWasda",
        }, {
            name: "COLUMNSasdas",
        }, {
            name: "HEREasds",
        }, ]
    } ];
        $scope.inputCatalogueList = [];
        angular.forEach(nodeCatalogues, function (item, key) {
            $scope.inputCatalogueList.push(item.name);
        });


        /* -- SELECTS -- */

        /**  fCatalogueController()
                Controls catalogue & column behaviour based on previous selections.

                If a catalogue is selected, disable it from remaining dropdown options.
                Conversely, if a catalogue is no longer selected, enable it elsewhere.

                Save column selection state and re-apply after any alterations to a
                particular row's catalogue.

                func isn't bound to a particular element.
        **/

        $scope.fCatalogueController = function(data){

            $scope.fResetWarnings();
            $scope.fResetErrors();

            $timeout( function() {

                var inputCatalogues = $scope.inputCatalogues;
                var outputCatalogues = $scope.outputCatalogues;
                var outputColumns = $scope.outputColumns;

                //  get currently selected Catalogues
                var outputCataloguesList = $scope.fGetOutputCatalogues();

                //  STATE has already changed after click event - capture these values before proceeding to (dis/en)able other attributes.
                var outputColumnsList=[];
                angular.forEach(outputColumns,function(value,key){
                    outputColumnsList.push([]);
                    if (value.length>0){
                        angular.forEach(value,function(valuea,keya){
                            outputColumnsList[key].push(valuea.name);
                        });
                    };
                });

                //  Loop through each of the inputCatalogue rows, making the appropriate changes based on current state.
                //  Note that throughout, key is the current row, ie. array(clickevent.this)
                angular.forEach($scope.inputCatalogues, function(value,key){
                    //console.log("-"+key+"-"+outputCataloguesList[key]);
                    var tempCatIndex;

                    angular.forEach($scope.inputCatalogues[key], function(valueb,keyb){
                        //console.log("  opt "+keyb+" "+$scope.inputCatalogues[key][keyb].name);

                        if ($.inArray($scope.inputCatalogues[key][keyb].name, outputCataloguesList)>-1) {
                            //  if is in array of selected options
                            //console.log("     selected somewhere ");
                            if ($scope.inputCatalogues[key][keyb].name==outputCataloguesList[key]){
                                //console.log("     set HERE "+$scope.inputCatalogues[key][keyb].name);
                                //  persist selected option state
                                //  loop through available columns
                                tempCatIndex=keyb;
                            } else {
                                //console.log("     OK TURN OFF "+$scope.inputCatalogues[key][keyb].name);
                                $scope.inputCatalogues[key][keyb].disabled=true;
                            };
                        } else {
                            //console.log("        "+$scope.inputCatalogues[key][keyb].name+' enable');
                            $scope.inputCatalogues[key][keyb].disabled=false;
                        };
                    });

                    //  Reset the state for this row (key)
                    if (undefined != tempCatIndex){
                        //console.log("row "+key+" "+tempCatIndex);
                        //console.log(angular.toJson(outputColumnsList[key]));
                        angular.forEach($scope.inputCatalogues[key][tempCatIndex].columns,function(valuec,keyc){
                            //console.log(valuec.name);
                            if ($.inArray(valuec.name,outputColumnsList[key])>-1){
                                $scope.inputCatalogues[key][tempCatIndex].columns[keyc].ticked=true;
                            } else {
                                $scope.inputCatalogues[key][tempCatIndex].columns[keyc].ticked=false;
                            };
                        });
                    };
                });
                console.log('-end fCatalogueController()');
                console.log('');
            },0);
        };


        // -- ADJUST CATALOGUES WHEN A NEW ONE IS SELECTED
        $scope.fCatClick = function(data){
            $scope.fCatalogueController(data);
            //populate the WHERE array (can choose from non-selected columns)
            $scope.fUpdateJoins();
            $scope.fUpdateWheres();
            $scope.fValidate();
        };


        // -- CLONE CAT INPUT --
        // function fAddCatalogue ()
        //    params:
        //    descript:   Pushes new array to inputCatalogues, number of select dropdowns
        //                depends on this via ng-repeat.
        //                Define nodeCatalogues within the scope of this function, so that
        //                each instance is a unique initialization
        $scope.fAddCatalogue = function(){

            $timeout( function() {  // Timeout with t=0 forces an $apply to update bindings
                var nodeCatalogues = [
    {
        name: "InputCatA",
        catalogueId: 1,
        survey: "GAMA",
        version: "v05",
        DMU: "InputCat",
        Date: "2010-05-21",
        description: "SS DR6 data of GAMA I survey regions. This is GAMA`s master input catalogue.",
        dimension: "960510 rows × 25 columns",
        contact: "Ivan Baldry",
        columns: [
        {
            cid: "1",
            name: "CATAID",
            units: "-",
            UCD: "meta.id;meta.main",
            description: "Unique GAMA ID of object"
        }, {
            cid: "2",
            name: "OBJID",
            units: "-",
            UCD: "meta.id;",
            description: "SDSS objid"
        }, {
            cid: "3",
            name: "RA",
            units: "deg",
            UCD: "pos.eq.ra",
            description: "J2000 coordinate"
        }, {
            cid: "4",
            name: "DEC",
            units: "deg",
            UCD: "pos.eq.dec",
            description: "J2000 coordinate"
        }, ]
    }, {
        name: "ExternalSpecAll",
        catalogueId: 2,
        survey: "GAMA",
        version: "v01",
        DMU: "ExternalSpec",
        Date: "2011-03-03",
        description: "This table lists all spectra of GAMA DR2 objects that are available from previous spectroscopic surveys (such as the SDSS), including duplicate observations. Every spectrum listed in this table is available in the GAMA DR2 database.",
        contact: "Joe Liske",
        columns: [{
            cid: "1",
            name: "SPECID",
            units: "-",
            UCD: "meta.id;meta.main",
            description: "Unique ID of spectrum"
        }, {
            cid: "2",
            name: "SURVEY",
            units: "-",
            UCD: "meta.dataset",
            description: "Survey this spectrum originated from"
        }, {
            cid: "3",
            name: "RA",
            units: "deg",
            UCD: "pos.eq.ra",
            description: "J2000 coordinate"
        }, {
            cid: "4",
            name: "DEC",
            units: "deg",
            UCD: "pos.eq.dec",
            description: "J2000 coordinate"
        }, ]
    },{
        name: "Test",
        catalogueId: 2,

        columns: [{
            name: "a",
        }, {
            name: "NEW",
        }, {
            name: "COLUMNS",
        }, {
            name: "HERE",
        }, ]
    },{
        name: "Test2Cat",
        catalogueId: 2,

        columns: [{
            name: "aasda",
        }, {
            name: "NEWasda",
        }, {
            name: "COLUMNSasdas",
        }, {
            name: "HEREasds",
        }, ]
    } ];
                var temp_node;

                temp_node=nodeCatalogues;

                if (temp_node.length>0){

                    var outputCataloguesList=[];

                    angular.forEach($scope.outputCatalogues, function(value,key){
                        //console.log($scope.outputCatalogues[key].length);
                        if ($scope.outputCatalogues[key].length>0){
                            outputCataloguesList.push($scope.outputCatalogues[key][0].name)
                        } else {
                            $scope.warning['wSelectCat']='Select a catalogue before adding another';
                            $scope.warning['warningFlag']=true;
                        };
                    });

                    if ($scope.warning['warningFlag']==false ){
                        //are all catalogues currently in use?
                        var availableCatsFlag=0;

                        angular.forEach(temp_node,function(value,key){
                            // loop through each of the new row options and if they appear in the
                            // output options catalogue, disable them on input and set ticked to false

                            //console.log(temp_node[key].name+" "+angular.toJson(outputCataloguesList));
                            //console.log($.inArray(temp_node[key].name, outputCataloguesList));
                            if ($.inArray(temp_node[key].name, outputCataloguesList) > -1){
                                //console.log(temp_node[key].name+" selected elsewhere");
                                temp_node[key].ticked=false;
                                temp_node[key].disabled=true;
                            } else {
                                //if this option hasn't been disabled, increment availableCatsFlag
                                availableCatsFlag++;
                            };
                        });

                        if (availableCatsFlag>0){
                            $scope.inputCatalogues.push(temp_node);
                            $scope.outputCatalogues.push([]);
                            $scope.fCatalogueController();
                        } else {
                            //error if availableCatsFlag == 0
                            $scope.error['eAddCats']='No more catalogues available!';
                            $scope.error['errorFlag']=true;
                        }
                    };

                } else {

                    $scope.error['eNoCats']='No catalogues available, please contact systems administrator';
                    $scope.error['errorFlag']=true;

                };

                // JOIN RULES
                //if more than one catalogues add in a join rule

                if ($scope.outputCatalogues.length > $scope.inputJoins.length+1){
                        //ensure the minimum # of joins is >= n-1 catalogues
                        $scope.fAddJoin();
                };

            },0);

        };

        // On load, populate the first select dropdown.
        $scope.fAddCatalogue();

        $scope.fOpenCat=function(){
            //$scope.fCatalogueController();
        };


        // -- REMOVE[POP] LAST CAT INPUT --
        // function fRemoveCatalogue ()
        //    descript: removes last array from inputCatalogues
        $scope.fRemoveCatalogue = function(data){
            //don't remove first element
            console.log(data);
            if ($scope.inputCatalogues.length>1){
                $scope.inputCatalogues.splice(data,1);
                $scope.outputCatalogues.splice(data,1);
            };

            $scope.fCatalogueController();
            $scope.fUpdateWheres();
            $timeout( function() {
                $scope.inputCatalogues;
                $scope.outputCatalogues;
            },0);
            $scope.error['errorFlag']=false;
        };


    // - - - -  JOINS - - - -

        Array.prototype.unique = function() {
            var a = [], l = this.length;
            for(var i=0; i<l; i++) {
              for(var j=i+1; j<l; j++)
                    if (this[i] === this[j]) j = ++i;
              a.push(this[i]);
            }
            return a;
        };

        // -- JOIN STATUS - are all catalogues accounted for?
        $scope.fJoinStatus = function (){
            $scope.fResetErrors();

            var outputJoinList=[];
            var temp_array=[];
            var temp_array_unique;
            var missingJoin = '';
            var temp_array_cats=[];


            angular.forEach($scope.outputJoins, function(value,key){
                outputJoinList.push([$scope.outputJoins[key][0].cat, $scope.outputJoinsB[key][0].cat]);

                //sort array of catalogues alphabetically
                outputJoinList[key].sort();

                //if match to self, ignore
                if (outputJoinList[key][0]!=outputJoinList[key][1]){
                    //concatenate to string
                   temp_array.push(outputJoinList[key][0]+outputJoinList[key][1]);
                   temp_array_cats.push([outputJoinList[key][0],outputJoinList[key][1]]);
                };

            });

            //check for unique-ness
            temp_array_unique = temp_array.unique();

            var temp_array_unique_cats=[];
            //attempt to find missing catalogue
            //go through the catalogues in the output array
            angular.forEach(temp_array_cats,function(value,key){
                var temp = value.sort();
                console.log(temp);
                // if that row does appear in the array of unique matches...
                if ($.inArray(temp[0]+temp[1],temp_array_unique)>-1){
                    //append to list
                    temp_array_unique_cats.push(temp[0],temp[1]);
                };
            });

             //check which of the output catalogues doesn't appear in the temp_array_unique_cats
             angular.forEach($scope.fGetOutputCatalogues(), function(value,key){
                 if ($.inArray(value,temp_array_unique_cats)<0){
                    missingJoin += value+" ";
                 }
             })


            if ((temp_array_unique.length+1) < $scope.outputCatalogues.length){
                $scope.error['errorFlag']=true;
                $scope.error['eMinJoin']='All catalogues must be joined. Missing: '+missingJoin+" ?"
            };

        };






        // -- UPDATE JOINS AFTER CHANGE IN SELECTS
        // function fUpdateJoins
        // descript:
        $scope.fUpdateJoins = function(){

            console.log('-fUpdateJoins()');
            //console.log(angular.toJson($scope.outputJoins));

            //SAVE STATE
            var outputJoins= $scope.outputJoins;
            var outputJoinsB= $scope.outputJoinsB;

            var outputJoinList=[];
            var outputJoinBList=[];
            var inputJoin=[];
            var inputJoinB=[];

            var outputJoinArray=[outputJoins, outputJoinsB];
            var outputJoinListArray=[outputJoinList, outputJoinBList];
            var inputJoinArray=[inputJoin,inputJoinB];
            var inputJoinsArray=[$scope.inputJoins,$scope.inputJoinsB];

            for (i=0; i<=outputJoinArray.length; i++){

                angular.forEach(outputJoinArray[i],function(value,key){
                    outputJoinListArray[i].push([]);
                    if (value.length>0){
                        angular.forEach(value,function(valuea,keya){
                            outputJoinListArray[i][key].push(valuea);
                        });
                    };
                });

                //cycle over outputJoinList as building new list?
                // if name and cat match, set ticked =true

                angular.forEach(inputJoinsArray[i], function (item, key) {

                    inputJoinArray[i] = [];

                    //console.log("outputWhereList["+key+"]: "+angular.toJson(outputWhereList[key]));
                    angular.forEach($scope.outputCatalogues, function (itemb, keyb) {
                        //only populate with selected catalogues
                        if (itemb.length>0){
                        //console.log('cycle over output catalogues: '+ key);
                            inputJoinArray[i].push({name:itemb[0].name, catGroup:true});
                            angular.forEach(itemb[0].columns, function (itemc, keyc) {
                                //associated catalogue is in the 'cat' property
                                //ie., each where selection contains the catalogue it belongs to
                                //console.log(itemc.name+" "+angular.toJson(outputWhereList[key]));
                                //match on the 'button name' ie., catname.columnname
                                if ((undefined != outputJoinListArray[i][key])&&(undefined != outputJoinListArray[i][key][0])&&(outputJoinListArray[i][key][0].buttonname==itemb[0].name+"."+itemc.name)){
                                    inputJoinArray[i].push({name:itemc.name, cat:itemb[0].name, buttonname: itemb[0].name+"."+itemc.name, ticked:true});
                                    //console.log("name: "+itemc.name+", cat: "+itemb[0].name);
                                } else {
                                    inputJoinArray[i].push({name:itemc.name, cat:itemb[0].name, buttonname: itemb[0].name+"."+itemc.name});
                                };
                            });
                            inputJoinArray[i].push({catGroup:false});
                        };
                    });

                    //set e.g., outputJoinList to joinListArray[i];
                    inputJoinsArray[i][key]=inputJoinArray[i];

                    //angular.copy creates a deep copy of the source (dropping the hash keys)
                    //$scope.inputJoinsB[key]=angular.copy(inputJoin);

                });
                window[inputJoinsArray[i]]=inputJoinsArray[i];
            };

            console.log('- end fUpdateJoins()');
        };

        // -- ADD JOIN INPUT --
        // function fAddWhere ()
        //    params:
        //    descript:
        $scope.fAddJoin = function(){
            //if first catalogue is blank throw warning
            if ($scope.outputCatalogues[0].length==0){
                $scope.warning['wSelectCat']='Select a catalogue to apply a constraint to.';
                $scope.warning['warningFlag']=true;
            };

            if ($scope.warning['warningFlag']==false ){
                $timeout( function() {
                    var inputJoinOperators = [{operator:"LEFT OUTER"}, {operator:"INNER"},{operator:"RIGHT OUTER"}];
                    $scope.inputJoinOperators.push(inputJoinOperators);
                    $scope.inputJoins.push([]); //create a new instance forcing a dom update
                    $scope.inputJoinsB.push([]); //create a new instance forcing a dom update
                    $scope.fUpdateJoins();
                },0);
            }
        };



        $scope.fRemoveJoin = function(data){
                $scope.error={errorFlag:false};
            if ($scope.inputJoins.length < $scope.outputCatalogues.length){
                $scope.error['errorFlag']=true;
                $scope.error['eMinJoin']='All catalogues must be joined. You cannot have fewer joins than (N-1)*tables.'
            } else {
                $scope.inputJoins.splice(data,1);
                $scope.inputJoinsB.splice(data,1);
                $scope.outputJoins.splice(data,1);
                $scope.outputJoinsB.splice(data,1);
                //$scope.fUpdateJoins();
                $timeout(function(){
                    $scope.inputJoins;
                    $scope.inputJoinsB;
                    $scope.outputJoins;
                    $scope.outputJoinsB;
                })
            };
        };


    // - - - - WHERES - - - -

        $scope.fUpdateWheres = function(){
            console.log('-fUpdateWheres()');

            //SAVE STATE
            var outputWheres= $scope.outputWheres;
            var outputWhereList=[];

            angular.forEach(outputWheres,function(value,key){
                outputWhereList.push([]);
                if (value.length>0){
                    angular.forEach(value,function(valuea,keya){
                        outputWhereList[key].push(valuea);
                    });
                };
            });

            //console.log(angular.toJson(outputWhereList));
            //associated catalogue is in the 'cat' property

            //cycle over outputWhereList as building new list?
            // if name and cat match, set ticked =true


            angular.forEach($scope.inputWheres, function (item, key) {
                $scope.inputWhere = [];

                //console.log("outputWhereList["+key+"]: "+angular.toJson(outputWhereList[key]));

                angular.forEach($scope.outputCatalogues, function (itemb, keyb) {
                    //only populate with selected catalogues
                    if (itemb.length>0){
                    //console.log('cycle over output catalogues: '+ key);
                        $scope.inputWhere.push({name:itemb[0].name, catGroup:true});
                        angular.forEach(itemb[0].columns, function (itemc, keyc) {
                            //associated catalogue is in the 'cat' property
                            //ie., each where selection contains the catalogue it belongs to
                            //console.log(itemc.name+" "+angular.toJson(outputWhereList[key]));

                            if ((undefined != outputWhereList[key])&&(undefined != outputWhereList[key][0])&&(outputWhereList[key][0].name==itemc.name)){
                                $scope.inputWhere.push({name:itemc.name, cat:itemb[0].name, ticked:true});
                                //console.log("name: "+itemc.name+", cat: "+itemb[0].name);
                            } else {
                                $scope.inputWhere.push({name:itemc.name, cat:itemb[0].name});
                            };
                        });
                        $scope.inputWhere.push({catGroup:false});
                    };
                });
                $scope.inputWheres[key]=$scope.inputWhere;
            });

            console.log('- end fUpdateWheres()');

        };


        $scope.fWhereClick = function(data){
            //console.log(data);
            //fUpdateWheres();
        }


        // -- ADD WHERE INPUT --
        // function fAddWhere ()
        //    params:
        //    descript:
        $scope.fAddWhere = function(){

            $scope.warning={warningFlag: false};

            //if first catalogue is blank throw warning
            if ($scope.outputCatalogues[0].length==0){
                $scope.warning['wSelectCat']='Select a catalogue to apply a constraint to.';
                $scope.warning['warningFlag']=true;
            };

            if ($scope.warning['warningFlag']==false ){
                $timeout( function() {
                    var inputWhereOperators = [{operator:'='},{operator:'\<'},{operator:'\>'},{operator:'<='},{operator:'\>='},{operator:'BETWEEN'},{operator:'LIKE'},{operator:'NULL'},{operator:'IN'}];

                    $scope.inputWheres.push([]); //create a new instance forcing a dom update
                    $scope.inputWhereOperators.push(inputWhereOperators);
                    $scope.fUpdateWheres();
                },0);
            }
        };

        // -- REMOVE[POP] LAST CAT INPUT --
        // function fRemoveCatalogue ()
        //    params:
        //    descript: removes last array from inputCatalogues
        $scope.fRemoveWhere = function(data){

            $scope.inputWheres.splice(data,1);
            $scope.outputWheres.splice(data,1);

            $scope.fUpdateWheres();
            $timeout( function() {
                $scope.inputWheres;
                $scope.outputWheres;
            },0);

        };



        $scope.fValidate=function(){
            //console.log(e.currentTarget);
            var warning=false;
            //loop over the output catalogues, if no value is set, change css + add warning
            angular.forEach($scope.outputCatalogues, function(value,key){
                if ($scope.outputCatalogues[key].length<1){
                    $('#outputCatalogue'+key).addClass('not-selected-warning');
                    warning=true;
                } else {
                    $('#outputCatalogue'+key).removeClass('not-selected-warning');
                }
            });
            return warning;
        };


        $scope.fBuildSQL=function(){
            $scope.fResetErrors;
            $scope.fResetWarnings();

            // If the validation throws errors, add an error message on 'submit'
            if ($scope.fValidate()){
                $scope.warning['warningFlag']=true;
                $scope.warning['Unselected Values']='Ensure all fields are populated'
            } else {

                $scope.fJoinStatus();

                $scope.outputSQLWHERE='';
                console.log($scope.outputWheres.length);

                $scope.fcheckboxEval = function(val){
                    var text = "";
                    if (val == true){
                        text = 'NOT'
                    } else if (val == false) {
                        text = "";
                    }
                    return text
                };

                $scope.fBetweenValue=function(operator, key){
                    var text = "";
                    if (operator=="BETWEEN"){
                        text=$scope.outputLowerWhereValue[key]+" and ";
                    }
                    return text;
                };

                angular.forEach($scope.outputWheres, function(value,key){
                    if (undefined == $scope.outputWhereOperator[key][0]){
                        //user has not selected operator for a row - alert
                        $scope.error['eWhereOperatorMissing']='Missing operator in row '+key;
                        $scope.error['errorFlag']=true;
                    } else if (undefined == $scope.outputWheres[key][0]){
                        $scope.error['eWhereOptionMissing']='Missing WHERE selector in row '+key;
                        $scope.error['errorFlag']=true;
                    } else {
                        $scope.outputSQLWHERE+=value[0].cat+"."+value[0].name+" "+
                        $scope.fcheckboxEval($scope.queryCheckbox[key])+" "+
                        $scope.outputWhereOperator[key][0].operator+" "+
                        $scope.fBetweenValue($scope.outputWhereOperator[key][0].operator,key)+
                        $scope.outputWhereValue[key];
                    };

                    if (key < $scope.outputWheres.length-1){
                        $scope.outputSQLWHERE+=", AND ";
                    };
                    //key is row
                });

            };

        };

        $scope.fWhereOperator = function(){
            $scope.error={errorFlag: false};
        };
        $scope.fResetErrors = function(){
            $scope.error={errorFlag: false};
        };
        $scope.fResetWarnings = function(){
            $scope.warning={warningFlag: false};
        };

        $scope.fGetOutputCatalogues = function(){
            var outputCataloguesList=[];
            var outputCatalogues = $scope.outputCatalogues;
                angular.forEach(outputCatalogues, function(value,key){
                    if (outputCatalogues[key].length>0){
                        outputCataloguesList.push(outputCatalogues[key][0].name);
                    }
                });
            return outputCataloguesList;
        }

    } ]); //end controller

})();

