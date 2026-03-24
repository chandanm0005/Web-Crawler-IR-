from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import urllib3

# Disable SSL warnings for unverified requests on local environments
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

pages = {}
visited = set()

STOPWORDS = {"is", "a", "the", "and", "in", "are", "for", "of", "to", "on", "with"}

def preprocess(text):
    text = text.lower()
    words = re.findall(r'\w+', text)
    return [word for word in words if word not in STOPWORDS]

def crawl(url, depth=1):
    if depth == 0 or url in visited:
        return
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=5, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        visited.add(url)
        
        text = soup.get_text()
        words = preprocess(text)
        pages[url] = words
        print(f"Crawled: {url} (found {len(words)} words)")
        
        for link in soup.find_all('a', href=True):
            next_url = urljoin(url, link['href'])
            if next_url.startswith("http"):
                crawl(next_url, depth - 1)
                
    except Exception as e:
        print(f"Failed to crawl {url}: {e}")

def search(query):
    query_words = preprocess(query)
    scores = {}
    if not query_words:
        return []
    
    for url, words in pages.items():
        score = sum(words.count(q) for q in query_words)
        if score > 0:
            scores[url] = score
    
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

# Crawl once at start
crawl("https://example.com", depth=1)

@app.route("/", methods=["GET", "POST"])
def home():
    results = []
    message = ""
    query = ""
    url_to_crawl = ""
    
    if request.method == "POST":
        url_to_crawl = request.form.get("url", "").strip()
        query = request.form.get("query", "").strip()
        
        if url_to_crawl:
            crawl(url_to_crawl, depth=1)
            message = f"Successfully indexed '{url_to_crawl}'! "
            
        if query:
            results = search(query)
            if not results:
                message += f"No matches found for '{query}'."
            else:
                message += f"Found matching results for '{query}'."
    
    return render_template("main.html", results=results, message=message, query=query, url_to_crawl=url_to_crawl)

if __name__ == "__main__":
    app.run(debug=True)