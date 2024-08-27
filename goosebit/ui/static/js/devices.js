let dataTable;

document.addEventListener("DOMContentLoaded", async () => {
    dataTable = new DataTable("#device-table", {
        responsive: true,
        paging: true,
        processing: false,
        serverSide: true,
        order: [],
        scrollCollapse: true,
        scroller: true,
        scrollY: "65vh",
        stateSave: true,
        stateLoadParams: (settings, data) => {
            // if save state is older than last breaking code change...
            if (data.time <= 1722434189000) {
                // ... delete it
                for (const key of Object.keys(data)) {
                    delete data[key];
                }
            }
        },
        select: true,
        rowId: "uuid",
        ajax: {
            url: "/ui/bff/devices/",
            contentType: "application/json",
        },
        initComplete: () => {
            updateBtnState();
        },
        columnDefs: [
            {
                targets: "_all",
                searchable: false,
                orderable: false,
                render: (data) => data || "-",
            },
        ],
        columns: [
            {
                data: "online",
                render: (data, type) => {
                    if (type === "display" || type === "filter") {
                        const color = data ? "success" : "danger";
                        return `
                        <div class="text-${color}">
                            ●
                        </div>
                        `;
                    }
                    return data;
                },
            },
            { data: "uuid", searchable: true, orderable: true },
            { data: "name", searchable: true, orderable: true },
            { data: "hw_model" },
            { data: "hw_revision" },
            { data: "feed", searchable: true, orderable: true },
            { data: "sw_version", searchable: true, orderable: true },
            { data: "sw_target_version" },
            { data: "update_mode", searchable: true, orderable: true },
            { data: "last_state", searchable: true, orderable: true },
            {
                data: "force_update",
                render: (data, type) => {
                    if (type === "display" || type === "filter") {
                        const color = data ? "success" : "muted";
                        return `
                        <div class="text-${color}">
                            ●
                        </div>
                        `;
                    }
                    return data;
                },
            },
            {
                data: "progress",
                render: (data, type) => {
                    if (type === "display" || type === "filter") {
                        return data ? `${data}%` : "-";
                    }
                    return data;
                },
            },
            { data: "last_ip" },
            {
                data: "last_seen",
                render: (data, type) => {
                    if (type === "display" || type === "filter") {
                        return secondsToRecentDate(data);
                    }
                    return data;
                },
            },
        ],
        layout: {
            top1Start: {
                buttons: [
                    {
                        text: '<i class="bi bi-check-all"></i>',
                        extend: "selectAll",
                        titleAttr: "Select All",
                    },
                    {
                        text: '<i class="bi bi-x"></i>',
                        extend: "selectNone",
                        titleAttr: "Clear Selection",
                    },
                    {
                        text: '<i class="bi bi-file-text"></i>',
                        action: () => {
                            const selectedDevice = dataTable.rows({ selected: true }).data().toArray()[0];
                            window.location.href = `/ui/logs/${selectedDevice.uuid}`;
                        },
                        className: "buttons-logs",
                        titleAttr: "View Log",
                    },
                ],
            },
            bottom1Start: {
                buttons: [
                    {
                        text: '<i class="bi bi-pen" ></i>',
                        action: () => {
                            const selectedDevice = dataTable.rows({ selected: true }).data().toArray()[0];
                            $("#device-selected-name").val(selectedDevice.name);
                            $("#device-selected-feed").val(selectedDevice.feed);

                            let selectedValue;
                            if (selectedDevice.update_mode === "Rollout") {
                                selectedValue = "rollout";
                            } else if (selectedDevice.update_mode === "Latest") {
                                selectedValue = "latest";
                            } else {
                                selectedValue = selectedDevice.sw_assigned;
                            }
                            $("#selected-sw").val(selectedValue);

                            new bootstrap.Modal("#device-config-modal").show();
                        },
                        className: "buttons-config",
                        titleAttr: "Configure Devices",
                    },
                    {
                        text: '<i class="bi bi-trash" ></i>',
                        action: async (e, dt) => {
                            const selectedDevices = dt
                                .rows({ selected: true })
                                .data()
                                .toArray()
                                .map((d) => d.uuid);
                            await deleteDevices(selectedDevices);
                        },
                        className: "buttons-delete",
                        titleAttr: "Delete Devices",
                    },
                    {
                        text: '<i class="bi bi-box-arrow-in-up-right"></i>',
                        action: async () => {
                            const selectedDevices = dataTable
                                .rows({ selected: true })
                                .data()
                                .toArray()
                                .map((d) => d.uuid);
                            await forceUpdateDevices(selectedDevices);
                        },
                        className: "buttons-force-update",
                        titleAttr: "Force Update",
                    },
                    {
                        text: '<i class="bi bi-pin-angle"></i>',
                        action: async () => {
                            const selectedDevices = dataTable
                                .rows({ selected: true })
                                .data()
                                .toArray()
                                .map((d) => d.uuid);
                            await pinDevices(selectedDevices);
                        },
                        className: "buttons-pin",
                        titleAttr: "Pin Version",
                    },
                ],
            },
        },
    });

    dataTable
        .on("select", () => {
            updateBtnState();
        })
        .on("deselect", () => {
            updateBtnState();
        });

    setInterval(() => {
        dataTable.ajax.reload(null, false);
    }, TABLE_UPDATE_TIME);

    await updateSoftwareSelection(true);

    // Config form submit
    const configForm = document.getElementById("device-config-form");
    configForm.addEventListener(
        "submit",
        async (event) => {
            if (configForm.checkValidity() === false) {
                event.preventDefault();
                event.stopPropagation();
                configForm.classList.add("was-validated");
            } else {
                event.preventDefault();
                await updateDeviceConfig();
                configForm.classList.remove("was-validated");
                configForm.reset();
                const modal = bootstrap.Modal.getInstance(document.getElementById("device-config-modal"));
                modal.hide();
            }
        },
        false,
    );
});

function updateBtnState() {
    if (dataTable.rows({ selected: true }).any()) {
        document.querySelector("button.buttons-select-none").classList.remove("disabled");
        document.querySelector("button.buttons-config").classList.remove("disabled");
        document.querySelector("button.buttons-force-update").classList.remove("disabled");
        document.querySelector("button.buttons-delete").classList.remove("disabled");
        document.querySelector("button.buttons-pin").classList.remove("disabled");
    } else {
        document.querySelector("button.buttons-select-none").classList.add("disabled");
        document.querySelector("button.buttons-config").classList.add("disabled");
        document.querySelector("button.buttons-force-update").classList.add("disabled");
        document.querySelector("button.buttons-delete").classList.add("disabled");
        document.querySelector("button.buttons-pin").classList.add("disabled");
    }
    if (dataTable.rows({ selected: true }).count() === 1) {
        document.querySelector("button.buttons-logs").classList.remove("disabled");
    } else {
        document.querySelector("button.buttons-logs").classList.add("disabled");
    }
}

async function updateDeviceConfig() {
    const devices = dataTable
        .rows({ selected: true })
        .data()
        .toArray()
        .map((d) => d.uuid);
    const name = document.getElementById("device-selected-name").value;
    const feed = document.getElementById("device-selected-feed").value;
    const software = document.getElementById("selected-sw").value;

    try {
        await patch_request("/ui/bff/devices", { devices, name, feed, software });
    } catch (error) {
        console.error("Update device config failed:", error);
    }

    setTimeout(updateDeviceList, 50);
}

async function forceUpdateDevices(devices) {
    try {
        await patch_request("/ui/bff/devices", { devices, force_update: true });
    } catch (error) {
        console.error("Update force update state failed:", error);
    }

    setTimeout(updateDeviceList, 50);
}

async function deleteDevices(devices) {
    try {
        await delete_request("/ui/bff/devices", { devices });
    } catch (error) {
        console.error("Delete device failed:", error);
    }

    setTimeout(updateDeviceList, 50);
}

async function pinDevices(devices) {
    try {
        await patch_request("/ui/bff/devices", { devices, pinned: true });
    } catch (error) {
        console.error("Error:", error);
    }

    setTimeout(updateDeviceList, 50);
}

function updateDeviceList() {
    dataTable.ajax.reload();
}
