from flask import Flask, request, send_file, jsonify, make_response
from PIL import Image, ImageEnhance
import requests, io, os, uuid
# from rembg import remove
 
 
app = Flask(__name__)
STATIC_DIR = 'static'
os.makedirs(STATIC_DIR, exist_ok=True)
 
def fetch_image_from_url(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch image from {url}")
    return Image.open(io.BytesIO(response.content)).convert("RGBA")
 
def apply_opacity(image, opacity):
    alpha = image.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    image.putalpha(alpha)
    return image
 
@app.route('/overlay', methods=['GET', 'POST'])
def overlay_image():
    if request.method == 'POST':
        data = request.get_json()
        background_url = data.get('background_url')
        overlay_url = data.get('overlay_url')
        opacity = float(data.get('opacity', 1.0))
    else:
        background_url = request.args.get('background_url')
        overlay_url = request.args.get('overlay_url')
        opacity = float(request.args.get('opacity', 1.0))
 
    if not background_url or not overlay_url:
        return jsonify({"error": "Both background_url and overlay_url are required"}), 400
 
    try:
        # Fetch background
        background = fetch_image_from_url(background_url)
 
        # Fetch and remove background from overlay image
        overlay_raw = requests.get(overlay_url)
        if overlay_raw.status_code != 200:
            raise Exception(f"Failed to fetch image from {overlay_url}")
        input_overlay = Image.open(io.BytesIO(overlay_raw.content)).convert("RGBA")
        # overlay_no_bg = remove(input_overlay)  # Rembg background removal
        overlay_no_bg = (input_overlay)  # Rembg background removal
 
        # Resize and apply opacity
        overlay_width = background.width // 10
        overlay_height = int((overlay_no_bg.height / overlay_no_bg.width) * overlay_width)
        overlay_resized = overlay_no_bg.resize((overlay_width, overlay_height))
        overlay = apply_opacity(overlay_resized, opacity)
 
        # Overlay position
        position = (background.width - overlay.width, 0)
        background.paste(overlay, position, overlay)
 
        # Save and return image as response
        filename = f"{uuid.uuid4().hex}.png"
        filepath = os.path.join(STATIC_DIR, filename)
        background.save(filepath, 'PNG')
 
        host = request.host_url.rstrip('/')
        image_url = f"{host}/static/{filename}"
 
        img_io = io.BytesIO()
        background.save(img_io, 'PNG')
        img_io.seek(0)
 
        response = make_response(send_file(img_io, mimetype='image/png'))
        response.headers['X-Image-URL'] = image_url
        return response
 
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
 
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5005)
