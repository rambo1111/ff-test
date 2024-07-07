var video = document.getElementById('video');
var captureCanvas = document.getElementById('canvas');
var capturedImagesDiv = document.getElementById('captured-images');
var startButton = document.getElementById('startButton');
var stopButton = document.getElementById('stopButton');
var captureButton = document.getElementById('captureButton');
var stream;

// Request camera access
function startCamera() {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true }).then(function(mediaStream) {
            stream = mediaStream;
            video.srcObject = stream;
            video.play();
        }).catch(function(error) {
            console.error("Error accessing the camera", error);
        });
    } else {
        alert('Your browser does not support getUserMedia API');
    }
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(function(track) {
            track.stop();
        });
        video.srcObject = null;
    }
}

function captureFrame() {
    captureCanvas.width = 300;
    captureCanvas.height = 300;
    var context = captureCanvas.getContext('2d');
    var videoWidth = video.videoWidth;
    var videoHeight = video.videoHeight;

    // Calculate the coordinates for cropping the 300x300 center of the video
    var startX = (videoWidth - 300) / 2;
    var startY = (videoHeight - 300) / 2;

    // Draw the video frame to the canvas
    context.drawImage(video, startX, startY, 300, 300, 0, 0, 300, 300);
    var dataURL = captureCanvas.toDataURL('image/png');
    
    // Send the captured frame to the server
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/upload', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function() {
        if (xhr.status === 200) {
            var response = JSON.parse(xhr.responseText);
            var img = document.createElement('img');
            img.src = dataURL;
            img.alt = 'Captured Frame';
            capturedImagesDiv.appendChild(img);
        }
    };
    xhr.send(JSON.stringify({ image: dataURL }));
}

startButton.addEventListener('click', startCamera);
stopButton.addEventListener('click', stopCamera);
captureButton.addEventListener('click', captureFrame);
