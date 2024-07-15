document.addEventListener("DOMContentLoaded", function() {
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
        initComplete:function(){
        },
        columnDefs: [],
        columns: [
            { data: 'id' },
            { data: 'created_at' },
            { data: 'name' },
            { data: 'hw_model' },
            { data: 'hw_revision' },
            { data: 'feed' },
            { data: 'flavor' },
            { data: 'fw_file' },
            { data: 'paused',
              render: function(data, type) {
                    if ( type === 'display' || type === 'filter' ) {
                        color = data ? "success" : "light"
                        return `
                        <div class="text-${color}">
                            ●
                        </div>
                        `
                    }
                    return data;
                }
            },
            { data: 'success_count' },
            { data: 'failure_count' },
        ],
        layout: {
            top1Start: {
                buttons: [
                ]
            },
            bottom1Start: {
                buttons: [
                ]
            }
        },
    });

    dataTable.ajax.reload();
});
