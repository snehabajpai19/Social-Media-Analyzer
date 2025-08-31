import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from utils.extract import extract_text_from_pdf, extract_text_from_image
from utils.analyze import analyze_text
from dotenv import load_dotenv

load_dotenv() 

# File types we accept via upload. Add more here if needed.
ALLOWED = {"pdf", "png", "jpg", "jpeg"}

def allowed(filename): 
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "devkey")

@app.route("/", methods=["GET", "POST"])  # Single page: upload + results
def index():
    if request.method == "POST":
        # Users can drag-n-drop or pick multiple files; we handle both paths.
        files = request.files.getlist("files")
        if not files or files[0].filename == "":
            flash("Please choose at least one PDF or image")
            return redirect(url_for("index"))

        results, errors = [], []
        for f in files:
            if not allowed(f.filename):
                errors.append(f"Unsupported: " + f.filename)
                continue
            name = secure_filename(f.filename)
            ext = name.rsplit(".", 1)[1].lower()
            try:
                text = extract_text_from_pdf(f.stream) if ext == "pdf" else extract_text_from_image(f.stream)
                text = (text or "").strip()
                if text:
                    results.append({"filename": name, "text": text})
                else:
                    errors.append(f"No text in {name}")
            except Exception as e:
                errors.append(f"Error in {name}: {e}")

        combined = "\n\n".join(r["text"] for r in results)
        analysis = analyze_text(combined) if combined else None

        # Render the same page with results and a combined analysis summary.
        return render_template(
            "index.html",
            results=results,
            errors=errors,
            analysis=analysis,
            combined_text=combined,
        )

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
