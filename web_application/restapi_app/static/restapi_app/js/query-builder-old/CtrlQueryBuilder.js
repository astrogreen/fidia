app.controller('Ctrl1', ['$scope', '$timeout', '$http', function($scope, $timeout, $http) {

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

        var nodeCataloguesGlobal = (function () {
            var json = null;
            $.ajax({
                'async': false,
                'global': false,
                'url': urlCataloguesGlobal,
                'dataType': "json",
                'success': function (data) {
                    json = data;
                }
            });
            return json;
        })();

        //$scope.inputCatalogueList = [];
        //angular.forEach(nodeCatalogues, function (item, key) {
        //    $scope.inputCatalogueList.push(item.name);
        //});


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

        // -- SELECT VALIDATION --

        $scope.fColClick = function(data){
            $scope.fValidate();
        };
        $scope.fColClose = function(data){
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
                var nodeCatalogues = angular.copy(nodeCataloguesGlobal);

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

                    $scope.error['eNoCats'] = 'No catalogues available, please support systems administrator';
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
            //console.log(data);
            if ($scope.inputCatalogues.length>1){
                $scope.inputCatalogues.splice(data,1);
                $scope.outputCatalogues.splice(data,1);
            };

            $scope.fCatalogueController();
            $scope.fUpdateJoins();
            $scope.fUpdateWheres();
            $timeout( function() {
                $scope.inputCatalogues;
                $scope.outputCatalogues;
            },0);
            //$scope.error['errorFlag']=false;
            $scope.fValidate();
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

            // NEW: disable all catalogues in the first join that aren't the first table.
            // get first output catalogue;
            if (undefined != $scope.fGetOutputCatalogues()[0]){
                var currentFirstCatalogue = $scope.fGetOutputCatalogues()[0];
                var disabledProperty = false;
            };


            for (var i = 0; i<=outputJoinArray.length; i++){

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
                            // DISABLE JOINA catalogues that aren't the first row (i=0)
                            // DISABLE JOINB catalogues that are the first row (i=1)
                            // shouldn't match to itself
                            if (i==0){
                                if (itemb[0].name == currentFirstCatalogue){
                                    disabledProperty = false;
                                } else {
                                    disabledProperty = true;
                                };
                            } else {
                                if (itemb[0].name != currentFirstCatalogue){
                                    disabledProperty = false;
                                } else {
                                    disabledProperty = true;
                                };
                            };

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
                                    inputJoinArray[i].push({name:itemc.name, cat:itemb[0].name, buttonname: itemb[0].name+"."+itemc.name, disabled:disabledProperty});
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
                $scope.inputJoinOperators.splice(data,1);
                $scope.outputJoinOperator.splice(data,1);
                //$scope.fUpdateJoins();
                $timeout(function(){
                    $scope.inputJoins;
                    $scope.inputJoinsB;
                    $scope.outputJoins;
                    $scope.outputJoinsB;
                })
            };
        };

        // -- VALIDATE JOINS
        $scope.fJoinClick= function(){
            $scope.fValidate();
        };
        $scope.fJoinOperator= function(){
            $scope.fValidate();
        };
        $scope.fJoinBClick= function(){
            $scope.fValidate();
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
            //console.log('OUTPUTWHERES'+angular.toJson(outputWhereList));
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
                            // if the [key] row of the selected outputWheres has a selection made on catalogue
                            // and column
                            // then iterating over available catalogues (itemb) and columns (itemc)
                            // ensure that the catalogue and col for this input match the selected option before
                            // ticking as true.
                            // (else, if a column exists in multiple catalogues, we get the double-tick bug, ASVO-445)
                            if ((undefined != outputWhereList[key])&&(undefined != outputWhereList[key][0])&&(outputWhereList[key][0].cat==itemb[0].name)&&(outputWhereList[key][0].name==itemc.name)){
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

        // -- ADD WHERE INPUT --
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
        // removes last array from inputCatalogues
        $scope.fRemoveWhere = function(data){

            $scope.inputWheres.splice(data,1);
            $scope.outputWheres.splice(data,1);

            $scope.inputWhereOperators.splice(data,1);
            $scope.outputWhereOperator.splice(data,1);

            $scope.outputWhereValue.splice(data,1);

            $scope.fUpdateWheres();

            $timeout( function() {
                $scope.inputWheres;
                $scope.outputWheres;
            },0);

        };


        // -- VALIDATE WHERE
        $scope.fWhereClick= function(){
            $scope.fValidate();
        };
        $scope.fWhereOperator= function(){
            $scope.fValidate();
        };
        $scope.fWhereValue= function(){
            $scope.fValidate();
        };

    // - - - - VALIDATION - - - -

        $scope.fValidate=function(){
            //console.log(e.currentTarget);
            //$scope.fUpdateJoins();
            $scope.fUpdateWheres();

            var warning=false;
            $scope.warning['warningFlag']=false;

            // TODO deal with outputwherevalue loop issues doesnt validate
            // hack - change shape of outputWhereValue to be iterable
            // this doesnt work well if user deletes a field entry and
            // doesnt replace it...
            var outputWhereValueTemp = [];

            for (var i= 0; i<$scope.inputWhereOperators.length;i++){
                var b = '';
                if (undefined != $scope.outputWhereValue[i]){
                    b = [($scope.outputWhereValue[i]).toString()];
                } else {
                    b = [];
                }
                outputWhereValueTemp.push(b);
            };
            //console.log('OUTPUTJOINS');
            //console.log(angular.toJson($scope.outputJoins));
            //console.log(angular.toJson($scope.outputJoinOperator));
            //console.log(angular.toJson($scope.outputJoinsB));

            var validationObj = [
                [$scope.outputCatalogues,"#outputCatalogue", ' catalogue on row '],
                [$scope.outputColumns, '#outputColumn', ' column(s) on row '],
                [$scope.outputJoins, '#outputJoins', ' first join on row '],
                [$scope.outputJoinsB, '#outputJoinsB', ' second join on row '],
                [$scope.outputJoinOperator,'#outputJoinOperator', ' join operator on row '],
                [$scope.outputWheres, '#outputWhere', ' where selection on row '],
                [$scope.outputWhereOperator,'#outputWhereOperator', ' where operator on row '],
                [outputWhereValueTemp, '#whereValue', ' where value on row ']
            ];

            // loop over output arrays and elements, check populated
            // if not append warning and return warning=true
            var missing = 'Missing ';

            for(var i=0; i<validationObj.length; i++) {
                angular.forEach(validationObj[i][0], function(value,key){
                    if (validationObj[i][0][key].length<1){

                        //validation for value box needs custom function
                        //if the operator for that row is null - bypass the compressor.
                        // if the current obj is the where value, and its defined, and the operator on that row is NULL
                        // then clear all warnings on the value box.
                        if ((validationObj[i][1]=="#whereValue") && (undefined != $scope.outputWhereOperator) &&
                            (undefined != $scope.outputWhereOperator[key][0]) && ($scope.outputWhereOperator[key][0].operator=="NULL")){
                                //console.log($scope.outputWhereOperator[key][0].operator)
                                $(validationObj[i][1]+key).removeClass('not-selected-warning');
                        } else {
                            // otherwise validate all fields (check not blank)
                            $(validationObj[i][1]+key).addClass('not-selected-warning');
                            $scope.warning['warningFlag']=true;
                            $scope.warning['Unselected Values']="Ensure all fields are populated. "
                            missing += validationObj[i][2]+key+',';
                            warning=true;
                            $('#query-builder-submit').attr('disabled', true);
                        }
                    } else {
                        $(validationObj[i][1]+key).removeClass('not-selected-warning');
                    }
                });
            };
            if (warning != true){
                $scope.fBuildSQL(warning);
            };
            $scope.warning['Unselected Values']+=missing;
            return warning;
        };

        console.log($scope.outputSQL);

        $scope.fBuildSQL=function(warning){
            // $scope.fResetErrors();
            // $scope.fResetWarnings();

            // If the validation throws errors, add an error message on 'submit'
            if (warning == true ){
                $scope.outputSQL = undefined;

                $('#query-builder-submit').attr('disabled', true);
            } else {
                $('#query-builder-submit').attr('disabled', false);
                $scope.fJoinStatus();
                $scope.outputSQL = '';
                $scope.outputSQLSELECT='SELECT ';
                $scope.outputSQLJOIN='';
                $scope.outputSQLWHERE='';

                $scope.fWhereSQL=function(operator,key, checkboxval){
                    var text = ""; var cbv = "";

                    if (operator == "BETWEEN" || operator == "NULL"){
                        if (checkboxval == true){
                            cbv = 'NOT '
                        } else if (checkboxval == false) {
                            cbv = "";
                        }
                    } else {
                        if (checkboxval == true){
                            cbv = '!'
                        } else if (checkboxval == false) {
                            cbv = "";
                        }
                    };

                    if (operator=="BETWEEN"){
                        text=" " + cbv + " " + operator+" " + $scope.outputLowerWhereValue[key] + " and " + $scope.outputWhereValue[key] + " ";
                    } else if (operator == "NULL"){
                        text = 'IS '+cbv+'NULL ';
                    } else {
                        text =" "+cbv+''+operator+" "+$scope.outputWhereValue[key];
                    }
                    return text;
                };


                //$scope.outputSQLWHERE+=whereCatAlias+"."+value[0].name+" "+
                //$scope.fcheckboxEval($scope.queryCheckbox[key])+" "+
                //$scope.outputWhereOperator[key][0].operator+" "+
                //$scope.fBetweenValue($scope.outputWhereOperator[key][0].operator,key)+
                //$scope.outputWhereValue[key];

                //SELECT t1.CATAID, t1.OBJID, t1.RA, t1.DEC, t1.FLAGS
                //FROM   InputCatA as t1
                //       INNER JOIN SpStandards as t2 on t2.CATAID = t1.CATAID
                //       INNER JOIN TilingCat as t3 on t3.CATAID = t1.CATAID

                //SELECT t1.CATAID, t1.A_NUV, t1.A_r, t2.PRIMTARGET, t2.PETRORAD_R, t3.CATAID, t3.OBJID,
                //       t3.RA
                //FROM   GalacticExtinction as t1
                //       LEFT OUTER JOIN InputCatA as t2 on t2.CATAID = t1.CATAID
                //       LEFT OUTER JOIN SpStandards as t3 on t3.CATAID = t1.CATAID


                //SELECTS

                //construct the output lists
                var outputCataloguesList = $scope.fGetOutputCatalogues();
                var outputColumns = $scope.outputColumns;
                var outputColumnsList=[];
                angular.forEach(outputColumns,function(value,key){
                    outputColumnsList.push([]);
                    if (value.length>0){
                        angular.forEach(value,function(valuea,keya){
                            outputColumnsList[key].push(valuea.name);
                        });
                    };
                });

                // construct SELECT
                //SELECT t1.CATAID, t1.A_NUV, t1.A_r, t2.PRIMTARGET, t2.PETRORAD_R, t3.CATAID, t3.OBJID,
                //       t3.RA
                var counter=1;
                var tablenameArr = [];
                angular.forEach(outputCataloguesList, function(value,key){
                    var tablename = 't'+counter;

                    angular.forEach(outputColumnsList[key],function(valueb,keyb){
                        $scope.outputSQLSELECT+=tablename+"."+valueb;
                        if (keyb < outputColumnsList[key].length-1){
                            $scope.outputSQLSELECT+=", ";
                        };
                    });
                    if (key < outputCataloguesList.length-1){
                            $scope.outputSQLSELECT+=", ";
                    };
                    counter++;
                    //FROM   GalacticExtinction as t1
                    tablenameArr.push([outputCataloguesList[key], tablename]);
                });
                //console.log(angular.toJson(tablenameArr))


                // if joins are present
                if (undefined != $scope.outputJoins[0]){
                    //first cat always first with this syntax:
                    $scope.outputSQLJOIN='FROM '+tablenameArr[0][0]+' AS '+tablenameArr[0][1]+" ";

                    //sort out joins
                    angular.forEach($scope.outputJoins, function(value,key){
                        var joinCatAliasB =''; var joinCatAlias ='';
                        //get table alias (tablenameArr looks like: [["ExternalSpecAll","t1"],["Test","t2"]])
                        angular.forEach(tablenameArr,function(valueb, keyb){
                            //catalogue
                            //console.log(valueb[0])
                            if ($scope.outputJoins[key][0].cat == valueb[0]){
                                joinCatAlias = valueb[1];
                            }
                            if ($scope.outputJoinsB[key][0].cat == valueb[0]){
                                joinCatAliasB = valueb[1];
                            }
                        });

                        $scope.outputSQLJOIN+='<br>'+$scope.outputJoinOperator[key][0].operator+' JOIN '
                            + $scope.outputJoinsB[key][0].cat + ' AS ' + joinCatAliasB + ' ON ' +
                            joinCatAliasB+'.'+$scope.outputJoinsB[key][0].name+' = '+joinCatAlias+'.'+$scope.outputJoins[key][0].name+' ';

                    });
                } else {
                    //if no joins (single table) append FROM to statement
                    $scope.outputSQLJOIN='FROM '+tablenameArr[0][0]+' AS '+tablenameArr[0][1]+" ";
                }


                // construct JOIN
                //FROM   GalacticExtinction as t1
                //       LEFT OUTER JOIN InputCatA as t2 on t2.CATAID = t1.CATAID
                //       LEFT OUTER JOIN SpStandards as t3 on t3.CATAID = t1.CATAID


                //FROM   GalacticExtinction as t1
                //       INNER JOIN InputCatA as t2 on t2.CATAID = t1.CATAID and t2.RA = t1.RA and t2.CATAID = t1.CATAID
                //       LEFT OUTER JOIN SpStandards as t3 on t3.CATAID = t1.CATAID



                //console.log($scope.outputSQLSELECT);
                //console.log(angular.toJson(outputColumnsList));
                //console.log(angular.toJson(outputCataloguesList));



                if (undefined != $scope.outputWheres[0]){
                    $scope.outputSQLWHERE='WHERE ';
                    angular.forEach($scope.outputWheres, function(value,key){
                        var whereCatAlias ='';

                        //get table alias (tablenameArr looks like: [["ExternalSpecAll","t1"],["Test","t2"]])
                        angular.forEach(tablenameArr,function(valueb, keyb){
                            if (value[0].cat == valueb[0]){
                                whereCatAlias = valueb[1];
                            }
                        });


                        if (undefined == $scope.outputWhereOperator[key][0]){
                            //user has not selected operator for a row - alert
                            $scope.error['eWhereOperatorMissing']='Missing operator in row '+key;
                            $scope.error['errorFlag']=true;
                        } else if (undefined == $scope.outputWheres[key][0]){
                            $scope.error['eWhereOptionMissing']='Missing WHERE selector in row '+key;
                            $scope.error['errorFlag']=true;
                        } else {
                            $scope.outputSQLWHERE+=whereCatAlias+"."+value[0].name+" "+
                            $scope.fWhereSQL($scope.outputWhereOperator[key][0].operator, key, $scope.queryCheckbox[key]) +'<br>';
                            //console.log($scope.fWhereSQL($scope.outputWhereOperator[key][0].operator, key, $scope.queryCheckbox[key] ))
                        };

                        if (key < $scope.outputWheres.length-1){
                            $scope.outputSQLWHERE+=" AND ";
                        };
                        //key is row
                    });
                };

                // construct full SQL
                $scope.outputSQL = $scope.outputSQLSELECT +' <br>'+ $scope.outputSQLJOIN +' <br>'+ $scope.outputSQLWHERE;
            };

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
        };

        $scope.fReset = function (){
            $($('.btn-cat-remove').get().reverse()).each(function(i, obj) {
                if ($(this).attr('data-value')>0){
                    $scope.fRemoveCatalogue($(this).attr('data-value'));
                };
            });
            $($('.btn-join-remove').get().reverse()).each(function(i, obj) {
                $scope.fRemoveJoin($(this).attr('data-value'));
            });
            $($('.btn-where-remove').get().reverse()).each(function(i, obj) {
                $scope.fRemoveWhere($(this).attr('data-value'));
            });

            $scope.outputSQL='';
            $scope.fValidate();
        };

    //end controller

  ///
}]);




