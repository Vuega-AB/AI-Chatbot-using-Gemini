import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Base URL
base_url = "https://www.imy.se/tillsyner/?query=&page="
base_site = "https://www.imy.se"

pdf_links = []

# Scrape first 5 pages
for page in range(1, 6):
    url = f"{base_url}{page}"
    print(f"Scraping page {page}...")

    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        continue  # Skip to next page

    # Parse HTML
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all links leading to report pages
    links = soup.find_all("a", href=True)

    report_links = []
    for link in links:
        href = link["href"]
        if "tillsyn" in href and not href.endswith(".pdf"):  # Ensure it's a report page
            full_link = urljoin(base_site, href)
            report_links.append(full_link)

    print(f"Found {len(report_links)} report pages on page {page}.")  # Debugging

    # Visit each report page and extract PDF links
    for report_url in report_links:
        try:
            report_response = requests.get(report_url, headers={"User-Agent": "Mozilla/5.0"})
            report_response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to fetch {report_url}: {e}")
            continue  # Skip to next report page

        report_soup = BeautifulSoup(report_response.text, "html.parser")
        pdfs = report_soup.find_all("a", href=True)

        found_pdf = False  # Track if we find PDFs on this page

        for pdf in pdfs:
            pdf_href = pdf["href"]
            if ".pdf" in pdf_href:
                pdf_link = urljoin(base_site, pdf_href.lstrip("/"))
                pdf_links.append(pdf_link)
                found_pdf = True
        
        if not found_pdf:
            print(f"No PDFs found on {report_url}")  # Debugging

# Print results
print(f"Found {len(pdf_links)} PDF links:")
for pdf in pdf_links:
    print(pdf)
