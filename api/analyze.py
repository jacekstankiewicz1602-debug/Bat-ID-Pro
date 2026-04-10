import sys
import os
import json
import uuid
from werkzeug.formparser import MultiPartParser
from werkzeug.datastructures import FileStorage

# Add the root directory to sys.path to allow importing from BattyBirdNET-Analyzer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from BattyBirdNET_Analyzer import analyze
from BattyBirdNET_Analyzer import config as cfg
from BattyBirdNET_Analyzer import utils

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

        # Vercel's 'request' object for Python functions is often a WSGI-like object
        # but the specific structure depends on the runtime version.
        # We'll use werkzeug to parse the stream if available.
        parser = MultiPartParser()
        boundary = content_type.split('=')[-1]
        
        # In Vercel, the body might be in request.body or request.stream
        stream = getattr(request, 'stream', None) or getattr(request, 'body', None)
        if not stream:
             return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No data received'}),
                'headers': {'Content-Type': 'application/json'}
            }
            
        data, files, _ = parser.parse(stream, boundary, request.content_length)
        
        audio_file = files.get('file')
        if not audio_file:
             return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No file uploaded with key "file"'}),
                'headers': {'Content-Type': 'application/json'}
            }

        # 2. Save Temporary File
        temp_id = str(uuid.uuid4())
        ext = audio_file.filename.split('.')[-1] if '.' in audio_file.filename else 'wav'
        temp_path = os.path.join('/tmp', f"{temp_id}.{ext}")
        audio_file.save(temp_path)

        # 3. Configure Analyzer
        # Base directory of the repository
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        analyzer_dir = os.path.join(base_dir, 'BattyBirdNET-Analyzer')

        # Set paths in config
        cfg.MODEL_PATH = os.path.join(analyzer_dir, 'checkpoints/V2.4/BirdNET_GLOBAL_6K_V2.4_Model_FP32.tflite')
        cfg.LABELS_FILE = os.path.join(analyzer_dir, 'checkpoints/V2.4/BirdNET_GLOBAL_6K_V2.4_Labels.txt')
        cfg.MDATA_MODEL_PATH = os.path.join(analyzer_dir, 'checkpoints/V2.4/BirdNET_GLOBAL_6K_V2.4_MData_Model_FP16.tflite')
        cfg.CODES_FILE = os.path.join(analyzer_dir, 'eBird_taxonomy_codes_2021E.json')
        
        # Use specific Bat Classifier
        cfg.CUSTOM_CLASSIFIER = os.path.join(analyzer_dir, 'checkpoints/bats/v1.0/BattyBirdNET-EU-256kHz.tflite')
        cfg.LABELS_FILE = os.path.join(analyzer_dir, 'checkpoints/bats/v1.0/BattyBirdNET-EU-256kHz_Labels.txt')
        
        # Runtime settings for Bat detection (256kHz models)
        cfg.SAMPLE_RATE = 256000
        cfg.SIG_LENGTH = 1.0 # 144000 / 256000
        cfg.SIG_OVERLAP = 0.25
        cfg.MIN_CONFIDENCE = 0.5
        
        # Load labels
        cfg.LABELS = utils.readLines(cfg.LABELS_FILE)
        cfg.TRANSLATED_LABELS = cfg.LABELS

        # 4. Run Analysis
        success, results = analyze.analyzeFile((temp_path, cfg.get_config()))

        # 5. Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if not success:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Analysis failed', 'results': results}),
                'headers': {'Content-Type': 'application/json'}
            }

        # 6. Format and Return Results
        formatted_results = []
        for timestamp, scores in results.items():
            # Get the top species for this segment
            # 'scores' is a list of [label, confidence]
            if scores:
                top_hit = scores[0]
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
                'results': formatted_results
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*' # CORS for frontend
            }
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {'Content-Type': 'application/json'}
        }
