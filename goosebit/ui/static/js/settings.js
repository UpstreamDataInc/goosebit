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
});

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
