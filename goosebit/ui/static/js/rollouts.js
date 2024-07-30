let dataTable;

document.addEventListener("DOMContentLoaded", async () => {
    dataTable = new DataTable("#rollout-table", {
        responsive: true,
        paging: true,
        processing: true,
        serverSide: true,
        aaSorting: [],
        scrollCollapse: true,
        scroller: true,
        scrollY: "65vh",
        stateSave: true,
        select: true,
        rowId: "id",
        ajax: {
            url: "/api/rollouts/all",
            contentType: "application/json",
        },
        initComplete: () => {
            updateBtnState();
        },
        columnDefs: [
            {
                targets: [1, 2, 3, 4],
                searchable: true,
                orderable: true,
            },
            {
                targets: "_all",
                searchable: false,
                orderable: false,
            },
        ],
        columns: [
            { data: "id" },
            { data: "created_at" },
            { data: "name" },
            { data: "feed" },
            { data: "flavor" },
            { data: "fw_file" },
            {
                data: "paused",
                render: (data, type) => {
                    if (type === "display" || type === "filter") {
                        const color = data ? "success" : "light";
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
                        action: () => {
                            new bootstrap.Modal("#rollout-create-modal").show();
                        },
                        className: "buttons-create",
                        titleAttr: "Create Rollout",
                    },
                    {
                        text: '<i class="bi bi-play-fill" ></i>',
                        action: (e, dt) => {
                            const selectedRollouts = dt
                                .rows({ selected: true })
                                .data()
                                .toArray()
                                .map((d) => d.id);
                            pauseRollouts(selectedRollouts, false);
                        },
                        className: "buttons-resume",
                        titleAttr: "Resume Rollouts",
                    },
                    {
                        text: '<i class="bi bi-pause-fill" ></i>',
                        action: (e, dt) => {
                            const selectedRollouts = dt
                                .rows({ selected: true })
                                .data()
                                .toArray()
                                .map((d) => d.id);
                            pauseRollouts(selectedRollouts, true);
                        },
                        className: "buttons-pause",
                        titleAttr: "Pause Rollouts",
                    },
                    {
                        text: '<i class="bi bi-trash" ></i>',
                        action: (e, dt) => {
                            const selectedRollouts = dt
                                .rows({ selected: true })
                                .data()
                                .toArray()
                                .map((d) => d.id);
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
        .on("select", () => {
            updateBtnState();
        })
        .on("deselect", () => {
            updateBtnState();
        });

    updateRolloutList();

    await updateFirmwareSelection();
});

function updateBtnState() {
    if (dataTable.rows({ selected: true }).any()) {
        document.querySelector("button.buttons-delete").classList.remove("disabled");
    } else {
        document.querySelector("button.buttons-delete").classList.add("disabled");
    }

    if (dataTable.rows((_, data) => data.paused, { selected: true }).any()) {
        document.querySelector("button.buttons-resume").classList.remove("disabled");
    } else {
        document.querySelector("button.buttons-resume").classList.add("disabled");
    }

    if (dataTable.rows((_, data) => !data.paused, { selected: true }).any()) {
        document.querySelector("button.buttons-pause").classList.remove("disabled");
    } else {
        document.querySelector("button.buttons-pause").classList.add("disabled");
    }
}

async function createRollout() {
    const name = document.getElementById("rollout-selected-name").value;
    const feed = document.getElementById("rollout-selected-feed").value;
    const flavor = document.getElementById("rollout-selected-flavor").value;
    const firmware_id = document.getElementById("selected-fw").value;

    try {
        await post("/api/rollouts", { name, feed, flavor, firmware_id });
    } catch (error) {
        console.error("Rollout creation failed:", error);
    }

    setTimeout(updateRolloutList, 50);
}

function updateRolloutList() {
    dataTable.ajax.reload();
}

async function deleteRollouts(ids) {
    try {
        await post("/api/rollouts/delete", { ids });
    } catch (error) {
        console.error("Rollouts deletion failed:", error);
    }

    updateBtnState();
    setTimeout(updateRolloutList, 50);
}

async function pauseRollouts(ids, paused) {
    try {
        await post("/api/rollouts/update", { ids, paused });
    } catch (error) {
        console.error(`Rollouts ${paused ? "pausing" : "unpausing"} failed:`, error);
    }

    setTimeout(updateRolloutList, 50);
}
