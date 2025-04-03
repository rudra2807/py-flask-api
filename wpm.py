import speech_recognition as sr
import math
from pydub import AudioSegment
from pydub.silence import detect_silence
import os
import re

def analyze_audio_metrics(audio_file_path,
                          min_silence_len=500,   # minimum silence length in ms
                          silence_thresh=-40,    # silence threshold (in dBFS)
                          filler_list=None,
                          filler_avg_duration=0.3):  # estimated duration per filler in sec
    """
    Analyze the audio file to calculate various speech metrics:
      - Detect and count filler words.
      - Detect pauses (silent segments) and calculate speaking time.
      - Compute words-per-minute (WPM) including and excluding fillers.
    """
    # Define a default list of common fillers if none provided
    if filler_list is None:
        filler_list = ["um", "uh", "er", "ah", "like", "you know"]

    # Load the audio file using pydub
    try:
        audio_segment = AudioSegment.from_file(audio_file_path)
    except Exception as e:
        return f"Error loading audio file: {e}"

    total_duration_sec = audio_segment.duration_seconds

    # Detect silent segments; each range is [start, end] in ms
    silence_ranges = detect_silence(audio_segment,
                                    min_silence_len=min_silence_len,
                                    silence_thresh=silence_thresh)
    # Total silence duration in seconds
    total_silence_duration_sec = sum((end - start) for start, end in silence_ranges) / 1000.0

    # Calculate speaking time (total duration minus detected silence)
    speaking_time_sec = total_duration_sec - total_silence_duration_sec

    # Use SpeechRecognition to obtain a transcript from the audio
    recognizer = sr.Recognizer()
    transcript = ""
    try:
        with sr.AudioFile(audio_file_path) as source:
            audio_data = recognizer.record(source)
            transcript = recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        transcript = ""
    except sr.RequestError as e:
        transcript = f"Request error: {e}"

    # Process the transcript for word and filler counts
    words = re.findall(r"\w+", transcript.lower())
    total_word_count = len(words)

    filler_count = 0
    for filler in filler_list:
        # Use regex word-boundary matching to avoid partial matches
        filler_count += len(re.findall(r'\b' + re.escape(filler) + r'\b', transcript.lower()))

    # Estimate total duration spent on fillers
    total_filler_duration_sec = filler_count * filler_avg_duration

    # Calculate actual speaking duration by excluding filler durations
    actual_speaking_duration_sec = speaking_time_sec - total_filler_duration_sec
    if actual_speaking_duration_sec < 0:
        actual_speaking_duration_sec = 0

    # Compute speaking rates (words per minute)
    speaking_time_min = speaking_time_sec / 60.0 if speaking_time_sec > 0 else 0
    actual_speaking_time_min = actual_speaking_duration_sec / 60.0 if actual_speaking_duration_sec > 0 else 0

    rate_including_fillers = math.floor(total_word_count / speaking_time_min) if speaking_time_min > 0 else 0
    rate_excluding_fillers = math.floor((total_word_count - filler_count) / actual_speaking_time_min) if actual_speaking_time_min > 0 else 0

    return {
        "total_duration_sec": total_duration_sec,
        "total_silence_duration_sec": total_silence_duration_sec,
        "speaking_time_sec_excluding_pauses": speaking_time_sec,
        "transcript": transcript,
        "total_word_count": total_word_count,
        "filler_count": filler_count,
        "estimated_filler_duration_sec": total_filler_duration_sec,
        "actual_speaking_duration_sec_excluding_fillers": actual_speaking_duration_sec,
        "rate_including_fillers_wpm": rate_including_fillers,
        "rate_excluding_fillers_wpm": rate_excluding_fillers,
        "silence_ranges_ms": silence_ranges
    }

def main():
    # Prompt the user for the audio file path
    audio_file = input("Enter the path to the audio file: ").strip()

    # Check if the file exists
    if not os.path.exists(audio_file):
        print("The provided audio file path does not exist. Please check the path and try again.")
        return

    # Analyze the provided audio file to compute speech metrics
    result = analyze_audio_metrics(audio_file)

    # Check if the result indicates an error
    if isinstance(result, str):
        print(result)
        return

    # Print the results
    print("\n=== Analysis Results ===")
    print("Total Duration (sec):", result["total_duration_sec"])
    print("Total Silence Duration (sec):", result["total_silence_duration_sec"])
    print("Speaking Time (sec) excluding pauses:", result["speaking_time_sec_excluding_pauses"])
    print("Actual Speaking Duration (sec) excluding fillers:", result["actual_speaking_duration_sec_excluding_fillers"])
    print("Total Word Count:", result["total_word_count"])
    print("Filler Count:", result["filler_count"])
    print("Rate (WPM) including fillers:", result["rate_including_fillers_wpm"])
    print("Rate (WPM) excluding fillers:", result["rate_excluding_fillers_wpm"])
    print("Transcript:", result["transcript"])
    print("Silence Ranges (ms):", result["silence_ranges_ms"])

if __name__ == "__main__":
    main()
