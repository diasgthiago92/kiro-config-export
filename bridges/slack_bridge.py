import sys
import json
import os
import requests

def load_env():
    env_path = os.path.expanduser('~/Documents/Main/Brain/.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

def send_message(channel, text):
    token = os.getenv('SLACK_BOT_TOKEN')
    if not token:
        return {"ok": False, "error": "SLACK_BOT_TOKEN não encontrado"}
    resp = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {token}"},
        json={"channel": channel, "text": text}
    )
    return resp.json()

def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        try:
            req = json.loads(line)
            id_ = req.get("id")
            method = req.get("method")

            if method == "initialize":
                response = {"jsonrpc": "2.0", "id": id_, "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "serverInfo": {"name": "slack-bridge", "version": "1.0.0"}
                }}
            elif method == "tools/list":
                response = {"jsonrpc": "2.0", "id": id_, "result": {"tools": [
                    {
                        "name": "send_message",
                        "description": "Envia uma mensagem para um canal ou usuário do Slack",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "channel": {"type": "string", "description": "ID do canal ou usuário (ex: C0B2X8FQ81M)"},
                                "text": {"type": "string", "description": "Texto da mensagem"}
                            },
                            "required": ["channel", "text"]
                        }
                    }
                ]}}
            elif method == "tools/call":
                args = req["params"].get("arguments", {})
                result = send_message(args["channel"], args["text"])
                if result.get("ok"):
                    content = f"✅ Mensagem enviada para {args['channel']}"
                else:
                    content = f"❌ Erro: {result.get('error')}"
                response = {"jsonrpc": "2.0", "id": id_, "result": {
                    "content": [{"type": "text", "text": content}]
                }}
            else:
                response = {"jsonrpc": "2.0", "id": id_, "error": {"code": -32601, "message": "Method not found"}}

            print(json.dumps(response), flush=True)
        except Exception as e:
            print(json.dumps({"jsonrpc": "2.0", "id": id_, "error": {"message": str(e)}}), flush=True)

if __name__ == "__main__":
    main()
