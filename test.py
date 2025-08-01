# from flask import Flask, request, send_file, jsonify
# from PIL import Image, ImageEnhance
# import requests
# import io
#
# app = Flask(__name__)
#
# def fetch_image_from_url(url):
#     response = requests.get(url)
#     if response.status_code != 200:
#         raise Exception(f"Failed to fetch image from {url}")
#     return Image.open(io.BytesIO(response.content)).convert("RGBA")
#
# def apply_opacity(image, opacity):
#     if image.mode != 'RGBA':
#         image = image.convert('RGBA')
#     alpha = image.split()[3]
#     alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
#     image.putalpha(alpha)
#     return image
#
# @app.route('/overlay', methods=['POST',"GET"])
# def overlay_image():
#     data = request.json
#     background_url = data.get('background_url')
#     overlay_url = data.get('overlay_url')
#     opacity = float(data.get('opacity', 1.0))  # default = fully opaque
#
#     if not background_url or not overlay_url:
#         return jsonify({"error": "Both background_url and overlay_url are required"}), 400
#
#     try:
#         background = fetch_image_from_url(background_url)
#         overlay = fetch_image_from_url(overlay_url)
#
#         # Resize overlay to be smaller (optional - here 25% of background)
#         overlay_width = background.width // 10
#         overlay_height = int((overlay.height / overlay.width) * overlay_width)
#         overlay = overlay.resize((overlay_width, overlay_height))
#
#         # Apply opacity
#         overlay = apply_opacity(overlay, opacity)
#
#         # Top-right position
#         position = (background.width - overlay.width, 0)
#
#         # Paste overlay
#         background.paste(overlay, position, overlay)
#
#         # Return final image
#         img_io = io.BytesIO()
#         background.save(img_io, 'PNG')
#         img_io.seek(0)
#         return send_file(img_io, mimetype='image/png')
#
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
#
# if __name__ == '__main__':
#     app.run(debug=True, host="0.0.0.0", port=5005)



from flask import Flask, request, send_file, jsonify, make_response
from PIL import Image, ImageEnhance
import requests, io, os, uuid

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
        background = fetch_image_from_url(background_url)
        overlay = fetch_image_from_url(overlay_url)

        overlay_width = background.width // 10
        overlay_height = int((overlay.height / overlay.width) * overlay_width)
        overlay = overlay.resize((overlay_width, overlay_height))

        overlay = apply_opacity(overlay, opacity)
        position = (background.width - overlay.width, 0)
        background.paste(overlay, position, overlay)

        # Save to disk
        filename = f"{uuid.uuid4().hex}.png"
        filepath = os.path.join(STATIC_DIR, filename)
        background.save(filepath, 'PNG')

        # Create public URL
        host = request.host_url.rstrip('/')
        image_url = f"{host}/static/{filename}"

        # Save image to memory to send as file
        img_io = io.BytesIO()
        background.save(img_io, 'PNG')
        img_io.seek(0)

        # Create response with file and custom header
        response = make_response(send_file(img_io, mimetype='image/png'))
        response.headers['X-Image-URL'] = image_url  # custom header
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5005)
