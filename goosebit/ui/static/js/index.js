let dataTable;

document.addEventListener("DOMContentLoaded", function () {
  dataTable = new DataTable("#device-table", {
    responsive: true,
    paging: false,
    scrollCollapse: true,
    scroller: true,
    scrollY: "65vh",
    stateSave: true,
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
      { data: "fw" },
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
            action: function (e, dt) {
              const selectedDevices = dt
                .rows({ selected: true })
                .data()
                .toArray();
              downloadLogins(selectedDevices);
            },
            className: "buttons-export-login",
            titleAttr: "Export Login",
          },
          {
            text: '<i class="bi bi-file-text"></i>',
            action: function (e, dt) {
              const selectedDevice = dt
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
    },
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
});

function updateBtnState() {
  if (dataTable.rows({ selected: true }).any()) {
    document
      .querySelector("button.buttons-select-none")
      .classList.remove("disabled");
    document
      .querySelector("button.buttons-export-login")
      .classList.remove("disabled");
  } else {
    document
      .querySelector("button.buttons-select-none")
      .classList.add("disabled");
    document
      .querySelector("button.buttons-export-login")
      .classList.add("disabled");
  }
  if (dataTable.rows({ selected: true }).count() === 1) {
    document.querySelector("button.buttons-logs").classList.remove("disabled");
  } else {
    document.querySelector("button.buttons-logs").classList.add("disabled");
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

function downloadLogins(devices) {
  const deviceLogins = devices.map((dev) => {
    return [
      dev["name"],
      `https://${dev["uuid"]}-access.loadsync.io`,
      dev["uuid"],
    ];
  });
  deviceLogins.unshift([
    "Building",
    "Access Link",
    "Serial Number/Wifi SSID",
    "Login/Wifi Password",
  ]);

  const csvContent =
    "data:text/csv;charset=utf-8," +
    deviceLogins.map((e) => e.join(",")).join("\n");
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", "LoadsyncLogins-Export.csv");
  document.body.appendChild(link);

  link.click();
}
