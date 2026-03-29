import streamlit as st
import instaloader
from urllib.parse import urlparse
import tempfile
import os
import zipfile
from PIL import Image
import json
from datetime import datetime

# --- CONFIG UI ---
st.set_page_config(page_title="Instagram Downloader Pro", page_icon="📸")

st.title("📸 Instagram Downloader Pro")

# --- HISTORY ---
HISTORY_FILE = "history.json"

def save_history(url):
    entry = {
        "url": url,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(entry)

    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)

# --- UTILS ---
def extract_shortcode(url):
    try:
        parsed = urlparse(url)
        return parsed.path.strip("/").split("/")[-1]
    except:
        return None

def download_post(url):
    shortcode = extract_shortcode(url)

    L = instaloader.Instaloader(
        save_metadata=False,
        download_comments=False,
        download_videos=True
    )

    temp_dir = tempfile.mkdtemp()

    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        # CARROUSEL
        if post.typename == "GraphSidecar":
            for i, node in enumerate(post.get_sidecar_nodes()):
                if node.is_video:
                    L.download_pic(os.path.join(temp_dir, f"video_{i}.mp4"), node.video_url, post.date)
                else:
                    L.download_pic(os.path.join(temp_dir, f"image_{i}.jpg"), node.display_url, post.date)

        # SINGLE
        else:
            if post.is_video:
                L.download_pic(os.path.join(temp_dir, "video.mp4"), post.video_url, post.date)
            else:
                L.download_post(post, target=temp_dir)

        return temp_dir, None

    except Exception as e:
        return None, str(e)

def zip_all(folder):
    zip_path = os.path.join(folder, "media.zip")

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in os.listdir(folder):
            if file.endswith((".jpg", ".png", ".mp4")):
                zipf.write(os.path.join(folder, file), file)

    return zip_path

# --- UI ---
url = st.text_input("🔗 Lien Instagram")

if st.button("🚀 Télécharger"):

    if not url:
        st.warning("Veuillez entrer une URL.")
    else:
        with st.spinner("Téléchargement en cours..."):
            folder, error = download_post(url)

        if error:
            st.error(error)
        else:
            save_history(url)

            files = os.listdir(folder)

            st.success(f"{len(files)} fichier(s) récupéré(s)")

            st.subheader("👀 Aperçu")

            cols = st.columns(3)

            for i, file in enumerate(files):
                path = os.path.join(folder, file)

                with cols[i % 3]:
                    if file.endswith(".mp4"):
                        st.video(path)
                    else:
                        st.image(Image.open(path), use_container_width=True)

            zip_path = zip_all(folder)

            with open(zip_path, "rb") as f:
                st.download_button(
                    "📥 Télécharger tout",
                    f,
                    file_name="instagram_media.zip"
                )

# --- HISTORY DISPLAY ---
st.subheader("📜 Historique")

history = load_history()

for item in reversed(history[-10:]):
    st.write(f"{item['date']} - {item['url']}")