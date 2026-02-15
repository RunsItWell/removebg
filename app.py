from flask import Flask, render_template, request, send_file
from withoutbg import WithoutBG
from PIL import Image
import os
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = "static/output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 🔥 LOAD MODEL SEKALI
bg_remover = WithoutBG.opensource()

MAX_SIZE = 1200  # 🔽 ukuran maksimal sisi terpanjang

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["image"]
        mode = request.form["mode"]
        compress = request.form.get("compress") is not None
        bgcolor = request.form.get("bgcolor", "#ffffff")

        uid = str(uuid.uuid4())
        input_path = os.path.join(UPLOAD_FOLDER, f"{uid}.png")
        transparent_path = os.path.join(UPLOAD_FOLDER, f"{uid}_transparent.png")

        file.save(input_path)

        # =========================
        # 🔹 REMOVE BACKGROUND
        # =========================
        result = bg_remover.remove_background(input_path)
        result.save(transparent_path)

        # =========================
        # 🔹 MODE: REMOVE BG ONLY
        # =========================
        if mode == "remove":
            img = Image.open(transparent_path).convert("RGBA")

            if compress:
                # 🔽 resize agar size turun beneran
                img.thumbnail((MAX_SIZE, MAX_SIZE), Image.LANCZOS)

                img.save(
                    transparent_path,
                    optimize=True,
                    compress_level=9
                )

            return send_file(transparent_path, as_attachment=True)

        # =========================
        # 🔹 MODE: REPLACE BG
        # =========================
        r, g, b = hex_to_rgb(bgcolor)

        foreground = Image.open(transparent_path).convert("RGBA")
        background = Image.new("RGBA", foreground.size, (r, g, b, 255))
        final_img = Image.alpha_composite(background, foreground)

        final_path = os.path.join(UPLOAD_FOLDER, f"{uid}.jpg")

        if compress:
            final_img.thumbnail((MAX_SIZE, MAX_SIZE), Image.LANCZOS)
            final_img.convert("RGB").save(
                final_path,
                quality=70,
                optimize=True
            )
        else:
            final_img.convert("RGB").save(final_path, quality=95)

        return send_file(final_path, as_attachment=True)

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
