const CHUNK_SIZE = 10 * 1024 * 1024; // 10 MB chunk size
const uploadForm = document.getElementById("upload-form");
const uploadFileInput = document.getElementById("file-upload");
const uploadFileSubmit = document.getElementById("file-upload-submit");
const uploadProgressBar = document.getElementById("upload-progress");

uploadForm.addEventListener("submit", (e) => {
  e.preventDefault();
  sendFileChunks(uploadFileInput.files[0]);
});

async function sendFileChunks(file) {
  const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
  let start = 0;
  let uploadedChunks = 0;

  uploadFileSubmit.disabled = true;
  uploadFileSubmit.classList.add("d-none");
  uploadFileInput.disabled = true;
  uploadProgressBar.parentElement.classList.remove("d-none");

  for (let i = 0; i < totalChunks; i++) {
    const end = Math.min(start + CHUNK_SIZE, file.size);
    const chunk = file.slice(start, end);
    const formData = new FormData();
    formData.append("chunk", chunk);
    formData.append("filename", file.name);
    if (i == 0) {
      formData.append("init", true);
    } else {
      formData.append("init", false);
    }

    if (i == totalChunks - 1) {
      formData.append("done", true);
    } else {
      formData.append("done", false);
    }

    const response = await fetch("/ui/upload/local", {
      method: "POST",
      body: formData,
    });

    if (response.ok) {
      uploadedChunks++;
      const progress = (uploadedChunks / totalChunks) * 100;
      uploadProgressBar.style.width = `${progress}%`;
      uploadProgressBar.innerHTML = `${Math.round(progress)}%`;
    } else {
      if (response.status === 400) {
        result = await response.json();
        alerts = document.getElementById("upload-alerts");
        alerts.innerHTML = `<div class="alert alert-warning alert-dismissible fade show" role="alert">
                    ${result["detail"]}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>`;
      }
    }

    start = end;
  }

  window.setTimeout(function () {
    resetProgress();
  }, 1000);
}

const urlForm = document.getElementById("url-form");
const urlFileInput = document.getElementById("file-url");
const urlFileSubmit = document.getElementById("url-submit");

urlForm.addEventListener("submit", (e) => {
  e.preventDefault();
  sendFileUrl(urlFileInput.value);
});

async function sendFileUrl(url) {
  const formData = new FormData();
  formData.append("url", url);

  const response = await fetch("/ui/upload/remote", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    if (response.status === 400) {
      result = await response.json();
      alerts = document.getElementById("url-alerts");
      alerts.innerHTML = `<div class="alert alert-warning alert-dismissible fade show" role="alert">
                ${result["detail"]}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>`;
    }
  }
}

function resetProgress() {
  uploadFileInput.disabled = false;
  uploadFileSubmit.disabled = false;
  uploadFileSubmit.classList.remove("d-none");
  urlFileInput.disabled = false;
  urlFileSubmit.disabled = false;
  uploadProgressBar.style.width = `0%`;
  uploadProgressBar.innerHTML = `0%`;
  uploadProgressBar.parentElement.classList.add("d-none");

  dataTable = $("#firmware-table").DataTable();
  dataTable.ajax.reload(null, false);
}

document.addEventListener("DOMContentLoaded", function () {
  var dataTable = new DataTable("#firmware-table", {
    responsive: true,
    paging: false,
    scrollCollapse: true,
    scroller: true,
    scrollY: "60vh",
    stateSave: true,
    ajax: {
      url: "/api/firmware/all",
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
      { data: "id" },
      { data: "version" },
      {
        data: "size",
        render: function (data, type, row) {
          if (type === "display" || type === "filter") {
            return (data / 1024 / 1024).toFixed(2) + "MB";
          }
          return data;
        },
      },
    ],
    select: true,
    rowId: "id",
    layout: {
      bottom1Start: {
        buttons: [
          {
            text: '<i class="bi bi-cloud-download" ></i>',
            action: function (e, dt, node, config) {
              selectedFirmware = dt
                .rows({ selected: true })
                .data()
                .toArray()
                .map((d) => d["id"]);
              downloadFirmware(selectedFirmware[0]);
            },
            className: "buttons-download",
            titleAttr: "Download Firmware",
          },
          {
            text: '<i class="bi bi-trash" ></i>',
            action: function (e, dt, node, config) {
              selectedFirmware = dt
                .rows({ selected: true })
                .data()
                .toArray()
                .map((d) => d["id"]);
              deleteFirmware(selectedFirmware);
            },
            className: "buttons-delete",
            titleAttr: "Delete Firmware",
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

  // Compatibility tooltip
  $(function () {
    $('[data-toggle="tooltip"]').tooltip();
  });

  $("#firmware-table tbody").on("mouseenter", "tr", function () {
    var rowData = dataTable.row(this).data();
    var compat = rowData["compatibility"];
    var list =
      compat && compat.map((c) => `<b>${c.model}-${c.revision}</b>`).join(", ");
    var tooltipText = `Compatibility: ${list}`;

    // Initialize Bootstrap tooltip
    $(this)
      .attr("title", tooltipText)
      .tooltip({
        placement: "top",
        trigger: "hover",
        container: "body",
        html: true,
      })
      .tooltip("show");
  });

  $("#firmware-table tbody").on("mouseleave", "tr", function () {
    $(this).tooltip("dispose");
  });

  setInterval(function () {
    dataTable.ajax.reload(null, false);
  }, TABLE_UPDATE_TIME);
});

function updateBtnState() {
  dataTable = $("#firmware-table").DataTable();
  if (dataTable.rows({ selected: true }).any()) {
    document
      .querySelector("button.buttons-delete")
      .classList.remove("disabled");
  } else {
    document.querySelector("button.buttons-delete").classList.add("disabled");
  }
  if (dataTable.rows({ selected: true }).count() == 1) {
    document
      .querySelector("button.buttons-download")
      .classList.remove("disabled");
  } else {
    document.querySelector("button.buttons-download").classList.add("disabled");
  }
}

function deleteFirmware(files) {
  fetch("/api/firmware/delete", {
    method: "POST",
    body: files,
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to delete firmware.");
      }
      updateFirmwareList();
      return response.json();
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}

function downloadFirmware(file) {
  window.location.href = `/api/download/${file}`;
}
