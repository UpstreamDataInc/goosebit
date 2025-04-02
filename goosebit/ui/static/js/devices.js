let dataTable;

const renderFunctions = {
    force_update: (data, type) => {
        if (type === "display") {
            const color = data ? "success" : "muted";
            return `
            <div class="text-${color}">
                ●
            </div>
            `;
        }
        return data;
    },
    progress: (data, type) => {
        if (type === "display" || type === "filter") {
            return data ? `${data}%` : "-";
        }
        return data;
    },
    polling: (data, type) => {
        return data ? "on time" : "overdue";
    },
    last_seen: (data, type) => {
        if (type === "display" || type === "filter") {
            return secondsToRecentDate(data);
        }
        return data;
    },
};

document.addEventListener("DOMContentLoaded", async () => {
    const columnConfig = await get_request("/ui/bff/devices/columns");
    for (const col in columnConfig.columns) {
        const colDesc = columnConfig.columns[col];
        const colName = colDesc.data;
        if (renderFunctions[colName]) {
            columnConfig.columns[col].render = renderFunctions[colName];
        }
    }

    dataTable = new DataTable("#device-table", {
        responsive: true,
        paging: true,
        processing: false,
        serverSide: true,
        order: { name: "id", dir: "asc" },
        scrollCollapse: true,
        scroller: true,
        scrollY: "65vh",
        stateSave: true,
        select: true,
        rowId: "id",
        ajax: {
            url: "/ui/bff/devices",
            data: (data) => {
                // biome-ignore lint/performance/noDelete: really has to be deleted
                delete data.columns;
            },
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
        columns: columnConfig.columns,
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
                            window.location.href = `/ui/logs/${selectedDevice.id}`;
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
                            const selectedDevices = dataTable.rows({ selected: true }).data().toArray();
                            const selectedDevice = selectedDevices[0];
                            updateSoftwareSelection(selectedDevices);
                            $("#device-name").val(selectedDevice.name);
                            $("#device-selected-feed").val(selectedDevice.feed);
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
                                .map((d) => d.id);
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
                                .map((d) => d.id);
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
                                .map((d) => d.id);
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
        updateDeviceList();
    }, TABLE_UPDATE_TIME);

    await updateSoftwareSelection();

    // Name update form submit
    const nameForm = document.getElementById("device-name-form");
    nameForm.addEventListener(
        "submit",
        async (event) => {
            if (nameForm.checkValidity() === false) {
                event.preventDefault();
                event.stopPropagation();
                nameForm.classList.add("was-validated");
            } else {
                event.preventDefault();
                await updateDeviceName();
                nameForm.classList.remove("was-validated");
                nameForm.reset();
                const modal = bootstrap.Modal.getInstance(document.getElementById("device-config-modal"));
                modal.hide();
            }
        },
        false,
    );

    // Rollout form submit
    const rolloutForm = document.getElementById("device-software-rollout-form");
    rolloutForm.addEventListener(
        "submit",
        async (event) => {
            if (rolloutForm.checkValidity() === false) {
                event.preventDefault();
                event.stopPropagation();
                rolloutForm.classList.add("was-validated");
            } else {
                event.preventDefault();
                await updateDeviceRollout();
                rolloutForm.classList.remove("was-validated");
                rolloutForm.reset();
                const modal = bootstrap.Modal.getInstance(document.getElementById("device-config-modal"));
                modal.hide();
            }
        },
        false,
    );

    // Manual software form submit
    const manualSoftwareForm = document.getElementById("device-software-manual-form");
    manualSoftwareForm.addEventListener(
        "submit",
        async (event) => {
            if (manualSoftwareForm.checkValidity() === false) {
                event.preventDefault();
                event.stopPropagation();
                manualSoftwareForm.classList.add("was-validated");
                if (document.getElementById("selected-sw").value === "") {
                    document.getElementById("selected-sw").parentElement.classList.add("is-invalid");
                }
            } else {
                event.preventDefault();
                await updateDeviceManualSoftware();
                manualSoftwareForm.classList.remove("was-validated");
                document.getElementById("selected-sw").parentElement.classList.remove("is-invalid");
                manualSoftwareForm.reset();
                const modal = bootstrap.Modal.getInstance(document.getElementById("device-config-modal"));
                modal.hide();
            }
        },
        false,
    );

    // Latest software form submit
    const latestSoftwareForm = document.getElementById("device-software-latest-form");
    latestSoftwareForm.addEventListener(
        "submit",
        async (event) => {
            if (latestSoftwareForm.checkValidity() === false) {
                event.preventDefault();
                event.stopPropagation();
                latestSoftwareForm.classList.add("was-validated");
            } else {
                event.preventDefault();
                await updateDeviceLatest();
                latestSoftwareForm.classList.remove("was-validated");
                latestSoftwareForm.reset();
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

async function updateDeviceName() {
    const devices = dataTable
        .rows({ selected: true })
        .data()
        .toArray()
        .map((d) => d.id);
    const name = document.getElementById("device-name").value;

    try {
        await patch_request("/ui/bff/devices", { devices, name });
    } catch (error) {
        console.error("Update device config failed:", error);
    }

    setTimeout(updateDeviceList, 50);
}

async function updateDeviceRollout() {
    const devices = dataTable
        .rows({ selected: true })
        .data()
        .toArray()
        .map((d) => d.id);
    const feed = document.getElementById("device-selected-feed").value;
    const software = "rollout";

    try {
        await patch_request("/ui/bff/devices", { devices, feed, software });
    } catch (error) {
        console.error("Update device config failed:", error);
    }

    setTimeout(updateDeviceList, 50);
}

async function updateDeviceManualSoftware() {
    const devices = dataTable
        .rows({ selected: true })
        .data()
        .toArray()
        .map((d) => d.id);
    const feed = null;
    const software = document.getElementById("selected-sw").value;

    try {
        await patch_request("/ui/bff/devices", { devices, feed, software });
    } catch (error) {
        console.error("Update device config failed:", error);
    }

    setTimeout(updateDeviceList, 50);
}

async function updateDeviceLatest() {
    const devices = dataTable
        .rows({ selected: true })
        .data()
        .toArray()
        .map((d) => d.id);
    const feed = null;
    const software = "latest";

    try {
        await patch_request("/ui/bff/devices", { devices, feed, software });
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
    const scrollPosition = $("#device-table").parent().scrollTop(); // Get current scroll position

    const selectedRows = dataTable
        .rows({ selected: true })
        .data()
        .toArray()
        .map((d) => d.id);

    dataTable.ajax.reload(() => {
        dataTable.rows().every(function () {
            const rowData = this.data();
            if (selectedRows.includes(rowData.id)) {
                this.select();
            }
        });
        $("#device-table").parent().scrollTop(scrollPosition); // Restore scroll position after reload
    }, false);
}
