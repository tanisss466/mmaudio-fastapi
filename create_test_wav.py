import wave
import struct

# Create a simple WAV file with a single tone
sample_rate = 44100
duration = 3  # seconds
frequency = 440  # Hz (A4 note)

# Create WAV file
with wave.open('test.wav', 'wb') as wav_file:
    # Set parameters
    wav_file.setnchannels(1)  # Mono
    wav_file.setsampwidth(2)  # 2 bytes per sample
    wav_file.setframerate(sample_rate)
    
    # Generate samples
    for i in range(duration * sample_rate):
        # Simple sine wave
        sample = int(32767.0 * 0.5)  # Just a constant value for simplicity
        packed_value = struct.pack('h', sample)
        wav_file.writeframes(packed_value)

print("Test WAV file created successfully!") 