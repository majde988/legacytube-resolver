from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/', methods=['POST'])
def resolve():
    data = request.get_json(silent=True) or {}
    url = data.get('url')
    
    if not url:
        return jsonify({"status": "error", "message": "No URL provided"}), 400

    # إعدادات yt-dlp لجلب رابط MP4 مدمج خفيف (360p / itag 18)
    ydl_opts = {
        'format': '18/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android_testsuite', 'mweb']
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            stream_url = info.get('url')
            
            # إرجاع نفس الـ JSON اللي يستناه الآيباد
            return jsonify({
                "status": "stream",
                "url": stream_url
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/', methods=['GET'])
def health():
    return "LegacyTube Resolver is Running!", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
