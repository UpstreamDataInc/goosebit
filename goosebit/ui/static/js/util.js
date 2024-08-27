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

async function updateSoftwareSelection(addSpecialMode = false) {
    try {
        const response = await fetch("/ui/bff/software");
        if (!response.ok) {
            console.error("Retrieving software list failed.");
            return;
        }
        const data = (await response.json()).data;
        const selectElem = document.getElementById("selected-sw");

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
            optionElem.textContent = `${item.version}`;
            const models = [...new Set(item.compatibility.map((item) => item.model))];
            optionElem.textContent = `${item.version} (${models})`;
            selectElem.appendChild(optionElem);
        }
    } catch (error) {
        console.error("Failed to fetch device data:", error);
    }
}

async function post_request(url, object) {
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(object),
    });

    if (!response.ok) {
        const result = await response.json();
        if (result.detail) {
            Swal.fire({
                title: "Warning",
                text: result.detail,
                icon: "warning",
                confirmButtonText: "Understood",
            });
        }

        throw new Error(`POST ${url} failed for ${JSON.stringify(object)}`);
    }
}
async function patch_request(url, object) {
    const response = await fetch(url, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(object),
    });

    if (!response.ok) {
        const result = await response.json();
        if (result.detail) {
            Swal.fire({
                title: "Warning",
                text: result.detail,
                icon: "warning",
                confirmButtonText: "Understood",
            });
        }

        throw new Error(`POST ${url} failed for ${JSON.stringify(object)}`);
    }
}
async function delete_request(url, object) {
    const response = await fetch(url, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(object),
    });

    if (!response.ok) {
        const result = await response.json();
        if (result.detail) {
            Swal.fire({
                title: "Warning",
                text: result.detail,
                icon: "warning",
                confirmButtonText: "Understood",
            });
        }

        throw new Error(`POST ${url} failed for ${JSON.stringify(object)}`);
    }
}
