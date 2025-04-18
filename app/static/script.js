function updateDevices() {
    $.get("/devices", function (data) {
        const tableBody = $("#devices tbody"); // Select table with id 'devices'
        tableBody.empty();
        tableBody.append(`<tr><th>IP Address</th><th>MAC Address</th><th>Last Checked</th></tr>`);
        data.devices.forEach(function (device) {
            tableBody.append(`<tr><td>${device.ip}</td><td>${device.mac}</td><td>${device.last_seen}</td></tr>`);
        });
    });
}
updateDevices();
setInterval(updateDevices, 5000);
