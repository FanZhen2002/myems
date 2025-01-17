'use strict';

app.controller('CombinedEquipmentEquipmentController', function (
    $scope,
    $window,
    $translate,
    CombinedEquipmentService,
    EquipmentService,
    CombinedEquipmentEquipmentService,
    toaster,
    SweetAlert) {
    $scope.cur_user = JSON.parse($window.localStorage.getItem("myems_admin_ui_current_user"));
    $scope.currentCombinedEquipment = {selected:undefined};

    $scope.getAllEquipments = function () {
      EquipmentService.getAllEquipments(function (response) {
          if (angular.isDefined(response.status) && response.status === 200) {
              $scope.equipments = response.data;
          } else {
              $scope.equipments = [];
          }
      });
    };

    $scope.getEquipmentsByCombinedEquipmentID = function (id) {
        CombinedEquipmentEquipmentService.getEquipmentsByCombinedEquipmentID(id, function (response) {
            if (angular.isDefined(response.status) && response.status === 200) {
                $scope.combinedequipmentequipments = response.data;
            } else {
                $scope.combinedequipmentequipments = [];
            }
        });
    };

  $scope.changeCombinedEquipment=function(item,model){
  	$scope.currentCombinedEquipment=item;
  	$scope.currentCombinedEquipment.selected=model;
  	$scope.getEquipmentsByCombinedEquipmentID($scope.currentCombinedEquipment.id);
  };

  $scope.getAllCombinedEquipments = function () {
    CombinedEquipmentService.getAllCombinedEquipments(function (response) {
        if (angular.isDefined(response.status) && response.status === 200) {
            $scope.combinedequipments = response.data;
        } else {
            $scope.combinedequipments = [];
        }
    });
  };

    $scope.pairEquipment = function (dragEl, dropEl) {
        var equipmentid = angular.element('#' + dragEl).scope().equipment.id;
        var combinedequipmentid = $scope.currentCombinedEquipment.id;
        let headers = { "User-UUID": $scope.cur_user.uuid, "Token": $scope.cur_user.token };
        CombinedEquipmentEquipmentService.addPair(combinedequipmentid, equipmentid, headers, function (response) {
            if (angular.isDefined(response.status) && response.status === 201) {
                toaster.pop({
                    type: "success",
                    title: $translate.instant("TOASTER.SUCCESS_TITLE"),
                    body: $translate.instant('TOASTER.BIND_EQUIPMENT_SUCCESS'),
                    showCloseButton: true,
                });

                $scope.getEquipmentsByCombinedEquipmentID($scope.currentCombinedEquipment.id);
            } else {
                toaster.pop({
                    type: "error",
                    title: $translate.instant(response.data.title),
                    body: $translate.instant(response.data.description),
                    showCloseButton: true,
                });
            }
        });
    };

    $scope.deleteEquipmentPair = function (dragEl, dropEl) {
        if (angular.element('#' + dragEl).hasClass('source')) {
            return;
        }
        var combinedequipmentequipmentid = angular.element('#' + dragEl).scope().combinedequipmentequipment.id;
        var combinedequipmentid = $scope.currentCombinedEquipment.id;
        let headers = { "User-UUID": $scope.cur_user.uuid, "Token": $scope.cur_user.token };
        CombinedEquipmentEquipmentService.deletePair(combinedequipmentid, combinedequipmentequipmentid, headers, function (response) {
            if (angular.isDefined(response.status) && response.status === 204) {
                toaster.pop({
                    type: "success",
                    title: $translate.instant("TOASTER.SUCCESS_TITLE"),
                    body: $translate.instant('TOASTER.UNBIND_EQUIPMENT_SUCCESS'),
                    showCloseButton: true,
                });

                $scope.getEquipmentsByCombinedEquipmentID($scope.currentCombinedEquipment.id);
            } else {
                toaster.pop({
                    type: "error",
                    title: $translate.instant(response.data.title),
                    body: $translate.instant(response.data.description),
                    showCloseButton: true,
                });
            }
        });
    };

    $scope.getAllEquipments();
    $scope.getAllCombinedEquipments();

  	$scope.$on('handleBroadcastCombinedEquipmentChanged', function(event) {
      $scope.getAllCombinedEquipments();
  	});
});
