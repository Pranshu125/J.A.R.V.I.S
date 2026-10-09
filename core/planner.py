import json

class HuggingGPTPlanner:
    """
    Stage 1 & 2 of the HuggingGPT Architecture.
    Takes a user query, parses it into a Directed Acyclic Graph (DAG) of sub-tasks.
    """
    @staticmethod
    def parse_tasks(llm_generate_func, user_query, window):
        prompt = (
            "You are an AI Task Planner. Break the user's request into a JSON array of sub-tasks. "
            "Each task must have an 'id', 'action' (the plugin name), and 'dep' (dependencies, or [-1]).\n"
            "Example Request: 'Search for weather in Tokyo and then tell me if I need an umbrella.'\n"
            "Output:\n"
            "[\n"
            "  {\"id\": \"task_1\", \"action\": \"web_search\", \"dep\": [-1], \"args\": \"Weather in Tokyo\"},\n"
            "  {\"id\": \"task_2\", \"action\": \"generate_response\", \"dep\": [\"task_1\"], \"args\": \"Based on <GENERATED>-task_1, do I need an umbrella?\"}\n"
            "]\n\n"
            f"User Request: {user_query}\n"
            "Strict JSON Output only:"
        )
        
        try:
            window.evaluate_js("addLog('SYSTEM', 'HuggingGPT: DAG Task Planning...')")
            json_str = llm_generate_func(prompt, window)
            # Try to extract just the JSON part in case LLM added conversation text
            start = json_str.find("[")
            end = json_str.rfind("]") + 1
            if start != -1 and end != 0:
                return json.loads(json_str[start:end])
        except Exception as e:
            window.evaluate_js(f"addLog('SYSTEM', 'Planner Fallback: {str(e)}')")
        
        # Fallback to a single generic task if JSON parsing fails
        return [{"id": "task_1", "action": "generate_response", "dep": [-1], "args": user_query}]
