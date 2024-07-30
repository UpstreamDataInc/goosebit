document.addEventListener("DOMContentLoaded", function () {
  var dataTable = new DataTable("#device-table", {
    responsive: true,
    paging: false,
    scrollCollapse: true,
    scroller: true,
    scrollY: "65vh",
    stateSave: true,
    select: true,
    rowId: "uuid",
    ajax: {
      url: "/api/devices/all",
      dataSrc: "",
    },
    initComplete: function () {
      updateBtnState();
    },
    columnDefs: [
      {
        targets: "_all",
        render: function (data, type, row) {
          return data || "❓";
        },
      },
    ],
    columns: [
      { data: "name" },
      {
        data: "online",
        render: function (data, type, row) {
          if (type === "display" || type === "filter") {
            color = data ? "success" : "danger";
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
        render: function (data, type, row) {
          if (type === "display" || type === "filter") {
            color = data ? "success" : "danger";
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
        render: function (data, type, row) {
          if (type === "display" || type === "filter") {
            return (data || "❓") + "%";
          }
          return data;
        },
      },
      { data: "last_ip" },
      {
        data: "last_seen",
        render: function (data, type, row) {
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
            action: function (e, dt, node, config) {
              selectedDevice = dataTable
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
            action: function (e, dt, node, config) {
              const input = document.getElementById("device-selected-name");
              const selectedDeviceName = dt
                .rows({ selected: true })
                .data()
                .toArray()
                .map((d) => d["name"])[0];
              input.value = selectedDeviceName;

              new bootstrap.Modal("#device-rename-modal").show();
            },
            className: "buttons-rename",
            titleAttr: "Rename Devices",
          },
          {
            text: '<i class="bi bi-gear" ></i>',
            action: function (e, dt, node, config) {
              new bootstrap.Modal("#device-config-modal").show();
            },
            className: "buttons-config",
            titleAttr: "Configure Devices",
          },
          {
            text: '<i class="bi bi-trash" ></i>',
            action: function (e, dt, node, config) {
              selectedDevices = dt
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
            action: function (e, dt, node, config) {
              selectedDevices = dataTable
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
            action: function (e, dt, node, config) {
              selectedDevices = dataTable
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
    let data = dataTable.row(e.target.closest("tr")).data();
    uuid = data["uuid"];
    updateDeviceName(uuid);
  });

  dataTable
    .on("select", function (e, dt, type, indexes) {
      updateBtnState();
    })
    .on("deselect", function (e, dt, type, indexes) {
      updateBtnState();
    });

  setInterval(function () {
    dataTable.ajax.reload(null, false);
  }, TABLE_UPDATE_TIME);

  updateFirmwareSelection(true);
});

function updateBtnState() {
  dataTable = $("#device-table").DataTable();
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
  if (dataTable.rows({ selected: true }).count() == 1) {
    document.querySelector("button.buttons-logs").classList.remove("disabled");
    document
      .querySelector("button.buttons-rename")
      .classList.remove("disabled");
  } else {
    document.querySelector("button.buttons-logs").classList.add("disabled");
    document.querySelector("button.buttons-rename").classList.add("disabled");
  }

  if (
    dataTable.rows({ selected: true }).ids().toArray().length ===
    dataTable.rows().ids().toArray().length
  ) {
    document
      .querySelector("button.buttons-select-all")
      .classList.add("disabled");
  } else {
    document
      .querySelector("button.buttons-select-all")
      .classList.remove("disabled");
  }
}

function updateDeviceConfig() {
  selectedDevices = dataTable
    .rows({ selected: true })
    .data()
    .toArray()
    .map((d) => d["uuid"]);
  selectedFirmware = document.getElementById("selected-fw").value;

  fetch("/api/devices/update", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      devices: selectedDevices,
      firmware: selectedFirmware,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to update devices.");
      }
      return response.json();
    })
    .catch((error) => {
      console.error("Error:", error);
    });

  setTimeout(updateDeviceList, 50);
}

function updateDeviceName() {
  selectedDevices = dataTable
    .rows({ selected: true })
    .data()
    .toArray()
    .map((d) => d["uuid"]);
  name = document.getElementById("device-selected-name").value;

  fetch("/api/devices/update", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      devices: selectedDevices,
      name: name,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to update devices.");
      }
      return response.json();
    })
    .catch((error) => {
      console.error("Error:", error);
    });

  setTimeout(updateDeviceList, 50);
}

function forceUpdateDevices(devices) {
  fetch("/api/devices/force_update", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      devices: devices,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to force device update.");
      }
      return response.json();
    })
    .catch((error) => {
      console.error("Error:", error);
    });

  setTimeout(updateDeviceList, 50);
}

function deleteDevices(devices) {
  fetch("/api/devices/delete", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      devices: devices,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to delete devices.");
      }
      return response.json();
    })
    .catch((error) => {
      console.error("Error:", error);
    });

  setTimeout(updateDeviceList, 50);
}

function pinDevices(devices) {
  fetch("/api/devices/update", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      devices: devices,
      pinned: true,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to update devices.");
      }
      return response.json();
    })
    .catch((error) => {
      console.error("Error:", error);
    });

  setTimeout(updateDeviceList, 50);
}

function updateDeviceList() {
  dataTable.ajax.reload();
}
