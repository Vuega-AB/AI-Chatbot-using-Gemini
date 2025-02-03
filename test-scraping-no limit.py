import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def get_all_links(base_url):
    """Extract all navigable links from the given page."""
    try:
        response = requests.get(base_url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch {base_url}: {e}")
        return set()

    soup = BeautifulSoup(response.text, "html.parser")
    all_links = set()

    for link in soup.find_all("a", href=True):
        href = link["href"]
        full_link = urljoin(base_url, href)
        parsed_link = urlparse(full_link)

        # Ignore links that navigate to external sites
        if parsed_link.netloc == urlparse(base_url).netloc:
            all_links.add(full_link)

    return all_links

def extract_pdfs(url):
    """Extract all PDF links from a given page."""
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return set()

    soup = BeautifulSoup(response.text, "html.parser")
    pdf_links = set()

    for link in soup.find_all("a", href=True):
        href = link["href"]
        if ".pdf" in href.lower():
            pdf_links.add(urljoin(url, href))

    return pdf_links

def scrape_pdfs(start_url):
    """Crawl pages and collect all PDF links."""
    visited_pages = set()
    pdf_links = set()
    pages_to_visit = {start_url}

    while pages_to_visit:
        current_page = pages_to_visit.pop()
        if current_page in visited_pages:
            continue

        visited_pages.add(current_page)
        print(f"Visiting: {current_page}")

        # Extract PDFs
        pdf_links.update(extract_pdfs(current_page))

        # Find more pages to visit
        new_links = get_all_links(current_page)
        pages_to_visit.update(new_links - visited_pages)

    print(f"\nFound {len(pdf_links)} PDF links:")
    for pdf in pdf_links:
        print(pdf)

# Example usage
start_url = "https://www.imy.se/tillsyner/"  # Change this to any starting URL
scrape_pdfs(start_url)
