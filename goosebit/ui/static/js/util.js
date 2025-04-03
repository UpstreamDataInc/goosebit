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

async function updateSoftwareSelection(devices = null) {
    try {
        const url = new URL("/ui/bff/software?order[0][dir]=desc&order[0][name]=version", window.location.origin);
        if (devices != null) {
            for (const device of devices) {
                url.searchParams.append("ids", device.id);
            }
        }
        const response = await fetch(url.toString());
        if (!response.ok) {
            console.error("Retrieving software list failed.");
            return;
        }
        const data = (await response.json()).data;
        const selectElem = document.getElementById("selected-sw");
        selectElem.innerHTML = "";

        for (const item of data) {
            const optionElem = document.createElement("option");
            optionElem.value = item.id;
            optionElem.textContent = `${item.version}`;
            const models = [...new Set(item.compatibility.map((item) => item.model))];
            optionElem.textContent = `${item.version} (${models})`;
            selectElem.appendChild(optionElem);
        }
        $("#selected-sw").selectpicker("destroy");
        if (data.length === 0) {
            selectElem.title = "No valid software found for selected device";
            if (devices != null) {
                if (devices.length > 1) {
                    selectElem.title += "s";
                }
            }
            selectElem.disabled = true;
        } else {
            selectElem.disabled = false;
            selectElem.title = "Select Software";
        }
        $("#selected-sw").selectpicker();
    } catch (error) {
        console.error("Failed to fetch device data:", error);
    }
}

async function get_request(url) {
    const response = await fetch(url, {
        method: "GET",
    });

    const result = await response.json();
    if (!response.ok) {
        if (result.detail) {
            Swal.fire({
                title: "Warning",
                text: result.detail,
                icon: "warning",
                confirmButtonText: "Understood",
            });
        }

        throw new Error(`GET ${url} failed for ${JSON.stringify(object)}`);
    }
    return result;
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
async function put_request(url, object) {
    const response = await fetch(url, {
        method: "PUT",
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

        throw new Error(`PUT ${url} failed for ${JSON.stringify(object)}`);
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

        throw new Error(`PATCH ${url} failed for ${JSON.stringify(object)}`);
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

        throw new Error(`DELETE ${url} failed for ${JSON.stringify(object)}`);
    }
}
