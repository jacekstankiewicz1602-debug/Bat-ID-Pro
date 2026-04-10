from batdetect2 import api
import numpy as np
import os

def test():
    print("Testing batdetect2...")
    # Create a dummy 1-second white noise signal at 256kHz
    sr = 256000
    duration = 1.0
    audio = np.random.uniform(-1, 1, int(sr * duration)).astype(np.float32)
    
    # In-memory audio processing if supported, or save to temp file
    temp_wav = "temp_test.wav"
    import soundfile as sf
    sf.write(temp_wav, audio, sr)
    
    try:
        print(f"Processing audio from {temp_wav}...")
        audio_data = api.load_audio(temp_wav)
        detections, features, spec = api.process_audio(audio_data, threshold=0.5)
        print(f"Success! Found {len(detections)} detections in dummy noise.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)

if __name__ == "__main__":
    test()
