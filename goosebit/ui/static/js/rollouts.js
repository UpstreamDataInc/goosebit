let dataTable;

const renderFunctions = {
    paused: (data, type) => {
        if (type === "display") {
            const color = data ? "danger" : "muted";
            return `
            <div class="text-${color}">
                ●
            </div>
            `;
        }
        return data;
    },
    created_at: (data, type) => new Date(data).toLocaleString(),
};

document.addEventListener("DOMContentLoaded", async () => {
    const columnConfig = await get_request("/ui/bff/rollouts/columns");
    for (const col in columnConfig.columns) {
        const colDesc = columnConfig.columns[col];
        const colName = colDesc.data;
        if (renderFunctions[colName]) {
            columnConfig.columns[col].render = renderFunctions[colName];
        }
    }

    dataTable = new DataTable("#rollout-table", {
        responsive: true,
        paging: true,
        processing: true,
        serverSide: true,
        order: {
            name: "created_at",
            dir: "desc",
        },
        scrollCollapse: true,
        scroller: true,
        scrollY: "65vh",
        stateSave: true,
        select: true,
        rowId: "id",
        ajax: {
            url: "/ui/bff/rollouts",
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
                if (document.getElementById("selected-sw").value === "") {
                    document.getElementById("selected-sw").parentElement.classList.add("is-invalid");
                }
                event.preventDefault();
                event.stopPropagation();
                form.classList.add("was-validated");
            } else {
                event.preventDefault();
                createRollout();
                form.classList.remove("was-validated");
                document.getElementById("selected-sw").parentElement.classList.remove("is-invalid");
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
    const scrollPosition = $("#rollout-table").parent().scrollTop(); // Get current scroll position

    dataTable.ajax.reload(() => {
        $("#rollout-table").parent().scrollTop(scrollPosition); // Restore scroll position after reload
    }, false);
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
