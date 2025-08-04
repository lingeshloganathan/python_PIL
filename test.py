from flask import Flask, request, send_file, jsonify, make_response
from PIL import Image, ImageEnhance
import requests, io, os, uuid

app = Flask(__name__)
STATIC_DIR = 'static'
os.makedirs(STATIC_DIR, exist_ok=True)

FIXED_OVERLAY_PATH = 'logo.png'

def fetch_image_from_url(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch image from {url}")
    image = Image.open(io.BytesIO(response.content))
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    return image

def load_fixed_overlay():
    if not os.path.exists(FIXED_OVERLAY_PATH):
        raise Exception("Fixed overlay image not found")
    image = Image.open(FIXED_OVERLAY_PATH)
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    return image

def apply_opacity(image, opacity):
    alpha = image.getchannel('A')
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    image.putalpha(alpha)
    return image

@app.route('/overlay', methods=['GET', 'POST'])
def overlay_image():
    try:
        if request.method == 'POST':
            data = request.get_json()
            background_url = data.get('background_url')
            opacity = float(data.get('opacity', 1.0))
        else:
            background_url = request.args.get('background_url')
            opacity = float(request.args.get('opacity', 1.0))

        if not background_url:
            return jsonify({"error": "background_url is required"}), 400

        # Load images
        background = fetch_image_from_url(background_url)
        overlay = load_fixed_overlay()

        # Resize overlay
        overlay_width = background.width // 10
        overlay_height = int((overlay.height / overlay.width) * overlay_width)
        overlay = overlay.resize((overlay_width, overlay_height))

        # Apply opacity
        overlay = apply_opacity(overlay, opacity)

        # Paste overlay at top-right
        position = (background.width - overlay.width, 0)
        background.paste(overlay, position, overlay)

        # Save final image
        filename = f"{uuid.uuid4().hex}.png"
        filepath = os.path.join(STATIC_DIR, filename)
        background.save(filepath, 'PNG')

        # Prepare public image URL
        host = request.host_url.rstrip('/')
        image_url = f"{host}/static/{filename}"

        # Return image + URL
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