import speech_recognition as sr

mic = sr.Recognizer()

with sr.Microphone() as source:
    mic.adjust_for_ambient_noise(source, duration=1)
    print("Ouvindo...")

    try:
        audio = mic.listen(source, timeout=5, phrase_time_limit=10)
        frase = mic.recognize_google(audio, language='pt-BR')
        print(f"Você falou: {frase}")
    except sr.WaitTimeoutError:
        print("Nenhum áudio detectado no tempo limite.")
    except sr.UnknownValueError:
        print("Desculpe, não entendi.")
    except sr.RequestError as e:
        print(f"Erro ao acessar o serviço de reconhecimento do Google: {e}")