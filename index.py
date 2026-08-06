import os
import sys
import re
import threading
import queue
import contextlib
import tempfile

import speech_recognition as sr
import gtts
import tkinter as tk
from tkinter import scrolledtext
from pygame import mixer
import time

# ============================================================
#  Funções de voz (mantidas do código original)
# ============================================================

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
        os.close(devnull)

def falar(texto):
    """Fala um texto usando a voz do Google (gTTS)."""
    tts = gtts.gTTS(text=texto, lang='pt-br')
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as fp:
        tts.save(fp.name)
        caminho = fp.name
    mixer.init()
    mixer.music.load(caminho)
    mixer.music.play()
    while mixer.music.get_busy():
        time.sleep(0.1)
    mixer.music.unload()  # aqui ele solta o arquivo
    os.unlink(caminho)

# ============================================================
#  Interface Gráfica (Tkinter)
# ============================================================

class AssistenteVozGUI:
    """Interface desktop para o assistente de voz."""

    # Cores (paleta esmaecida estilo Catppuccin)
    COR_FUNDO = "#1e1e2e"
    COR_CHAT = "#313244"
    COR_TEXTO = "#cdd6f4"
    COR_USER = "#89b4fa"
    COR_BOT = "#a6e3a1"
    COR_SISTEMA = "#f9e2af"
    COR_MIC_PRONTO = "#a6e3a1"
    COR_MIC_OUVINDO = "#f38ba8"
    COR_MIC_PROCESSANDO = "#f9e2af"

    def __init__(self, root):
        self.root = root
        self.root.title("Assistente de Voz")
        self.root.geometry("520x650")
        self.root.configure(bg=self.COR_FUNDO)
        self.root.resizable(False, False)

        # Estado interno
        self.nome = ""
        self.ouvindo = False
        self.processando = False
        self.fila_eventos = queue.Queue()

        self._montar_interface()
        self._processar_fila()

    # --------------------------------------------------------
    #  Montagem da interface
    # --------------------------------------------------------

    def _montar_interface(self):
        """Constói todos os elementos visuais da janela."""

        # Título
        tk.Label(
            self.root, text="🎙️ Assistente de Voz",
            font=("Segoe UI", 16, "bold"),
            bg=self.COR_FUNDO, fg=self.COR_TEXTO
        ).pack(pady=(15, 2))

        tk.Label(
            self.root, text="Clique no microfone ou digite um comando",
            font=("Segoe UI", 9),
            bg=self.COR_FUNDO, fg="#9399b2"
        ).pack(pady=(0, 8))

        # Área de chat (histórico de conversa)
        frame_chat = tk.Frame(self.root, bg=self.COR_FUNDO)
        frame_chat.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 8))

        self.chat = scrolledtext.ScrolledText(
            frame_chat, wrap=tk.WORD,
            font=("Segoe UI", 11),
            bg=self.COR_CHAT, fg=self.COR_TEXTO,
            insertbackground=self.COR_TEXTO,
            relief=tk.FLAT, bd=0,
            state=tk.DISABLED
        )
        self.chat.pack(fill=tk.BOTH, expand=True)

        # Tags de cor para cada tipo de mensagem
        self.chat.tag_config("user", foreground=self.COR_USER, font=("Segoe UI", 11, "bold"))
        self.chat.tag_config("bot", foreground=self.COR_BOT, font=("Segoe UI", 11, "bold"))
        self.chat.tag_config("system", foreground=self.COR_SISTEMA, font=("Segoe UI", 10, "italic"))

        # Label de status (logo abaixo do chat)
        self.status_label = tk.Label(
            self.root, text="Pronto",
            font=("Segoe UI", 10),
            bg=self.COR_FUNDO, fg="#9399b2"
        )
        self.status_label.pack(pady=(0, 5))

        # Botão de microfone
        self.btn_mic = tk.Button(
            self.root, text="🎤 Ouvir",
            font=("Segoe UI", 13, "bold"),
            bg=self.COR_MIC_PRONTO, fg=self.COR_FUNDO,
            activebackground="#89d884", activeforeground=self.COR_FUNDO,
            relief=tk.FLAT, bd=0,
            width=15, height=2,
            cursor="hand2",
            command=self.alternar_escuta
        )
        self.btn_mic.pack(pady=(0, 10))

        # Campo de texto (bônus: digitar comandos além de falar)
        frame_entry = tk.Frame(self.root, bg=self.COR_FUNDO)
        frame_entry.pack(fill=tk.X, padx=15, pady=(0, 15))

        self.entry = tk.Entry(
            frame_entry,
            font=("Segoe UI", 11),
            bg=self.COR_CHAT, fg=self.COR_TEXTO,
            insertbackground=self.COR_TEXTO,
            relief=tk.FLAT, bd=0
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 5))
        self.entry.bind("<Return>", lambda e: self.enviar_texto())

        tk.Button(
            frame_entry, text="Enviar",
            font=("Segoe UI", 10, "bold"),
            bg=self.COR_USER, fg=self.COR_FUNDO,
            activebackground="#74a8fc", activeforeground=self.COR_FUNDO,
            relief=tk.FLAT, bd=0,
            padx=15, cursor="hand2",
            command=self.enviar_texto
        ).pack(side=tk.RIGHT)

        # Mensagem de boas-vindas
        self._adicionar_chat("Assistente", "Olá! Clique no microfone ou digite algo pra começar.", "bot")

    # --------------------------------------------------------
    #  Manipulação do chat
    # --------------------------------------------------------

    def _adicionar_chat(self, remetente, texto, tag):
        """Adiciona uma mensagem na área de chat (sempre na main thread)."""
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, f"{remetente}: ", tag)
        self.chat.insert(tk.END, f"{texto}\n\n")
        self.chat.see(tk.END)
        self.chat.config(state=tk.DISABLED)

    # --------------------------------------------------------
    #  Fila de eventos (ponte entre threads)
    # --------------------------------------------------------

    def _enviar_evento(self, **evento):
        """Coloca um evento na fila (pode ser chamado de qualquer thread)."""
        self.fila_eventos.put(evento)

    def _processar_fila(self):
        """Lê e processa eventos da fila (roda na main thread via after)."""
        try:
            while True:
                evt = self.fila_eventos.get_nowait()
                tipo = evt.get("tipo")

                if tipo == "chat":
                    self._adicionar_chat(evt["remetente"], evt["texto"], evt["tag"])

                elif tipo == "status":
                    self.status_label.config(text=evt["texto"])

                elif tipo == "botao":
                    self.btn_mic.config(
                        text=evt["texto"],
                        bg=evt["bg"],
                        activebackground=evt.get("active_bg", evt["bg"])
                    )

                elif tipo == "sair":
                    self.root.after(300, self.root.quit)

        except queue.Empty:
            pass

        # Reagenda a verificação da fila a cada 100ms
        self.root.after(100, self._processar_fila)

    # --------------------------------------------------------
    #  Reconhecimento de voz (thread separada)
    # --------------------------------------------------------

    def alternar_escuta(self):
        """Inicia a escuta do microfone numa thread separada."""
        if self.ouvindo or self.processando:
            return  # Já está ocupado, ignora o clique

        threading.Thread(target=self._escutar, daemon=True).start()

    def _escutar(self):
        """Worker: escuta o microfone, reconhece e processa o comando."""
        self.ouvindo = True

        # Botão vermelho: ouvindo
        self._enviar_evento(
            tipo="botao",
            texto="🔴 Ouvindo...",
            bg=self.COR_MIC_OUVINDO,
            active_bg="#eb6f92"
        )
        self._enviar_evento(tipo="status", texto="Ouvindo... fale algo")

        try:
            with silenciar_alsa():
                with sr.Microphone() as source:
                    mic = sr.Recognizer()
                    mic.adjust_for_ambient_noise(source, duration=1)
                    audio = mic.listen(source, timeout=5, phrase_time_limit=10)

            # Botão amarelo: processando
            self.processando = True
            self.ouvindo = False
            self._enviar_evento(
                tipo="botao",
                texto="⚡ Processando...",
                bg=self.COR_MIC_PROCESSANDO,
                active_bg="#e6d99b"
            )
            self._enviar_evento(tipo="status", texto="Processando...")

            frase = mic.recognize_google(audio, language='pt-BR')

            # Mostra o que o usuário falou
            self._enviar_evento(tipo="chat", remetente="Você", texto=frase, tag="user")

            # Processa e responde
            resposta = self._processar_comando(frase)
            self._enviar_evento(tipo="chat", remetente="Assistente", texto=resposta, tag="bot")

            # Fala a resposta (na própria thread, não trava a GUI)
            falar(resposta)

            # Se foi comando de sair, fecha a janela
            if 'sair' in frase.lower() or 'encerrar' in frase.lower():
                self._enviar_evento(tipo="sair")

        except sr.WaitTimeoutError:
            self._enviar_evento(
                tipo="chat", remetente="Sistema",
                texto="Nenhum áudio detectado no tempo limite.", tag="system"
            )
        except sr.UnknownValueError:
            self._enviar_evento(
                tipo="chat", remetente="Sistema",
                texto="Não entendi, pode repetir?", tag="system"
            )
            falar("Não entendi, pode repetir?")
        except sr.RequestError as e:
            self._enviar_evento(
                tipo="chat", remetente="Sistema",
                texto=f"Erro no serviço do Google: {e}", tag="system"
            )

        finally:
            self.ouvindo = False
            self.processando = False
            # Botão verde: pronto
            self._enviar_evento(
                tipo="botao",
                texto="🎤 Ouvir",
                bg=self.COR_MIC_PRONTO,
                active_bg="#89d884"
            )
            self._enviar_evento(tipo="status", texto="Pronto")

    # --------------------------------------------------------
    #  Envio por texto (campo de digitação)
    # --------------------------------------------------------

    def enviar_texto(self):
        """Processa comando digitado no campo de texto."""
        texto = self.entry.get().strip()
        if not texto:
            return

        self.entry.delete(0, tk.END)

        # Mostra o texto do usuário
        self._adicionar_chat("Você", texto, "user")

        # Processa e mostra a resposta
        resposta = self._processar_comando(texto)
        self._adicionar_chat("Assistente", resposta, "bot")

        # Fala a resposta numa thread separada (não trava a GUI)
        threading.Thread(target=falar, args=(resposta,), daemon=True).start()

        # Comando de sair
        if 'sair' in texto.lower() or 'encerrar' in texto.lower():
            self.root.after(500, self.root.quit)

    # --------------------------------------------------------
    #  Lógica de comandos (igual ao código original)
    # --------------------------------------------------------

    def _processar_comando(self, frase):
        """Processa a frase reconhecida/digitada e retorna a resposta."""
        frase_lower = frase.lower()

        if 'ajudar' in frase_lower:
            return "Em que posso ajudar?"

        elif 'meu nome é' in frase_lower:
            match = re.search(r'meu nome é (.+)', frase, re.IGNORECASE)
            if match:
                self.nome = match.group(1).strip()
                return f"Muito prazer, {self.nome}!"
            return "Não consegui entender seu nome."

        elif 'meu nome' in frase_lower and self.nome:
            return f"Seu nome é {self.nome}"

        elif 'sair' in frase_lower or 'encerrar' in frase_lower:
            return "Até logo!"

        else:
            return f"Você disse: {frase}"

# ============================================================
#  Inicialização
# ============================================================

def main():
    root = tk.Tk()
    app = AssistenteVozGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()