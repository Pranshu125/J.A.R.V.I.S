"""
Drop-in Single-File Plugin Template for J.A.R.V.I.S. / F.R.I.D.A.Y.
Copy this file to `plugins/my_plugin.py` (remove leading underscore) to unlock a new skill automatically.
"""

def my_custom_skill(parameters: dict, player=None, speak=None) -> str:
    topic = parameters.get("topic", "general")
    if player:
        player.write_log(f"[CustomSkill] Running on topic: {topic}")
    return f"Custom skill executed for {topic}, sir."


PLUGIN = {
    "name": "my_custom_skill",
    "description": "Template skill demonstrating the 1-file drop-in plugin architecture.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "topic": {"type": "STRING", "description": "Topic to process"},
        },
        "required": ["topic"],
    },
    "handler": my_custom_skill,
}
