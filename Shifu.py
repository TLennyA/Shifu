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
import re


# ============================================================
# SHIFU
# ============================================================

VERSIONE = "0.10.1"

MODELLO = "llama3.2:3b"
VOCE = "it-IT-ElsaNeural"

FILE_AUDIO = "shifu_voice.mp3"
FILE_MEMORIA = "memoria.json"

OLLAMA_URL = "http://localhost:11434/api/chat"

recognizer = sr.Recognizer()

# Evita che il riconoscimento tagli troppo presto le frasi
recognizer.pause_threshold = 0.8
recognizer.non_speaking_duration = 0.4
recognizer.phrase_threshold = 0.3


# ============================================================
# MEMORIA
# ============================================================

def carica_memoria():

    if not os.path.exists(FILE_MEMORIA):
        return {
            "profilo": {},
            "conversazioni": []
        }

    try:

        with open(
            FILE_MEMORIA,
            "r",
            encoding="utf-8"
        ) as file:

            dati = json.load(file)

        # Compatibilità con la vecchia memoria
        if isinstance(dati, list):

            return {
                "profilo": {},
                "conversazioni": dati
            }

        if not isinstance(dati, dict):

            return {
                "profilo": {},
                "conversazioni": []
            }

        if "profilo" not in dati:
            dati["profilo"] = {}

        if "conversazioni" not in dati:
            dati["conversazioni"] = []

        return dati

    except Exception as errore:

        print(
            "ERRORE MEMORIA:",
            errore
        )

        return {
            "profilo": {},
            "conversazioni": []
        }


def salva_memoria():

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

        print(
            "ERRORE SALVATAGGIO MEMORIA:",
            errore
        )


memoria = carica_memoria()


# ============================================================
# PROFILO UTENTE
# ============================================================

def nome_utente():

    profilo = memoria.get(
        "profilo",
        {}
    )

    return profilo.get(
        "nome"
    )


def salva_nome(nome):

    nome = nome.strip()

    if not nome:
        return

    nome = nome[0].upper() + nome[1:].lower()

    memoria.setdefault(
        "profilo",
        {}
    )

    memoria["profilo"]["nome"] = nome

    salva_memoria()

    print(
        "💾 Nome salvato:",
        nome
    )


def estrai_nome(testo):

    testo = testo.strip()

    # --------------------------------------------------------
    # Mi chiamo Lenny
    # --------------------------------------------------------

    pattern = re.search(
        r"\bmi\s+chiamo\s+([A-Za-zÀ-ÖØ-öø-ÿ'-]+)",
        testo,
        re.IGNORECASE
    )

    if pattern:

        nome = pattern.group(1)

        # Evita di salvare parole che non sono nomi
        parole_non_nome = {
            "come",
            "oggi",
            "domani",
            "così",
            "lenny?" 
        }

        if nome.lower() not in parole_non_nome:

            return nome

    # --------------------------------------------------------
    # Sono Lenny
    # --------------------------------------------------------

    pattern = re.search(
        r"\bsono\s+([A-Za-zÀ-ÖØ-öø-ÿ'-]+)",
        testo,
        re.IGNORECASE
    )

    if pattern:

        nome = pattern.group(1)

        parole_non_nome = {
            "stanco",
            "stanca",
            "felice",
            "triste",
            "qui",
            "arrivato",
            "arrivata"
        }

        if nome.lower() not in parole_non_nome:

            return nome

    # --------------------------------------------------------
    # Il mio nome è Lenny
    # --------------------------------------------------------

    pattern = re.search(
        r"\bil\s+mio\s+nome\s+(?:è|e)\s+([A-Za-zÀ-ÖØ-öø-ÿ'-]+)",
        testo,
        re.IGNORECASE
    )

    if pattern:

        return pattern.group(1)

    return None


# ============================================================
# MEMORIA CONVERSAZIONE
# ============================================================

def registra_memoria(utente, shifu):

    conversazioni = memoria.setdefault(
        "conversazioni",
        []
    )

    conversazioni.append(
        {
            "utente": utente,
            "shifu": shifu
        }
    )

    if len(conversazioni) > 100:

        memoria["conversazioni"] = conversazioni[-100:]

    salva_memoria()


def memoria_recente():

    conversazioni = memoria.get(
        "conversazioni",
        []
    )

    elementi = conversazioni[-10:]

    if not elementi:

        return "Nessuna conversazione recente."

    testo = ""

    for elemento in elementi:

        testo += (
            "Utente: "
            + str(elemento.get("utente", ""))
            + "\n"
            + "Shifu: "
            + str(elemento.get("shifu", ""))
            + "\n\n"
        )

    return testo


# ============================================================
# VOCE
# ============================================================

def parla(testo):

    print()
    print(
        "🐉 Shifu:",
        testo
    )

    async def genera_audio():

        comunicatore = edge_tts.Communicate(
            str(testo),
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
# RICONOSCIMENTO VOCALE
# ============================================================

def ascolta():

    print()
    print(
        "🎤 Shifu sta ascoltando..."
    )

    with sr.Microphone() as source:

        # Calibrazione ambientale
        recognizer.adjust_for_ambient_noise(
            source,
            duration=0.5
        )

        print(
            "🎧 Parla..."
        )

        audio = recognizer.listen(
            source,
            timeout=10,
            phrase_time_limit=20
        )

    print(
        "🧠 Sto trascrivendo..."
    )

    try:

        testo = recognizer.recognize_google(
            audio,
            language="it-IT"
        )

        return testo.strip()

    except sr.UnknownValueError:

        return None

    except sr.RequestError as errore:

        print(
            "ERRORE GOOGLE SPEECH:",
            errore
        )

        raise


# ============================================================
# TOOL
# ============================================================

TOOLS = [

    {
        "type": "function",

        "function": {

            "name": "open_app",

            "description": (
                "Apre una applicazione Windows "
                "tra quelle autorizzate."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "app": {

                        "type": "string",

                        "description": (
                            "Applicazione da aprire. "
                            "Possibili valori: "
                            "chrome, notepad, calculator, "
                            "explorer, settings, discord."
                        )
                    }
                },

                "required": [
                    "app"
                ]
            }
        }
    },

    {
        "type": "function",

        "function": {

            "name": "open_website",

            "description": (
                "Apre un sito Web autorizzato."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "site": {

                        "type": "string",

                        "description": (
                            "Sito da aprire. "
                            "Possibili valori: "
                            "google, youtube."
                        )
                    }
                },

                "required": [
                    "site"
                ]
            }
        }
    }

]


# ============================================================
# SICUREZZA
# ============================================================

def richiede_conferma(nome_tool, argomenti):

    # Per ora queste azioni sono considerate sicure.
    # Le azioni distruttive verranno aggiunte più avanti
    # con conferma obbligatoria.

    if nome_tool == "open_app":

        app = str(
            argomenti.get(
                "app",
                ""
            )
        ).lower()

        if app in [
            "chrome",
            "google chrome",
            "notepad",
            "blocco note",
            "calculator",
            "calcolatrice",
            "explorer",
            "esplora file",
            "settings",
            "impostazioni",
            "discord"
        ]:

            return False

    if nome_tool == "open_website":

        return False

    return True


def conferma_vocale():

    try:

        with sr.Microphone() as source:

            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.3
            )

            print(
                "🎤 In attesa della conferma..."
            )

            audio = recognizer.listen(
                source,
                timeout=8,
                phrase_time_limit=5
            )

        risposta = recognizer.recognize_google(
            audio,
            language="it-IT"
        )

        risposta = risposta.lower().strip()

        print(
            "👤 Conferma:",
            risposta
        )

        si = [
            "sì",
            "si",
            "ok",
            "okay",
            "vai",
            "procedi",
            "confermo",
            "confermo shifu",
            "fallo"
        ]

        return risposta in si

    except Exception as errore:

        print(
            "ERRORE CONFERMA:",
            errore
        )

        return False


def chiedi_conferma(nome_tool, argomenti):

    if nome_tool == "open_app":

        app = argomenti.get(
            "app",
            "applicazione"
        )

        messaggio = (
            "Questa operazione richiede "
            "la tua conferma. "
            "Vuoi che apra "
            + str(app)
            + "?"
        )

    elif nome_tool == "open_website":

        sito = argomenti.get(
            "site",
            "il sito"
        )

        messaggio = (
            "Vuoi che apra "
            + str(sito)
            + "?"
        )

    else:

        messaggio = (
            "Questa operazione richiede "
            "la tua conferma. "
            "Vuoi procedere?"
        )

    parla(
        messaggio
    )

    return conferma_vocale()


# ============================================================
# ESECUZIONE TOOL
# ============================================================

def esegui_tool(nome_tool, argomenti):

    print()
    print(
        "🛠️ TOOL:",
        nome_tool
    )

    print(
        "📦 PARAMETRI:",
        argomenti
    )

    # ========================================================
    # OPEN APP
    # ========================================================

    if nome_tool == "open_app":

        app = str(
            argomenti.get(
                "app",
                ""
            )
        ).lower().strip()

        # ----------------------------------------------------
        # CHROME
        # ----------------------------------------------------

        if app in [
            "chrome",
            "google chrome"
        ]:

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

                    try:

                        subprocess.Popen(
                            [percorso]
                        )

                        return (
                            "Google Chrome "
                            "è stato aperto."
                        )

                    except Exception as errore:

                        print(
                            "ERRORE CHROME:",
                            errore
                        )

                        return (
                            "Non sono riuscito "
                            "ad aprire Chrome."
                        )

            return (
                "Non ho trovato "
                "Google Chrome."
            )

        # ----------------------------------------------------
        # NOTEPAD
        # ----------------------------------------------------

        if app in [
            "notepad",
            "blocco note"
        ]:

            try:

                subprocess.Popen(
                    ["notepad.exe"]
                )

                return (
                    "Il blocco note "
                    "è stato aperto."
                )

            except Exception as errore:

                print(
                    "ERRORE NOTEPAD:",
                    errore
                )

                return (
                    "Non sono riuscito "
                    "ad aprire il blocco note."
                )

        # ----------------------------------------------------
        # CALCOLATRICE
        # ----------------------------------------------------

        if app in [
            "calculator",
            "calcolatrice"
        ]:

            try:

                subprocess.Popen(
                    ["calc.exe"]
                )

                return (
                    "La calcolatrice "
                    "è stata aperta."
                )

            except Exception as errore:

                print(
                    "ERRORE CALCOLATRICE:",
                    errore
                )

                return (
                    "Non sono riuscito "
                    "ad aprire la calcolatrice."
                )

        # ----------------------------------------------------
        # ESPLORA FILE
        # ----------------------------------------------------

        if app in [
            "explorer",
            "esplora file",
            "esplora"
        ]:

            try:

                subprocess.Popen(
                    ["explorer.exe"]
                )

                return (
                    "Esplora File "
                    "è stato aperto."
                )

            except Exception as errore:

                print(
                    "ERRORE EXPLORER:",
                    errore
                )

                return (
                    "Non sono riuscito "
                    "ad aprire Esplora File."
                )

        # ----------------------------------------------------
        # IMPOSTAZIONI
        # ----------------------------------------------------

        if app in [
            "settings",
            "impostazioni"
        ]:

            try:

                os.startfile(
                    "ms-settings:"
                )

                return (
                    "Le impostazioni "
                    "sono state aperte."
                )

            except Exception as errore:

                print(
                    "ERRORE IMPOSTAZIONI:",
                    errore
                )

                return (
                    "Non sono riuscito "
                    "ad aprire le impostazioni."
                )

        # ----------------------------------------------------
        # DISCORD
        # ----------------------------------------------------

        if app == "discord":

            try:

                subprocess.Popen(
                    [
                        "cmd",
                        "/c",
                        "start",
                        "",
                        "discord:"
                    ]
                )

                return (
                    "Discord è stato aperto."
                )

            except Exception as errore:

                print(
                    "ERRORE DISCORD:",
                    errore
                )

                return (
                    "Non sono riuscito "
                    "ad aprire Discord."
                )

        return (
            "Questa applicazione "
            "non è autorizzata."
        )

    # ========================================================
    # OPEN WEBSITE
    # ========================================================

    if nome_tool == "open_website":

        sito = str(
            argomenti.get(
                "site",
                ""
            )
        ).lower().strip()

        siti = {

            "google":
                "https://www.google.com",

            "youtube":
                "https://www.youtube.com"

        }

        if sito not in siti:

            return (
                "Questo sito "
                "non è autorizzato."
            )

        try:

            webbrowser.open(
                siti[sito]
            )

            return (
                "Ho aperto "
                + sito
                + "."
            )

        except Exception as errore:

            print(
                "ERRORE WEB:",
                errore
            )

            return (
                "Non sono riuscito "
                "ad aprire il sito."
            )

    return (
        "Strumento non riconosciuto."
    )


# ============================================================
# RICERCA WEB
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
        "quando",
        "ultima",
        "ultimo",
        "recente",
        "recenti"

    ]

    testo = testo.lower()

    return any(
        parola in testo
        for parola in parole
    )


def cerca_web(query):

    print()
    print(
        "🔎 Shifu sta cercando sul Web..."
    )

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
                "Nessun risultato trovato."
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
# OLLAMA
# ============================================================

def chiama_ollama(messages, tools=None):

    payload = {

        "model": MODELLO,

        "messages": messages,

        "stream": False,

        "options": {
            "temperature": 0.2
        }

    }

    if tools:

        payload["tools"] = tools

    try:

        risposta = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120
        )

        risposta.raise_for_status()

        return risposta.json()

    except requests.exceptions.ConnectionError:

        print(
            "ERRORE: Ollama non raggiungibile."
        )

        return None

    except Exception as errore:

        print(
            "ERRORE OLLAMA:",
            errore
        )

        return None


# ============================================================
# ESTRAZIONE TOOL
# ============================================================

def estrai_tool_call(dati):

    if not dati:
        return None, None

    message = dati.get(
        "message",
        {}
    )

    # --------------------------------------------------------
    # TOOL CALL NATIVO
    # --------------------------------------------------------

    tool_calls = message.get(
        "tool_calls"
    )

    if tool_calls:

        primo = tool_calls[0]

        function = primo.get(
            "function",
            {}
        )

        nome = function.get(
            "name"
        )

        argomenti = function.get(
            "arguments",
            {}
        )

        if isinstance(
            argomenti,
            str
        ):

            try:

                argomenti = json.loads(
                    argomenti
                )

            except Exception:

                argomenti = {}

        return (
            nome,
            argomenti
        )

    # --------------------------------------------------------
    # JSON NEL CONTENT
    # --------------------------------------------------------

    content = message.get(
        "content",
        ""
    )

    if not content:
        return None, None

    testo = content.strip()

    # Cerca il primo blocco JSON
    match = re.search(
        r"\{.*\}",
        testo,
        re.DOTALL
    )

    if not match:
        return None, None

    possibile_json = match.group(0)

    try:

        dati_json = json.loads(
            possibile_json
        )

        if not isinstance(
            dati_json,
            dict
        ):

            return None, None

        nome = (
            dati_json.get("name")
            or dati_json.get("tool")
            or dati_json.get("function")
        )

        argomenti = (
            dati_json.get("parameters")
            or dati_json.get("arguments")
            or dati_json.get("args")
            or {}
        )

        if nome:

            return (
                nome,
                argomenti
            )

    except Exception:

        pass

    return None, None


# ============================================================
# CERVELLO
# ============================================================

def pensa(testo):

    nome = nome_utente()

    # --------------------------------------------------------
    # RICONOSCIMENTO NOME
    # --------------------------------------------------------

    nuovo_nome = estrai_nome(
        testo
    )

    if nuovo_nome:

        salva_nome(
            nuovo_nome
        )

        nome = nuovo_nome

    # --------------------------------------------------------
    # MEMORIA
    # --------------------------------------------------------

    memoria_testo = memoria_recente()

    profilo = ""

    if nome:

        profilo = (
            "\nIl nome dell'utente è: "
            + nome
            + "\n"
        )

    # --------------------------------------------------------
    # RICERCA WEB
    # --------------------------------------------------------

    risultati_web = ""

    if serve_ricerca(testo):

        risultati_web = cerca_web(
            testo
        )

    # --------------------------------------------------------
    # SYSTEM PROMPT
    # --------------------------------------------------------

    system_prompt = """

Ti chiami Shifu.

Sei un assistente personale intelligente,
amichevole, naturale e curioso.

Parli sempre in italiano.

Il tuo utente può avere un nome
memorizzato nella memoria.

Usa il nome dell'utente naturalmente
quando è appropriato, senza ripeterlo
in ogni frase.

Devi distinguere tra conversazione
normale e richieste operative.

Puoi utilizzare gli strumenti disponibili
quando l'utente chiede realmente
di eseguire un'azione.

Non inventare mai di aver eseguito
una operazione.

Se un'operazione non è stata eseguita,
dillo chiaramente.

Le risposte devono essere naturali,
brevi e adatte alla voce.

MEMORIA RECENTE:
""" + memoria_testo + profilo

    # --------------------------------------------------------
    # WEB
    # --------------------------------------------------------

    if risultati_web:

        system_prompt += """

RISULTATI DELLA RICERCA WEB:

""" + risultati_web

    messages = [

        {
            "role": "system",
            "content": system_prompt
        },

        {
            "role": "user",
            "content": testo
        }

    ]

    # --------------------------------------------------------
    # OLLAMA
    # --------------------------------------------------------

    dati = chiama_ollama(
        messages,
        TOOLS
    )

    if dati is None:

        risposta = (
            "Non riesco a collegarmi "
            "al mio cervello."
        )

        registra_memoria(
            testo,
            risposta
        )

        return risposta

    # --------------------------------------------------------
    # TOOL
    # --------------------------------------------------------

    nome_tool, argomenti = estrai_tool_call(
        dati
    )

    # --------------------------------------------------------
    # RISPOSTA NORMALE
    # --------------------------------------------------------

    if nome_tool is None:

        risposta = dati.get(
            "message",
            {}
        ).get(
            "content",
            ""
        )

        if not risposta:

            risposta = (
                "Non ho una risposta "
                "in questo momento."
            )

        registra_memoria(
            testo,
            risposta
        )

        return risposta

    # --------------------------------------------------------
    # TOOL TROVATO
    # --------------------------------------------------------

    print()
    print(
        "🤖 Ollama ha scelto il tool:",
        nome_tool
    )

    print(
        "📦 Argomenti:",
        argomenti
    )

    # --------------------------------------------------------
    # SICUREZZA
    # --------------------------------------------------------

    if richiede_conferma(
        nome_tool,
        argomenti
    ):

        if not chiedi_conferma(
            nome_tool,
            argomenti
        ):

            risposta = (
                "Va bene, operazione annullata."
            )

            registra_memoria(
                testo,
                risposta
            )

            return risposta

    # --------------------------------------------------------
    # ESEGUI
    # --------------------------------------------------------

    risultato = esegui_tool(
        nome_tool,
        argomenti
    )

    # --------------------------------------------------------
    # RISPOSTA FINALE
    # --------------------------------------------------------

    risposta = str(
        risultato
    )

    # Prova a chiedere a Ollama
    # di formulare una risposta naturale.

    try:

        messaggio_finale = [

            {
                "role": "system",
                "content": (
                    "Sei Shifu. "
                    "Rispondi in italiano "
                    "in modo breve e naturale. "
                    "Descrivi solamente "
                    "il risultato reale "
                    "dell'azione."
                )
            },

            {
                "role": "user",
                "content": (
                    "Richiesta dell'utente: "
                    + testo
                    + "\n\nRisultato dell'azione: "
                    + str(risultato)
                )
            }

        ]

        finale = chiama_ollama(
            messaggio_finale
        )

        if finale:

            contenuto = finale.get(
                "message",
                {}
            ).get(
                "content",
                ""
            )

            if contenuto:

                risposta = contenuto

    except Exception as errore:

        print(
            "ERRORE RISPOSTA FINALE:",
            errore
        )

    registra_memoria(
        testo,
        risposta
    )

    return risposta


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
print("🛠️ Tool: ATTIVI")
print("🔐 Sicurezza: ATTIVA")

nome = nome_utente()

if nome:

    print(
        "👤 Utente:",
        nome
    )

else:

    print(
        "👤 Utente: non ancora conosciuto"
    )

print("==========================================")
print()

if nome:

    messaggio_avvio = (
        "Ciao "
        + nome
        + "! Sono Shifu. "
        "Sono pronto."
    )

else:

    messaggio_avvio = (
        "Ciao! Sono Shifu. "
        "Sono pronto. "
        "Dimmi come ti chiami e lo ricorderò."
    )

parla(
    messaggio_avvio
)


# ============================================================
# CICLO PRINCIPALE
# ============================================================

while True:

    try:

        testo = ascolta()

        if not testo:

            print(
                "❓ Non ho capito."
            )

            parla(
                "Non ho capito. "
                "Puoi ripetere?"
            )

            continue

        print()
        print(
            "👤 Tu:",
            testo
        )

        comando = testo.lower().strip()

        # ----------------------------------------------------
        # USCITA
        # ----------------------------------------------------

        if comando in [

            "esci",
            "stop",
            "chiudi shifu",
            "spegni shifu",
            "chiudi"

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
            "⏱️ Non ho sentito nulla."
        )

    except sr.UnknownValueError:

        print(
            "❓ Non ho capito."
        )

        parla(
            "Non ho capito. "
            "Puoi ripetere?"
        )

    except sr.RequestError as errore:

        print(
            "❌ ERRORE RICONOSCIMENTO VOCALE:",
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
            "❌ ERRORE GENERALE:",
            errore
        )

        time.sleep(1)
