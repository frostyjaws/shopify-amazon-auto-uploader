import streamlit as st
import requests
import os
import json
from PIL import Image
from io import BytesIO

# === CREDENTIALS ===
SHOPIFY_TOKEN = st.secrets["SHOPIFY_TOKEN"]
SHOPIFY_STORE = st.secrets["SHOPIFY_STORE"]
IMGBB_API_KEY = st.secrets["IMGBB_API_KEY"]
LWA_CLIENT_ID = st.secrets["LWA_CLIENT_ID"]
LWA_CLIENT_SECRET = st.secrets["LWA_CLIENT_SECRET"]
REFRESH_TOKEN = st.secrets["REFRESH_TOKEN"]
MARKETPLACE_ID = st.secrets["MARKETPLACE_ID"]
SELLER_ID = st.secrets["SELLER_ID"]

DESCRIPTION = """
<p>Celebrate the arrival of your little one with our adorable Custom Baby onesie&reg;, the perfect baby shower gift that will be cherished for years to come...</p>
"""

BULLETS = [
    "🎨 High-Quality Ink Printing: Our Baby Bodysuit features vibrant, long-lasting colors...",
    "🎖️ Proudly Veteran-Owned: Show your support for our heroes...",
    "👶 Comfort and Convenience: Crafted from soft, breathable materials...",
    "🎁 Perfect Baby Shower Gift: A sweet and meaningful addition to any baby's wardrobe.",
    "📏Versatile Sizing & Colors: Available in a range of sizes and colors..."
]

VARIATIONS = [
    "Newborn White Short Sleeve", "Newborn White Long Sleeve", "Newborn Natural Short Sleeve",
    "0-3M White Short Sleeve", "0-3M White Long Sleeve", "0-3M Pink Short Sleeve", "0-3M Blue Short Sleeve",
    "3-6M White Short Sleeve", "3-6M White Long Sleeve", "3-6M Blue Short Sleeve", "3-6M Pink Short Sleeve",
    "6M Natural Short Sleeve", "6-9M White Short Sleeve", "6-9M White Long Sleeve", "6-9M Pink Short Sleeve",
    "6-9M Blue Short Sleeve", "12M White Short Sleeve", "12M White Long Sleeve", "12M Natural Short Sleeve",
    "12M Pink Short Sleeve", "12M Blue Short Sleeve", "18M White Short Sleeve", "18M White Long Sleeve",
    "18M Natural Short Sleeve", "24M White Short Sleeve", "24M White Long Sleeve", "24M Natural Short Sleeve"
]

def upload_and_create_shopify_product(uploaded_file, title_slug, title_full):
    uploaded_file.seek(0)
    imgbb_url = "https://api.imgbb.com/1/upload"
    files = {
        "key": (None, IMGBB_API_KEY),
        "name": (None, title_slug),
        "image": uploaded_file
    }
    res = requests.post(imgbb_url, files=files)
    res.raise_for_status()
    image_url = res.json()["data"]["url"]

    shopify_url = f"https://{SHOPIFY_STORE}/admin/api/2023-01/products.json"
    headers = {"X-Shopify-Access-Token": SHOPIFY_TOKEN, "Content-Type": "application/json"}
    payload = {
        "product": {
            "title": title_full,
            "handle": title_slug,
            "body_html": DESCRIPTION,
            "vendor": "NOFO VIBES",
            "product_type": "Baby Bodysuit",
            "tags": "baby,funny,onesie,cute,custom",
            "images": [{"src": image_url}]
        }
    }
    r = requests.post(shopify_url, json=payload, headers=headers, verify=False)
    r.raise_for_status()
    return r.json()["product"]["images"][0]["src"]

def generate_amazon_json_feed(title, image_url):
    import random

    def patched_size_value(v):
        if v in ["Newborn White Short Sleeve", "0-3M White Short Sleeve"]:
            return v
        return v

    def format_slug(t):
        slug = ''.join([w[0] for w in t.split() if w]).upper()[:3]
        return f"{slug}-{random.randint(1000,9999)}"

    def format_variation_sku(slug, variation):
        parts = variation.split()
        size = parts[0].replace("Newborn", "NB").replace("0-3M", "03M").replace("3-6M", "36M") \
                       .replace("6-9M", "69M").replace("6M", "06M").replace("12M", "12M") \
                       .replace("18M", "18M").replace("24M", "24M")
        color = parts[1][0].upper()
        sleeve = "SS" if "Short" in variation else "LS"
        return f"{slug}-{size}-{color}-{sleeve}"

    def extract_color_and_sleeve(variation):
        color_map = "White"
        sleeve_type = "Short Sleeve" if "Short" in variation else "Long Sleeve"
        for w in variation.split():
            if w.lower() in ["white", "pink", "blue", "natural"]:
                color_map = w.capitalize()
        return color_map, sleeve_type

    slug = format_slug(title)
    parent_sku = f"{slug}-PARENT"

    messages = [{
        "messageId": 1,
        "sku": parent_sku,
        "operationType": "UPDATE",
        "productType": "LEOTARD",
        "requirements": "LISTING",
        "attributes": {
            "item_name": [{"value": f"{title} - Baby Boy Girl Clothes Bodysuit Funny Cute"}],
            "brand": [{"value": "NOFO VIBES"}],
            "variation_theme": [{"name": "SIZE/COLOR"}],
            "parentage_level": [{"value": "parent"}],
        }
    }]

    price_map = {v: 21.99 for v in VARIATIONS}
    price_map.update({
        "Newborn White Long Sleeve": 22.99,
        "0-3M White Long Sleeve": 22.99,
        "3-6M White Long Sleeve": 22.99,
        "6-9M White Long Sleeve": 22.99,
        "12M White Long Sleeve": 22.99,
        "18M White Long Sleeve": 22.99,
        "24M White Long Sleeve": 22.99,
    })

    for idx, variation in enumerate(VARIATIONS, start=2):
        sku = format_variation_sku(slug, variation)
        color_map, sleeve_type = extract_color_and_sleeve(variation)
        size_value = patched_size_value(variation)

        attributes = {
            "item_name": [{"value": f"{title} - Baby Boy Girl Clothes Bodysuit Funny Cute"}],
            "brand": [{"value": "NOFO VIBES"}],
            "variation_theme": [{"name": "SIZE/COLOR"}],
            "parentage_level": [{"value": "child"}],
            "child_parent_sku_relationship": [{
                "child_relationship_type": "variation",
                "parent_sku": parent_sku
            }],
            "size": [{"value": size_value}],
            "color": [{"value": "multi"}],
            "style": [{"value": sleeve_type}],
            "list_price": [{"currency": "USD", "value": price_map[variation]}],
            "main_product_image_locator": [{
                "media_location": image_url,
                "marketplace_id": "ATVPDKIKX0DER"
            }],
        }

        messages.append({
            "messageId": idx,
            "sku": sku,
            "operationType": "UPDATE",
            "productType": "LEOTARD",
            "requirements": "LISTING",
            "attributes": attributes
        })

    return json.dumps({
        "header": {
            "sellerId": SELLER_ID,
            "version": "2.0",
            "issueLocale": "en_US"
        },
        "messages": messages
    }, indent=2)

def get_amazon_access_token():
    r = requests.post("https://api.amazon.com/auth/o2/token", data={
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": LWA_CLIENT_ID,
        "client_secret": LWA_CLIENT_SECRET
    })
    r.raise_for_status()
    return r.json()["access_token"]

def submit_amazon_json_feed(json_feed, access_token):
    doc_res = requests.post(
        "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/documents",
        headers={"x-amz-access-token": access_token, "Content-Type": "application/json"},
        json={"contentType": "application/json"}
    )
    doc_res.raise_for_status()
    doc = doc_res.json()
    requests.put(doc["url"], data=json_feed.encode("utf-8"),
                 headers={"Content-Type": "application/json"}).raise_for_status()
    feed_res = requests.post(
        "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/feeds",
        headers={"x-amz-access-token": access_token, "Content-Type": "application/json"},
        json={
            "feedType": "JSON_LISTINGS_FEED",
            "marketplaceIds": [MARKETPLACE_ID],
            "inputFeedDocumentId": doc["feedDocumentId"]
        }
    )
    feed_res.raise_for_status()
    return feed_res.json()["feedId"]

# === UI ===
uploaded_files = st.file_uploader(
    "Upload PNG Files (Hold Ctrl or Shift to select multiple)",
    type="png", accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.write("Processing:", uploaded_file.name)
        file_stem = os.path.splitext(uploaded_file.name)[0]
        title_full = file_stem.replace("-", " ").replace("_", " ").title() + " - Baby Bodysuit"
        handle = file_stem.lower().replace(" ", "-").replace("_", "-") + "-baby-bodysuit"
        uploaded_file.seek(0)
        image_url = upload_and_create_shopify_product(uploaded_file, handle, title_full)
        token = get_amazon_access_token()
        feed_json = generate_amazon_json_feed(file_stem, image_url)
        feed_id = submit_amazon_json_feed(feed_json, token)
        st.success(f"✅ Feed submitted. Feed ID: {feed_id}")
