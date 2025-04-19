async function updateDevices() {
    try {
        const data = JSON.parse(await eel.getDeviceList()());
        const tableBody = $("#devices tbody");
        data.forEach(function (device) {
            let row = $(`#devices tbody tr[data-ip="${device.ip}"]`);
            if (row.length === 0) {
                // Add new row
                tableBody.append(`<tr data-ip="${device.ip}"><td>${device.ip}</td><td>${device.mac}</td><td>${device.last_seen}</td></tr>`);
            } else {
                // Update existing row
                row.find("td:nth-child(2)").text(device.mac);
                row.find("td:nth-child(3)").text(device.last_seen);
            }
        });
    } catch (error) {
        console.error("Error updating devices:", error);
    }
}

updateDevices();
setInterval(updateDevices, 5000);

$(document).ready(function () {
    eel.start_scan();
});
