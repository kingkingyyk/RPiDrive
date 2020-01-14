google.charts.load("current", {"packages":["corechart"]});
google.charts.setOnLoadCallback(retrieveRealtimeUpdate);

var animationTime = 50;
var networkSpeedResult;
var networkSpeedChartOpt = {
    title: "Bandwidth (KB/s)",
    animation:{
        duration: animationTime,
        easing: "inAndOut",
        startup: true,
    },
    explorer: {
        actions: ["dragToPan", "rightClickToReset"],
    },
    legend: { position: "none" },
    vAxis: {minValue: 0},
    fontName: "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Oxygen-Sans,Ubuntu,Cantarell,'Helvetica Neue',sans-serif",
    interpolateNulls: true,
};
var networkSpeedChart;

var networkUsageResult;
var networkUsageChartOpt = {
    title: "Total Network Usage",
    focusTarget: "category",
    tooltip: { isHtml: true }
};
var networkUsageChart;


function generateNetworkUsageTooltip(category, value) {
    var unit = ["MB", "GB", "TB", "PB"];
    index = 0;
    while (value > 1024) {
        value /= 1024;
        index++;
    }
    value = Math.round(value*10)/10;
    return "<div style='padding: 10px'><p>"+category+"</p><p><b>"+value+" "+unit[index]+"</b></p></div>";
}

function updateNetworkData(data) {
    if (!networkSpeedResult) {
        networkSpeedResult = new google.visualization.DataTable();
        networkSpeedResult.addColumn("date", "Time");
        networkSpeedResult.addColumn("number", "Download");
        networkSpeedResult.addColumn("number", "Upload");

        networkSpeedChart = new google.visualization.LineChart(document.getElementById("network-speed-chart"));
    }
    while (networkSpeedResult.getNumberOfRows() > 30)
    {
        networkSpeedResult.removeRow(0);
    }
    networkSpeedResult.addRow([new Date(), data["download-speed"], data["upload-speed"]]);
    networkSpeedChart.draw(networkSpeedResult, networkSpeedChartOpt);
    $("#network-usage-download-value-display").text("Download Speed : "+data["download-speed-natural"]);
    $("#network-usage-upload-value-display").text("Upload Speed : "+data["upload-speed-natural"]);

    if (!networkUsageResult) {
        networkUsageResult = new google.visualization.DataTable();
        networkUsageResult.addColumn("string", "Type");
        networkUsageResult.addColumn("number", "Size");
        networkUsageResult.addColumn({type: "string", role: "tooltip", "p": {"html": true}});
        networkUsageChart = new google.visualization.PieChart(document.getElementById("network-usage-chart"));
    } else {
        while (networkUsageResult.getNumberOfRows() > 0) networkUsageResult.removeRow(0);
    }
    networkUsageResult.addRow(["Download", data["total-downloads"], generateNetworkUsageTooltip("Download", data["total-downloads"])]);
    networkUsageResult.addRow(["Upload", data["total-uploads"], generateNetworkUsageTooltip("Upload", data["total-uploads"])]);

    networkUsageChart.draw(networkUsageResult, networkUsageChartOpt);

}

function updateSystemData(data) {
    for (var category in data) {
        if (data.hasOwnProperty(category)) {
            data[category].forEach(function(item){
                tdKey = "#status-"+item[0];
                tdValue = item[2];
                $(tdKey).html(tdValue);
            });
        }
    }
}

function retrieveRealtimeUpdate() {
    $.get("system-status/update", function(data) {
        updateNetworkData(data["network_data"]);
        updateSystemData(data["system_data"]);
        setTimeout(retrieveRealtimeUpdate, 1000);
    });
}