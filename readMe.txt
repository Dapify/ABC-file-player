ABC File Player
Created by Dónal Gilligan

A Python-based music synthesizer that converts ABC notation files into playable audio with various sound customization options.

FEATURES:
- Multiple Waveforms: Sine, Square, Sawtooth, and Triangle waves
- Customizable Parameters: Adjustable loudness, BPM, and pitch shifting
- Background Noise: Optional white, pink, or brown noise layers
- Audio Mixing: Blend with external WAV files
- ADSR Envelope: Smooth note transitions with attack, decay, sustain, and release
- Real-time Playback: Instant audio generation and playback
- WAV Export: Save your creations as audio files

REQUIREMENTS:

Python Version:
- Python 3.10.5 (required for PyAudio compatibility)

Libraries:
- pyaudio
- soundfile
- numpy
- scipy
- os
- sys
- time
- pickle

INSTALLATION:
1. Clone or download the project files
2. Install required dependencies:
   pip install pyaudio soundfile numpy scipy
3. Run the application:
   python abc_player.py

USAGE:

Menu Options:
1. Select Waveform - Choose from Sine, Square, Sawtooth, or Triangle waves
2. Set Loudness - Adjust volume between 0.0 and 1.0
3. ABC File Path - Specify path to your ABC notation file
4. Change BPM - Set playback speed (40-240 BPM)
5. Shift Pitch - Transpose notes by semitones
6. Background Noise - Add white, pink, or brown noise
7. Mix with WAV - Blend with external audio files
8. Play File - Generate and play audio in real-time
9. Save as WAV - Export audio to file
10. Exit - Quit the application

INCLUDED FILES:
- ABCTest.abc - Default test file
- chineseDance.abc - Sample music file

ABC FILE FORMAT:
The player supports standard ABC notation including:
- Notes: A-G, a-g (two octaves)
- Rests: z
- Duration modifiers: Numbers (A2) and fractions (A/2)
- Basic headers: Key (K:) and Note Length (L:)

TECHNICAL DETAILS:
- Sample Rate: 44.1 kHz (CD quality)
- Audio Format: 16-bit PCM for playback, 32-bit float for processing
- Platform: Developed and tested on Windows 11
- IDE: Visual Studio Code

FILE STRUCTURE:
ABC-file-player/
├── abc_player.py          # Main application
├── ABCTest.abc           # Default ABC file
├── chineseDance.abc      # Sample music file
└── saved-files/          # Directory for exported WAV files

TROUBLESHOOTING:

Common Issues:
1. PyAudio Installation: Ensure Python 3.10.5 is used for compatibility
2. File Not Found: Verify ABC file paths are correct
3. Audio Playback: Check system audio drivers and volume

Error Handling:
- The application includes comprehensive error handling for file operations
- Invalid inputs are caught with user-friendly messages
- Default values provided for missing configurations

DEVELOPMENT:
Created by Dónal Gilligan

This project demonstrates:
- Digital audio synthesis
- ABC notation parsing
- Real-time audio processing
- User interface design for audio applications