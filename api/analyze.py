import sys
import os
import json
import uuid
import base64
import io
import numpy as np
from PIL import Image

# Add the root directory to sys.path to allow importing from BattyBirdNET-Analyzer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from batty_birdnet_analyzer import analyze
from batty_birdnet_analyzer import config as cfg
from batty_birdnet_analyzer import utils
from batty_birdnet_analyzer import audio

from werkzeug.wrappers import Request, Response

def generate_spectrogram(sig, rate):
    """Generates a base64 encoded spectrogram PNG image using only Numpy."""
    # STFT parameters
    n_fft = 1024
    hop_length = 512
    window = np.hanning(n_fft)
    
    def get_stft(x):
        frames = []
        for i in range(0, len(x) - n_fft, hop_length):
            frame = x[i:i + n_fft] * window
            frames.append(np.fft.rfft(frame))
        return np.array(frames)

    # Magnitude spectrogram
    S = np.abs(get_stft(sig))
    S_dB = 20 * np.log10(np.maximum(1e-5, S))
    
    # Normalize to 0-255
    S_min, S_max = S_dB.min(), S_dB.max()
    if S_max > S_min:
        S_dB_norm = ((S_dB - S_min) / (S_max - S_min) * 255).astype(np.uint8)
    else:
        S_dB_norm = np.zeros_like(S_dB, dtype=np.uint8)
    
    # Simple "Magma" Colormap LUT
    lut = np.zeros((256, 3), dtype=np.uint8)
    for i in range(256):
        lut[i] = [
            int(min(255, i * 1.8)), # Red
            int(min(255, i * 0.9)), # Green
            int(min(255, i * 0.4))  # Blue
        ]
    
    # Apply colormap and rotate
    img_data = lut[S_dB_norm.T]
    img_data = np.flipud(img_data)
    
    img = Image.fromarray(img_data)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')

@Request.application
def application(request):
    """Glowne API Flask/WSGI - obsluguje Vercel"""
    
    if request.method == 'OPTIONS':
         return Response('', status=200, headers={'Access-Control-Allow-Origin': '*'})
         
    if request.method != 'POST':
        return Response(
            json.dumps({'error': 'Method not allowed. Use POST.'}), 
            status=405, 
            mimetype='application/json'
        )

    try:
        content_type = request.headers.get('Content-Type', '')
        if 'multipart/form-data' not in content_type:
            return Response(json.dumps({'error': 'Content-Type must be multipart/form-data'}), status=400, mimetype='application/json')

        audio_file = request.files.get('file')
        if not audio_file:
            return Response(json.dumps({'error': 'No file uploaded with key "file"'}), status=400, mimetype='application/json')

        min_confidence = float(request.form.get('min_confidence', 0.5))
        selected_model = request.form.get('model', 'BattyBirdNET-EU-256kHz')

        # 2. Save Temporary File
        temp_id = str(uuid.uuid4())
        ext = audio_file.filename.split('.')[-1] if '.' in audio_file.filename else 'wav'
        temp_path = os.path.join('/tmp', f"{temp_id}.{ext}")
        audio_file.save(temp_path)

        # 3. Configure Analyzer
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        analyzer_dir = os.path.join(base_dir, 'batty_birdnet_analyzer')

        # Default paths
        cfg.MODEL_PATH = os.path.join(analyzer_dir, 'checkpoints/V2.4/BirdNET_GLOBAL_6K_V2.4_Model_FP32.tflite')
        cfg.MDATA_MODEL_PATH = os.path.join(analyzer_dir, 'checkpoints/V2.4/BirdNET_GLOBAL_6K_V2.4_MData_Model_FP16.tflite')
        cfg.CODES_FILE = os.path.join(analyzer_dir, 'eBird_taxonomy_codes_2021E.json')
        
        # User Selected Model
        cfg.CUSTOM_CLASSIFIER = os.path.join(analyzer_dir, f'checkpoints/bats/v1.0/{selected_model}.tflite')
        cfg.LABELS_FILE = os.path.join(analyzer_dir, f'checkpoints/bats/v1.0/{selected_model}_Labels.txt')
        
        if not os.path.exists(cfg.CUSTOM_CLASSIFIER):
             # Fallback
             cfg.CUSTOM_CLASSIFIER = os.path.join(analyzer_dir, 'checkpoints/bats/v1.0/BattyBirdNET-EU-256kHz.tflite')
             cfg.LABELS_FILE = os.path.join(analyzer_dir, 'checkpoints/bats/v1.0/BattyBirdNET-EU-256kHz_Labels.txt')

        cfg.SAMPLE_RATE = 256000
        cfg.SIG_LENGTH = 1.0
        cfg.SIG_OVERLAP = 0.25
        cfg.MIN_CONFIDENCE = min_confidence
        
        cfg.LABELS = utils.readLines(cfg.LABELS_FILE)
        cfg.TRANSLATED_LABELS = cfg.LABELS

        # 4. Run Analysis
        success, results = analyze.analyzeFile((temp_path, cfg.get_config()))

        # 5. Generate Spectrogram
        sig, rate = audio.openAudioFile(temp_path, sample_rate=cfg.SAMPLE_RATE, duration=3.0)
        spec_base64 = generate_spectrogram(sig, rate)

        # 6. Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if not success:
            return Response(json.dumps({'error': 'Analysis failed'}), status=500, mimetype='application/json')

        # 7. Format Results
        formatted_results = []
        for timestamp, scores in results.items():
            if scores:
                top_hit = scores[0]
                if float(top_hit[1]) >= min_confidence:
                    formatted_results.append({
                        'timestamp': timestamp,
                        'species': top_hit[0],
                        'confidence': float(top_hit[1])
                    })

        return Response(json.dumps({
            'success': True,
            'filename': audio_file.filename,
            'results': formatted_results,
            'spectrogram': spec_base64
        }), status=200, mimetype='application/json', headers={'Access-Control-Allow-Origin': '*'})

    except Exception as e:
        return Response(json.dumps({'error': str(e)}), status=500, mimetype='application/json')

app = application
