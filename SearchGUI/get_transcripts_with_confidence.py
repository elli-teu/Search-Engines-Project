import json


def get_transcripts_with_confidence(file, t_len):
    document = json.load(file)
    alternatives = document["results"]
    confidence_score = float(document["confidence"]) #Nyhet

    episode_word_count = 0
    for alt in alternatives:
        try:
            episode_word_count += len(alt["alternatives"][0]["transcript"].split())
        except KeyError:
            pass

    #t_len = 250
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
                starttimes.append(float(starttime[:-1]))
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
                endtimes.append(float(endtime[:-1]))
                starttimes.append(float(endtime[:-1])) #good enough
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
    endtimes.append(float(alternatives[-1]["alternatives"][0]["words"][-1]["endTime"][:-1]))

    assert(all((len(transcripts) == len(endtimes), len(transcripts) == len(starttimes))), f"Transcripts, endtimes and starttimes are not the same length! {len(transcripts)} {len(endtimes)} {len(starttimes)}")

    confidence_scores = [confidence_score] * len(transcripts) #Nyhet
    
    return (transcripts, starttimes, endtimes, confidence_scores)
