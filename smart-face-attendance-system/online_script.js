// online_script.js

document.addEventListener('DOMContentLoaded', () => {
    const entrySection = document.getElementById('entry-section');
    const cameraSection = document.getElementById('camera-section');
    const startBtn = document.getElementById('startBtn');
    const regNoInput = document.getElementById('regNoInput');
    const video = document.getElementById('video');
    const statusDiv = document.getElementById('status');
    const captureCanvas = document.createElement('canvas');

    // **UPDATED:** Point to the Express.js API gateway on port 3000
    const API_URL = 'http://127.0.0.1:3000/api';

    let regNo = '';
    let isProcessing = false;
    let verificationInterval;

    startBtn.addEventListener('click', () => {
        regNo = regNoInput.value.trim();
        if (!regNo) {
            alert('Please enter a registration number.');
            return;
        }
        entrySection.style.display = 'none';
        cameraSection.style.display = 'block';
        startWebcam();
    });

    function startWebcam() {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                video.srcObject = stream;
                video.play();
                statusDiv.textContent = "Camera started. Verifying your presence periodically...";
                verifyPresence(); 
                verificationInterval = setInterval(verifyPresence, 15000);
            })
            .catch(err => {
                console.error("Error accessing webcam: " + err);
                statusDiv.textContent = "Error: Could not access webcam.";
            });
    }

    function verifyPresence() {
        if (isProcessing || video.readyState !== video.HAVE_ENOUGH_DATA) return;
        isProcessing = true;
        statusDiv.textContent = "Verifying...";

        captureCanvas.width = video.videoWidth;
        captureCanvas.height = video.videoHeight;
        captureCanvas.getContext('2d').drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);

        captureCanvas.toBlob(blob => {
            const formData = new FormData();
            formData.append('image', blob, 'capture.jpg');
            formData.append('reg_no', regNo); 

            // **UPDATED:** Fetch from the Express.js API gateway
            fetch(`${API_URL}/mark_online`, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                statusDiv.textContent = data.message;
                statusDiv.style.color = data.success ? 'green' : 'red';
            })
            .catch(error => {
                console.error('Fetch problem:', error);
                statusDiv.textContent = "Error connecting to the server.";
                statusDiv.style.color = 'red';
            })
            .finally(() => {
                isProcessing = false;
            });
        }, 'image/jpeg');
    }
});