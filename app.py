from flask import Flask, request, jsonify
import os
import uuid
from wpm import analyze_audio_metrics  # Import the function from your existing module
from pydub import AudioSegment

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/analyze', methods=['POST'])
def analyze():
    # Check if a file part is present in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save the uploaded file to a temporary location
    filename = f"{uuid.uuid4()}_{file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    try:
        # Convert the uploaded .aac file to .wav using pydub.
        # Increase analyzeduration and probesize to help ffmpeg parse the file.
        audio = AudioSegment.from_file(filepath)
        wav_filepath = "myWav.wav"
        audio.export(wav_filepath, format="wav")
        
        # Process the converted .wav file using your existing function
        result = analyze_audio_metrics(wav_filepath)
    except Exception as e:
        # Remove temporary files in case of an error
        if os.path.exists(filepath):
            os.remove(filepath)
        if 'wav_filepath' in locals() and os.path.exists(wav_filepath):
            os.remove(wav_filepath)
        return jsonify({'error': str(e)}), 500

    # Cleanup: remove both the original and converted files
    if os.path.exists(filepath):
        os.remove(filepath)
    if os.path.exists(wav_filepath):
        os.remove(wav_filepath)
    
    # Return the analysis results as JSON
    return jsonify(result)

@app.route('/test', methods=['GET'])
def test():
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
