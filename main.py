import os
import base64
import atexit
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image
from potrace import Bitmap, POTRACE_TURNPOLICY_MINORITY
import fontforge

app = Flask(__name__)
CAPTURED_FRAMES_FOLDER = 'captured_frames'
PROCESSED_FRAMES_FOLDER = 'processed_frames'
SVG_FOLDER = 'svgs'
TTF_PATH = 'myfont.ttf'
os.makedirs(CAPTURED_FRAMES_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FRAMES_FOLDER, exist_ok=True)
os.makedirs(SVG_FOLDER, exist_ok=True)

def cleanup_on_exit():
    try:
        deleted_files = []
        for folder in [CAPTURED_FRAMES_FOLDER, PROCESSED_FRAMES_FOLDER, SVG_FOLDER]:
            files = os.listdir(folder)
            for file in files:
                file_path = os.path.join(folder, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted_files.append(file)
        if os.path.isfile(TTF_PATH):
            os.remove(TTF_PATH)
            deleted_files.append(TTF_PATH)
        print(f"Cleanup completed. Deleted files: {deleted_files}")
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")

atexit.register(cleanup_on_exit)

def enhance_contrast_brightness_dilate(image_path, output_path, kernel_size=(3, 3)):
    img = cv2.imread(image_path)
    alpha = 1.5
    beta = 10
    adjusted = np.clip(alpha * img + beta, 0, 255).astype(np.uint8)
    kernel = np.ones(kernel_size, dtype=np.uint8)
    dilated = cv2.erode(adjusted, kernel, iterations=1)
    cv2.imwrite(output_path, dilated)

def file_to_svg(input_path, output_path):
    image = Image.open(input_path).convert('L')
    bm = Bitmap(image, blacklevel=0.5)
    plist = bm.trace(turdsize=2, turnpolicy=POTRACE_TURNPOLICY_MINORITY, alphamax=1, opticurve=False, opttolerance=0.2)
    with open(output_path, "w") as fp:
        fp.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {image.width} {image.height}">')
        parts = []
        for curve in plist:
            fs = curve.start_point
            parts.append(f"M{fs.x},{fs.y}")
            for segment in curve.segments:
                if segment.is_corner:
                    a, b = segment.c, segment.end_point
                    parts.append(f"L{a.x},{a.y}L{b.x},{b.y}")
                else:
                    a, b, c = segment.c1, segment.c2, segment.end_point
                    parts.append(f"C{a.x},{a.y} {b.x},{b.y} {c.x},{c.y}")
            parts.append("z")
        fp.write(f'<path d="{"".join(parts)}" fill="black"/>')
        fp.write("</svg>")

@app.route('/')
def index():
    files = sorted(os.listdir(CAPTURED_FRAMES_FOLDER), key=lambda x: int(x.split('.')[0]))
    return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload():
    data = request.json.get('image')
    if not data:
        return jsonify({'error': 'No image data'}), 400
    image_data = base64.b64decode(data.split(',')[1])
    files = os.listdir(CAPTURED_FRAMES_FOLDER)
    next_number = len(files) + 1
    filename = f"{next_number}.png"
    file_path = os.path.join(CAPTURED_FRAMES_FOLDER, filename)
    with open(file_path, 'wb') as f:
        f.write(image_data)
    return jsonify({'filename': filename})

@app.route('/process_images', methods=['POST'])
def process_images():
    try:
        # Step 1: Enhance and dilate captured images
        for filename in os.listdir(CAPTURED_FRAMES_FOLDER):
            input_path = os.path.join(CAPTURED_FRAMES_FOLDER, filename)
            processed_path = os.path.join(PROCESSED_FRAMES_FOLDER, filename)
            enhance_contrast_brightness_dilate(input_path, processed_path)
        
        # Step 2: Convert processed images to SVG
        for filename in os.listdir(PROCESSED_FRAMES_FOLDER):
            input_path = os.path.join(PROCESSED_FRAMES_FOLDER, filename)
            char_index = int(os.path.splitext(filename)[0]) - 1
            characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
            if char_index < 0 or char_index >= len(characters):
                continue
            char = characters[char_index]
            svg_path = os.path.join(SVG_FOLDER, f"{char}.svg")
            file_to_svg(input_path, svg_path)
        
        # Step 3: Generate TTF font from SVGs
        font = fontforge.font()
        for filename in os.listdir(SVG_FOLDER):
            char = os.path.splitext(filename)[0]
            if len(char) != 1:
                print(f"Skipping invalid character file: {filename}")
                continue
            glyph = font.createChar(ord(char))
            svg_path = os.path.join(SVG_FOLDER, filename)
            glyph.importOutlines(svg_path)
        font.generate(TTF_PATH)

        return jsonify({'message': 'Processing complete. TTF file generated.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_ttf')
def download_ttf():
    try:
        return send_file(TTF_PATH, as_attachment=True, download_name='myfont.ttf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cleanup', methods=['POST'])
def cleanup():
    try:
        deleted_files = []
        for folder in [CAPTURED_FRAMES_FOLDER, PROCESSED_FRAMES_FOLDER, SVG_FOLDER]:
            files = os.listdir(folder)
            for file in files:
                file_path = os.path.join(folder, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted_files.append(file)
        if os.path.isfile(TTF_PATH):
            os.remove(TTF_PATH)
            deleted_files.append(TTF_PATH)
        return jsonify({'deleted_files': deleted_files}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
