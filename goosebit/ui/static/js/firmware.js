const CHUNK_SIZE = 10 * 1024 * 1024; // 10 MB chunk size
const uploadForm = document.getElementById("upload-form");
const uploadFileInput = document.getElementById("file-upload");
const uploadFileSubmit = document.getElementById("file-upload-submit");
const uploadProgressBar = document.getElementById("upload-progress");

let dataTable;

uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    await sendFileChunks(uploadFileInput.files[0]);
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
        if (i === 0) {
            formData.append("init", "true");
        } else {
            formData.append("init", "false");
        }

        if (i === totalChunks - 1) {
            formData.append("done", "true");
        } else {
            formData.append("done", "false");
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
                const result = await response.json();
                const alerts = document.getElementById("upload-alerts");
                alerts.innerHTML = `<div class="alert alert-warning alert-dismissible fade show" role="alert">
                    ${result.detail}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>`;
            }
        }

        start = end;
    }

    window.setTimeout(() => {
        resetProgress();
    }, 1000);
}

const urlForm = document.getElementById("url-form");
const urlFileInput = document.getElementById("file-url");
const urlFileSubmit = document.getElementById("url-submit");

urlForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    await sendFileUrl(urlFileInput.value);
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
            const result = await response.json();
            const alerts = document.getElementById("url-alerts");
            alerts.innerHTML = `<div class="alert alert-warning alert-dismissible fade show" role="alert">
                ${result.detail}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>`;
        }
    }
}

function updateFirmwareList() {
    dataTable.ajax.reload(null, false);
}

function resetProgress() {
    uploadFileInput.disabled = false;
    uploadFileSubmit.disabled = false;
    uploadFileSubmit.classList.remove("d-none");
    urlFileInput.disabled = false;
    urlFileSubmit.disabled = false;
    uploadProgressBar.style.width = "0%";
    uploadProgressBar.innerHTML = "0%";
    uploadProgressBar.parentElement.classList.add("d-none");

    updateFirmwareList();
}

document.addEventListener("DOMContentLoaded", () => {
    const buttons = [
        {
            text: '<i class="bi bi-cloud-download" ></i>',
            action: (e, dt) => {
                const selectedFirmware = dt
                    .rows({ selected: true })
                    .data()
                    .toArray()
                    .map((d) => d.id);
                downloadFirmware(selectedFirmware[0]);
            },
            className: "buttons-download",
            titleAttr: "Download Firmware",
        },
        {
            text: '<i class="bi bi-trash" ></i>',
            action: async (e, dt) => {
                const selectedFirmware = dt
                    .rows({ selected: true })
                    .data()
                    .toArray()
                    .map((d) => d.id);
                await deleteFirmware(selectedFirmware);
            },
            className: "buttons-delete",
            titleAttr: "Delete Firmware",
        },
    ];

    // add create button at the beginning if upload modal exists
    if ($("#upload-modal").length > 0) {
        buttons.unshift({
            text: '<i class="bi bi-plus" ></i>',
            action: () => {
                new bootstrap.Modal("#upload-modal").show();
            },
            className: "buttons-create",
            titleAttr: "Add Firmware",
        });
    }

    dataTable = new DataTable("#firmware-table", {
        responsive: true,
        paging: true,
        processing: false,
        serverSide: true,
        order: [2, "desc"],
        scrollCollapse: true,
        scroller: true,
        scrollY: "60vh",
        stateSave: true,
        stateLoadParams: (settings, data) => {
            // if save state is older than last breaking code change...
            if (data.time <= 1722415428000) {
                // ... delete it
                for (const key of Object.keys(data)) {
                    delete data[key];
                }
            }
        },
        ajax: {
            url: "/api/firmware/all",
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
            { data: "id", visible: false },
            { data: "name", searchable: true },
            { data: "version", searchable: true, orderable: true },
            {
                data: "size",
                render: (data, type) => {
                    if (type === "display" || type === "filter") {
                        return `${(data / 1024 / 1024).toFixed(2)}MB`;
                    }
                    return data;
                },
            },
        ],
        select: true,
        rowId: "id",
        layout: {
            bottom1Start: {
                buttons,
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

    // Compatibility tooltip
    $(() => {
        $('[data-toggle="tooltip"]').tooltip();
    });

    $("#firmware-table tbody")
        .on("mouseenter", "tr", function () {
            const rowData = dataTable.row(this).data();
            const compat = rowData.compatibility;
            let tooltipText = "";
            if (compat) {
                const result = compat.reduce((acc, { model, revision }) => {
                    if (!acc[model]) {
                        acc[model] = [];
                    }
                    acc[model].push(revision);
                    return acc;
                }, {});

                tooltipText = Object.entries(result)
                    .map(([model, revision]) => `<b>${model}</b> [${revision.join(", ")}]`)
                    .join(", ");
            }

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
        })
        .on("mouseleave", "tr", function () {
            $(this).tooltip("dispose");
        });

    updateFirmwareList();
});

function updateBtnState() {
    if (dataTable.rows({ selected: true }).any()) {
        document.querySelector("button.buttons-delete").classList.remove("disabled");
    } else {
        document.querySelector("button.buttons-delete").classList.add("disabled");
    }
    if (dataTable.rows({ selected: true }).count() === 1) {
        document.querySelector("button.buttons-download").classList.remove("disabled");
    } else {
        document.querySelector("button.buttons-download").classList.add("disabled");
    }
}

async function deleteFirmware(files) {
    try {
        await post("/api/firmware/delete", files);
        updateFirmwareList();
    } catch (error) {
        console.error("Deleting firmwares failed:", error);
    }
}

function downloadFirmware(file) {
    window.location.href = `/api/download/${file}`;
}
