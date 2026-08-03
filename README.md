# 🎙️ Assistente de Voz em Python

Um assistente de voz simples que reconhece fala em português brasileiro e responde com voz natural usando a API do Google. O projeto usa `SpeechRecognition` para capturar áudio do microfone e `gTTS` para síntese de voz.

---

## 📋 Visão Geral

O assistente escuta o microfone, converte a fala em texto usando o reconhecimento de voz do Google, identifica comandos específicos e responde com voz sintetizada. Ele roda em loop contínuo até que o usuário diga "sair" ou "encerrar".

**Comandos disponíveis:**

| Comando | Ação |
|---|---|
| "ajudar" | O assistente pergunta em que pode ajudar |
| "meu nome é [nome]" | Registra o nome do usuário e cumprimenta |
| "meu nome" | Recupera o nome cadastrado |
| "sair" ou "encerrar" | Encerra o programa |

---

## ✅ Pré-requisitos

- **Python 3.8 ou superior**
- **Microfone funcionando** no computador
- **Conexão com internet** (necessária para o reconhecimento de voz e síntese de fala do Google)
- **FFmpeg** (necessário para reproduzir áudio MP3)

---

## 🔧 Instalação

### 1. Instalar o Python

#### Linux (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

#### macOS

```bash
brew install python
```

#### Windows

Baixe o instalador em [python.org](https://www.python.org/downloads/) e marque a opção **"Add Python to PATH"** durante a instalação.

---

### 2. Instalar dependências de áudio do sistema

#### Linux (Debian/Ubuntu)

```bash
sudo apt install portaudio19-dev python3-pyaudio mpg123
```

> **Nota:** O `mpg123` é o player de áudio usado para reproduzir as respostas em voz. O `portaudio19-dev` é necessário para o `pyaudio`, que captura o áudio do microfone.

#### macOS

```bash
brew install portaudio mpg123
```

#### Windows

Não é necessário instalar nada extra. O `pyaudio` no Windows já vem com os binários necessários no pip.

---

### 3. Criar e ativar o ambiente virtual

#### Linux / macOS

```bash
cd /caminho/para/o/projeto
python3 -m venv venv
source venv/bin/activate
```

#### Windows

```cmd
cd C:\caminho\para\o\projeto
python -m venv venv
venv\Scripts\activate
```

> Se aparecer o erro `ensurepip is not available` no Linux, instale o pacote correspondente:
> ```bash
> sudo apt install python3-venv
> ```

---

### 4. Instalar as dependências do Python

Com o ambiente virtual ativado, instale as bibliotecas:

```bash
pip install SpeechRecognition pyaudio gTTS
```

#### Windows (se o pyaudio falhar)

```bash
pip install pipwin
pipwin install pyaudio
```

---

## ⚙️ Configuração do Ambiente

Não há arquivos de configuração adicionais. O projeto não usa chaves de API próprias, pois o `SpeechRecognition` e o `gTTS` utilizam as APIs públicas do Google sem necessidade de autenticação.

---

## ▶️ Como Executar

Com o ambiente virtual ativado e as dependências instaladas:

```bash
python assistente_voz.py
```

Ao iniciar, o assistente vai:

1. Falar "Olá, vamos começar. Fale alguma coisa."
2. Exibir os comandos disponíveis no terminal
3. Começar a escutar o microfone

Fale um dos comandos listados na tabela acima. O assistente vai responder por voz e mostrar no terminal o que reconheceu.

---

## 🧠 Como Funciona

O código é dividido em três partes principais:

### 1. Silenciamento do ALSA (apenas Linux)

```python
@contextlib.contextmanager
def silenciar_alsa():
    ...
```

No Linux, o sistema de áudio ALSA exibe vários avisos no terminal (sobre dispositivos inexistentes, JACK server, etc.) sempre que o microfone é aberto. Esta função redireciona a saída de erro em nível de sistema operacional para `/dev/null` apenas durante a abertura do microfone, mantendo os `print()` normais funcionando.

- **No Windows e macOS**, essa função não tem efeito, pois o ALSA não existe nesses sistemas.

### 2. Síntese de Voz (gTTS)

```python
def falar(texto):
    ...
```

A função `falar()` recebe um texto, envia para a API do Google Text-to-Speech, recebe um arquivo MP3 temporário, toca com o `mpg123` (Linux/macOS) e depois exclui o arquivo.

- A voz é a mesma do Google Tradutor, em português brasileiro (`lang='pt-br'`).
- Há um pequeno delay de 1 a 2 segundos para gerar o áudio, pois depende de uma requisição de internet.

### 3. Loop Principal de Reconhecimento

```python
def main():
    ...
```

O loop principal:

1. Abre o microfone e ajusta o ruído ambiente (`adjust_for_ambient_noise`)
2. Escuta o áudio com tempo limite de 5 segundos e duração máxima de 10 segundos por frase
3. Envia o áudio para o `recognize_google` com idioma `pt-BR`
4. Verifica se a frase contém algum dos comandos programados
5. Executa a ação correspondente (falar, registrar nome, encerrar)
6. Se não reconhecer, exibe "Não entendi, pode repetir?" e continua o loop

### Tratamento de Erros

| Exceção | Quando ocorre |
|---|---|
| `WaitTimeoutError` | Nenhum som foi detectado em 5 segundos |
| `UnknownValueError` | O áudio foi capturado, mas o Google não conseguiu interpretar a fala |
| `RequestError` | Falha de conexão com o serviço do Google (sem internet, por exemplo) |

---

## 📁 Estrutura do Projeto

```
projeto-agenda/
├── assistente_voz.py    # Código principal do assistente
├── venv/                # Ambiente virtual (criado na instalação)
└── README.md            # Este arquivo
```

---

## 📝 Observações Finais

- **Internet é obrigatória:** tanto o reconhecimento de voz quanto a síntese de fala dependem da API do Google. Sem conexão, o assistente não funciona.
- **Qualidade do microfone:** o reconhecimento depende da clareza do áudio. Ambientes muito ruidosos podem reduzir a precisão. O `adjust_for_ambient_noise` ajuda, mas não resolve completamente.
- **Privacidade:** o áudio capturado é enviado para os servidores do Google para processamento. Não use este projeto para processar informações sensíveis.
- **Delay de resposta:** por usar `gTTS` (que gera o áudio online), há um pequeno atraso entre o comando e a resposta. Para respostas instantâneas, considere alternativas offline como `pyttsx3` com `espeak-ng`, embora a qualidade da voz seja inferior.
- **Suporte a voz offline:** se quiser substituir o `gTTS` por uma solução offline, instale `pyttsx3` e `espeak-ng` (Linux) ou use as vozes nativas do sistema (Windows/macOS). A qualidade será mais robótica, mas não precisará de internet para responder.

---

## 🐛 Solução de Problemas

| Problema | Solução |
|---|---|
| `ensurepip is not available` | Instale `python3-venv` (Linux) |
| `mpg123: not found` | Instale com `sudo apt install mpg123` (Linux) ou `brew install mpg123` (macOS) |
| Erro ao instalar `pyaudio` | Instale `portaudio19-dev` antes (Linux) ou use `pipwin` (Windows) |
| Avisos do ALSA no terminal | Já tratado no código com `silenciar_alsa()`. Se persistir, rode com `python assistente_voz.py 2>/dev/null` |
| "Não entendi" repetidamente | Verifique se o microfone está funcionando, fale mais perto e em ambiente silencioso |
| `RequestError` | Verifique sua conexão com a internet |
