google.charts.load('current', {'packages':['corechart']});
google.charts.setOnLoadCallback(retrieveNetworkDataAndUpdate);

var animationTime = 50;
var network_speed_result;
var network_speed_chart_options = {
    title: 'Bandwidth (KB/s)',
    animation:{
        duration: animationTime,
        easing: 'inAndOut',
        startup: true,
    },
    explorer: {
        actions: ['dragToPan', 'rightClickToReset'],
    },
    legend: { position: 'none' },
    vAxis: {minValue: 0},
    fontName: '-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Oxygen-Sans,Ubuntu,Cantarell,"Helvetica Neue",sans-serif',
    interpolateNulls: true,
};
var network_speed_chart;

var network_usage_result;
var network_usage_chart_options = {
    title: 'Total Network Usage',
    focusTarget: 'category',
    tooltip: { isHtml: true }
};
var network_usage_chart;


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



function retrieveNetworkDataAndUpdate() {
    $.get('system-status/network', function(data) {
        if (!network_speed_result) {
            network_speed_result = new google.visualization.DataTable();
            network_speed_result.addColumn('date', 'Time');
            network_speed_result.addColumn('number', 'Download');
            network_speed_result.addColumn('number', 'Upload');

            network_speed_chart = new google.visualization.LineChart(document.getElementById('network-speed-chart'));
        }
        while (network_speed_result.getNumberOfRows() > 30)
        {
            network_speed_result.removeRow(0);
        }
        network_speed_result.addRow([new Date(), data['download-speed'], data['upload-speed']]);
        network_speed_chart.draw(network_speed_result, network_speed_chart_options);
        $("#network-usage-download-value-display").text('Download Speed : '+data['download-speed-natural']);
        $("#network-usage-upload-value-display").text('Upload Speed : '+data['upload-speed-natural']);

        if (!network_usage_result) {
            network_usage_result = new google.visualization.DataTable();
            network_usage_result.addColumn("string", "Type");
            network_usage_result.addColumn("number", "Size");
            network_usage_result.addColumn({type: 'string', role: 'tooltip', 'p': {'html': true}});
            network_usage_chart = new google.visualization.PieChart(document.getElementById('network-usage-chart'));
        } else {
            while (network_usage_result.getNumberOfRows() > 0) network_usage_result.removeRow(0);
        }
        network_usage_result.addRow(['Download', data['total-downloads'], generateNetworkUsageTooltip('Download', data['total-downloads'])]);
        network_usage_result.addRow(['Upload', data['total-uploads'], generateNetworkUsageTooltip('Upload', data['total-uploads'])]);

        network_usage_chart.draw(network_usage_result, network_usage_chart_options);

        setTimeout(retrieveNetworkDataAndUpdate, 1000);
    });
}