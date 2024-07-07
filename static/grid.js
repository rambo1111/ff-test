var gridCanvas = document.getElementById('grid');

function drawGrid() {
    var context = gridCanvas.getContext('2d');
    context.strokeStyle = 'red';
    context.lineWidth = 1;

    // Draw vertical lines
    for (let i = 1; i < 3; i++) {
        context.moveTo(i * 300 / 3, 0);
        context.lineTo(i * 300 / 3, 300);
    }

    // Draw horizontal lines
    for (let i = 1; i < 3; i++) {
        context.moveTo(0, i * 300 / 3);
        context.lineTo(300, i * 300 / 3);
    }

    context.stroke();
}

// Draw the grid initially
drawGrid();
