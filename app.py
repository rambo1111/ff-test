import os
import cv2
import numpy as np
from PIL import Image
import potrace
import fontforge
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

def enhance_contrast_brightness_erode(image_path):
    img = cv2.imread(image_path)
    alpha = 1.5
    beta = 10
    adjusted = np.clip(alpha * img + beta, 0, 255).astype(np.uint8)
    kernel = np.ones((3, 3), dtype=np.uint8)
    eroded = cv2.erode(adjusted, kernel, iterations=1)
    return eroded

def convert_to_svg(image, output_path):
    image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))
    bitmap = potrace.Bitmap(np.array(image))
    path = bitmap.trace()
    with open(output_path, "w") as f:
        f.write('<svg xmlns="http://www.w3.org/2000/svg">\n')
        f.write('<path d="')
        for curve in path:
            f.write(f'M{curve.start_point.x},{curve.start_point.y} ')
            for segment in curve:
                if segment.is_corner:
                    f.write(f'L{segment.c.x},{segment.c.y} L{segment.end_point.x},{segment.end_point.y} ')
                else:
                    f.write(f'C{segment.c1.x},{segment.c1.y} {segment.c2.x},{segment.c2.y} {segment.end_point.x},{segment.end_point.y} ')
            f.write('Z ')
        f.write('"/>\n</svg>')

def create_ttf_from_svgs(svg_files, output_font_path):
    font = fontforge.font()
    for char, svg_file in svg_files.items():
        glyph = font.createChar(ord(char))
        glyph.importOutlines(svg_file)
    font.generate(output_font_path)

@app.post("/generate-font")
def generate_font():
    input_directory = 'input_images'
    output_font_path = 'myfont.ttf'
    svg_files = {}
    for filename in os.listdir(input_directory):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            input_path = os.path.join(input_directory, filename)
            eroded_image = enhance_contrast_brightness_erode(input_path)
            char_index = int(os.path.splitext(filename)[0])
            if 1 <= char_index <= 26:
                char = chr(char_index + 64)
            elif 27 <= char_index <= 52:
                char = chr(char_index + 70)
            elif 53 <= char_index <= 62:
                char = chr(char_index - 5)
            else:
                continue
            svg_path = f"{os.path.splitext(input_path)[0]}.svg"
            convert_to_svg(eroded_image, svg_path)
            svg_files[char] = svg_path
    create_ttf_from_svgs(svg_files, output_font_path)
    return JSONResponse(content={"message": "Font generation complete.", "font_path": output_font_path})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
