let dataTable;

document.addEventListener("DOMContentLoaded", () => {
    dataTable = new DataTable("#device-table", {
        responsive: true,
        paging: true,
        processing: false,
        serverSide: true,
        scrollCollapse: true,
        scroller: true,
        scrollY: "65vh",
        stateSave: true,
        stateLoadParams: (settings, data) => {
            // if save state is older than last breaking code change...
            if (data.time <= 1722434386000) {
                // ... delete it
                for (const key of Object.keys(data)) {
                    delete data[key];
                }
            }
        },
        ajax: {
            url: "/ui/bff/devices",
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
            { data: "name", searchable: true, orderable: true },
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
            { data: "sw_version", searchable: true, orderable: true },
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
        select: true,
        rowId: "uuid",
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
                        text: '<i class="bi bi-file-earmark-arrow-down"></i>',
                        action: (e, dt) => {
                            const selectedDevices = dt.rows({ selected: true }).data().toArray();
                            downloadLogins(selectedDevices);
                        },
                        className: "buttons-export-login",
                        titleAttr: "Export Login",
                    },
                    {
                        text: '<i class="bi bi-file-text"></i>',
                        action: (e, dt) => {
                            const selectedDevice = dt.rows({ selected: true }).data().toArray()[0];
                            window.location.href = `/ui/logs/${selectedDevice.uuid}`;
                        },
                        className: "buttons-logs",
                        titleAttr: "View Log",
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
});

function updateBtnState() {
    if (dataTable.rows({ selected: true }).any()) {
        document.querySelector("button.buttons-select-none").classList.remove("disabled");
        document.querySelector("button.buttons-export-login").classList.remove("disabled");
    } else {
        document.querySelector("button.buttons-select-none").classList.add("disabled");
        document.querySelector("button.buttons-export-login").classList.add("disabled");
    }
    if (dataTable.rows({ selected: true }).count() === 1) {
        document.querySelector("button.buttons-logs").classList.remove("disabled");
    } else {
        document.querySelector("button.buttons-logs").classList.add("disabled");
    }
}

function downloadLogins(devices) {
    const deviceLogins = devices.map((dev) => {
        return [dev.name, `https://${dev.uuid}-access.loadsync.io`, dev.uuid];
    });
    deviceLogins.unshift(["Building", "Access Link", "Serial Number/Wifi SSID", "Login/Wifi Password"]);

    const csvContent = `data:text/csv;charset=utf-8,${deviceLogins.map((e) => e.join(",")).join("\n")}`;
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "LoadsyncLogins-Export.csv");
    document.body.appendChild(link);

    link.click();
}
