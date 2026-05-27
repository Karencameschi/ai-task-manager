from flask import Flask, render_template, request, jsonify
from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

client = Anthropic()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze_task():
    data = request.get_json()

    task = data.get("task", "")

    if not task.strip():
        return jsonify({"error": "Por favor, insira uma tarefa."}), 400
    prompt = f"""Você é um assistente de produtividade. Analise a seguinte tarefa e responda em português:

Tarefa: {task}

Responda EXATAMENTE neste formato (sem texto extra):
PRIORIDADE: [Alta/Média/Baixa]
TEMPO ESTIMADO: [ex: 2 horas, 30 minutos]
DIFICULDADE: [Fácil/Médio/Difícil]
SUBTAREFAS:
- [subtarefa 1]
- [subtarefa 2]
- [subtarefa 3]
DICA: [uma dica rápida para executar essa tarefa]"""
    
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    response_text = message.content[0].text

    result = parse_response(response_text)

    return jsonify(result)

def parse_response(text):
    """
    Tranforma a resposta em texto da IA em um dicionário organizado.
    Dicionários em Python são como amários com etiquetas (chave: valor).
    """
    result = {
        "prioridade": "Média",
        "tempo": "Indefinido",
        "dificuldade": "Médio",
        "subtarefas": [],
        "dica": "" 
    }

    lines = text.strip().split("\n")

    reading_subtasks = False

    for line in lines:
        line = line.strip()

        if line.startswith("PRIORIDADE:"):
            result["prioridade"] = line.split(": ", 1)[1]
            reading_subtasks = False

        elif line.startswith("TEMPO ESTIMADO:"):
            result["tempo"] = line.split(": ", 1)[1]
            reading_subtasks = False

        elif line.startswith("DIFICULDADE:"):
            result["dificuldade"] = line.split(": ", 1)[1]
            reading_subtasks = False

        elif line.startswith("SUBTAREFAS:"):
            reading_subtasks = True

        elif line.startswith("DICA:"):
            result["dica"] = line.split(": ", 1)[1]
            reading_subtasks = False

        elif reading_subtasks and line.startswith("- "):
            result["subtarefas"].append(line[2:])

    return result

if __name__ == "__main__":
    app.run(debug=True)