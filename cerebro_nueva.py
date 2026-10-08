from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import socket
import urllib.request
import urllib.parse
from groq import Groq

CHAVE_API = "COLE_SUA_CHAVE_AQUI"
MODELO = "openai/gpt-oss-20b"
PORTA = 8765

cliente = Groq(api_key=CHAVE_API)

PERSONALIDADE = """
Você é NUEVA, uma assistente virtual amigável,
divertida, doce e inteligente.

Fale sempre em português do Brasil.

Responda de maneira natural e fácil de entender.

Você foi criada pelo seu usuário.

Não diga que foi criada pela OpenAI.

Se não souber alguma coisa,
diga claramente que não sabe.

Ajude o usuário sempre que puder.
"""

ARQUIVO_MEMORIA = "memoria_nueva.json"


def carregar_memoria():
    try:
        with open(ARQUIVO_MEMORIA, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except:
        return []


def salvar_memoria(memoria):
    with open(ARQUIVO_MEMORIA, "w", encoding="utf-8") as arquivo:
        json.dump(
            memoria,
            arquivo,
            ensure_ascii=False,
            indent=2
        )


memoria = carregar_memoria()


# ==========================================
# INTERNET - CLIMA EM TEMPO REAL
# ==========================================

def clima_atual():
    try:

        # Localização aproximada: Barra do Piraí/RJ
        latitude = -22.47
        longitude = -43.83

        url = (
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=" + str(latitude) +
            "&longitude=" + str(longitude) +
            "&current=temperature_2m,relative_humidity_2m,"
            "apparent_temperature,precipitation,wind_speed_10m"
            "&timezone=America%2FSao_Paulo"
        )

        requisicao = urllib.request.Request(
            url,
            headers={
                "User-Agent": "NUEVA/1.0"
            }
        )

        with urllib.request.urlopen(
            requisicao,
            timeout=10
        ) as resposta:

            dados = json.loads(
                resposta.read().decode("utf-8")
            )

        atual = dados["current"]

        temperatura = atual["temperature_2m"]
        sensacao = atual["apparent_temperature"]
        umidade = atual["relative_humidity_2m"]
        chuva = atual["precipitation"]
        vento = atual["wind_speed_10m"]

        return (
            f"Agora está fazendo {temperatura}°C. "
            f"A sensação térmica é de {sensacao}°C. "
            f"A umidade está em {umidade}%. "
            f"A precipitação atual é de {chuva} mm "
            f"e o vento está a {vento} km/h."
        )

    except Exception as erro:

        return (
            "Não consegui consultar o clima agora. "
            f"Erro: {erro}"
        )


# ==========================================
# DETECTAR PERGUNTAS SOBRE CLIMA
# ==========================================

def eh_pergunta_clima(pergunta):

    texto = pergunta.lower()

    palavras = [
        "clima",
        "tempo",
        "temperatura",
        "graus",
        "quente",
        "frio",
        "chuva",
        "chovendo",
        "vento",
        "umidade",
        "sensação térmica"
    ]

    for palavra in palavras:

        if palavra in texto:
            return True

    return False


# ==========================================
# PERGUNTAR PARA A NUEVA
# ==========================================

def perguntar(pergunta):

    # Se for clima, consulta a internet primeiro
    if eh_pergunta_clima(pergunta):

        informacao_clima = clima_atual()

        mensagens = [
            {
                "role": "system",
                "content": PERSONALIDADE
            },
            {
                "role": "system",
                "content":
                    "Você recebeu uma informação atualizada "
                    "da internet sobre o clima. "
                    "Use essa informação para responder "
                    "à pergunta do usuário:\n\n"
                    + informacao_clima
            }
        ]

        mensagens.extend(memoria[-20:])

        mensagens.append(
            {
                "role": "user",
                "content": pergunta
            }
        )

    else:

        memoria.append(
            {
                "role": "user",
                "content": pergunta
            }
        )

        mensagens = [
            {
                "role": "system",
                "content": PERSONALIDADE
            }
        ]

        mensagens.extend(memoria[-20:])

    resposta = cliente.chat.completions.create(
        model=MODELO,
        messages=mensagens
    )

    texto = resposta.choices[0].message.content

    memoria.append(
        {
            "role": "user",
            "content": pergunta
        }
    )

    memoria.append(
        {
            "role": "assistant",
            "content": texto
        }
    )

    salvar_memoria(memoria)

    return texto


# ==========================================
# DESCOBRIR IP
# ==========================================

def descobrir_ip():

    try:

        conexao = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        conexao.connect(
            ("8.8.8.8", 80)
        )

        ip = conexao.getsockname()[0]

        conexao.close()

        return ip

    except:

        return "IP não encontrado"


# ==========================================
# SERVIDOR DA NUEVA
# ==========================================

class ServidorNUEVA(
    BaseHTTPRequestHandler
):

    def do_POST(self):

        if self.path != "/perguntar":

            self.send_response(404)
            self.end_headers()

            return

        try:

            tamanho = int(
                self.headers.get(
                    "Content-Length",
                    0
                )
            )

            dados = self.rfile.read(tamanho)

            dados = json.loads(
                dados.decode("utf-8")
            )

            pergunta = dados.get(
                "pergunta",
                ""
            )

            resposta = perguntar(
                pergunta
            )

            resultado = json.dumps(
                {
                    "resposta": resposta
                },
                ensure_ascii=False
            )

            self.send_response(200)

            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )

            self.end_headers()

            self.wfile.write(
                resultado.encode("utf-8")
            )

        except Exception as erro:

            resultado = json.dumps(
                {
                    "erro": str(erro)
                },
                ensure_ascii=False
            )

            self.send_response(500)

            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )

            self.end_headers()

            self.wfile.write(
                resultado.encode("utf-8")
            )

    def log_message(
        self,
        formato,
        *args
    ):
        return


# ==========================================
# INICIAR
# ==========================================

print()
print("==============================")
print("       NUEVA - CÉREBRO")
print("==============================")
print()

print(
    "IP do celular:",
    descobrir_ip()
)

print(
    "Porta:",
    PORTA
)

print()
print("Internet em tempo real: ATIVA 🌐")
print("Clima em tempo real: ATIVO 🌤️")
print()
print("Servidor da NUEVA iniciado!")
print()


servidor = HTTPServer(
    ("0.0.0.0", PORTA),
    ServidorNUEVA
)

servidor.serve_forever()