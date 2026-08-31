import speech_recognition as sr
import requests
from ddgs import DDGS
import asyncio
import edge_tts
import pygame
import os
import time
import json
import subprocess
import webbrowser


# ============================================================
# CONFIGURAZIONE SHIFU
# ============================================================

VERSIONE = "0.9.1"

MODELLO = "llama3.2:3b"
VOCE = "it-IT-ElsaNeural"

FILE_AUDIO = "shifu_voice.mp3"
FILE_MEMORIA = "memoria.json"

OLLAMA_URL = "http://localhost:11434/api/chat"

recognizer = sr.Recognizer()


# ============================================================
# MEMORIA
# ============================================================

def carica_memoria():

    if not os.path.exists(FILE_MEMORIA):
        return []

    try:

        with open(
            FILE_MEMORIA,
            "r",
            encoding="utf-8"
        ) as file:

            dati = json.load(file)

            if isinstance(dati, list):
                return dati

            return []

    except Exception as errore:

        print("ERRORE MEMORIA:", errore)

        return []


def salva_memoria(memoria):

    try:

        with open(
            FILE_MEMORIA,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                memoria,
                file,
                ensure_ascii=False,
                indent=2
            )

    except Exception as errore:

        print("ERRORE SALVATAGGIO MEMORIA:", errore)


memoria = carica_memoria()


# ============================================================
# OLLAMA
# ============================================================

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
                            "amichevole, naturale e curioso. "
                            "Parli sempre in italiano. "
                            "Ricordi il contesto quando ti viene fornito. "
                            "Non inventare informazioni. "
                            "Le tue risposte vengono lette a voce, "
                            "quindi devono essere naturali e abbastanza brevi."
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

        print(
            "ERRORE: Ollama non è raggiungibile."
        )

        return (
            "Non riesco a collegarmi "
            "al mio cervello."
        )

    except Exception as errore:

        print(
            "ERRORE OLLAMA:",
            errore
        )

        return (
            "Ho avuto un problema "
            "mentre elaboravo la richiesta."
        )


# ============================================================
# RICERCA WEB
# ============================================================

def cerca_web(query):

    print()
    print("🔎 Shifu sta cercando sul Web...")
    print("🔎 Query:", query)

    try:

        risultati = []

        with DDGS() as ddgs:

            elementi = ddgs.text(
                query,
                max_results=5
            )

            for elemento in elementi:

                titolo = elemento.get(
                    "title",
                    ""
                )

                descrizione = elemento.get(
                    "body",
                    ""
                )

                link = elemento.get(
                    "href",
                    ""
                )

                risultati.append(
                    f"Titolo: {titolo}\n"
                    f"Informazioni: {descrizione}\n"
                    f"Link: {link}"
                )

        if not risultati:

            return (
                "Non ho trovato "
                "risultati sul Web."
            )

        return "\n\n".join(
            risultati
        )

    except Exception as errore:

        print(
            "ERRORE RICERCA WEB:",
            errore
        )

        return (
            "La ricerca Web "
            "non è disponibile."
        )


# ============================================================
# DECISIONE RICERCA WEB
# ============================================================

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


# ============================================================
# TROVA CHROME
# ============================================================

def trova_chrome():

    percorsi = [

        os.path.expandvars(
            r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"
        ),

        os.path.expandvars(
            r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
        ),

        os.path.expandvars(
            r"%LocalAppData%\Google\Chrome\Application\chrome.exe"
        )

    ]

    for percorso in percorsi:

        if os.path.exists(percorso):

            return percorso

    return None


# ============================================================
# CONTROLLO COMPUTER
# ============================================================

def esegui_comando_pc(testo):

    comando = testo.lower().strip()

    # ========================================================
    # CHROME
    # ========================================================

    if (
        "apri chrome" in comando
        or "apri google chrome" in comando
    ):

        print()
        print("💻 Shifu sta aprendo Chrome...")

        try:

            chrome = trova_chrome()

            if chrome is None:

                print(
                    "❌ Chrome non trovato."
                )

                return (
                    "Non riesco a trovare "
                    "Google Chrome sul computer."
                )

            subprocess.Popen(
                [chrome]
            )

            print(
                "✅ Chrome avviato:",
                chrome
            )

            return (
                "Chrome è stato avviato."
            )

        except Exception as errore:

            print(
                "❌ ERRORE CHROME:",
                errore
            )

            return (
                "Non sono riuscito "
                "ad aprire Chrome."
            )

    # ========================================================
    # BLOCCO NOTE
    # ========================================================

    if (
        "apri blocco note" in comando
        or "apri il blocco note" in comando
        or "apri notepad" in comando
    ):

        print()
        print(
            "💻 Shifu sta aprendo il Blocco Note..."
        )

        try:

            subprocess.Popen(
                ["notepad.exe"]
            )

            print(
                "✅ Blocco Note avviato."
            )

            return (
                "Il blocco note è stato aperto."
            )

        except Exception as errore:

            print(
                "❌ ERRORE BLOCCO NOTE:",
                errore
            )

            return (
                "Non sono riuscito "
                "ad aprire il blocco note."
            )

    # ========================================================
    # CALCOLATRICE
    # ========================================================

    if (
        "apri calcolatrice" in comando
        or "apri la calcolatrice" in comando
    ):

        print()
        print(
            "💻 Shifu sta aprendo la Calcolatrice..."
        )

        try:

            subprocess.Popen(
                ["calc.exe"]
            )

            print(
                "✅ Calcolatrice avviata."
            )

            return (
                "La calcolatrice è stata aperta."
            )

        except Exception as errore:

            print(
                "❌ ERRORE CALCOLATRICE:",
                errore
            )

            return (
                "Non sono riuscito "
                "ad aprire la calcolatrice."
            )

    # ========================================================
    # ESPLORA FILE
    # ========================================================

    if (
        "apri esplora file" in comando
        or "apri esplora risorse" in comando
        or "apri esplora" in comando
    ):

        print()
        print(
            "💻 Shifu sta aprendo Esplora File..."
        )

        try:

            subprocess.Popen(
                ["explorer.exe"]
            )

            print(
                "✅ Esplora File avviato."
            )

            return (
                "Esplora File è stato aperto."
            )

        except Exception as errore:

            print(
                "❌ ERRORE ESPLORA FILE:",
                errore
            )

            return (
                "Non sono riuscito "
                "ad aprire Esplora File."
            )

    # ========================================================
    # IMPOSTAZIONI WINDOWS
    # ========================================================

    if (
        "apri impostazioni" in comando
        or "apri le impostazioni" in comando
    ):

        print()
        print(
            "💻 Shifu sta aprendo le Impostazioni..."
        )

        try:

            os.startfile(
                "ms-settings:"
            )

            print(
                "✅ Impostazioni avviate."
            )

            return (
                "Le impostazioni di Windows "
                "sono state aperte."
            )

        except Exception as errore:

            print(
                "❌ ERRORE IMPOSTAZIONI:",
                errore
            )

            return (
                "Non sono riuscito "
                "ad aprire le impostazioni."
            )

    # ========================================================
    # YOUTUBE
    # ========================================================

    if "apri youtube" in comando:

        print()
        print(
            "🌐 Shifu sta aprendo YouTube..."
        )

        try:

            webbrowser.open(
                "https://www.youtube.com"
            )

            return (
                "YouTube è stato aperto."
            )

        except Exception as errore:

            print(
                "❌ ERRORE YOUTUBE:",
                errore
            )

            return (
                "Non sono riuscito "
                "ad aprire YouTube."
            )

    # ========================================================
    # GOOGLE
    # ========================================================

    if (
        "apri google" in comando
        and "chrome" not in comando
    ):

        print()
        print(
            "🌐 Shifu sta aprendo Google..."
        )

        try:

            webbrowser.open(
                "https://www.google.com"
            )

            return (
                "Google è stato aperto."
            )

        except Exception as errore:

            print(
                "❌ ERRORE GOOGLE:",
                errore
            )

            return (
                "Non sono riuscito "
                "ad aprire Google."
            )

    # ========================================================
    # NESSUN COMANDO
    # ========================================================

    return None


# ============================================================
# VOCE
# ============================================================

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

            os.remove(
                FILE_AUDIO
            )

    except Exception:

        pass


# ============================================================
# SALVA NELLA MEMORIA
# ============================================================

def registra_memoria(utente, risposta):

    global memoria

    memoria.append(
        {
            "utente": utente,
            "shifu": risposta
        }
    )

    if len(memoria) > 100:

        memoria = memoria[-100:]

    salva_memoria(
        memoria
    )


# ============================================================
# CERVELLO
# ============================================================

def pensa(testo):

    try:

        # ----------------------------------------------------
        # PRIMA CONTROLLIAMO I COMANDI DEL PC
        # ----------------------------------------------------

        comando_pc = esegui_comando_pc(
            testo
        )

        if comando_pc is not None:

            registra_memoria(
                testo,
                comando_pc
            )

            return comando_pc

        # ----------------------------------------------------
        # MEMORIA RECENTE
        # ----------------------------------------------------

        memoria_recente = memoria[-10:]

        contesto_memoria = ""

        if memoria_recente:

            contesto_memoria = (
                "\n\nCONVERSAZIONI RECENTI:\n"
            )

            for elemento in memoria_recente:

                utente_memoria = elemento.get(
                    "utente",
                    ""
                )

                shifu_memoria = elemento.get(
                    "shifu",
                    ""
                )

                contesto_memoria += (
                    "Utente: "
                    + utente_memoria
                    + "\n"
                    + "Shifu: "
                    + shifu_memoria
                    + "\n\n"
                )

        # ----------------------------------------------------
        # RICERCA WEB
        # ----------------------------------------------------

        if serve_ricerca(testo):

            risultati = cerca_web(
                testo
            )

            prompt = (

                "DOMANDA DELL'UTENTE:\n"

                + testo

                + "\n\n"

                + "MEMORIA RECENTE:\n"

                + contesto_memoria

                + "\n"

                + "RISULTATI WEB:\n"

                + risultati

                + "\n\n"

                + "Rispondi in italiano. "
                "Usa i risultati Web quando sono utili. "
                "Usa la memoria recente quando è pertinente. "
                "Non inventare informazioni. "
                "Se i risultati Web non sono sufficienti, "
                "dillo chiaramente."
            )

        else:

            prompt = (

                "MEMORIA RECENTE:\n"

                + contesto_memoria

                + "\n"

                + "NUOVA DOMANDA DELL'UTENTE:\n"

                + testo
            )

        # ----------------------------------------------------
        # OLLAMA
        # ----------------------------------------------------

        risposta = parla_con_ollama(
            prompt
        )

        # ----------------------------------------------------
        # MEMORIA
        # ----------------------------------------------------

        registra_memoria(
            testo,
            risposta
        )

        return risposta

    except Exception as errore:

        print()
        print(
            "❌ ERRORE CERVELLO:",
            errore
        )

        return (
            "Ho avuto un problema "
            "mentre pensavo."
        )


# ============================================================
# AVVIO
# ============================================================

print()
print("==========================================")
print("🐉 SHIFU V" + VERSIONE)
print("==========================================")
print("🧠 Modello:", MODELLO)
print("🔊 Voce:", VOCE)
print("🌐 Ricerca: DuckDuckGo")
print("💾 Memoria: locale")
print("🔗 Ollama: HTTP locale")
print("💻 Controllo PC: ATTIVO")
print("🔐 Sicurezza: COMANDI LIMITATI")
print("==========================================")
print()

parla(
    "Ciao! Sono Shifu. "
    "La mia memoria locale è pronta. "
    "Il controllo del computer è attivo."
)


# ============================================================
# CICLO PRINCIPALE
# ============================================================

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

        print(
            "🧠 Sto elaborando..."
        )

        testo = recognizer.recognize_google(
            audio,
            language="it-IT"
        )

        print()
        print("👤 Tu:", testo)

        comando = testo.lower().strip()

        # ----------------------------------------------------
        # USCITA
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # PENSA
        # ----------------------------------------------------

        risposta = pensa(
            testo
        )

        # ----------------------------------------------------
        # PARLA
        # ----------------------------------------------------

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
            "Ho un problema "
            "con il riconoscimento vocale."
        )

    except KeyboardInterrupt:

        print()
        print(
            "🐉 Shifu chiuso."
        )

        break

    except Exception as errore:

        print()
        print(
            "ERRORE GENERALE:",
            errore
        )

        time.sleep(1)
