let dataTable;

const renderFunctions = {
    enabled: (data, type) => {
        if (type === "display") {
            const color = data ? "success" : "muted";
            return `
            <div class="text-${color}">
                ●
            </div>
            `;
        }
        return data;
    },
    permissions: (data, type) => {
        return data.join(",");
    },
};

document.addEventListener("DOMContentLoaded", async () => {
    const columnConfig = await get_request("/ui/bff/settings/users/columns");
    for (const col in columnConfig.columns) {
        const colDesc = columnConfig.columns[col];
        const colName = colDesc.data;
        if (renderFunctions[colName]) {
            columnConfig.columns[col].render = renderFunctions[colName];
        }
    }

    dataTable = new DataTable("#users-table", {
        responsive: true,
        paging: true,
        processing: false,
        serverSide: true,
        order: { name: "username", dir: "asc" },
        scrollCollapse: true,
        scroller: true,
        scrollY: "65vh",
        stateSave: true,
        select: true,
        rowId: "username",
        ajax: {
            url: "/ui/bff/settings/users",
            data: (data) => {
                // biome-ignore lint/performance/noDelete: really has to be deleted
                delete data.columns;
            },
            contentType: "application/json",
        },
        initComplete: () => {
            updateBtnState();
        },
        layout: {
            top1Start: {
                buttons: [],
            },
            bottom1Start: {
                buttons: [
                    {
                        text: '<i class="bi bi-plus" ></i>',
                        action: async () => {
                            const permissionsSelection = document.getElementById("create-user-permissions");
                            permissionsSelection.innerHTML = await createPermissions();
                            new bootstrap.Modal("#create-user-modal").show();
                        },
                        className: "buttons-create-user",
                        titleAttr: "Add User",
                    },
                    {
                        text: '<i class="bi bi-play-fill" ></i>',
                        action: (e, dt) => {
                            const selectedUsers = dt
                                .rows({ selected: true })
                                .data()
                                .toArray()
                                .map((d) => d.username);
                            enableUsers(selectedUsers, true);
                        },
                        className: "buttons-enable-users",
                        titleAttr: "Enable Users",
                    },
                    {
                        text: '<i class="bi bi-pause-fill" ></i>',
                        action: (e, dt) => {
                            const selectedUsers = dt
                                .rows({ selected: true })
                                .data()
                                .toArray()
                                .map((d) => d.username);
                            enableUsers(selectedUsers, false);
                        },
                        className: "buttons-disable-users",
                        titleAttr: "Disable Users",
                    },
                    {
                        text: '<i class="bi bi-trash" ></i>',
                        action: async (e, dt) => {
                            const selectedUsers = dt
                                .rows({ selected: true })
                                .data()
                                .toArray()
                                .map((d) => d.username);
                            deleteUsers(selectedUsers);
                        },
                        className: "buttons-delete-users",
                        titleAttr: "Delete Users",
                    },
                ],
            },
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
    });

    dataTable
        .on("select", () => {
            updateBtnState();
        })
        .on("deselect", () => {
            updateBtnState();
        });

    setInterval(() => {
        updateUsersList();
    }, TABLE_UPDATE_TIME);
    const form = document.getElementById("create-user-form");
    form.addEventListener("submit", (event) => {
        const permissionsContainer = document.getElementById("create-user-permissions");
        const permissions = [
            ...permissionsContainer.querySelectorAll('input[type="checkbox"]:checked:not(:disabled)'),
        ].map((checkbox) => checkbox.value);
        const permissionsValidatorCheckbox = document.getElementById("create-user-permissions-validator");
        permissionsValidatorCheckbox.checked = permissions.length > 0;

        if (form.checkValidity() === false) {
            if (permissions.length === 0) {
                permissionsContainer.classList.add("is-invalid");
            }
            event.preventDefault();
            event.stopPropagation();
            form.classList.add("was-validated");
        } else {
            event.preventDefault();
            createUser();
            form.classList.remove("was-validated");
            permissionsContainer.classList.remove("is-invalid");
            form.reset();
            const modal = bootstrap.Modal.getInstance(document.getElementById("create-user-modal"));
            modal.hide();
        }
    });
});

function updateBtnState() {
    if (dataTable.rows({ selected: true }).any()) {
        document.querySelector("button.buttons-delete-users").classList.remove("disabled");
        document.querySelector("button.buttons-disable-users").classList.remove("disabled");
        document.querySelector("button.buttons-enable-users").classList.remove("disabled");
    } else {
        document.querySelector("button.buttons-delete-users").classList.add("disabled");
        document.querySelector("button.buttons-disable-users").classList.add("disabled");
        document.querySelector("button.buttons-enable-users").classList.add("disabled");
    }
    if (dataTable.rows({ selected: true }).count() === 1) {
    } else {
    }
}

function updateUsersList() {
    const scrollPosition = $("#users-table").parent().scrollTop(); // Get current scroll position

    const selectedRows = dataTable
        .rows({ selected: true })
        .data()
        .toArray()
        .map((d) => d.username);

    dataTable.ajax.reload(() => {
        dataTable.rows().every(function () {
            const rowData = this.data();
            if (selectedRows.includes(rowData.username)) {
                this.select();
            }
        });
        $("#users-table").parent().scrollTop(scrollPosition); // Restore scroll position after reload
    }, false);
}

async function createPermissions() {
    const permissions = await get_request("/ui/bff/settings/permissions");

    innerAccordion = document.createElement("div");
    innerAccordion.classList = "accordion-body p-0";

    for (innerPermission in permissions.sub_permissions) {
        dropdown = createPermissionDropdown(permissions.sub_permissions[innerPermission]);
        innerAccordion.innerHTML += dropdown;
    }

    return `<div class="input-group d-flex">
        <div class="input-group-text p-2 px-3">
            <input class="form-check-input mt-0 ignore-validation" type="checkbox" value="${permissions.value}"  id="${permissions.value}-checkbox" onchange="permissionCheckOnUpdate(this)">
        </div>
        <div class="d-flex flex-fill accordion rounded-start-0">
            <div class="accordion-item w-100 rounded-start-0">
                <div class="accordion-header w-100">
                    <button class="accordion-button collapsed py-2 rounded-start-0"
                        type="button"
                        data-bs-toggle="collapse"
                        data-bs-target="#${permissions.value}">
                        ${permissions.description}
                    </button>
                </div>
                <div id="${permissions.value}" class="accordion-collapse collapse">
                    ${innerAccordion.outerHTML}
                </div>
            </div>
        </div>
    </div>`;
}

function createPermissionDropdown(permission) {
    if (!permission.sub_permissions) {
        return `<div class="input-group d-flex border-top">
            <div class="input-group-text p-2 px-3 rounded-0 border-0">
                <input class="form-check-input mt-0 ignore-validation" type="checkbox" value="${permission.value}" data-permission-parent="${permission.parent}">
            </div>
            <div class="d-flex flex-fill my-auto py-2 p-3 border-start">
                ${permission.description}
            </div>
        </div>`;
    }

    subAccordion = document.createElement("div");
    subAccordion.classList = "accordion-body p-0";

    for (innerPermission in permission.sub_permissions) {
        dropdown = createPermissionDropdown(permission.sub_permissions[innerPermission]);
        subAccordion.innerHTML += dropdown;
    }
    permissionId = permission.value.replaceAll(".", "-");

    return `<div class="input-group d-flex border-top">
        <div class="input-group-text p-2 px-3 rounded-0 border-0 border-start">
            <input class="form-check-input mt-0" type="checkbox" value="${permission.value}" id="${permissionId}-checkbox" data-permission-parent="${permission.parent}" onchange="permissionCheckOnUpdate(this)">
        </div>
        <div class="d-flex flex-fill accordion accordion-flush border-start">
            <div class="accordion-item w-100 rounded-start-0">
                <div class="accordion-header w-100">
                    <button class="accordion-button py-2 collapsed rounded-start-0"
                        type="button"
                        data-bs-toggle="collapse"
                        data-bs-target="#${permissionId}">
                        ${permission.description}
                    </button>
                </div>
                <div id="${permissionId}" class="accordion-collapse collapse">
                    ${subAccordion.outerHTML}
                </div>
            </div>
        </div>
    </div>`;
}

function permissionCheckOnUpdate(checkbox) {
    const childPermissions = document.querySelectorAll(`input[data-permission-parent="${checkbox.value}"`);
    for (const permissionCheckbox of childPermissions) {
        permissionCheckbox.checked = checkbox.checked;
        permissionCheckbox.disabled = checkbox.checked;
        permissionCheckbox.dispatchEvent(new Event("change"));
    }
}

async function createUser() {
    const username = document.getElementById("create-user-username").value;
    const password = document.getElementById("create-user-password").value;

    const permissionsContainer = document.getElementById("create-user-permissions");
    const permissions = [...permissionsContainer.querySelectorAll('input[type="checkbox"]:checked:not(:disabled)')].map(
        (checkbox) => checkbox.value,
    );

    try {
        await post_request("/ui/bff/settings/users", {
            username: username,
            password: password,
            permissions: permissions,
        });
    } catch (error) {
        console.error("User creation failed:", error);
    }

    setTimeout(updateUsersList, 50);
}

async function deleteUsers(usernames) {
    try {
        await delete_request("/ui/bff/settings/users", { usernames });
    } catch (error) {
        console.error("Users deletion failed:", error);
    }

    updateBtnState();
    setTimeout(updateUsersList, 50);
}

async function enableUsers(usernames, enabled) {
    try {
        await patch_request("/ui/bff/settings/users", { usernames, enabled });
    } catch (error) {
        console.error(`Users ${enabled ? "enabling" : "disabling"} failed:`, error);
    }

    setTimeout(updateUsersList, 50);
}
