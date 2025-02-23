// ==UserScript==
// @name         Auto-Accept Rides on SIXT 1.6 production
// @namespace    http://tampermonkey.net/
// @version      1.6
// @description  Automatically accepts rides based on class and payout conditions with a buffer to prevent duplicate selection.
// @author       You
// @match        https://dcp.orange.sixt.com/availableRides*
// @icon         data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==
// @grant        none
// @require      https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js
// ==/UserScript==

(function() {
    'use strict';

    const rideParameters = [
        { type: "Ride", payout: 150, driver: "Raza Ul Habib Tahir", vehicle: "FR19 DZG" },
        { type: "Business", payout: 120, driver: "Raza Ul Habib Tahir", vehicle: "FR19 DZG" },
        { type: "First", payout: 98, driver: "Raza Ul Habib Tahir", vehicle: "KM19 WDS" },
        { type: "Business XL", payout: 120, driver: "Raza Ul Habib Tahir", vehicle: "KX19UBY" },
        { type: "Ride XL", payout: 120, driver: "Raza Ul Habib Tahir", vehicle: "KX19UBY" }
    ];

    let acceptedRides = new Set(); // Tracks recently accepted rides

    function checkForMatchingRides() {
console.log('listening');
        const rideRows = document.querySelectorAll('.available-rides-table tbody tr');

        rideRows.forEach(row => {
            const rideType = row.querySelector('.class')?.innerText.trim();
            const payoutText = row.querySelector('.payout')?.innerText.replace('£', '').trim();
            const payout = parseFloat(payoutText);
            const acceptButton = row.querySelector('.button.button-outline');

            rideParameters.forEach(param => {
                const rideKey = `${rideType}-${payout}`; // Unique key for tracking

                if (rideType === param.type && payout >= param.payout && !acceptedRides.has(rideKey)) {
                    console.log(`Accepting ride: ${rideType} - £${payout}`);
                    acceptedRides.add(rideKey); // Mark ride as accepted

                    acceptButton.click();

                    // Clear this ride from the buffer after 10 seconds
                    setTimeout(() => {
                        acceptedRides.delete(rideKey);
                        console.log(`Cleared from buffer: ${rideKey}`);
                    }, 10000);

                    // Wait for modal to open and process selection
                    setTimeout(() => {
                        handleModalReopen(() => {
                            selectDriverAndVehicle(param.driver, param.vehicle);
                        });
                    }, 100);
                }
            });
        });
    }

    function handleModalReopen(callback) {
        const modal = document.querySelector(".modal");
        if (!modal || modal.style.display === "modal-open") {
            console.log("Modal closed. Reopening...");
            setTimeout(() => {
                handleModalReopen(callback);
            }, 500);
        } else {
            console.log("Modal open. Proceeding...");
            callback();
        }
    }

    function selectDriverAndVehicle(driver, vehicle) {
        console.log("Selecting driver...");

        const driverDropdown = document.querySelector("#react-select-2-input")?.closest('.react-select__control');

        if (driverDropdown && isDropdownOnSelect(driverDropdown)) {
            driverDropdown.dispatchEvent(new MouseEvent("mousedown", { bubbles: true }));

            setTimeout(() => {
                const driverOption = getDropdownOption(driver);
                if (driverOption) {
                    driverOption.click();
                    console.log("Driver selected:", driver);

                    setTimeout(() => {
                        selectVehicle(vehicle);
                    }, 200);
                }
            }, 100);
        } else {
            console.warn("Driver dropdown not found or already selected.");
        }
    }

    function selectVehicle(vehicle) {
        console.log("Selecting vehicle...");

        const vehicleDropdown = document.querySelector("#react-select-3-input")?.closest('.react-select__control');

        if (vehicleDropdown && isDropdownOnSelect(vehicleDropdown)) {
            vehicleDropdown.dispatchEvent(new MouseEvent("mousedown", { bubbles: true }));

            setTimeout(() => {
                const vehicleOption = getDropdownOption(vehicle);
                if (vehicleOption) {
                    vehicleOption.click();
                    console.log("Vehicle selected:", vehicle);
                    setTimeout(() => {
                    const cancelButton = document.querySelector(".close-button.btn.btn-primary");
                    if (cancelButton) {
                        cancelButton.click();
                        console.log('cancel pressed');

                    }
                }, 300);
                }
            }, 100);

            setTimeout(() => {location.reload();}, 3000);
        } else {
            console.warn("Vehicle dropdown not found or already selected.");
            location.reload();
        }
    }

    function isDropdownOnSelect(dropdown) {
        const valueContainer = dropdown.querySelector(".react-select__single-value");
        return valueContainer && valueContainer.innerText.trim() === "Select";
    }

    function getDropdownOption(text) {
        return Array.from(document.querySelectorAll('.react-select__option'))
            .find(option => option.innerText.trim() === text);
    }



    setTimeout(() => {
        checkForMatchingRides();
        // Subsequent calls every 1.5 seconds
        setInterval(checkForMatchingRides, 1500);
    }, 3000);

})();
