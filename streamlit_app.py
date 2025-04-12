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

DESCRIPTION = "Celebrate the arrival of your little one with a beautifully printed baby bodysuit from NOFO VIBES. Crafted for comfort and made with love!"
BULLETS = [
    "🎨 High-Quality Ink Printing",
    "🎖️ Proudly Veteran-Owned",
    "👶 Comfort and Convenience",
    "🎁 Perfect Baby Shower Gift",
    "🔯 Versatile Sizing & Colors"
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
    response = requests.post(imgbb_url, files=files)
    response.raise_for_status()
    image_url = response.json()["data"]["url"]

    shopify_url = f"https://{SHOPIFY_STORE}/admin/api/2023-01/products.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_TOKEN,
        "Content-Type": "application/json"
    }
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
    r = requests.post(shopify_url, json=payload, headers=headers)
    r.raise_for_status()
    return image_url

def generate_amazon_json_feed(title, image_url):
    messages = []
    for idx, var in enumerate(VARIATIONS, start=1):
        abbr = "SS" if "Short" in var else "LS"
        sku = f"{title}-{var.replace(' ', '')}-{abbr}"
        messages.append({
            "messageId": idx,
            "sku": sku,
            "operationType": "UPDATE",
            "productType": "BABY_ONE_PIECE",
            "attributes": {
                "brand": [{"value": "NOFO VIBES"}],
                "item_name": [{"value": f"{title} - Baby Bodysuit"}],
                "product_description": [{"value": DESCRIPTION}],
                "manufacturer": [{"value": "NOFO VIBES"}],
                "bullet_point": [{"value": b} for b in BULLETS],
                "main_image_url": [{"value": image_url}],
                "standard_price": [{"value": "21.99", "currency": "USD"}],
                "quantity": [{"value": "999"}],
                "variation_theme": [{"value": "size_name"}],
                "size_name": [{"value": var}],
                "external_product_id": [{"value": "REPLACE_WITH_UPC"}],
                "external_product_id_type": [{"value": "UPC"}]
            }
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

    upload = requests.put(doc["url"], data=json_feed.encode("utf-8"), headers={"Content-Type": "application/json"})
    upload.raise_for_status()

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
    return feed_res
::contentReference[oaicite:6]{index=6}
 
