#!/usr/bin/env bash
# One-time setup for a fresh workspace. Safe to run again.
set -e
cd "$(dirname "$0")"

which ffmpeg >/dev/null || { echo "ffmpeg missing: install it (apt-get install -y ffmpeg)"; exit 1; }
pip install -q --break-system-packages kokoro-onnx soundfile pillow numpy

# Voice model (Kokoro, free, runs locally). Hosted on GitHub releases.
mkdir -p .tts
[ -s .tts/kokoro.onnx ] || curl -sSL -o .tts/kokoro.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
[ -s .tts/voices.bin ]  || curl -sSL -o .tts/voices.bin  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin

# Fonts used by every scene: Inter (UI) and DejaVu Sans Mono (code/hex).
if [ ! -f /usr/share/fonts/opentype/inter/Inter-Bold.otf ]; then
  tmp=$(mktemp -d)
  curl -sSL -o "$tmp/inter.zip" https://github.com/rsms/inter/releases/download/v4.0/Inter-4.0.zip
  python3 -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "$tmp/inter.zip" "$tmp/inter"
  mkdir -p /usr/share/fonts/opentype/inter
  find "$tmp/inter" -name 'Inter-*.otf' -path '*extras/otf*' -exec cp {} /usr/share/fonts/opentype/inter/ \; 2>/dev/null || true
  find "$tmp/inter" -name 'Inter-*.otf' -exec cp -n {} /usr/share/fonts/opentype/inter/ \;
fi
[ -f /usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf ] || echo "WARNING: DejaVu Sans Mono missing (apt-get install -y fonts-dejavu-core)"

# Fonts for the chalk (Kalam) and paper (Fredoka, Nunito) styles, from google/fonts (OFL).
mkdir -p /usr/share/fonts/truetype/extra
for f in ofl/kalam/Kalam-Regular.ttf ofl/kalam/Kalam-Bold.ttf ofl/kalam/Kalam-Light.ttf "ofl/nunito/Nunito%5Bwght%5D.ttf" "ofl/fredoka/Fredoka%5Bwdth,wght%5D.ttf"; do
  n=$(basename "$f"); [ -s "/usr/share/fonts/truetype/extra/$n" ] || curl -sSfL -o "/usr/share/fonts/truetype/extra/$n" "https://raw.githubusercontent.com/google/fonts/main/$f"
done

python3 -c "import kokoro_onnx, soundfile, PIL; print('setup ok')"
