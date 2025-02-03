import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pdfplumber
import os

def scrape_pdfs(base_url, base_site, max_pages=5):
    """Scrapes PDF links from the given website."""
    pdf_links = []
    
    for page in range(1, max_pages + 1):
        url = f"{base_url}{page}"
        st.write(f"🔍 Scraping page {page}...")

        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
        except requests.RequestException as e:
            st.error(f"❌ Failed to fetch {url}: {e}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.find_all("a", href=True)

        report_links = [urljoin(base_site, link["href"]) for link in links if "tillsyn" in link["href"] and not link["href"].endswith(".pdf")]
        st.write(f"📄 Found {len(report_links)} report pages on page {page}.")

        for report_url in report_links:
            try:
                report_response = requests.get(report_url, headers={"User-Agent": "Mozilla/5.0"})
                report_response.raise_for_status()
            except requests.RequestException as e:
                st.error(f"❌ Failed to fetch {report_url}: {e}")
                continue

            report_soup = BeautifulSoup(report_response.text, "html.parser")
            pdfs = report_soup.find_all("a", href=True)
            
            for pdf in pdfs:
                pdf_href = pdf["href"]
                if ".pdf" in pdf_href:
                    pdf_link = urljoin(base_site, pdf_href.lstrip("/"))
                    pdf_links.append(pdf_link)
    
    st.write(f"✅ Found {len(pdf_links)} PDF links:")
    return pdf_links

def download_pdf(pdf_url):
    """Downloads a PDF file and returns the file path."""
    pdf_name = os.path.basename(urlparse(pdf_url).path)  # Extract filename from URL
    save_path = f"downloads/{pdf_name}"

    os.makedirs("downloads", exist_ok=True)  # Ensure folder exists

    try:
        response = requests.get(pdf_url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        with open(save_path, "wb") as file:
            file.write(response.content)
        return save_path, pdf_name
    except requests.RequestException as e:
        st.error(f"❌ Failed to download PDF {pdf_url}: {e}")
        return None, None

def extract_text_from_pdf(pdf_path):
    """Extracts text from a downloaded PDF file."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text + "\n"
    except Exception as e:
        st.error(f"⚠️ Error extracting text from {pdf_path}: {e}")
    
    return text

# Streamlit UI
st.title("📄 PDF Scraper & Text Extractor")

base_url = st.text_input("🌐 Enter the base URL (with page parameter placeholder):")
base_site = st.text_input("🏠 Enter the base site URL:")
max_pages = st.number_input("📄 Enter the number of pages to scrape:", min_value=1, value=5, step=1)

if st.button("🚀 Start Scraping"):
    pdf_links = scrape_pdfs(base_url, base_site, max_pages)

    if pdf_links:
        first_pdf_url = pdf_links[0]
        pdf_path, pdf_name = download_pdf(first_pdf_url)

        if pdf_path:
            st.success(f"✅ Successfully downloaded: **{pdf_name}**")

            text = extract_text_from_pdf(pdf_path)
            text_file_path = f"downloads/{pdf_name.replace('.pdf', '.txt')}"

            with open(text_file_path, "w", encoding="utf-8") as f:
                f.write(text)

            st.write("📜 **Extracted Text Preview:**")
            st.text_area("Preview:", text[:1000])  # Display first 1000 characters

            st.download_button(
                label=f"📥 Download Extracted Text - {pdf_name.replace('.pdf', '.txt')}",
                data=text,
                file_name=pdf_name.replace('.pdf', '.txt'),
                mime="text/plain",
            )

            st.download_button(
                label=f"📥 Download Original PDF - {pdf_name}",
                data=open(pdf_path, "rb").read(),
                file_name=pdf_name,
                mime="application/pdf",
            )
