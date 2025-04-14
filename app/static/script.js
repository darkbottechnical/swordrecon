function updateDevices() {
    $.get("/devices", function (data) {
        const tableBody = $("table tbody");
        tableBody.empty();
        tableBody.append(`<tr><th>IP Address</th><th>MAC Address</th></tr>`);
        data.devices.forEach(function (device) {
            tableBody.append(`<tr><td>${device.ip}</td><td>${device.mac}</td></tr>`);
        });
    });
}
setInterval(updateDevices, 5000);
