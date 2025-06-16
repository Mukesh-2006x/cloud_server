import os
import shutil
from flask import Flask, request, redirect, url_for, render_template_string, send_from_directory, abort

app = Flask(__name__)
BASE_DIR = os.path.abspath("storage")
os.makedirs(BASE_DIR, exist_ok=True)

HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>My Cloud Drive with Folders</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; background: #f9f9f9; }
    h1 { color: #333; }
    ul { list-style: none; padding-left: 0; }
    li { background: #fff; margin-bottom: 10px; padding: 10px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; }
    a { text-decoration: none; color: #007bff; }
    a:hover { text-decoration: underline; }
    form.inline { display: inline; margin: 0; }
    button { background: #e74c3c; border: none; color: white; padding: 5px 10px; border-radius: 4px; cursor: pointer; }
    button:hover { background: #c0392b; }
    .upload-section, .folder-section { margin-bottom: 25px; }
    input[type="text"] { padding: 5px; font-size: 1rem; }
  </style>
</head>
<body>

<h1>My Cloud Drive</h1>

<div class="folder-section">
  <form action="{{ url_for('create_folder', current_path=current_path) }}" method="post">
    <input type="text" name="foldername" placeholder="New folder name" required />
    <button type="submit">Create Folder</button>
  </form>
</div>

<div class="upload-section">
  <form action="{{ url_for('upload', current_path=current_path) }}" method="post" enctype="multipart/form-data">
    <input type="file" name="file" required />
    <button type="submit">Upload File</button>
  </form>
</div>

<h3>Current path: /{{ current_path }}</h3>

{% if parent_path is not none %}
  <p><a href="{{ url_for('index', current_path=parent_path) }}">⬆️ Go up</a></p>
{% endif %}

<ul>
  {% for folder in folders %}
  <li>
    <a href="{{ url_for('index', current_path=(current_path + '/' + folder).strip('/')) }}">📁 {{ folder }}</a>
    <form action="{{ url_for('delete_folder', folder_path=(current_path + '/' + folder).strip('/')) }}" method="post" class="inline" onsubmit="return confirm('Delete folder {{ folder }} and all its contents?');">
      <button type="submit">Delete</button>
    </form>
  </li>
  {% endfor %}
  {% for file in files %}
  <li>
    <a href="{{ url_for('download_file', filename=(current_path + '/' + file).strip('/')) }}" target="_blank">📄 {{ file }}</a>
    <form action="{{ url_for('delete_file', filename=(current_path + '/' + file).strip('/')) }}" method="post" class="inline" onsubmit="return confirm('Delete file {{ file }}?');">
      <button type="submit">Delete</button>
    </form>
  </li>
  {% endfor %}
</ul>

</body>
</html>
"""

def secure_path(path):
    safe_path = os.path.normpath("/" + path).lstrip("/")
    full_path = os.path.join(BASE_DIR, safe_path)
    if not full_path.startswith(BASE_DIR):
        abort(403)
    return full_path, safe_path

@app.route("/", defaults={"current_path": ""})
@app.route("/<path:current_path>")
def index(current_path):
    full_path, safe_path = secure_path(current_path)
    if not os.path.exists(full_path):
        abort(404)
    if not os.path.isdir(full_path):
        return send_from_directory(BASE_DIR, safe_path)

    items = os.listdir(full_path)
    folders = [f for f in items if os.path.isdir(os.path.join(full_path, f))]
    files = [f for f in items if os.path.isfile(os.path.join(full_path, f))]

    if safe_path == "":
        parent_path = None
    else:
        parent_path = "/".join(safe_path.split("/")[:-1])

    return render_template_string(HTML,
                                  folders=folders,
                                  files=files,
                                  current_path=safe_path,
                                  parent_path=parent_path)

@app.route("/upload/", defaults={"current_path": ""}, methods=["POST"])
@app.route("/upload/<path:current_path>", methods=["POST"])
def upload(current_path):
    full_path, safe_path = secure_path(current_path)
    if 'file' not in request.files:
        return redirect(url_for('index', current_path=safe_path))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index', current_path=safe_path))
    file.save(os.path.join(full_path, file.filename))
    return redirect(url_for('index', current_path=safe_path))

@app.route("/delete_file/<path:filename>", methods=["POST"])
def delete_file(filename):
    full_path, safe_path = secure_path(filename)
    if os.path.isfile(full_path):
        os.remove(full_path)
    return redirect(url_for('index', current_path=os.path.dirname(safe_path)))

@app.route("/delete_folder/<path:folder_path>", methods=["POST"])
def delete_folder(folder_path):
    full_path, safe_path = secure_path(folder_path)
    if os.path.isdir(full_path):
        shutil.rmtree(full_path)
    return redirect(url_for('index', current_path=os.path.dirname(safe_path)))

@app.route("/create_folder/", defaults={"current_path": ""}, methods=["POST"])
@app.route("/create_folder/<path:current_path>", methods=["POST"])
def create_folder(current_path):
    full_path, safe_path = secure_path(current_path)
    foldername = request.form.get("foldername")
    if foldername:
        new_folder_path = os.path.join(full_path, foldername)
        try:
            os.mkdir(new_folder_path)
        except FileExistsError:
            pass
    return redirect(url_for('index', current_path=safe_path))

@app.route("/files/<path:filename>")
def download_file(filename):
    full_path, safe_path = secure_path(filename)
    return send_from_directory(BASE_DIR, safe_path, as_attachment=False)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090)

