import os
import math
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import yt_dlp
import ffmpeg

app = Flask(__name__)
CORS(app)

OUTPUT_DIR = "clips"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route('/process', methods=['POST'])
def process_video():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL missing'}), 400

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'input_video.%(ext)s',
        'overwrites': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    probe = ffmpeg.probe('input_video.mp4')
    duration = float(probe['format']['duration'])
    clip_length = 60
    total_clips = math.ceil(duration / clip_length)

    clips_list = []
    for i in range(total_clips):
        start_time = i * clip_length
        clip_filename = f"clip_{i+1}.mp4"
        clip_path = os.path.join(OUTPUT_DIR, clip_filename)

        (
            ffmpeg
            .input('input_video.mp4', ss=start_time, t=clip_length)
            .output(clip_path, c='copy')
            .run(overwrite_output=True)
        )

        clips_list.append({
            'clip_name': f'Clip {i+1} (1 Min)',
            'download_url': f'/download/{clip_filename}'
        })

    return jsonify({'clips': clips_list})

@app.route('/download/<filename>', methods=['GET'])
def download_clip(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
