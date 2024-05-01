import json
from sentence_transformers import SentenceTransformer


def get_transcripts(file):
    document = json.load(file)
    alternatives = document["results"]

    episode_word_count = 0
    for alt in alternatives:
        try:
            episode_word_count += len(alt["alternatives"][0]["transcript"].split())
        except KeyError:
            pass

    t_len = 250
    remainder = 0
    if(episode_word_count < t_len):
        t_len = episode_word_count
    else:
        extra = (episode_word_count%t_len) // (episode_word_count//t_len)
        remainder = episode_word_count % (t_len+extra)
        t_len = t_len+extra

    transcripts = []
    starttimes = []
    endtimes = []
    
    transcriptbuilder_len = 0
    transcriptbuilder = ""
    final_t_iterator = 0
    if(remainder == 0):
        r = 0
    else:
        r = 1
    for alt in alternatives:
        try:
            transcript = alt["alternatives"][0]["transcript"]
            t_split = transcript.split()
            transcript_len = len(t_split)
            if(transcriptbuilder_len == 0):# only runs once, kinda jank
                starttime = alt["alternatives"][0]["words"][0]["startTime"]
                starttimes.append(float(starttime))
            if(transcriptbuilder_len + transcript_len <= t_len+r):
                transcriptbuilder_len += transcript_len
                if(transcript[0] == " "):
                    transcriptbuilder += transcript
                else:
                    transcriptbuilder += " " + transcript
            else: # complete new transcript + extra
                offset = (t_len+r - transcriptbuilder_len)
                finaltranscript = transcriptbuilder + " " + " ".join(t_split[:offset])
                endtime = alt["alternatives"][0]["words"][offset-1]["endTime"]
                transcriptbuilder = " ".join(t_split[offset:]) #reset builder
                transcriptbuilder_len = len(transcriptbuilder.split())
                transcripts.append(finaltranscript)
                endtimes.append(float(endtime))
                starttimes.append(float(endtime)) #good enough
                final_t_iterator += 1
                if(final_t_iterator >= remainder):
                    r = 0

        except KeyError:
            pass
        except NotImplementedError as e:
            print(e)
            exit(1)

    #ugly
    transcripts.append(transcriptbuilder)
    endtimes.append(float(alternatives[-1]["alternatives"][0]["words"][-1]["endTime"]))

    assert(len(transcripts) == len(endtimes) == len(starttimes), f"Transcripts, endtimes and starttimes are not the same length! {len(transcripts)} {len(endtimes)} {len(starttimes)}")

    return (transcripts, starttimes, endtimes)

def get_transcript_actions(file, model: SentenceTransformer, episode_filename: str, showID: str):
    actions = []

    (transcripts, starttimes, endtimes) = get_transcripts(file)
    attempts = 0
    success = False
    while attempts < 5 and not success:
        try:
            vectors = model.encode(transcripts)
            success = True
        except Exception as e:
            print(f"Error with transcripts")
            print(e)
            attempts += 1
    
    if not success:
        print("Not success, exiting")
        exit(1)

    for i in range(len(transcripts)):
        transcript = transcripts[i]
        starttime = starttimes[i]
        endtime = endtimes[i]
        vector = vectors[i]

        contents = {
            "_id": episode_filename + "_" + str(i),
            "transcript": transcript,
            "show_id": showID,
            "starttime": starttime,
            "endtime": endtime,
            "vector": vector
        }

        actions.append(contents)

    return actions