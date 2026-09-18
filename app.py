from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/', methods=['POST'])
def resolve():
    data = request.get_json(silent=True) or {}
    url = data.get('url')
    
    if not url:
        return jsonify({"status": "error", "message": "No URL provided"}), 400

    # إعدادات متطورة لتجاوز حظر الـ Datacenter
    ydl_opts = {
        'format': '18/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 15,
        'extractor_args': {
            'youtube': {
                'player_client': ['android_creator', 'mweb'],
                'player_skip': ['webpage', 'configs']  # تخطي صفحة الويب التي تطلب الكابتشا
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            stream_url = info.get('url')
            
            return jsonify({
                "status": "stream",
                "url": stream_url
            })
    except Exception as e:
        # محاولة ثانية بكليينت احتياطي إذا فشل الأول
        try:
            ydl_opts['extractor_args']['youtube']['player_client'] = ['tv_embedded']
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return jsonify({
                    "status": "stream",
                    "url": info.get('url')
                })
        except Exception as e2:
            return jsonify({"status": "error", "message": str(e2)}), 500

@app.route('/', methods=['GET'])
def health():
    return "LegacyTube Resolver is Running!", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
