import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def get_all_links(base_url):
    try:
        response = requests.get(base_url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except requests.RequestException as e:
        st.error(f"Failed to fetch {base_url}: {e}")
        return set()

    soup = BeautifulSoup(response.text, "html.parser")
    all_links = set()

    for link in soup.find_all("a", href=True):
        href = link["href"]
        full_link = urljoin(base_url, href)
        parsed_link = urlparse(full_link)
        if parsed_link.netloc == urlparse(base_url).netloc:
            all_links.add(full_link)

    return all_links

def extract_pdfs(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except requests.RequestException as e:
        st.error(f"Failed to fetch {url}: {e}")
        return set()

    soup = BeautifulSoup(response.text, "html.parser")
    pdf_links = set()
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if ".pdf" in href.lower():
            pdf_links.add(urljoin(url, href))

    return pdf_links

def scrape_pdfs(start_url):
    visited_pages = set()
    pdf_links = set()
    pages_to_visit = {start_url}

    while pages_to_visit:
        current_page = pages_to_visit.pop()
        if current_page in visited_pages:
            continue

        visited_pages.add(current_page)
        pdf_links.update(extract_pdfs(current_page))
        new_links = get_all_links(current_page)
        pages_to_visit.update(new_links - visited_pages)

    return list(pdf_links)

def main():
    st.title("PDF Scraper with Pagination")
    start_url = st.text_input("Enter a URL to scrape PDFs:", "https://www.imy.se/tillsyner/")
    if st.button("Scrape PDFs"):
        with st.spinner("Scraping..."):
            pdfs = scrape_pdfs(start_url)
            st.session_state["pdf_links"] = pdfs
            st.session_state["page"] = 1

    if "pdf_links" in st.session_state:
        pdfs = st.session_state["pdf_links"]
        page = st.session_state.get("page", 1)
        per_page = 10
        total_pages = (len(pdfs) + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page

        st.write(f"Showing {min(len(pdfs), end_idx)}/{len(pdfs)} PDFs")
        for pdf in pdfs[start_idx:end_idx]:
            st.markdown(f"[Download PDF]({pdf})")

        col1, col2 = st.columns([1, 1])
        with col1:
            if page > 1:
                if st.button("Previous"):
                    st.session_state["page"] = page - 1
                    st.experimental_rerun()
        with col2:
            if page < total_pages:
                if st.button("Next"):
                    st.session_state["page"] = page + 1
                    st.experimental_rerun()

if __name__ == "__main__":
    main()
