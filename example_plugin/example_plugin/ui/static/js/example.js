document.addEventListener("DOMContentLoaded", async () => {
    const cardData = await get_request("/plugins/example_plugin/ui/bff/example");

    if (Number.isInteger(cardData.device_count)) {
        deviceCountCard = document.getElementById("device-count-card");
        deviceCount = document.getElementById("device-count");

        deviceCount.innerHTML = cardData.device_count;
        deviceCountCard.hidden = false;
    }
    if (Number.isInteger(cardData.software_count)) {
        softwareCountCard = document.getElementById("software-count-card");
        softwareCount = document.getElementById("software-count");

        softwareCount.innerHTML = cardData.software_count;
        softwareCountCard.hidden = false;
    }
});
