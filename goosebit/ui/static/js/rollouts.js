let dataTable;

document.addEventListener("DOMContentLoaded", async () => {
    dataTable = new DataTable("#rollout-table", {
        responsive: true,
        paging: true,
        processing: true,
        serverSide: true,
        order: [1, "desc"],
        scrollCollapse: true,
        scroller: true,
        scrollY: "65vh",
        stateSave: true,
        stateLoadParams: (settings, data) => {
            // if save state is older than last breaking code change...
            if (data.time <= 1722413708000) {
                // ... delete it
                for (const key of Object.keys(data)) {
                    delete data[key];
                }
            }
        },
        select: true,
        rowId: "id",
        ajax: {
            url: "/ui/bff/rollouts",
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
            },
        ],
        columns: [
            { data: "id", visible: false },
            { data: "created_at", orderable: true, render: (data) => new Date(data).toLocaleString() },
            { data: "name", searchable: true, orderable: true },
            { data: "feed", searchable: true, orderable: true },
            { data: "sw_file" },
            { data: "sw_version" },
            {
                data: "paused",
                render: (data, type) => {
                    if (type === "display" || type === "filter") {
                        const color = data ? "danger" : "muted";
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
                        titleAttr: "Add Rollout",
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

    await updateSoftwareSelection();

    // Creation form submit
    const form = document.getElementById("rollout-form");
    form.addEventListener(
        "submit",
        (event) => {
            if (form.checkValidity() === false) {
                event.preventDefault();
                event.stopPropagation();
                form.classList.add("was-validated");
            } else {
                event.preventDefault();
                createRollout();
                form.classList.remove("was-validated");
                form.reset();
                const modal = bootstrap.Modal.getInstance(document.getElementById("rollout-create-modal"));
                modal.hide();
            }
        },
        false,
    );
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
    const software_id = document.getElementById("selected-sw").value;

    try {
        await post_request("/ui/bff/rollouts", { name, feed, software_id });
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
        await delete_request("/ui/bff/rollouts", { ids });
    } catch (error) {
        console.error("Rollouts deletion failed:", error);
    }

    updateBtnState();
    setTimeout(updateRolloutList, 50);
}

async function pauseRollouts(ids, paused) {
    try {
        await patch_request("/ui/bff/rollouts", { ids, paused });
    } catch (error) {
        console.error(`Rollouts ${paused ? "pausing" : "unpausing"} failed:`, error);
    }

    setTimeout(updateRolloutList, 50);
}
