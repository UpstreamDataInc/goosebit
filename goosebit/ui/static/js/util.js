function secondsToRecentDate(t) {
    if (t == null) {
        return null;
    }
    const time = Number(t);
    const d = Math.floor(time / 86400);
    const h = Math.floor((time % 86400) / 3600);
    const m = Math.floor(((time % 86400) % 3600) / 60);
    const s = Math.floor(((time % 86400) % 3600) % 60);

    if (d > 0) {
        return d + (d === 1 ? " day" : " days");
    }
    if (h > 0) {
        return h + (h === 1 ? " hour" : " hours");
    }
    if (m > 0) {
        return m + (m === 1 ? " minute" : " minutes");
    }
    return s + (s === 1 ? " second" : " seconds");
}

async function updateFirmwareSelection(addSpecialMode = false) {
    try {
        const response = await fetch("/api/firmware/all");
        if (!response.ok) {
            console.error("Retrieving firmwares failed.");
            return;
        }
        const data = (await response.json()).data;
        const selectElem = document.getElementById("selected-fw");

        if (addSpecialMode) {
            let optionElem = document.createElement("option");
            optionElem.value = "rollout";
            optionElem.textContent = "Rollout";
            selectElem.appendChild(optionElem);

            optionElem = document.createElement("option");
            optionElem.value = "latest";
            optionElem.textContent = "Latest";
            selectElem.appendChild(optionElem);
        }

        for (const item of data) {
            const optionElem = document.createElement("option");
            optionElem.value = item.id;
            optionElem.textContent = item.name;
            selectElem.appendChild(optionElem);
        }
    } catch (error) {
        console.error("Failed to fetch device data:", error);
    }
}

async function post(url, object) {
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(object),
    });

    if (!response.ok) {
        throw new Error(`POST ${url} failed for ${JSON.stringify(object)}`);
    }
}
