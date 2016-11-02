# TODO: Post-Mortem -- Well, as a full-blown game this is probably a flub.  The computer can't respond quickly enough for some notes because when they are played quickly, the notes start to blur together, particularly with the violin when the notes aren't coming out with a consistent pitch each time a beginner tries to play them.  If I were playing single notes on a fretted instrument this might work, but one note at a time on guitar or ukulele is lame.  I also find it really difficult to pay attention to the game and my violin technique at the same time.  If I can't do that, despite being a smart person with some musical talent, I can't expect that many other beginners will be able to do it.  They would have to be some kind of violin prodigy who doesn't need my game in the first place.  And this makes me question what good making such a game would be to begin with; the violin is just a fundamentally more difficult instrument than the guitar, which has some learning games for it.

# TODO: What I can do is "refurbish" this game into a smaller game which teaches people how to read sheet music.  Without it being able to instruct someone in how to play full songs in real time and give a reliable score back, it would not warrant becoming a really large project, but I can still do something fun and possibly useful with this code.

# from __future__ import division # Importing this and print could be necessary for later applications in Python 2.7.
#from matplotlib.mlab import find # Don't remember why I had this anymore.
import sys, math, pyaudio, sched, time, threading, audioop, re, numpy as np # Importing time next!

min_freq = 133.0; max_freq = 1000.0 # I had 96 min originally, seems unnecessarily low for playing but might be good to go low for tuning.
#min_period = int(44100 / max_freq + 0.5); max_period = int(44100 / min_freq + 0.5)
min_period = int(48000 / max_freq + 0.5); max_period = int(48000 / min_freq + 0.5)
sens = 0.1
note_names_list = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']
run = 1 # This will end the main loop
songiter = 0; note = "A"; notes_played = []; score = 0; totalscore = 0
s = sched.scheduler(time.time, time.sleep) # Constant variables, sampling rate of 44100 isn't applied as a variable.  I've changed the 44100 to 48000 to try and improve the accuracy but saw little to no difference.

def compute_minpos(amd): # Compute the minimum position with the average magnitude difference.
    amd2 = amd[min_period:max_period]
    min_pos = amd2.argmin(); max_pos = amd2.argmax()
    min_val = amd2[min_pos]; max_val = amd2[max_pos]
    offset = int(sens * float((max_val - min_val))) + min_val
    p = min_period
    while ((p <= max_period) & (amd[p] > offset)):
        p = p + 1
    search_length = min_period / 2
    min_val = amd[p]
    minpos = p
    i = p
    while ((i < p + search_length) & (i <= max_period)):
        i = i + 1
        if (amd[i] < min_val):
            min_val = amd[i]
            minpos = i
            return minpos
        else:
            return None

def AMDF(frame, maxShift): # Average magnitude difference frame.
    frameSize = len(frame)
    amd = np.zeros(maxShift)
    for i in range(1, int(maxShift)):
        AuxFrame1 = frame[0:(frameSize - i)]
        AuxFrame2 = frame[i:frameSize]
        AuxFrame1 = np.asarray(AuxFrame1)
        AuxFrame2 = np.asarray(AuxFrame2)
        diff = ((AuxFrame1) - (AuxFrame2))
        amd[i] = sum(abs(diff))
    return abs(amd)

def freq_to_note(freq): # The frequency is the sample size divided by the minimum position, determined by ComputeMinPos from having the AMDF function processing signal and maxshift.
    lnote = (math.log(freq) - math.log(440)) / math.log(2) + 4.0
    oct = math.floor(lnote)
    interval_cents = 1200 * (lnote - oct)
    offset = 50.0
    x = 1; note = "A"
    #if (interval_cents >= 1150): # A lot of this octave stuff I don't need outside of a tuner
    #    interval_cents -= 1200
    #    ++oct
    #else:
    for p in range(11):
        if (interval_cents >= offset) and (interval_cents < (offset + 100)):
            note = note_names_list[x]
            interval_cents -= (p * 100)
            break
        offset += 100
        x += 1
    return note#, oct

# Setup PyAudio stream
try:
    stream = pyaudio.PyAudio().open(format=pyaudio.paInt16,
                        channels=1,
                        rate=48000,
                        input=True,
                        frames_per_buffer=1024)
except:
    print("Audio input device not found.")
    run = 0
    sys.exit()

f = open('Twinkle Twinkle Little Star', 'r')
lines = f.readlines()

song_title = lines[0]
print(song_title, end='')

song_measures = lines[1].split()

song_measure_tempo = lines[2]
#print('Delay per measure (tempo): %s' % song_measure_tempo)

for i in song_measures:
    totalscore += len(i) # Same problem as before, just length won't do...

f.close() # Reads the song data from the song file, sharps and flats might become an issue later based upon how I keep score.  I figure an F would match an F# for one point, I'll need to solve that.

def notematch(notestr):
    return re.findall('[CDEFGAH][#b]?', notestr)

while True:
    try:
        song_measure_tempo = int(input("Enter a seconds per measure value, maximum speed is 3: ")) # If I go faster than 3, it fails to recognize notes :(
        break
    except:
        pass

    print("Enter an integer number!")

print("Song starting in five seconds...")
time.sleep(5)

def songprint():

    global songiter, notes_played, score, totalscore, run

    if songiter < len(song_measures):
        if songiter > 0:
            for notes in song_measures[songiter - 1]:
                for i in notes_played:
                    if i in notematch(notes):
                        score += 1
        print('%s, %s / %s, Notes heard: %s' % (song_measures[songiter], score, totalscore, notes_played))  # a measure to print and play
        notes_played = []
        songiter += 1
    else:
        for notes in song_measures[songiter - 1]:
            for i in notes_played:
                if i in notematch(notes):
                    score += 1
        notes_played = []
        print("Song finished! Final score: %s / %s." % (score, totalscore))
        run = 0
        sys.exit() # Note, this isn't exiting the whole program, just the thread.

    s.enter(song_measure_tempo, 1, songprint, ()) # duration here, currently 2, will set the tempo rate for later on, going to start slow at 3
    s.run()

thread = threading.Thread(target=songprint)
thread.daemon = True # I wonder what this is for?
thread.start()

while run == 1:

    try:
        raw = stream.read(1024) # 1024 is the "chunk" size, or frames per buffer? I forget.
    except:
        continue

    # pyaudio and AMD stuff
    signal = np.fromstring(raw, dtype=np.int16) # Data type from the stream I think, like paInt16.
    maxShift = len(signal); amd = AMDF(signal, maxShift); minpos = compute_minpos(amd)

    # volume
    data = stream.read(1024); volume = audioop.rms(data, 2)  # here's where you calculate the volume

    if minpos is not None and volume > 400:
        freq = 48000 / (minpos)
        note = freq_to_note(freq) # originally set note, oct
        if note not in notes_played:
            notes_played.append(note)

# TODO next:
    # Slowed down versions of songs should be easy to implement

    # A tetra-chord or scale on one string turns into a major chord on another, or something... I should review the youtube video on this, it sounds like a good learning tool for the violin.  And some sound "happy" while others sound "sad" which could be neat.

    # If someone wears headphones, an advanced feature could be to play over your own earlier playing to hear multiple stringed instruments.

    # Playing the audio first with a high-end midi as an option would also be helpful.

    # I'll want to use my 3d model to insure that the violin or viola is set up, held etc. properly.
