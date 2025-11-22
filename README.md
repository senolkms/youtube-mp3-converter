# YouTube MP3 & MP4 Dönüştürücü (Premium)

Modern arayüzü ve gelişmiş özellikleri ile kullanıcı dostu bir YouTube medya indirme uygulaması.

## 🌟 Özellikler

- **Çoklu Format Desteği:**
  - 🎵 **MP3:** Yüksek kaliteli ses dosyası (Thumbnail ve Metadata gömülü)
  - � **MP4:** Video ve ses bir arada (1080p, 720p, 480p seçenekleri)
- **Gelişmiş Metadata:** İndirilen MP3 dosyalarına otomatik olarak kapak resmi (thumbnail), sanatçı ve şarkı bilgileri işlenir.
- **Otomatik Temizlik:** Sunucu diskini korumak için 1 saatten eski dosyalar otomatik olarak silinir.
- **Modern Arayüz:** Glassmorphism tasarım, animasyonlu geçişler ve mobil uyumlu (responsive) yapı.
- **Canlı İlerleme Takibi:** İndirme ve dönüştürme sürecini anlık olarak yüzde ve durum mesajlarıyla takip edebilirsiniz.

## 🚀 Kurulum

1. **Gereksinimler:**
   - Python 3.8 veya üzeri
   - FFmpeg (Medya dönüştürme ve metadata işlemleri için **ZORUNLUDUR**)

2. **Projeyi Klonlayın veya İndirin:**
   ```bash
   git clone https://github.com/senolkms/youtube-mp3-converter.git
   cd youtube-mp3-converter
   ```

3. **Bağımlılıkları Yükleyin:**
   ```bash
   pip install -r requirements.txt
   ```

4. **FFmpeg Kurulumu:**
   - **Windows:** [FFmpeg İndir](https://ffmpeg.org/download.html) ve `bin` klasörünü sistem PATH'ine ekleyin.
   - **macOS:** `brew install ffmpeg`
   - **Linux:** `sudo apt-get install ffmpeg`

## 💻 Kullanım

1. **Uygulamayı Başlatın:**
   ```bash
   python app.py
   ```

2. **Tarayıcıyı Açın:**
   `http://localhost:5000` adresine gidin.

3. **İndirme Yapın:**
   - YouTube video bağlantısını yapıştırın.
   - Formatı (MP3 veya MP4) seçin.
   - Kaliteyi belirleyin (MP4 için).
   - "Dönüştür" butonuna tıklayın.

## ⚙️ Teknik Detaylar

- **Backend:** Flask (Python)
- **İndirme Motoru:** yt-dlp
- **Medya İşleme:** FFmpeg
- **Frontend:** HTML5, CSS3 (Vanilla), JavaScript (Vanilla)

## ⚠️ Yasal Uyarı

Bu proje yalnızca eğitim ve kişisel kullanım amaçlıdır. Lütfen telif hakkı yasalarına saygı gösterin ve yalnızca izin verilen içerikleri indirin.
