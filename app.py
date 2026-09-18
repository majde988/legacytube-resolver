import os
from flask import Flask, jsonify, request
import yt_dlp

app = Flask(__name__)

COOKIE_PATH = None

# 1. فحص المتغير البيئي وصناعة الملف أوتوماتيكياً
cookies_env = os.environ.get("YOUTUBE_COOKIES")
if cookies_env:
  COOKIE_PATH = "/tmp/cookies.txt"
  with open(COOKIE_PATH, "w") as f:
    f.write(cookies_env.strip())
  print("==> Cookies loaded successfully from Environment Variable!", flush=True)

# 2. فحص المسارات الاحتياطية
elif os.path.exists("/etc/secrets/cookies.txt"):
  COOKIE_PATH = "/etc/secrets/cookies.txt"
elif os.path.exists("cookies.txt"):
  COOKIE_PATH = "cookies.txt"


@app.route("/", methods=["POST"])
def resolve():
  data = request.get_json(silent=True) or {}
  url = data.get("url")

  if not url:
    return jsonify({"status": "error", "message": "No URL provided"}), 400

  ydl_opts = {
      "format": "18/best[ext=mp4]/best",
      "quiet": True,
      "no_warnings": True,
      "socket_timeout": 20,
      "cookiefile": COOKIE_PATH,
  }

  try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(url, download=False)
      stream_url = info.get("url")

      if not stream_url and "formats" in info:
        for f in info["formats"]:
          if f.get("format_id") == "18" or (
              f.get("ext") == "mp4" and f.get("vcodec") != "none"
          ):
            stream_url = f.get("url")
            break

      return jsonify({"status": "stream", "url": stream_url})
  except Exception as e:
    return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/", methods=["GET"])
def health():
  return (
      f"LegacyTube Resolver is Running! (Cookies: {COOKIE_PATH is not None})",
      200,
  )


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=10000)
