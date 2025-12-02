// combined_script.js
document.addEventListener('DOMContentLoaded', () => {
    // ##########################################
    // ### ATTENDANCE MARKING LOGIC
    // ##########################################
    const video = document.getElementById('video');
    const statusDiv = document.getElementById('status');
    const overlayCanvas = document.getElementById('overlayCanvas');
    const context = overlayCanvas.getContext('2d');
    const captureCanvas = document.createElement('canvas');

    // **UPDATED:** Point to the Express.js API gateway on port 3000
    const API_URL = 'http://127.0.0.1:3000/api';
    const endpoint = document.title.includes('IN') ? '/mark_in' : '/mark_out';
    
    let isProcessing = false;
    let initialStatusText = document.title.includes('IN') ? 'Ready to check IN.' : 'Ready to check OUT.';
    statusDiv.textContent = initialStatusText;

    // Start the webcam
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            video.srcObject = stream;
            video.play();
            video.onloadeddata = () => {
                overlayCanvas.width = video.videoWidth;
                overlayCanvas.height = video.videoHeight;
                setInterval(markAttendance, 1500);
            };
        })
        .catch(err => {
            console.error("Error accessing webcam: " + err);
            statusDiv.textContent = "Error: Could not access webcam. Please allow camera permissions.";
        });

    function markAttendance() {
        if (isProcessing || video.readyState !== video.HAVE_ENOUGH_DATA) return;
        isProcessing = true;
        
        captureCanvas.width = video.videoWidth;
        captureCanvas.height = video.videoHeight;
        captureCanvas.getContext('2d').drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);
        
        captureCanvas.toBlob(blob => {
            const formData = new FormData();
            formData.append('image', blob, 'capture.jpg');

            // **UPDATED:** Fetch from the Express.js API gateway
            fetch(`${API_URL}${endpoint}`, { method: 'POST', body: formData })
                .then(response => response.json())
                .then(data => {
                    context.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
                    
                    if (data.box_coords) {
                        const [x1, y1, x2, y2] = data.box_coords;
                        context.strokeStyle = data.box_color;
                        context.lineWidth = 3;
                        context.strokeRect(x1, y1, x2 - x1, y2 - y1);
                        
                        context.fillStyle = data.box_color;
                        context.font = '18px Arial';
                        const displayText = `${data.name} (${data.reg_no})`;
                        context.fillText(displayText, x1, y1 > 20 ? y1 - 10 : 20);
                    }

                    statusDiv.textContent = data.message;
                    setTimeout(() => {
                        statusDiv.textContent = initialStatusText;
                        context.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
                    }, 3000);
                })
                .catch(error => {
                    console.error('Fetch problem:', error);
                    statusDiv.textContent = `Error: Could not connect to server.`;
                })
                .finally(() => {
                    setTimeout(() => { isProcessing = false; }, 500);
                });
        }, 'image/jpeg');
    }

    // ##########################################
    // ### HISTORY SEARCH LOGIC
    // ##########################################
    const searchBtn = document.getElementById('searchBtn');
    const regNoInput = document.getElementById('regNoInput');
    const resultsContainer = document.getElementById('resultsContainer');

    searchBtn.addEventListener('click', fetchHistory);
    regNoInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') fetchHistory();
    });

    function fetchHistory() {
        const regNo = regNoInput.value.trim();
        if (!regNo) {
            alert('Please enter a registration number.');
            return;
        }
        resultsContainer.innerHTML = '<p>Loading...</p>';

        // **UPDATED:** Fetch history from the Express.js API gateway
        fetch(`${API_URL}/get_history/${regNo}`)
            .then(response => response.json())
            .then(data => {
                displayResults(data);
            })
            .catch(error => {
                console.error('Error fetching history:', error);
                resultsContainer.innerHTML = '<p style="color: red;">Error fetching data.</p>';
            });
    }

    function displayResults(data) {
        if (!data || data.length === 0) {
            resultsContainer.innerHTML = '<p>No records found for this registration number.</p>';
            return;
        }
        const studentName = data[0].name;
        let tableHTML = `<h3>History for ${studentName} (${data[0].reg_no})</h3>
            <table class="history-table">
                <thead><tr><th>Date</th><th>Time</th><th>Status</th><th>Mode</th></tr></thead>
                <tbody>`;
        data.forEach(record => {
            tableHTML += `<tr>
                <td>${record.date}</td>
                <td>${record.time}</td>
                <td class="status-${record.type.toLowerCase()}">${record.type.toUpperCase()}</td>
                <td>${record.mode}</td>
            </tr>`;
        });
        tableHTML += `</tbody></table>`;
        resultsContainer.innerHTML = tableHTML;
    }
});