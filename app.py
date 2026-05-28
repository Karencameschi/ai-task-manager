import os
from flask import Flask, render_template, request, jsonify
from anthropic import Anthropic, APIError
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

api_key = os.getenv("ANTHROPIC_API_KEY")
client = Anthropic(api_key=api_key)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze_task():
    data = request.get_json()
    task = data.get("task", "")

    if not task.strip():
        return jsonify({"error": "Por favor, insira uma tarefa."}), 400
    
    system_prompt = """Você é um assistente de produtividade. Analise a tarefa recebida e responda EXATAMENTE neste formato (sem texto extra):
PRIORIDADE: [Alta/Média/Baixa]
TEMPO ESTIMADO: [ex: 2 horas, 30 minutos]
DIFICULDADE: [Fácil/Médio/Difícil]
SUBTAREFAS:
- [subtarefa 1]
- [subtarefa 2]
- [subtarefa 3]
DICA: [uma dica rápida para executar essa tarefa]"""
    
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user","content": f"Tarefa: {task}"}
            ]
        )

        response_text = message.content[0].text
        result = parse_response(response_text)
        return jsonify(result)
    
    except APIError as e:
        return jsonify({"error": "Erro de comunicação com a IA. Verifique sua API Key."}), 500
    except Exception as e:
        return jsonify({"error": "Ocorreu um erro interno no servidor."}), 500
    

def parse_response(text: str) -> dict:
    
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