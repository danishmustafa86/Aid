# utils/voice_utils.py
import os
from elevenlabs.client import ElevenLabs
from elevenlabs import play

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

def speech_to_text(audio_file_path: str) -> str:
    """
    Convert voice input into text using ElevenLabs STT.
    """
    with open(audio_file_path, "rb") as f:
        transcript = client.speech_to_text.convert(
            model_id="scribe_v1",
            file=f,
        )
    return transcript.text

def text_to_speech(text: str, voice_id="JBFqnCBsd6RMkjVDRZzb", save_path="output.mp3") -> str:
    """
    Convert agent text reply into speech and save as an MP3 file.
    """
    try:
        # Split long text into chunks to avoid API limits
        max_chunk_length = 1000  # Adjust based on your ElevenLabs plan
        text_chunks = [text[i:i+max_chunk_length] for i in range(0, len(text), max_chunk_length)]
        
        all_audio_chunks = []
        
        for i, chunk in enumerate(text_chunks):
            print(f"Processing text chunk {i+1}/{len(text_chunks)}: {len(chunk)} characters")
            
            audio = client.text_to_speech.convert(
                text=chunk,
                voice_id=voice_id,
                model_id="eleven_turbo_v2_5",
                output_format="mp3_44100_128",
            )
            
            # Collect all audio chunks
            chunk_data = b""
            for audio_chunk in audio:
                if audio_chunk:
                    chunk_data += audio_chunk
            all_audio_chunks.append(chunk_data)
        
        # Combine all audio chunks
        with open(save_path, "wb") as f:
            for chunk_data in all_audio_chunks:
                f.write(chunk_data)
        
        print(f"Audio file saved successfully: {save_path} ({len(all_audio_chunks)} chunks)")
        return save_path
        
    except Exception as e:
        print(f"Error in text_to_speech: {str(e)}")
        # Fallback: create a simple audio file or return empty
        with open(save_path, "wb") as f:
            f.write(b"")  # Empty file as fallback
        return save_path
