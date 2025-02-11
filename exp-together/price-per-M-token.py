import requests
from bs4 import BeautifulSoup

# URL of Together AI pricing page
URL = "https://www.together.ai/pricing#inference"

def get_all_model_pricing():
    response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code != 200:
        return {"Error": "Failed to fetch pricing data"}
    
    soup = BeautifulSoup(response.text, "html.parser")

    pricing_data = []

    # Find all model blocks
    model_blocks = soup.find_all("li", class_="pricing_item")

    for model_block in model_blocks:
        # Extract model name from the pricing head
        model_name_tag = model_block.find("h3", class_="heading-style-h8")
        model_name = model_name_tag.get_text(strip=True) if model_name_tag else "Unknown Model"

        # Extract all pricing variations inside the model
        variations = model_block.find_all("li", class_="pricing_content-row")

        for variation in variations:
            cols = variation.find_all("div", class_="pricing_content-cell")

            if len(cols) >= 2:
                variant_name = cols[0].get_text(strip=True)
                price = cols[1].get_text(strip=True)

                pricing_data.append({
                    "Model": model_name,
                    "Variant": variant_name,
                    "Price": price
                })

    return pricing_data

# Fetch and print model pricing dynamically
pricing_info = get_all_model_pricing()
for entry in pricing_info:
    print(entry)
