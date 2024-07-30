document.addEventListener("DOMContentLoaded", function () {
  var dataTable = new DataTable("#rollout-table", {
    responsive: true,
    paging: false,
    scrollCollapse: true,
    scroller: true,
    scrollY: "65vh",
    stateSave: true,
    select: true,
    rowId: "id",
    ajax: {
      url: "/api/rollouts/all",
      dataSrc: "",
    },
    initComplete: function () {
      updateBtnState();
    },
    columnDefs: [],
    columns: [
      { data: "id" },
      { data: "created_at" },
      { data: "name" },
      { data: "feed" },
      { data: "flavor" },
      { data: "fw_file" },
      {
        data: "paused",
        render: function (data, type) {
          if (type === "display" || type === "filter") {
            color = data ? "success" : "light";
            return `
                        <div class="text-${color}">
                            ●
                        </div>
                        `;
          }
          return data;
        },
      },
      { data: "success_count" },
      { data: "failure_count" },
    ],
    layout: {
      top1Start: {
        buttons: [],
      },
      bottom1Start: {
        buttons: [
          {
            text: '<i class="bi bi-plus" ></i>',
            action: function (e, dt, node, config) {
              new bootstrap.Modal("#rollout-create-modal").show();
            },
            className: "buttons-create",
            titleAttr: "Create Rollout",
          },
          {
            text: '<i class="bi bi-play-fill" ></i>',
            action: function (e, dt, node, config) {
              selectedRollouts = dt
                .rows({ selected: true })
                .data()
                .toArray()
                .map((d) => d["id"]);
              pauseRollouts(selectedRollouts, false);
            },
            className: "buttons-resume",
            titleAttr: "Resume Rollouts",
          },
          {
            text: '<i class="bi bi-pause-fill" ></i>',
            action: function (e, dt, node, config) {
              selectedRollouts = dt
                .rows({ selected: true })
                .data()
                .toArray()
                .map((d) => d["id"]);
              pauseRollouts(selectedRollouts, true);
            },
            className: "buttons-pause",
            titleAttr: "Pause Rollouts",
          },
          {
            text: '<i class="bi bi-trash" ></i>',
            action: function (e, dt, node, config) {
              selectedRollouts = dt
                .rows({ selected: true })
                .data()
                .toArray()
                .map((d) => d["id"]);
              deleteRollouts(selectedRollouts);
            },
            className: "buttons-delete",
            titleAttr: "Delete Rollouts",
          },
        ],
      },
    },
  });

  dataTable
    .on("select", function (e, dt, type, indexes) {
      updateBtnState();
    })
    .on("deselect", function (e, dt, type, indexes) {
      updateBtnState();
    });

  updateRolloutList();

  updateFirmwareSelection();
});

function updateBtnState() {
  dataTable = $("#rollout-table").DataTable();

  if (dataTable.rows({ selected: true }).any()) {
    document
      .querySelector("button.buttons-delete")
      .classList.remove("disabled");
  } else {
    document.querySelector("button.buttons-delete").classList.add("disabled");
  }

  if (dataTable.rows((_, data) => data.paused, { selected: true }).any()) {
    document
      .querySelector("button.buttons-resume")
      .classList.remove("disabled");
  } else {
    document.querySelector("button.buttons-resume").classList.add("disabled");
  }

  if (dataTable.rows((_, data) => !data.paused, { selected: true }).any()) {
    document.querySelector("button.buttons-pause").classList.remove("disabled");
  } else {
    document.querySelector("button.buttons-pause").classList.add("disabled");
  }
}

function createRollout() {
  name = document.getElementById("rollout-selected-name").value;
  feed = document.getElementById("rollout-selected-feed").value;
  flavor = document.getElementById("rollout-selected-flavor").value;
  selectedFirmware = document.getElementById("selected-fw").value;

  fetch("/api/rollouts", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: name,
      feed: feed,
      flavor: flavor,
      firmware_id: selectedFirmware,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to create rollout.");
      }
      return response.json();
    })
    .catch((error) => {
      console.error("Error:", error);
    });

  setTimeout(updateRolloutList, 50);
}

function updateRolloutList() {
  dataTable = $("#rollout-table").DataTable();
  dataTable.ajax.reload();
}

function deleteRollouts(rollouts) {
  fetch("/api/rollouts/delete", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      ids: rollouts,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to delete rollouts.");
      }
      return response.json();
    })
    .catch((error) => {
      console.error("Error:", error);
    });

  updateBtnState();
  setTimeout(updateRolloutList, 50);
}

function pauseRollouts(rollouts, state) {
  fetch("/api/rollouts/update", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      ids: rollouts,
      paused: state,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to update rollouts.");
      }
      return response.json();
    })
    .catch((error) => {
      console.error("Error:", error);
    });

  setTimeout(updateRolloutList, 50);
}
