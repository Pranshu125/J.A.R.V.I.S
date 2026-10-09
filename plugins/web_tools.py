from core.plugin_manager import registry
import webbrowser

@registry.register(
    name="web_search",
    description="Searches the web invisibly for facts. Argument should be the query."
)
def web_search(query):
    try:
        from duckduckgo_search import DDGS
        results = DDGS().text(query, max_results=1)
        if results:
            return results[0]['body']
        return "No results found."
    except Exception as e:
        return str(e)

@registry.register(
    name="open_browser",
    description="Physically opens the web browser to a search query or URL."
)
def open_browser(query):
    webbrowser.open(f"https://www.google.com/search?q={query}")
    return f"Browser opened to {query}"
