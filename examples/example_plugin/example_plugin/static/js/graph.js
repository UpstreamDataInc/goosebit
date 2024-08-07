document.addEventListener("DOMContentLoaded", async () => {
    response = await get("/api/example_plugin/graph");
    data = await response.json();
    const options = {
        series: data.series,
        labels: data.labels,
        chart: {
            type: "donut",
            height: "100%",
        },
        title: { text: "Hardware", style: { color: "#FFFFFF" } },

        legend: {
            labels: {
                colors: "#FFFFFF",
            },
        },
    };

    const chart = new ApexCharts(document.querySelector("#hardware-pie"), options);
    chart.render();
});
