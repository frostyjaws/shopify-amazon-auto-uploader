import streamlit as st
import requests
import os
import json
from PIL import Image
import re

# === CREDENTIALS ===
SHOPIFY_TOKEN = st.secrets["SHOPIFY_TOKEN"]
SHOPIFY_STORE = st.secrets["SHOPIFY_STORE"]
IMGBB_API_KEY = st.secrets["IMGBB_API_KEY"]
LWA_CLIENT_ID = st.secrets["LWA_CLIENT_ID"]
LWA_CLIENT_SECRET = st.secrets["LWA_CLIENT_SECRET"]
REFRESH_TOKEN = st.secrets["REFRESH_TOKEN"]
MARKETPLACE_ID = st.secrets["MARKETPLACE_ID"]
SELLER_ID = st.secrets["SELLER_ID"]

# === COPY TEXT ===
DESCRIPTION = """
<p>Celebrate the arrival of your little one with our adorable Custom Baby onesie&reg;...</p>
"""

BULLETS = [
    "🎨 High-Quality Ink Printing...",
    "🎖️ Proudly Veteran-Owned...",
    "👶 Comfort and Convenience...",
    "🎁 Perfect Baby Shower Gift...",
    "📏 Versatile Sizing & Colors..."
]

# === UPDATED VARIATIONS ===
VARIATIONS = [
    ("Newborn Short Sleeve", "White"),
    ("0–3M Short Sleeve", "White"),
    ("3–6M Short Sleeve", "White"),
    ("6–9M Short Sleeve", "White"),
    ("12M Short Sleeve", "White"),
    ("18M Short Sleeve", "White"),
    ("24M Short Sleeve", "White"),

    ("0–3M Short Sleeve", "Natural"),
    ("3–6M Short Sleeve", "Natural"),
    ("6–9M Short Sleeve", "Natural"),
    ("12M Short Sleeve", "Natural"),

    ("0–3M Short Sleeve", "Pink"),
    ("3–6M Short Sleeve", "Pink"),
    ("6–9M Short Sleeve", "Pink"),

    ("0–3M Short Sleeve", "Blue"),
    ("3–6M Short Sleeve", "Blue"),
    ("6–9M Short Sleeve", "Blue"),

    ("Newborn Long Sleeve", "White"),
    ("0–3M Long Sleeve", "White"),
    ("3–6M Long Sleeve", "White"),
    ("6–9M Long Sleeve", "White"),
    ("12M Long Sleeve", "White"),
    ("18M Long Sleeve", "White"),
    ("24M Long Sleeve", "White"),
]

PRICE_MAP = {
    ("Newborn Short Sleeve", "White"): 29.99,
    ("0–3M Short Sleeve", "White"): 29.99,
    ("3–6M Short Sleeve", "White"): 29.99,
    ("6–9M Short Sleeve", "White"): 29.99,
    ("12M Short Sleeve", "White"): 29.99,
    ("18M Short Sleeve", "White"): 29.99,
    ("24M Short Sleeve", "White"): 29.99,

    ("0–3M Short Sleeve", "Natural"): 33.99,
    ("3–6M Short Sleeve", "Natural"): 33.99,
    ("6–9M Short Sleeve", "Natural"): 33.99,
    ("12M Short Sleeve", "Natural"): 33.99,

    ("0–3M Short Sleeve", "Pink"): 33.99,
    ("3–6M Short Sleeve", "Pink"): 33.99,
    ("6–9M Short Sleeve", "Pink"): 33.99,

    ("0–3M Short Sleeve", "Blue"): 33.99,
    ("3–6M Short Sleeve", "Blue"): 33.99,
    ("6–9M Short Sleeve", "Blue"): 33.99,

    ("Newborn Long Sleeve", "White"): 30.99,
    ("0–3M Long Sleeve", "White"): 30.99,
    ("3–6M Long Sleeve", "White"): 30.99,
    ("6–9M Long Sleeve", "White"): 30.99,
    ("12M Long Sleeve", "White"): 30.99,
    ("18M Long Sleeve", "White"): 30.99,
    ("24M Long Sleeve", "White"): 30.99,
}

# === SKU HELPERS ===
def safe_title_to_base_slug(raw_title: str) -> str:
    t = raw_title.strip().lower().replace("_", " ").replace("-", " ")
    t = re.sub(r"[^a-z0-9\s]+", "", t)
    t = re.sub(r"\s+", "-", t).strip("-")
    return t

def parent_sku_from_slug(slug: str) -> str:
    base = slug.replace("-", "")
    return f"{base}-Parent".upper()

def child_sku_from_slug_and_variation(slug: str, size_label: str, color_label: str) -> str:
    base = slug.replace("-", "")
    size_compact = re.sub(r"\s+", "", size_label)
    color_compact = re.sub(r"\s+", "", color_label)
    return f"{base}-{size_compact}{color_compact}".upper()

# === SHOPIFY UPLOAD ===
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
    r = requests.post(shopify_url, json=payload, headers=headers, verify=False)
    r.raise_for_status()
    shopify_product = r.json()
    shopify_image_url = shopify_product["product"]["images"][0]["src"]
    return shopify_image_url

# === AMAZON JSON FEED BUILDER ===
def generate_amazon_json_feed(title, image_url):
    import json

    slug = safe_title_to_base_slug(title)
    parent_sku = parent_sku_from_slug(slug)

    messages = [{
        "messageId": 1,
        "sku": parent_sku,
        "operationType": "UPDATE",
        "productType": "LEOTARD",
        "requirements": "LISTING",
        "attributes": {
            "item_name": [{"value": f"{title} - Baby Boy Girl Clothes Bodysuit Funny Cute"}],
            "brand": [{"value": "NOFO VIBES"}],
            "item_type_keyword": [{"value": "infant-and-toddler-bodysuits"}],
            "product_description": [{"value": DESCRIPTION}],
            "bullet_point": [{"value": b} for b in BULLETS],
            "target_gender": [{"value": "unisex-baby"}],
            "age_range_description": [{"value": "Infant"}],
            "material": [{"value": "Cotton"}],
            "department": [{"value": "Baby"}],
            "variation_theme": [{"value": "SIZE-COLOR"}],
            "parentage_level": [{"value": "parent"}],
            "model_number": [{"value": "NBV"}],
            "model_name": [{"value": title}],
            "import_designation": [{"value": "Made in USA"}],
            "country_of_origin": [{"value": "US"}],
            "condition_type": [{"value": "new_new"}],
            "batteries_required": [{"value": False}],
            "fabric_type": [{"value": "100% cotton"}],
            "supplier_declared_has_product_identifier_exemption": [{"value": True}]
        }
    }]

    msg_id = 2
    for (size_label, color_label) in VARIATIONS:
        sku = child_sku_from_slug_and_variation(slug, size_label, color_label)
        price = PRICE_MAP[(size_label, color_label)]
        sleeve_type = "Short Sleeve" if "Short" in size_label else "Long Sleeve"

        attributes = {
            "item_name": [{"value": f"{title} - Baby Boy Girl Clothes Bodysuit Funny Cute"}],
            "brand": [{"value": "NOFO VIBES"}],
            "item_type_keyword": [{"value": "infant-and-toddler-bodysuits"}],
            "product_description": [{"value": DESCRIPTION}],
            "bullet_point": [{"value": b} for b in BULLETS],
            "target_gender": [{"value": "unisex-baby"}],
            "age_range_description": [{"value": "Infant"}],
            "material": [{"value": "Cotton"}],
            "department": [{"value": "Baby"}],
            "variation_theme": [{"value": "SIZE-COLOR"}],
            "parentage_level": [{"value": "child"}],
            "child_parent_sku_relationship": [{
                "child_relationship_type": "variation",
                "parent_sku": parent_sku
            }],
            "size": [{"value": size_label}],
            "color": [{"value": color_label}],
            "style": [{"value": sleeve_type}],
            "model_number": [{"value": "NBV"}],
            "model_name": [{"value": "Crew Neck Bodysuit"}],
            "import_designation": [{"value": "Made in USA"}],
            "country_of_origin": [{"value": "US"}],
            "condition_type": [{"value": "new_new"}],
            "batteries_required": [{"value": False}],
            "fabric_type": [{"value": "100% cotton"}],
            "supplier_declared_has_product_identifier_exemption": [{"value": True}],
            "care_instructions": [{"value": "Machine Wash"}],
            "list_price": [{"currency": "USD", "value": price}],
            "main_product_image_locator": [{
                "media_location": image_url,
                "marketplace_id": "ATVPDKIKX0DER"
            }],
            "fulfillment_availability": [{
                "quantity": 999,
                "fulfillment_channel_code": "DEFAULT",
                "marketplace_id": "ATVPDKIKX0DER"
            }]
        }

        messages.append({
            "messageId": msg_id,
            "sku": sku,
            "operationType": "UPDATE",
            "productType": "LEOTARD",
            "requirements": "LISTING",
            "attributes": attributes
        })
        msg_id += 1

    return json.dumps({
        "header": {
            "sellerId": SELLER_ID,
            "version": "2.0",
            "issueLocale": "en_US"
        },
        "messages": messages
    }, indent=2)
