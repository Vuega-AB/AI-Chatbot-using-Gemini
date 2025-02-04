import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pdfplumber
import os

def scrape_pdfs(base_url, base_site, max_pages=5):
    pdf_links = set()
    progress_bar = st.progress(0)
    
    for page in range(1, max_pages + 1):
        progress_bar.progress(page / max_pages)
        url = f"{base_url}{page}"
        st.write(f"### Scraping page {page}...")

        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
        except requests.RequestException as e:
            st.error(f"Failed to fetch {url}: {e}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.find_all("a", href=True)
        
        report_links = [urljoin(base_site, link["href"]) for link in links if "tillsyn" in link["href"] and not link["href"].endswith(".pdf")]
        st.write(f"Found {len(report_links)} report pages on page {page}.")
        
        for report_url in report_links:
            try:
                report_response = requests.get(report_url, headers={"User-Agent": "Mozilla/5.0"})
                report_response.raise_for_status()
            except requests.RequestException as e:
                st.error(f"Failed to fetch {report_url}: {e}")
                continue

            report_soup = BeautifulSoup(report_response.text, "html.parser")
            pdfs = report_soup.find_all("a", href=True)
            
            for pdf in pdfs:
                pdf_href = pdf["href"]
                if ".pdf" in pdf_href:
                    pdf_link = urljoin(base_site, pdf_href.lstrip("/"))
                    pdf_links.add(pdf_link)
    
    progress_bar.empty()
    pdf_links = list(pdf_links)  # Convert set to list for indexing
    
    if pdf_links:
        st.write(f"## Found {len(pdf_links)} PDF links:")
        for i, pdf in enumerate(pdf_links, start=1):
            st.markdown(f"{i}. [Download PDF]({pdf})")
    else:
        st.warning("No PDF links found.")
    
    return pdf_links

def download_pdf(pdf_url, save_path="sample.pdf"):
    """Downloads a PDF file from a URL."""
    try:
        response = requests.get(pdf_url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        with open(save_path, "wb") as file:
            file.write(response.content)
        return save_path
    except requests.RequestException as e:
        st.error(f"Failed to download PDF {pdf_url}: {e}")
        return None

def extract_text_from_pdf(pdf_path):
    """Extracts text from a downloaded PDF file."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        st.error(f"Error extracting text from {pdf_path}: {e}")
    
    return text

st.title("📄 PDF Scraper & Text Extractor")
st.markdown("This tool scrapes and extracts text from PDF files found on specified websites.")

base_url = st.text_input("Enter the base URL (with page parameter placeholder):")
base_site = st.text_input("Enter the base site URL:")
max_pages = st.number_input("Enter the number of pages to scrape:", min_value=1, value=5, step=1)

if st.button("🔍 Start Scraping"):
    pdf_links = scrape_pdfs(base_url, base_site, max_pages)
    if pdf_links:
        first_pdf_url = pdf_links[0]
        st.write(f"### Downloading first PDF: [Click here]({first_pdf_url})")

        pdf_path = download_pdf(first_pdf_url, "sample.pdf")
        if pdf_path:
            text = extract_text_from_pdf(pdf_path)
            
            # Save the text to a file
            text_file_path = "extracted_text.txt"
            with open(text_file_path, "w", encoding="utf-8") as f:
                f.write(text)
            
            st.success("Extracted text saved successfully.")
            
            with st.expander("📜 Extracted Text Preview"):
                st.text_area("Extracted Text:", text[:1000], height=300)
