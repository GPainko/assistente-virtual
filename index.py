import os
import sys
import contextlib
import speech_recognition as sr
import re
from gtts import gTTS
import tempfile

@contextlib.contextmanager
def silenciar_alsa():
    """Silencia os avisos do ALSA/JACK em nível de OS."""
    stderr_fd = sys.stderr.fileno()
    salva_stderr = os.dup(stderr_fd)
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, stderr_fd)
    try:
        yield
    finally:
        os.dup2(salva_stderr, stderr_fd)
        os.close(salva_stderr)
        os.close(devnull)

def falar(texto):
    """Fala um texto usando a voz do Google (gTTS)."""
    tts = gTTS(text=texto, lang='pt-br')
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as fp:
        tts.save(fp.name)
        caminho = fp.name
    os.system(f'mpg123 -q {caminho}')
    os.unlink(caminho)

def main():
    mic = sr.Recognizer()
    nome = ""

    falar("Olá, vamos começar. Fale alguma coisa.")
    print("=== Assistente de Voz Iniciado ===")
    print("Comandos disponíveis: 'ajudar', 'meu nome é ...', 'qual é meu nome', 'sair'")
    print()

    while True:
        try:
            with silenciar_alsa():
                with sr.Microphone() as source:
                    mic.adjust_for_ambient_noise(source, duration=1)
                    print("Ouvindo...")
                    audio = mic.listen(source, timeout=5, phrase_time_limit=10)

            frase = mic.recognize_google(audio, language='pt-BR')
            print(f"Você falou: {frase}")

            # Comando: ajudar
            if 'ajudar' in frase.lower():
                falar("Em que posso ajudar?")
                print(">> Algo relacionado a ajuda.")

            # Comando: meu nome é ...
            elif 'meu nome é' in frase.lower():
                match = re.search(r'meu nome é (.+)', frase, re.IGNORECASE)
                if match:
                    nome = match.group(1).strip()
                    falar(f"Muito prazer, {nome}")
                    print(f">> Nome registrado: {nome}")

            # Comando: qual é meu nome
            elif 'meu nome' in frase.lower() and nome:
                falar(f"Seu nome é {nome}")
                print(f">> Nome cadastrado: {nome}")

            # Comando: sair
            elif 'sair' in frase.lower() or 'encerrar' in frase.lower():
                falar("Até logo!")
                print(">> Encerrando...")
                break

            else:
                falar(f"Você disse: {frase}")

        except sr.WaitTimeoutError:
            print("Nenhum áudio detectado no tempo limite.")
        except sr.UnknownValueError:
            print("Não entendi, pode repetir?")
        except sr.RequestError as e:
            print(f"Erro no serviço do Google: {e}")

if __name__ == '__main__':
    main()