let dataTable;

document.addEventListener("DOMContentLoaded", async function () {
  dataTable = new DataTable("#device-table", {
    responsive: true,
    paging: true,
    processing: false,
    serverSide: true,
    scrollCollapse: true,
    scroller: true,
    scrollY: "65vh",
    stateSave: true,
    select: true,
    rowId: "uuid",
    ajax: {
      url: "/api/devices/all",
      contentType: "application/json",
    },
    initComplete: function () {
      updateBtnState();
    },
    columnDefs: [
      {
        targets: [0, 2, 5, 6, 8, 14],
        searchable: true,
        orderable: true,
      },
      {
        targets: "_all",
        searchable: false,
        orderable: false,
        render: function (data) {
          return data || "❓";
        },
      },
    ],
    columns: [
      { data: "name" },
      {
        data: "online",
        render: function (data, type) {
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
      { data: "uuid" },
      { data: "hw_model" },
      { data: "hw_revision" },
      { data: "feed" },
      { data: "flavor" },
      { data: "fw" },
      { data: "update_mode" },
      {
        data: "force_update",
        render: function (data, type) {
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
      { data: "fw_version" },
      {
        data: "progress",
        render: function (data, type) {
          if (type === "display" || type === "filter") {
            return (data || "❓") + "%";
          }
          return data;
        },
      },
      { data: "last_ip" },
      {
        data: "last_seen",
        render: function (data, type) {
          if (type === "display" || type === "filter") {
            return secondsToRecentDate(data);
          }
          return data;
        },
      },
      { data: "state" },
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
            action: function () {
              const selectedDevice = dataTable
                .rows({ selected: true })
                .data()
                .toArray()[0];
              window.location.href = `/ui/logs/${selectedDevice["uuid"]}`;
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
            action: function (e, dt) {
              const input = document.getElementById("device-selected-name");
              input.value = dt
                .rows({ selected: true })
                .data()
                .toArray()
                .map((d) => d["name"])[0];

              new bootstrap.Modal("#device-rename-modal").show();
            },
            className: "buttons-rename",
            titleAttr: "Rename Devices",
          },
          {
            text: '<i class="bi bi-gear" ></i>',
            action: function () {
              new bootstrap.Modal("#device-config-modal").show();
            },
            className: "buttons-config",
            titleAttr: "Configure Devices",
          },
          {
            text: '<i class="bi bi-trash" ></i>',
            action: function (e, dt) {
              const selectedDevices = dt
                .rows({ selected: true })
                .data()
                .toArray()
                .map((d) => d["uuid"]);
              deleteDevices(selectedDevices);
            },
            className: "buttons-delete",
            titleAttr: "Delete Devices",
          },
          {
            text: '<i class="bi bi-box-arrow-in-up-right"></i>',
            action: function () {
              const selectedDevices = dataTable
                .rows({ selected: true })
                .data()
                .toArray()
                .map((d) => d["uuid"]);
              forceUpdateDevices(selectedDevices);
            },
            className: "buttons-force-update",
            titleAttr: "Force Update",
          },
          {
            text: '<i class="bi bi-pin-angle"></i>',
            action: function () {
              const selectedDevices = dataTable
                .rows({ selected: true })
                .data()
                .toArray()
                .map((d) => d["uuid"]);
              pinDevices(selectedDevices);
            },
            className: "buttons-pin",
            titleAttr: "Pin Version",
          },
        ],
      },
    },
  });

  dataTable.on("click", "button.edit-name", function (e) {
    const data = dataTable.row(e.target.closest("tr")).data();
    updateDeviceName(data["uuid"]);
  });

  dataTable
    .on("select", function () {
      updateBtnState();
    })
    .on("deselect", function () {
      updateBtnState();
    });

  setInterval(function () {
    dataTable.ajax.reload(null, false);
  }, TABLE_UPDATE_TIME);

  await updateFirmwareSelection(true);
});

function updateBtnState() {
  if (dataTable.rows({ selected: true }).any()) {
    document
      .querySelector("button.buttons-select-none")
      .classList.remove("disabled");
    document
      .querySelector("button.buttons-config")
      .classList.remove("disabled");
    document
      .querySelector("button.buttons-force-update")
      .classList.remove("disabled");
    document
      .querySelector("button.buttons-delete")
      .classList.remove("disabled");
    document.querySelector("button.buttons-pin").classList.remove("disabled");
  } else {
    document
      .querySelector("button.buttons-select-none")
      .classList.add("disabled");
    document.querySelector("button.buttons-config").classList.add("disabled");
    document
      .querySelector("button.buttons-force-update")
      .classList.add("disabled");
    document.querySelector("button.buttons-delete").classList.add("disabled");
    document.querySelector("button.buttons-pin").classList.add("disabled");
  }
  if (dataTable.rows({ selected: true }).count() === 1) {
    document.querySelector("button.buttons-logs").classList.remove("disabled");
    document
      .querySelector("button.buttons-rename")
      .classList.remove("disabled");
  } else {
    document.querySelector("button.buttons-logs").classList.add("disabled");
    document.querySelector("button.buttons-rename").classList.add("disabled");
  }
}

async function updateDeviceConfig() {
  const devices = dataTable
    .rows({ selected: true })
    .data()
    .toArray()
    .map((d) => d["uuid"]);
  const firmware = document.getElementById("selected-fw").value;

  try {
    await post("/api/devices/update", { devices, firmware });
  } catch (error) {
    console.error("Update device config failed:", error);
  }

  setTimeout(updateDeviceList, 50);
}

async function updateDeviceName() {
  const devices = dataTable
    .rows({ selected: true })
    .data()
    .toArray()
    .map((d) => d["uuid"]);
  name = document.getElementById("device-selected-name").value;

  try {
    await post("/api/devices/update", { devices, name });
  } catch (error) {
    console.error("Update device name failed:", error);
  }

  setTimeout(updateDeviceList, 50);
}

async function forceUpdateDevices(devices) {
  try {
    await post("/api/devices/force_update", { devices });
  } catch (error) {
    console.error("Update force update state failed:", error);
  }

  setTimeout(updateDeviceList, 50);
}

async function deleteDevices(devices) {
  try {
    await post("/api/devices/delete", { devices });
  } catch (error) {
    console.error("Delete device failed:", error);
  }

  setTimeout(updateDeviceList, 50);
}

async function pinDevices(devices) {
  try {
    await post("/api/devices/update", { devices, pinned: true });
  } catch (error) {
    console.error("Error:", error);
  }

  setTimeout(updateDeviceList, 50);
}

function updateDeviceList() {
  dataTable.ajax.reload();
}
