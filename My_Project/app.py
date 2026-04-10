from flask import Flask, request, jsonify
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import os, time, struct, re
from datetime import datetime

app = Flask(__name__)

@app.route("/start-recording", methods=["POST"])
def start_recording():
    data = request.json
    person = data.get("personName", "unknown")
    word = data.get("word", "sample")
    duration = int(data.get("duration", 1))
    samples = int(data.get("samples", 1))

    base_folder = "recordings"
    wav_folder = os.path.join(base_folder, "wav")
    hex_folder = os.path.join(base_folder, "hex")
    os.makedirs(wav_folder, exist_ok=True)
    os.makedirs(hex_folder, exist_ok=True)

    fs = 8000  # 8 kHz
    devices = sd.query_devices()
    best_device = sd.default.device

    def find_next_index(folder, prefix="sample_", ext=".wav"):
        files = [f for f in os.listdir(folder) if f.startswith(prefix) and f.endswith(ext)]
        indices = []
        for f in files:
            match = re.search(r"sample_(\d+)", f)
            if match:
                indices.append(int(match.group(1)))
        return max(indices, default=0) + 1

    start_index = find_next_index(wav_folder)

    for i in range(samples):
        current_index = start_index + i
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"Recording sample {current_index} for '{word}'...")
        audio = sd.rec(int(fs * duration), samplerate=fs, channels=1, dtype="int16")
        sd.wait()

        wav_filename = os.path.join(wav_folder, f"sample_{current_index}_{person}_{word}_{timestamp}.wav")
        txt_filename = os.path.join(hex_folder, f"sample_{current_index}_{person}_{word}_{timestamp}.txt")

        write(wav_filename, fs, audio)

        audio_flat = audio.flatten()
        with open(txt_filename, "w") as f:
            for sample in audio_flat:
                hex_val = format(struct.unpack("<H", struct.pack("<h", int(sample)))[0], "04x")
                f.write(hex_val + "\n")

    return jsonify({
        "message": f"✅ Recorded {samples} samples for '{word}' by {person}.",
        "wav_folder": wav_folder,
        "hex_folder": hex_folder
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
