const puppeteer = require('puppeteer');
require('dotenv').config(); // Add this to use environment variables

const rideParameters = [
    { type: "Ride", payout: 150, driver: "Raza Ul Habib Tahir", vehicle: "FR19 DZG" },
    { type: "Business", payout: 120, driver: "Raza Ul Habib Tahir", vehicle: "FR19 DZG" },
    { type: "First", payout: 98, driver: "Raza Ul Habib Tahir", vehicle: "KM19 WDS" },
    { type: "Business XL", payout: 120, driver: "Raza Ul Habib Tahir", vehicle: "KX19UBY" },
    { type: "Ride XL", payout: 120, driver: "Raza Ul Habib Tahir", vehicle: "KX19UBY" }
];

const acceptedRides = new Set(); // Tracks recently accepted rides

(async () => {
    // Get the bearer token from environment variable
    const bearerToken = process.env.BEARER_TOKEN;
    if (!bearerToken) {
        console.error('Error: BEARER_TOKEN environment variable not set');
        return;
    }

    // Launch the browser
    const browser = await puppeteer.launch({ headless: false });
    const page = await browser.newPage();

    // Set the Authorization header with Bearer token
    await page.setExtraHTTPHeaders({
        'Authorization': `Bearer ${bearerToken}`
    });

    // Navigate to the target page
    await page.goto('https://dcp.orange.sixt.com/availableRides?page=1');

    // Function to check for matching rides
    async function checkForMatchingRides() {
        console.log('Checking for matching rides...');

        // Evaluate the page to find ride rows
        const rides = await page.$$eval('.available-rides-table tbody tr', (rows) => {
            return rows.map(row => {
                const rideType = row.querySelector('.class')?.innerText.trim();
                const payoutText = row.querySelector('.payout')?.innerText.replace('£', '').trim();
                const payout = parseFloat(payoutText);
                const acceptButton = row.querySelector('.button.button-outline');
                return { rideType, payout, acceptButton: acceptButton ? true : false };
            });
        });

        // Process each ride
        for (let i = 0; i < rides.length; i++) {
            const { rideType, payout, acceptButton } = rides[i];
            const rideKey = `${rideType}-${payout}`;

            rideParameters.forEach(async param => {
                if (rideType === param.type && payout >= param.payout && !acceptedRides.has(rideKey)) {
                    console.log(`Accepting ride: ${rideType} - £${payout}`);
                    acceptedRides.add(rideKey);

                    // Click the accept button
                    await page.click(`.available-rides-table tbody tr:nth-child(${i + 1}) .button.button-outline`);

                    // Handle modal and select driver/vehicle
                    await handleModalReopen(page, param.driver, param.vehicle);

                    // Clear the ride from the buffer after 10 seconds
                    setTimeout(() => {
                        acceptedRides.delete(rideKey);
                        console.log(`Cleared from buffer: ${rideKey}`);
                    }, 10000);
                }
            });
        }
    }

    // Function to handle modal reopening
    async function handleModalReopen(page, driver, vehicle) {
        console.log('Handling modal...');

        // Wait for the modal to appear
        await page.waitForSelector('.modal', { visible: true });

        // Select driver
        await page.click('#react-select-2-input');
        await page.type('#react-select-2-input', driver);
        await page.keyboard.press('Enter');

        // Select vehicle
        await page.click('#react-select-3-input');
        await page.type('#react-select-3-input', vehicle);
        await page.keyboard.press('Enter');

        // Close the modal
        await page.click('.close-button.btn.btn-primary');
        console.log('Modal closed.');
    }

    // Run the check every 1.5 seconds
    setInterval(async () => {
        await checkForMatchingRides();
    }, 1500);
})();