import sys
import os
import json
import uuid
import base64
import io
import numpy as np
from werkzeug.formparser import MultiPartParser
from PIL import Image

# Add the root directory to sys.path to allow importing from BattyBirdNET-Analyzer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from BattyBirdNET_Analyzer import analyze
from BattyBirdNET_Analyzer import config as cfg
from BattyBirdNET_Analyzer import utils
from BattyBirdNET_Analyzer import audio

def generate_spectrogram(sig, rate):
    """Generates a base64 encoded spectrogram PNG image."""
    import librosa
    
    # Compute Mel-spectrogram
    # For bats, we use higher frequency resolution
    S = librosa.feature.melspectrogram(y=sig, sr=rate, n_mels=128, fmax=rate/2)
    S_dB = librosa.power_to_db(S, ref=np.max)
    
    # Normalize to 0-255
    S_dB_norm = ((S_dB - S_dB.min()) / (S_dB.max() - S_dB.min()) * 255).astype(np.uint8)
    
    # Create an image using a "Magma"-like color mapping
    # Simple mapping: 0 (black/dark) -> 255 (yellow/bright)
    # We can create a LUT for better visual quality
    lut = np.zeros((256, 3), dtype=np.uint8)
    for i in range(256):
        # Fake Magma: dark purple -> red -> orange -> yellow
        lut[i] = [
            int(min(255, i * 1.5)), 
            int(min(255, i * 0.8)), 
            int(min(255, i * 0.3))
        ]
    
    # Apply colormap
    img_data = lut[S_dB_norm]
    # Flip vertically so low frequencies are at the bottom
    img_data = np.flipud(img_data)
    
    img = Image.fromarray(img_data)
    
    # Save to buffer
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def handler(request):
    if request.method != 'POST':
        return {
            'statusCode': 405,
            'body': json.dumps({'error': 'Method not allowed. Use POST.'}),
            'headers': {'Content-Type': 'application/json'}
        }

    try:
        # 1. Handle Multipart Upload
        content_type = request.headers.get('Content-Type', '')
        if 'multipart/form-data' not in content_type:
             return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Content-Type must be multipart/form-data'}),
                'headers': {'Content-Type': 'application/json'}
            }

        parser = MultiPartParser()
        boundary = content_type.split('=')[-1]
        stream = getattr(request, 'stream', None) or getattr(request, 'body', None)
        
        if not stream:
             return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No data received'}),
                'headers': {'Content-Type': 'application/json'}
            }
            
        form_data, files, _ = parser.parse(stream, boundary, request.content_length)
        
        audio_file = files.get('file')
        if not audio_file:
             return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No file uploaded with key "file"'}),
                'headers': {'Content-Type': 'application/json'}
            }

        # Extra Parameters
        min_confidence = float(form_data.get('min_confidence', 0.5))
        selected_model = form_data.get('model', 'BattyBirdNET-EU-256kHz')

        # 2. Save Temporary File
        temp_id = str(uuid.uuid4())
        ext = audio_file.filename.split('.')[-1] if '.' in audio_file.filename else 'wav'
        temp_path = os.path.join('/tmp', f"{temp_id}.{ext}")
        audio_file.save(temp_path)

        # 3. Configure Analyzer
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        analyzer_dir = os.path.join(base_dir, 'BattyBirdNET-Analyzer')

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
        # Load a few seconds for the visual
        sig, rate = audio.openAudioFile(temp_path, sample_rate=cfg.SAMPLE_RATE, duration=3.0)
        spec_base64 = generate_spectrogram(sig, rate)

        # 6. Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if not success:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Analysis failed'}),
                'headers': {'Content-Type': 'application/json'}
            }

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

        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'filename': audio_file.filename,
                'results': formatted_results,
                'spectrogram': spec_base64
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {'Content-Type': 'application/json'}
        }
