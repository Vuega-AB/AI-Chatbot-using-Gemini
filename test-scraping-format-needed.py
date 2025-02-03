import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def scrape_pdfs(base_url, base_site, max_pages=5):
    pdf_links = []
    
    for page in range(0, max_pages + 1):
        url = f"{base_url}{page}"
        print(f"Scraping page {page}...")

        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to fetch {url}: {e}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.find_all("a", href=True)

        report_links = [urljoin(base_site, link["href"]) for link in links if "tillsyn" in link["href"] and not link["href"].endswith(".pdf")]
        print(f"Found {len(report_links)} report pages on page {page}.")

        for report_url in report_links:
            try:
                report_response = requests.get(report_url, headers={"User-Agent": "Mozilla/5.0"})
                report_response.raise_for_status()
            except requests.RequestException as e:
                print(f"Failed to fetch {report_url}: {e}")
                continue

            report_soup = BeautifulSoup(report_response.text, "html.parser")
            pdfs = report_soup.find_all("a", href=True)
            
            for pdf in pdfs:
                pdf_href = pdf["href"]
                if ".pdf" in pdf_href:
                    pdf_link = urljoin(base_site, pdf_href.lstrip("/"))
                    pdf_links.append(pdf_link)
    
    print(f"Found {len(pdf_links)} PDF links:")
    for pdf in pdf_links:
        print(pdf)
    
    return pdf_links

# Example usage
if __name__ == "__main__":
    base_url = input("Enter the base URL (with page parameter placeholder): ")
    base_site = input("Enter the base site URL: ")
    max_pages = int(input("Enter the number of pages to scrape: "))
    scrape_pdfs(base_url, base_site, max_pages)
