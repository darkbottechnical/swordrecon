function updateDevices() {
    $.get("/devices", function (data) {
        const tableBody = $("table tbody");
        tableBody.empty();
        data.devices.forEach(function (device) {
            tableBody.append(`<tr><td>${device.ip}</td><td>${device.mac}</td></tr>`);
        });
    });
}
setInterval(updateDevices, 5000);
