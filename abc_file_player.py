#Created by Dónal Gilligan

#python version 3.10.5 required for pyaudio to work
#Used layout for menu code for this assignment in my code but modified to fit criteria
#Utilised concepts from sample code provided on moodle page and AI for planning stages, time estimation and pointing in the right direction for initial bug fixing

import os
from pickle import TRUE
import sys
import time
import pyaudio
import soundfile as sf
import numpy as np
from scipy import signal

#I added base variables here so you can play and save the track instantly
selectedWaveform = "sine"
selectedLoudness = 1
ABCFilePath = "ABCTest.abc"
selectedBPM = 100
pitchInput = 0  
backgroundInput = 0
isMixing = False
mixingWav = ""

def cls():
    os.system('cls' if os.name=='nt' else 'clear')

def backgroundNoiseGenerator(duration):
    sampleRate = 44100 #this is the standard sample rate for CDs
    sampleNum = int(duration*sampleRate) #amount of samples found by how long the track is

    if backgroundInput==1: #this is white noise which is completly random static noise.
        noise = np.random.normal(0, 0.3, sampleNum)
    elif backgroundInput==2: #this is pink noise which has more bass and less treble than white noise
        noise = np.random.normal(0, 1, sampleNum) #generate white noise first and then filter it
        b = [0.05, 0.12, 0.25] #these filter coefficients shape the white noise into pink noise by filtering high frequencies more than low frequencies
        a = [1, -0.75, 0.6]
        noise = signal.lfilter(b, a, noise) * 0.2 #apply the coefficients to make pink noise and scale it down
    elif backgroundInput==3: #this is brown noise which has even more bass and less treble than pink noise
        noise = np.cumsum(np.random.normal(0, 1, sampleNum)) #generate brown noise by integrating white noise
        noise = noise - np.mean(noise) 
        noise = noise / np.max(np.abs(noise)) * 0.4 
    return noise


def waveformGenerator(frequency, duration, sampleRate = 44100):
    if frequency == 0: #silence or rest when freq 0
        return np.zeros(int(duration * sampleRate)) #make a list of zeros with the 

    t = np.linspace(0, duration, int(sampleRate * duration), endpoint=False)

    if selectedWaveform == "sine":
        wave = np.sin(2 * np.pi * frequency * t) #formula for all wave types adapted from previous examples
    elif selectedWaveform == "square":
        wave = signal.square(2 * np.pi * frequency * t)
    elif selectedWaveform == "sawtooth":
        wave = signal.sawtooth(2 * np.pi * frequency * t)
    elif selectedWaveform == "triangle":
        wave = signal.sawtooth(2 * np.pi * frequency * t, width=0.5)
    else:
        wave = np.sin(2 * np.pi * frequency * t)

    return wave * selectedLoudness #make sure the loudness is added on the end

def ADSR(noteAudio): #this function is to ensure that the sound being generated isnt harsh
    length = len(noteAudio)
    if length == 0:
        return noteAudio

    envelope = np.ones(length) #initialize envelope array with ones

    attack=0.05 #attack is how fast the note reaches full volume
    decay=0.15 #decay is how fast the note drops to the sustain level
    sustain=0.58 #sustain is the level the note stays at until release
    release=0.3 #release is how fast the note fades to silence

    attackLength = int(attack * length) #make lengths for each section
    decayLength = int(decay * length)
    releaseLength = int(release * length)
    sustainLength = max(0, length - attackLength - decayLength - releaseLength) #sustain length is whatever is left over

    if attackLength > 0:
        envelope[:attackLength] = np.linspace(0, 1, attackLength) #attack goes from 0 to 1 in volume

    if decayLength > 0:
        start = attackLength
        end = attackLength + decayLength
        envelope[start:end] = np.linspace(1, sustain, decayLength) #decay goes from 1 to the set sustain level

    if sustainLength > 0:
        start = attackLength + decayLength
        end = start + sustainLength
        envelope[start:end] = sustain #sustain stays at the same level throughout its the baseline until release

    if releaseLength > 0:
        start = length - releaseLength
        envelope[start:] = np.linspace(sustain, 0, releaseLength) #release goes from sustain level to 0 at the end

    return noteAudio * envelope #apply the envelope to the note audio
    

def ABCParser(ABCFilePath):
    try:
        with open(ABCFilePath, 'r') as f:
            lines = f.readlines() #read in the lines of the file
        
        kIN = False #set to true when in the K: section
        notesAndDuration = []
        nDuration = 0.25 #default duration for each note is a quarter note

        for i in lines:
            i = i.strip()
            if not i or i.startswith('%'): #ignore empty lines and comments
                continue

            if len(i) > 1 and i[1] == ':': #iterate through header lines until K:
                if i[0] == 'K':
                    kIN = True #we are now in the K: section so we can start reading notes
                elif i[0] == 'L': #check for default note length line
                    if '/' in i:
                        parts = i.split(':')[1].split('/') #split it by the colon and then the slash to get numerator and denominator
                        if len(parts) == 2:
                            numerator, denominator = parts #extract numerator and denominator
                            nDuration = float(numerator) / float(denominator) #calculate default note duration
                continue

            if kIN:
                # Process the music line character by character
                j = 0
                while j < len(i): #iterate through each character in the line until the end
                    char = i[j] 
                    
                    # Skip bar lines, spaces, and colons
                    if char in '|: \t':
                        j += 1
                        continue
                    
                    # Check if this is a note (A-G, a-g) or rest (z)
                    if char.upper() in 'CDEFGAB' or char in 'zZ': #if there is a note or rest found
                        noteDict = {'pitch': char, 'duration': nDuration} #initialize note info dictionary
                        
                        # Look ahead for duration modifiers
                        j += 1
                        durMulti = 1.0 #to extend the note if needed
                        durDiv = 1.0 #to shorten the note
                        
                        while j < len(i):
                            next_char = i[j]
                            
                            # Number after note (e.g., A2 = 2x duration)
                            if next_char.isdigit():
                                num_str = ''
                                while j < len(i) and i[j].isdigit():
                                    num_str += i[j]
                                    j += 1
                                durMulti = float(num_str) #set the multiplier for duration
                                break
                                
                            # Slash for fractions (e.g., A/2 = half duration)
                            elif next_char == '/':
                                j += 1
                                if j < len(i) and i[j].isdigit():
                                    div_str = ''
                                    while j < len(i) and i[j].isdigit():
                                        div_str += i[j]
                                        j += 1
                                    durDiv = float(div_str) #set the divisor for duration
                                break
                                
                            # Other characters don't modify duration
                            else:
                                break
                        
                        # Calculate final duration
                        noteDict['duration'] = nDuration * durMulti / durDiv
                        notesAndDuration.append(noteDict)
                        
                    else:
                        j += 1
        
        return notesAndDuration
    
    except Exception as e:
        print("Error parsing ABC file", e) #error handling
        return []
    
def convertNtoF(noteC): #convert note character to frequency value
    frequency_dict = { #applied hardcoded frequencies for notes found from resources given in moodle 
        'C': 261.63, 'D': 293.66, 'E': 329.63, 'F': 349.23, 
        'G': 392.00, 'A': 440.00, 'B': 493.88,
        'c': 523.25, 'd': 587.33, 'e': 659.25, 'f': 698.46, #two octaves
        'g': 783.99, 'a': 880.00, 'b': 987.77
    }

    if noteC in frequency_dict: #check if note is in dictionary
        bFreq = frequency_dict[noteC]

        if pitchInput != 0: 
            bFreq = bFreq * (2**(pitchInput/12)) #pitch shifting formula is the twelth root of 2 raised to the number of semitones shifted

        return bFreq
    
def playing(audio, sampleRate=44100):
    try:
        p = pyaudio.PyAudio()

        stream = p.open(format=pyaudio.paInt16, #this was adapted from previous examples but modified for this use case
                       channels=1,
                       rate=sampleRate,
                       output=True)

        convToBytes = (audio * 32767).astype(np.int16).tobytes() #convert float32 audio to int16 for pyaudio 32767 is max value for int16
        stream.write(convToBytes)

        stream.stop_stream()
        stream.close()
        p.terminate()
        return True
    except:
        print("Error playing audio")
        return False
        

def waveform():
    cls()
    global selectedWaveform
    print("Selecting a waveform")
    print("1) Sine wave\n2) Square wave\n3) Sawtooth wave\n4) Triangle Wave")
    while True:
        waveformInput = int(input("Select waveform 1-4: "))
        if waveformInput == 1:
            print("Sine wave waveform selected")
            selectedWaveform = "sine"
            time.sleep(3) #sleep gives the user time to read the output
            break
        elif waveformInput == 2:
            print("Square wave waveform selected")  
            selectedWaveform = "square"
            time.sleep(3)
            break
        elif waveformInput == 3: 
            print("Sawtooth wave waveform selected")  
            selectedWaveform = "sawtooth"
            time.sleep(3)
            break  
        elif waveformInput == 4:
            print("Triangle wave waveform selected")
            selectedWaveform = "triangle"
            time.sleep(3)   
            break
        else:
            print("invalid selection")
            time.sleep(3)

def loudness():
    cls()
    global selectedLoudness
    print("Setting the loudness")
    while True:
        try:
            loudnessValue = float(input("Input the loudness value between 0.0 and 1.0: "))
        except:
            print("Must be a Float")
            continue
        if loudnessValue>=0.0 and loudnessValue<=1.0:
            print("Loudness set to", loudnessValue)
            selectedLoudness = loudnessValue
            time.sleep(3)
            break
        else:
            print("invalid selection")

def abc():
    cls()
    global ABCFilePath
    print("Indicating the ABC file path")
    while True:
        filePath = input("Input the ABC file path here: ")
        if os.path.exists(filePath):
            if filePath.endswith(".abc"): #has to be an abc file
                ABCFilePath = filePath
                print("File exists and is ready for use")
                print("Inputed selection: ",ABCFilePath)
                time.sleep(3)
                break
            else:
                print("Must be a .abc file. Try again")
        else:
            print("File path is invalid or does not exist. Try again")
    

def bpm():
    cls()
    global selectedBPM
    print("Changing speed (BPM)")
    while True:
        try:
            bpm = int(input("Input the BPM value here (between 40 and 240 BPM) ")) #anything slower or faster is not a valid tempo for music
        except:
            print("Must be a integer number")
            continue
        if bpm >= 40 and bpm <= 240:
            selectedBPM = bpm
            print("BPM selection: ",selectedBPM)
            time.sleep(3)
            break
        else:
            print("Please enter a valid BPM within the range")

def pitch():
    cls()
    global pitchInput
    print("Shifting pitch")
    print("Input the pitch shift value here (in semitones)")
    while True:
        pitchShift = input()
        if pitchShift.strip("-").isdigit(): #allow negative and positive integers
            print("Pitch Shift selection: ",pitchShift," semitones")
            pitchInput =  int(pitchShift) #store as integer
            time.sleep(3)
            break
        print("Please enter a valid number (in semitones)")

def backgroundNoise():
    cls()
    global backgroundInput
    print("Adding background noise")
    print("1) White noise \n2) Pink noise \n3) Brown noise \n0) None") 
    while True: #until a valid option is selected
        backgroundNoise = input("Choose 0-3: ").lower()
        if backgroundNoise == "white" or backgroundNoise == "1": #both text and number inputs accepted 
            print("White Noise selected")
            backgroundInput = 1
            time.sleep(3)
            break
        elif backgroundNoise == "pink" or backgroundNoise == "2":
            backgroundInput = 2
            print("Pink Noise selected")
            time.sleep(3)
            break
        elif backgroundNoise == "brown" or backgroundNoise == "3":
            print("Brown Noise selected")
            backgroundInput = 3
            time.sleep(3)
            break
        elif backgroundNoise == "none" or backgroundNoise == "0": #allow user not to add background noise
            print("No Background Noise selected")
            backgroundInput = 4
            time.sleep(3)
            break
        else:
            print("Please enter a valid type (White, Pink, Brown or None [1-4])")

def mixWav():
    cls()
    global isMixing
    global mixingWav
    isMixing = True #set mixing flag to true
    print("Mix within an external WAV file")
    wavFile = input("Enter the WAV file path here: ")
    if os.path.exists(wavFile):
            if wavFile.endswith(".wav"): #has to be a wav file
                print("WAV file found and ready for mixing")
                mixingWav = wavFile
                time.sleep(3)
                return wavFile
    else:
        print("File path is invalid or does not exist. Try again")
        time.sleep(3)
        return

def play():
    cls()
    print("Playing the file")
    if ABCFilePath == "ABCTest.abc":
        print("Using default .abc file")
        time.sleep(3)
    else:
        print("Using ",ABCFilePath," file")
        time.sleep(3)

    try:
        notes = ABCParser(ABCFilePath) #get the notes from the file
        sampleRate = 44100

        audioArray = np.array([], dtype=np.float32) #initialize empty array for the audio in float32 format

        i = 0
        for note_info in notes:
            note = note_info['pitch'] #get the note character
            print("Playing: ",note)
            note_duration = note_info['duration'] * (60/selectedBPM) * 4  # Convert to seconds
            
            if note in 'zZ':
                rest_audio = np.zeros(int(note_duration * sampleRate)) #silence for rests
                audioArray = np.concatenate([audioArray, rest_audio]) #add it to the audio array
            else: 
                frequency = convertNtoF(note) #first initialize note to frequency conversion
                note_audio = waveformGenerator(frequency, note_duration, sampleRate) #then generate the waveform
                note_audio = ADSR(note_audio) #apply ADSR envelope
                audioArray = np.concatenate([audioArray, note_audio.astype(np.float32)]) # convert to float32 and add to array using concatenation
                    
            # Add gap between notes except after last one
            if i < len(notes) - 1:
                gap = np.zeros(int(0.05 * sampleRate)) #short gap of silence between notes
                audioArray = np.concatenate([audioArray, gap]) #add it to the audio array
        
            i += 1 #iterate counter
        
        if backgroundInput != 0: #if background noise is selected
            print("Adding background noise to track")
            total_duration = len(audioArray) / sampleRate  #calculate total duration of the audio
            background_noise = backgroundNoiseGenerator(total_duration) #generate and mix the background noise
            audioArray = (audioArray * 0.7) + (background_noise * 0.3)

        if isMixing and mixingWav: #if mixing flag is true AND we have a valid file
            try:
                print("Mixing with external WAV file:", mixingWav)
                wavData, wavSampleRate = sf.read(mixingWav, dtype='float32') #read in the wav file to mix with
                
                if len(wavData.shape) > 1: # Convert stereo to mono if needed
                    wavData = np.mean(wavData, axis=1) #convert to mono by averaging channels

                if wavSampleRate != sampleRate: #resample if sample rates dont match
                    num_samples = int(len(wavData) * sampleRate / wavSampleRate) #calculate new number of samples by ratio of sample rates
                    wavData = signal.resample(wavData, num_samples) 
                
                # Match lengths and mix
                min_length = min(len(audioArray), len(wavData))
                audioArray = audioArray[:min_length] #minimize both arrays to the shortest length
                wavData = wavData[:min_length]
                
                # Mix with equal balance
                audioArray = (audioArray * 0.5) + (wavData * 0.5) #mix the two audio arrays and have it ready for playing
                print("Successfully mixed with WAV file")
                
            except Exception as e:
                print("Error during mixing")

        playing(audioArray, sampleRate) #play the final audio array from the function

    except Exception as e:
        print("Error playing file: ", e)
    
    time.sleep(3)


def saveWav(): #this is functionally almost identical to play function but saves a given file name instead of plays
    cls()
    print("Saving the music as a WAV file")
    saveFile = input("Enter file name here: ")
    cls()
    print("Playing the file")
    if ABCFilePath == "ABC-file-path/ABCTest.abc":
        print("Using default .abc file")
        time.sleep(3)
    else:
        print("Using ",ABCFilePath," file")
        time.sleep(3)

    try:
        notes = ABCParser(ABCFilePath) #get the notes from the file
        sampleRate = 44100

        audioArray = np.array([], dtype=np.float32) #initialize empty array for the audio in float32 format

        i = 0
        for note_info in notes:
            note = note_info['pitch'] #get the note character
            print("Playing: ",note)
            note_duration = note_info['duration'] * (60/selectedBPM) * 4  # Convert to seconds
            
            if note in 'zZ':
                rest_audio = np.zeros(int(note_duration * sampleRate)) #silence for rests
                audioArray = np.concatenate([audioArray, rest_audio]) #add it to the audio array
            else: 
                frequency = convertNtoF(note) #first initialize note to frequency conversion
                note_audio = waveformGenerator(frequency, note_duration, sampleRate) #then generate the waveform
                note_audio = ADSR(note_audio) #apply ADSR envelope
                audioArray = np.concatenate([audioArray, note_audio.astype(np.float32)]) # convert to float32 and add to array using concatenation
                    
            # Add gap between notes except after last one
            if i < len(notes) - 1:
                gap = np.zeros(int(0.05 * sampleRate)) #short gap of silence between notes
                audioArray = np.concatenate([audioArray, gap]) #add it to the audio array
        
            i += 1 #iterate counter
        
        if backgroundInput != 0: #if background noise is selected
            print("Adding background noise to track")
            total_duration = len(audioArray) / sampleRate  #calculate total duration of the audio
            background_noise = backgroundNoiseGenerator(total_duration) #generate and mix the background noise
            audioArray = (audioArray * 0.7) + (background_noise * 0.3)

        if isMixing and mixingWav: #if mixing flag is true AND we have a valid file
            try:
                print("Mixing with external WAV file:", mixingWav)
                wavData, wavSampleRate = sf.read(mixingWav, dtype='float32') #read in the wav file to mix with
                
                if len(wavData.shape) > 1: # Convert stereo to mono if needed
                    wavData = np.mean(wavData, axis=1) #convert to mono by averaging channels

                if wavSampleRate != sampleRate: #resample if sample rates dont match
                    num_samples = int(len(wavData) * sampleRate / wavSampleRate) #calculate new number of samples by ratio of sample rates
                    wavData = signal.resample(wavData, num_samples) 
                
                # Match lengths and mix
                min_length = min(len(audioArray), len(wavData))
                audioArray = audioArray[:min_length] #minimize both arrays to the shortest length
                wavData = wavData[:min_length]
                
                # Mix with equal balance
                audioArray = (audioArray * 0.5) + (wavData * 0.5) #mix the two audio arrays and have it ready for playing
                print("Successfully mixed with WAV file")
                
            except Exception as e:
                print("Error during mixing")

        saveFile = "saved-files/"+saveFile #ammended to save in the ABC-file-player folder
        sf.write(saveFile,audioArray,sampleRate)#write the file to the given path
        print("Save succesful. File saved in:",saveFile)

    except Exception as e:
        print("Error saving file: ", e)
    
    time.sleep(3)

def exit():
    cls()    
    yes_no = input("Are you sure you want to exit the program?(y=yes/n=no)")
    if yes_no=='y':
        sys.exit()



if __name__ == "__main__":
    while TRUE:
        cls() #menu edited from given code
        print("1) Selecting a waveform")
        print("2) Setting the loudness")
        print("3) Indicating the ABC file path")
        print("4) Changing speed (BPM)")
        print("5) Shifting pitch")
        print("6) Adding background noise")
        print("7) Mixing within an external WAV file")
        print("8) Playing the file")
        print("9) Saving the music as WAV file")
        print("10) Exit")
        inputText = input("Please select a number between 1 and 10: ")
        match inputText:
            case '1':
                waveform()
            case '2':
                loudness()
            case '3':
                abc()
            case '4':
                bpm()
            case '5':
                pitch()            
            case '6':
                backgroundNoise() 
            case '7':
                mixWav()
            case '8':
                play()
            case '9':
                saveWav()
            case '10':
                exit()           
            case _:
                cls()
                print("The input value is not valid. Please try again.")
                input()