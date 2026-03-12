from urllib.parse import quote_plus
import webbrowser

_browser = None


def _ensure_browser():
    global _browser
    if _browser is None:
        from integrations.browser.selenium_client import SeleniumBrowser

        _browser = SeleniumBrowser(headless=False)
    return _browser


def google_search(query: str) -> str:
    if not query:
        return "I need a query to search."
    try:
        browser = _ensure_browser()
        titles = browser.google_search(query)
        if not titles:
            return "No results found."
        return "Top results: " + " | ".join(titles)
    except Exception:
        url = "https://www.google.com/search?q=" + quote_plus(query)
        webbrowser.open(url)
        return f"Opening Google search for {query}"


def open_link(url: str) -> str:
    browser = _ensure_browser()
    browser.open_url(url)
    return f"Opened {url} in automated browser."


def read_page_title() -> str:
    browser = _ensure_browser()
    return f"Page title is: {browser.get_page_title()}"

