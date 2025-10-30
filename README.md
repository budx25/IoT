# Servo + LDR ML Project (Assignment 2 Upgrade)

### Folder Contents
- `ldr_servo_dataset.csv` — dataset contoh
- `train_model.py` — script training model RandomForest
- `server_inference.py` — Flask API untuk prediksi servo angle
- `esp32_sketch.ino` — kode Arduino ESP32
- `requirements.txt` — dependensi Python

### Langkah Cepat
1. Install dependensi:
   ```bash
   python -m venv venv
   source venv/bin/activate  # atau venv\Scripts\activate di Windows
   pip install -r requirements.txt
