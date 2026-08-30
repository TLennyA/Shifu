import speech_recognition as sr
import requests
from ddgs import DDGS
import asyncio
import edge_tts
import pygame
import os
import time


# ==============================
# CONFIGURAZIONE SHIFU
# ==============================


MODELLO = "llama3.2:3b"
VOCE = "it-IT-ElsaNeural"
FILE_AUDIO = "shifu_voice.mp3"


OLLAMA_URL = "http://localhost:11434/api/chat"


recognizer = sr.Recognizer()




# ==============================
# OLLAMA
# ==============================


def parla_con_ollama(prompt):
    try:
        risposta = requests.post(
            OLLAMA_URL,
            json={
                "model": MODELLO,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Ti chiami Shifu. "
                            "Sei un assistente personale intelligente, "
                            "amichevole e naturale. "
                            "Parli sempre in italiano. "
                            "Rispondi in modo chiaro e abbastanza breve "
                            "perché le risposte vengono lette a voce. "
                            "Non inventare informazioni."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False
            },
            timeout=120
        )


        risposta.raise_for_status()


        dati = risposta.json()


        return dati["message"]["content"]


    except requests.exceptions.ConnectionError:
        print("ERRORE: Ollama non è raggiungibile.")
        return "Non riesco a collegarmi al mio cervello."


    except Exception as errore:
        print("ERRORE OLLAMA:", errore)
        return "Ho avuto un problema mentre elaboravo la richiesta."




# ==============================
# RICERCA WEB
# ==============================


def cerca_web(query):
    print()
    print("🔎 Shifu sta cercando sul Web...")


    try:
        risultati = []


        with DDGS() as ddgs:
            elementi = ddgs.text(
                query,
                max_results=5
            )


            for elemento in elementi:
                titolo = elemento.get("title", "")
                descrizione = elemento.get("body", "")
                link = elemento.get("href", "")


                risultati.append(
                    "Titolo: "
                    + titolo
                    + "\nInformazioni: "
                    + descrizione
                    + "\nLink: "
                    + link
                )


        if not risultati:
            return "Non ho trovato risultati sul Web."


        return "\n\n".join(risultati)


    except Exception as errore:
        print("ERRORE RICERCA WEB:", errore)
        return "La ricerca Web non è disponibile in questo momento."




# ==============================
# DECISIONE RICERCA
# ==============================


def serve_ricerca(testo):


    parole = [
        "meteo",
        "tempo",
        "gradi",
        "temperatura",
        "oggi",
        "domani",
        "adesso",
        "ora",
        "notizie",
        "news",
        "prezzo",
        "quanto costa",
        "orario",
        "orari",
        "ultime notizie",
        "risultato",
        "risultati",
        "chi è",
        "cosa è",
        "quando"
    ]


    testo = testo.lower()


    return any(
        parola in testo
        for parola in parole
    )




# ==============================
# VOCE
# ==============================


def parla(testo):


    print()
    print("🐉 Shifu:", testo)


    async def genera_audio():


        comunicatore = edge_tts.Communicate(
            testo,
            VOCE
        )


        await comunicatore.save(
            FILE_AUDIO
        )


    try:


        asyncio.run(
            genera_audio()
        )


        pygame.mixer.init()


        pygame.mixer.music.load(
            FILE_AUDIO
        )


        pygame.mixer.music.play()


        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)


        pygame.mixer.music.stop()
        pygame.mixer.quit()


    except Exception as errore:


        print(
            "ERRORE VOCE:",
            errore
        )


    try:


        if os.path.exists(FILE_AUDIO):
            os.remove(FILE_AUDIO)


    except Exception:
        pass




# ==============================
# CERVELLO DI SHIFU
# ==============================


def pensa(testo):


    try:


        if serve_ricerca(testo):


            risultati = cerca_web(testo)


            prompt = (
                "L'utente ti ha fatto questa domanda:\n\n"
                + testo
                + "\n\n"
                + "Hai effettuato una ricerca sul Web.\n\n"
                + "RISULTATI TROVATI:\n"
                + risultati
                + "\n\n"
                + "Rispondi alla domanda usando "
                + "le informazioni trovate. "
                + "Se i risultati non contengono "
                + "la risposta, dillo chiaramente. "
                + "Non inventare dati. "
                + "Rispondi in italiano e in modo naturale."
            )


            return parla_con_ollama(
                prompt
            )


        else:


            return parla_con_ollama(
                testo
            )


    except Exception as errore:


        print(
            "ERRORE CERVELLO:",
            errore
        )


        return (
            "Ho avuto un problema "
            "mentre pensavo."
        )




# ==============================
# AVVIO
# ==============================


print()
print("==============================")
print("🐉 SHIFU V0.7")
print("==============================")
print("🧠 Modello:", MODELLO)
print("🔊 Voce:", VOCE)
print("🌐 Ricerca: DuckDuckGo")
print("🔗 Ollama: HTTP locale")
print("==============================")
print()


parla(
    "Ciao! Sono Shifu. "
    "Sono pronta ad aiutarti."
)




# ==============================
# CICLO PRINCIPALE
# ==============================


while True:


    try:


        print()
        print("🎤 Shifu sta ascoltando...")


        with sr.Microphone() as source:


            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.5
            )


            audio = recognizer.listen(
                source,
                timeout=10,
                phrase_time_limit=15
            )


        print("🧠 Sto elaborando...")


        testo = recognizer.recognize_google(
            audio,
            language="it-IT"
        )


        print()
        print("👤 Tu:", testo)


        comando = testo.lower().strip()


        if comando in [
            "esci",
            "stop",
            "chiudi shifu",
            "spegni shifu"
        ]:


            parla(
                "Va bene. A presto!"
            )


            break


        risposta = pensa(
            testo
        )


        parla(
            risposta
        )


        time.sleep(
            0.3
        )


    except sr.WaitTimeoutError:


        print(
            "Non ho sentito nulla. "
            "Riprovo..."
        )


    except sr.UnknownValueError:


        print(
            "Non ho capito."
        )


        parla(
            "Non ho capito. "
            "Puoi ripetere?"
        )


    except sr.RequestError as errore:


        print(
            "ERRORE RICONOSCIMENTO VOCALE:",
            errore
        )


        parla(
            "Ho un problema con "
            "il riconoscimento vocale."
        )


    except KeyboardInterrupt:


        print()
        print("🐉 Shifu chiuso.")
        break


    except Exception as errore:


        print()
        print(
            "ERRORE GENERALE:",
            errore
        )


        time.sleep(1)
