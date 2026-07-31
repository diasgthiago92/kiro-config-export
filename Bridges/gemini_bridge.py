#!/usr/bin/env python3
"""MCP Bridge para Gemini (Antigravity CLI) — usa autenticação local existente."""

import json
import sys
import subprocess

AGY_BIN = "/Users/[YOUR_USER]/.local/bin/agy"

TOOLS = {
    "gemini_chat": {
        "description": "Envia prompt ao Gemini via Antigravity CLI e retorna resposta",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Prompt a enviar ao Gemini"},
                "model": {"type": "string", "description": "Modelo (opcional, default: gemini-3.6-flash)"},
                "system_instruction": {"type": "string", "description": "Contexto/papel para o Gemini assumir (prefixado ao prompt)"},
                "effort": {"type": "string", "enum": ["low", "medium", "high"], "description": "Profundidade de raciocínio (low/medium/high). Default: high"}
            },
            "required": ["prompt"]
        }
    }
}


def handle_request(request):
    method = request.get("method")

    if method == "tools/list":
        return {"tools": [{"name": k, **v} for k, v in TOOLS.items()]}

    if method == "tools/call":
        params = request["params"]
        args = params.get("arguments", {})

        if params["name"] == "gemini_chat":
            prompt = args["prompt"]
            system = args.get("system_instruction")
            model = args.get("model")
            effort = args.get("effort", "high")

            # Se tem system instruction, prefixa ao prompt
            if system:
                full_prompt = f"[Instrução de sistema: {system}]\n\n{prompt}"
            else:
                full_prompt = prompt

            cmd = [AGY_BIN, "-p", full_prompt, "--sandbox"]
            if model:
                cmd.extend(["--model", model])
            if effort:
                cmd.extend(["--effort", effort])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip() or "Erro desconhecido"
                return {"content": [{"type": "text", "text": f"ERRO: {error_msg}"}]}

            return {"content": [{"type": "text", "text": result.stdout.strip()}]}

    return {"error": f"Unknown method: {method}"}


def main():
    input_data = sys.stdin.read()
    request = json.loads(input_data)
    result = handle_request(request)
    print(json.dumps({"jsonrpc": "2.0", "id": request.get("id", 1), "result": result}))


if __name__ == "__main__":
    main()
