import os
from flask import Flask, jsonify, request
import yt_dlp

app = Flask(__name__)


@app.route('/', methods=['POST'])
def resolve():
  data = request.get_json(silent=True) or {}
  url = data.get('url')

  if not url:
    return jsonify({'status': 'error', 'message': 'No URL provided'}), 400

  # إعدادات yt-dlp مع تفعيل الكوكيز الرسمية
  ydl_opts = {
      'format': '18/best[ext=mp4]/best',
      'quiet': True,
      'no_warnings': True,
      'socket_timeout': 20,
      'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
  }

  try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(url, download=False)
      stream_url = info.get('url')

      # احتياط: إذا كان الرابط داخل قائمة formats
      if not stream_url and 'formats' in info:
        for f in info['formats']:
          if f.get('format_id') == '18' or (
              f.get('ext') == 'mp4' and f.get('vcodec') != 'none'
          ):
            stream_url = f.get('url')
            break

      return jsonify({'status': 'stream', 'url': stream_url})
  except Exception as e:
    return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/', methods=['GET'])
def health():
  return 'LegacyTube Resolver is Running!', 200


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=10000)
