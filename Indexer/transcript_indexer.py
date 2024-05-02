import json
from sentence_transformers import SentenceTransformer
import torch.nn.functional as F
from setup import MATRYOSHKA_DIM

def get_transcripts(file, t_len):
    document = json.load(file)
    alternatives = document["results"]

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
    
    starttimes.append(float(alternatives[-1]["alternatives"][0]["words"][0]["startTime"][:-1]))
    for alt in alternatives:
        try:
            transcript = alt["alternatives"][0]["transcript"]
            t_split = transcript.split()
            transcript_len = len(t_split)
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

                while(transcriptbuilder_len > t_len+r):
                    builderExtraList = transcriptbuilder.split()
                    transcripts.append(" ".join(builderExtraList[:(t_len+r)])) #extra bit of transcript that was too long
                    offset = offset+t_len+r
                    endtime = alt["alternatives"][0]["words"][offset-1]["endTime"]
                    endtimes.append(float(endtime[:-1]))
                    starttimes.append(float(endtime[:-1]))
                    transcriptbuilder = " ".join(builderExtraList[(t_len+r):]) #reset builder
                    transcriptbuilder_len = len(transcriptbuilder.split())
                    final_t_iterator += 1
                    if(final_t_iterator >= remainder):
                        r = 0
        except KeyError:
            pass
        except NotImplementedError as e:
            print(e)
            exit(1)
        except IndexError as e:
            print(e)
            print("In file: ", file.name)
            print(len(alt["alternatives"][0]["words"]))
            print("Offset: ", offset)
            exit(1)

    #ugly
    transcripts.append(transcriptbuilder)
    endtimes.append(float(alternatives[-1]["alternatives"][0]["words"][-1]["endTime"][:-1]))

    assert all((len(transcripts) == len(endtimes), len(transcripts) == len(starttimes))), f"Transcripts, endtimes and starttimes are not the same length! {len(transcripts)} {len(endtimes)} {len(starttimes)}"

    return (transcripts, starttimes, endtimes)

def get_transcript_actions(file, model: SentenceTransformer, episode_filename: str, showID: str, transcript_length: int):
    actions = []

    (transcripts, starttimes, endtimes) = get_transcripts(file, transcript_length)
    encode_transcripts = ["search_document: " + t for t in transcripts]
    attempts = 0
    success = False
    while attempts < 5 and not success:
        try:
            embeddings = model.encode(encode_transcripts, convert_to_tensor=True)
            embeddings = F.layer_norm(embeddings, normalized_shape=(embeddings.shape[1],))
            embeddings = embeddings[:, :MATRYOSHKA_DIM]
            vectors = F.normalize(embeddings, p=2, dim=1)
            success = True
        except Exception as e:
            print(f"Error with transcripts")
            print(e)
            attempts += 1
    
    if not success:
        print("Not success, exiting")
        exit(1)

    assert len(vectors) == len(transcripts), f"Transcripts and vectors are not the same length! {len(transcripts)} {len(vectors)}"

    for i in range(len(transcripts)):
        transcript = transcripts[i]
        starttime = starttimes[i]
        endtime = endtimes[i]
        vector = vectors[i].tolist()

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