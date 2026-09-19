import os
import uuid
from flask import Flask, Response, jsonify, request, stream_with_context
import requests
import yt_dlp

app = Flask(__name__)

# ذاكرة مؤقتة لتخزين روابط الفيديو
stream_cache = {}

# 1. فحص وتحميل الكوكيز
COOKIE_PATH = None
cookies_env = os.environ.get("YOUTUBE_COOKIES")
if cookies_env:
  COOKIE_PATH = "/tmp/cookies.txt"
  with open(COOKIE_PATH, "w") as f:
    f.write(cookies_env.strip())
  print(
      "==> Cookies loaded successfully from Environment Variable!", flush=True
  )
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

      if not stream_url:
        return (
            jsonify({"status": "error", "message": "No stream URL found"}),
            404,
        )

      # صناعة رمز مؤقت وتخزين الرابط في السيرفر
      token = uuid.uuid4().hex[:12]
      stream_cache[token] = stream_url

      # صناعة رابط البروكسي الخاص بسيرفر Render
      base_host = request.host_url.rstrip("/")
      proxy_url = f"{base_host}/stream/{token}"

      print(f"==> Stream proxied to: {proxy_url}", flush=True)

      return jsonify({"status": "stream", "url": proxy_url})
  except Exception as e:
    return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/stream/<token>")
def proxy_stream(token):
  real_url = stream_cache.get(token)
  if not real_url:
    return "Stream expired or not found", 404

  # تمرير الـ Range Headers من مشغل الآيباد إلى قوقل
  req_headers = {}
  if "Range" in request.headers:
    req_headers["Range"] = request.headers["Range"]

  # الاتصال بقوقل من سيرفر Render
  r = requests.get(real_url, headers=req_headers, stream=True)

  # تجهيز الهيدرز للآيباد مع دعم الـ Range الكامل (HTTP 206)
  excluded_headers = [
      "content-encoding",
      "content-length",
      "transfer-encoding",
      "connection",
  ]
  resp_headers = [
      (name, value)
      for (name, value) in r.raw.headers.items()
      if name.lower() not in excluded_headers
  ]

  resp_headers.append(("Accept-Ranges", "bytes"))
  if "Content-Range" in r.headers:
    resp_headers.append(("Content-Range", r.headers["Content-Range"]))
  if "Content-Length" in r.headers:
    resp_headers.append(("Content-Length", r.headers["Content-Length"]))
  if "Content-Type" in r.headers:
    resp_headers.append(("Content-Type", r.headers["Content-Type"]))
  else:
    resp_headers.append(("Content-Type", "video/mp4"))

  def generate():
    for chunk in r.iter_content(chunk_size=1024 * 64):
      if chunk:
        yield chunk

  return Response(
      stream_with_context(generate()),
      status=r.status_code,
      headers=resp_headers,
  )


@app.route("/", methods=["GET"])
def health():
  return (
      f"LegacyTube Resolver & Stream Proxy is Running! (Cookies:"
      f" {COOKIE_PATH is not None})",
      200,
  )


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=10000)
