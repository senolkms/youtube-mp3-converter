from flask import Flask, render_template, request, send_file, jsonify, Response, stream_with_context

import yt_dlp
import os
import tempfile
import uuid
import re
import json
import time
import threading
import queue
import glob

app = Flask(__name__)

# Geçici dosyalar için klasör
TEMP_DIR = tempfile.gettempdir()
DOWNLOAD_DIR = os.path.join(TEMP_DIR, 'youtube_downloads')

# İndirme klasörünü oluştur
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# İlerleme durumlarını saklamak için global sözlük
progress_hooks = {}

def check_ffmpeg():
    """FFmpeg'in kurulu olup olmadığını kontrol et"""
    import shutil
    return shutil.which('ffmpeg') is not None

def cleanup_old_files():
    """1 saatten eski dosyaları temizle"""
    while True:
        try:
            current_time = time.time()
            # 1 saat (3600 saniye)
            max_age = 3600
            
            for filename in os.listdir(DOWNLOAD_DIR):
                file_path = os.path.join(DOWNLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age:
                        try:
                            os.remove(file_path)
                            print(f"Eski dosya silindi: {filename}")
                        except Exception as e:
                            print(f"Dosya silinirken hata: {e}")
                            
        except Exception as e:
            print(f"Temizlik işleminde hata: {e}")
            
        # 10 dakikada bir kontrol et
        time.sleep(600)

# Temizlik işlemini arka planda başlat
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

def sanitize_filename(filename):
    """Dosya adındaki geçersiz karakterleri temizle"""
    invalid_chars = r'[<>:"/\\|?*]'
    filename = re.sub(invalid_chars, '_', filename)
    filename = filename.strip(' .')
    if len(filename) > 200:
        filename = filename[:200]
    return filename

def get_unique_filename(directory, base_name, extension):
    """Benzersiz dosya adı oluştur"""
    full_path = os.path.join(directory, f"{base_name}.{extension}")
    if not os.path.exists(full_path):
        return full_path
    
    counter = 1
    while True:
        new_name = f"{base_name} ({counter})"
        full_path = os.path.join(directory, f"{new_name}.{extension}")
        if not os.path.exists(full_path):
            return full_path
        counter += 1

def progress_hook(d, task_id):
    """yt-dlp için ilerleme kancası"""
    if d['status'] == 'downloading':
        try:
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            if total > 0:
                percent = (downloaded / total) * 100
                progress_hooks[task_id] = {
                    'status': 'downloading',
                    'percent': percent,
                    'speed': d.get('speed', 0),
                    'eta': d.get('eta', 0)
                }
        except Exception:
            pass
    elif d['status'] == 'finished':
        progress_hooks[task_id] = {
            'status': 'processing',
            'percent': 100
        }

def download_media_thread(url, format_type, quality, task_id, result_queue):
    """Arka planda indirme işlemi"""
    try:
        has_ffmpeg = check_ffmpeg()
        
        # Video bilgilerini al
        ydl_opts_info = {
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
        
        clean_title = sanitize_filename(title)
        temp_filename = str(uuid.uuid4())
        temp_output_path = os.path.join(DOWNLOAD_DIR, f"{temp_filename}.%(ext)s")
        
        # İndirme ayarları
        ydl_opts = {
            'outtmpl': temp_output_path,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [lambda d: progress_hook(d, task_id)],
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # Metadata ve Thumbnail ayarları
            'writethumbnail': True,
            'addmetadata': True,
        }
        
        if format_type == 'mp3':
            ydl_opts['format'] = 'bestaudio/best'
            if has_ffmpeg:
                ydl_opts['postprocessors'] = [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    },
                    {
                        'key': 'FFmpegMetadata',
                        'add_chapters': True,
                        'add_metadata': True,
                    },
                    {
                        'key': 'EmbedThumbnail',
                    }
                ]
        else:
            if quality == 'best':
                ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best'
            else:
                height = int(quality)
                ydl_opts['format'] = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best'
            
            if has_ffmpeg:
                ydl_opts['postprocessors'] = [
                    {
                        'key': 'FFmpegVideoRemuxer',
                        'preferedformat': 'mp4',
                    },
                    {
                        'key': 'FFmpegMetadata',
                        'add_chapters': True,
                        'add_metadata': True,
                    },
                    {
                        'key': 'EmbedThumbnail',
                    }
                ]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        # Dosya uzantısını ve yolunu belirle
        if format_type == 'mp3':
            extension = 'mp3' if has_ffmpeg else 'm4a'
            if has_ffmpeg:
                 temp_file = os.path.join(DOWNLOAD_DIR, f"{temp_filename}.mp3")
            else:
                 temp_file = os.path.join(DOWNLOAD_DIR, f"{temp_filename}.m4a")
                 if not os.path.exists(temp_file):
                     for ext in ['webm', 'opus', 'ogg', 'aac', 'flac']:
                         pot = os.path.join(DOWNLOAD_DIR, f"{temp_filename}.{ext}")
                         if os.path.exists(pot):
                             temp_file = pot
                             extension = ext
                             break
        else:
            extension = 'mp4'
            temp_file = os.path.join(DOWNLOAD_DIR, f"{temp_filename}.mp4")
            if not os.path.exists(temp_file):
                 for ext in ['webm', 'mkv']:
                     pot = os.path.join(DOWNLOAD_DIR, f"{temp_filename}.{ext}")
                     if os.path.exists(pot):
                         temp_file = pot
                         extension = ext
                         break

        # Thumbnail dosyalarını temizle (yt-dlp bazen geride bırakabilir)
        for f in glob.glob(os.path.join(DOWNLOAD_DIR, f"{temp_filename}.*")):
            if f != temp_file and not f.endswith(f".{extension}"):
                try:
                    os.remove(f)
                except:
                    pass

        if not temp_file or not os.path.exists(temp_file):
            raise Exception("Dosya oluşturulamadı")

        final_file = get_unique_filename(DOWNLOAD_DIR, clean_title, extension)
        os.rename(temp_file, final_file)
        
        progress_hooks[task_id] = {'status': 'completed', 'filename': os.path.basename(final_file), 'title': title}
        
    except Exception as e:
        progress_hooks[task_id] = {'status': 'error', 'error': str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_download', methods=['POST'])
def start_download():
    try:
        data = request.json
        url = data.get('url')
        format_type = data.get('format', 'mp3')
        quality = data.get('quality', 'best')
        
        if not url:
            return jsonify({'error': 'URL gerekli'}), 400
            
        task_id = str(uuid.uuid4())
        progress_hooks[task_id] = {'status': 'starting', 'percent': 0}
        
        # Arka planda indirmeyi başlat
        thread = threading.Thread(target=download_media_thread, args=(url, format_type, quality, task_id, None))
        thread.start()
        
        return jsonify({'task_id': task_id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/progress/<task_id>')
def progress(task_id):
    def generate():
        while True:
            if task_id in progress_hooks:
                data = progress_hooks[task_id]
                yield f"data: {json.dumps(data)}\n\n"
                if data['status'] in ['completed', 'error']:
                    break
            else:
                yield f"data: {json.dumps({'status': 'waiting'})}\n\n"
            time.sleep(0.5)
            
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/get_file/<filename>')
def get_file(filename):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    return jsonify({'error': 'Dosya bulunamadı'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)