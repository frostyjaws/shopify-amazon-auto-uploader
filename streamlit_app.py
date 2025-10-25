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
<p>Celebrate the arrival of your little one with our adorable Custom Baby onesie&reg;, the perfect baby shower gift that will be cherished for years to come. This charming piece of baby clothing is an ideal new baby gift for welcoming a newborn into the world. Whether it's for a baby announcement, a pregnancy reveal, or a special baby shower, this baby onesie&reg; is sure to delight.</p>

<p>Our Custom Baby onesie&reg; features a playful and cute design, perfect for showcasing your baby's unique personality. Made with love and care, this baby onesie&reg; is designed to keep your baby comfortable and stylish. It's an essential item in cute baby clothes, making it a standout piece for any new arrival.</p>

<p>Perfect for both baby boys and girls, this versatile baby onesie&reg; is soft, comfortable, and durable, ensuring it can withstand numerous washes. The easy-to-use snaps make changing a breeze, providing convenience for busy parents.</p>

<p>Whether you're looking for a personalized baby onesie&reg;, a funny baby onesie&reg;, or a cute baby onesie&reg;, this Custom Baby onesie&reg; has it all. It's ideal for celebrating the excitement of a new baby, featuring charming and customizable designs. This makes it a fantastic option for funny baby clothes that bring a smile to everyone's face.</p>

<p>Imagine gifting this delightful baby onesie&reg; at a baby shower or using it as a memorable baby announcement or pregnancy reveal. It's perfect for anyone searching for a unique baby gift, announcement baby onesie&reg;, or a special new baby onesie&reg;.</p>

<p>This baby onesie&reg; is not just an item of clothing; it's a keepsake that celebrates the joy and wonder of a new life.</p>

<p>From baby boy clothes to baby girl clothes, this baby onesie&reg; is perfect for any newborn. Whether it's a boho design, a Father's Day gift, or custom baby clothes, this piece is a wonderful addition to any baby's wardrobe.</p>
"""

BULLETS = [
    "🎨 High-Quality Ink Printing: Our Baby Bodysuit features vibrant, long-lasting colors thanks to direct-to-garment printing, ensuring that your baby's outfit looks fantastic wash after wash.",
    "🎖️ Proudly Veteran-Owned: Show your support for our heroes while dressing your little one in style with this adorable newborn romper from a veteran-owned small business.",
    "👶 Comfort and Convenience: Crafted from soft, breathable materials, this Bodysuit provides maximum comfort for your baby. Plus, the convenient snap closure makes diaper changes a breeze.",
    "🎁 Perfect Baby Shower Gift: This funny Baby Bodysuit makes for an excellent baby shower gift or a thoughtful present for any new parents. It's a sweet and meaningful addition to any baby's wardrobe.",
    "📏Versatile Sizing & Colors: Available in a range of sizes and colors, ensuring the perfect fit. Check our newborn outfit boy and girl sizing guide to find the right one for your little one."
]

VARIATIONS = [
    # White Short Sleeve
    "Newborn White Short Sleeve",
    "0-3M White Short Sleeve",
    "3-6M White Short Sleeve",
    "6-9M White Short Sleeve",
    "12M White Short Sleeve",
    "18M White Short Sleeve",
    "24M White Short Sleeve",

    # Natural Short Sleeve
    "0-3M Natural Short Sleeve",
    "3-6M Natural Short Sleeve",
    "6-9M Natural Short Sleeve",
    "12M Natural Short Sleeve",

    # Pink Short Sleeve
    "0-3M Pink Short Sleeve",
    "3-6M Pink Short Sleeve",
    "6-9M Pink Short Sleeve",

    # Blue Short Sleeve
    "0-3M Blue Short Sleeve",
    "3-6M Blue Short Sleeve",
    "6-9M Blue Short Sleeve",

    # White Long Sleeve
    "Newborn White Long Sleeve",
    "0-3M White Long Sleeve",
    "3-6M White Long Sleeve",
    "6-9M White Long Sleeve",
    "12M White Long Sleeve",
    "18M White Long Sleeve",
    "24M White Long Sleeve",
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
    r = requests.post(shopify_url, json=payload, headers=headers, verify=False)
    r.raise_for_status()
    shopify_product = r.json()
    shopify_image_url = shopify_product["product"]["images"][0]["src"]
    return shopify_image_url

def generate_amazon_json_feed(title, image_url):
    import random
    import json

    variations = VARIATIONS

    def format_slug(title):
        slug = ''.join([w[0] for w in title.split() if w]).upper()[:3]
        return f"{slug}-{random.randint(1000, 9999)}"

    def format_variation_sku(slug, variation):
        parts = variation.split()
        size = (
            parts[0]
            .replace("Newborn", "NB")
            .replace("0-3M", "03M")
            .replace("3-6M", "36M")
            .replace("6-9M", "69M")
            .replace("12M", "12M")
            .replace("18M", "18M")
            .replace("24M", "24M")
        )
        color = parts[1][0].upper()
        sleeve = "SS" if "Short" in variation else "LS"
        return f"{slug}-{size}-{color}-{sleeve}"

    def extract_color_and_sleeve(variation):
        color_map = "White"
        sleeve_type = "Short Sleeve" if "Short" in variation else "Long Sleeve"
        for word in variation.split():
            if word.lower() in ["white", "pink", "blue", "natural"]:
                color_map = word.capitalize()
        return color_map, sleeve_type

    slug = format_slug(title)

    price_map = {
        # White Short Sleeve
        "Newborn White Short Sleeve": 29.99,
        "0-3M White Short Sleeve": 29.99,
        "3-6M White Short Sleeve": 29.99,
        "6-9M White Short Sleeve": 29.99,
        "12M White Short Sleeve": 29.99,
        "18M White Short Sleeve": 29.99,
        "24M White Short Sleeve": 29.99,

        # Natural Short Sleeve
        "0-3M Natural Short Sleeve": 33.99,
        "3-6M Natural Short Sleeve": 33.99,
        "6-9M Natural Short Sleeve": 33.99,
        "12M Natural Short Sleeve": 33.99,

        # Pink Short Sleeve
        "0-3M Pink Short Sleeve": 33.99,
        "3-6M Pink Short Sleeve": 33.99,
        "6-9M Pink Short Sleeve": 33.99,

        # Blue Short Sleeve
        "0-3M Blue Short Sleeve": 33.99,
        "3-6M Blue Short Sleeve": 33.99,
        "6-9M Blue Short Sleeve": 33.99,

        # White Long Sleeve
        "Newborn White Long Sleeve": 30.99,
        "0-3M White Long Sleeve": 30.99,
        "3-6M White Long Sleeve": 30.99,
        "6-9M White Long Sleeve": 30.99,
        "12M White Long Sleeve": 30.99,
        "18M White Long Sleeve": 30.99,
        "24M White Long Sleeve": 30.99,
    }

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
            "item_type_keyword": [{"value": "infant-and-toddler-bodysuits"}],
            "product_description": [{"value": DESCRIPTION}],
            "bullet_point": [{"value": b} for b in BULLETS],
            "target_gender": [{"value": "female"}],
            "age_range_description": [{"value": "Infant"}],
            "material": [{"value": "Cotton"}],
            "department": [{"value": "Baby Girls"}],
            "variation_theme": [{"name": "SIZE/COLOR"}],
            "parentage_level": [{"value": "parent"}],
            "model_number": [{"value": "NBV"}],
            "model_name": [{"value": title}],
            "import_designation": [{"value": "Imported"}],
            "country_of_origin": [{"value": "US"}],
            "condition_type": [{"value": "new_new"}],
            "batteries_required": [{"value": False}],
            "fabric_type": [{"value": "100% cotton"}],
            "supplier_declared_dg_hz_regulation": [{"value": "not_applicable"}],
            "supplier_declared_has_product_identifier_exemption": [{"value": True}]
        }
    }]

    for idx, variation in enumerate(variations, start=2):
        sku = format_variation_sku(slug, variation)
        color_map, sleeve_type = extract_color_and_sleeve(variation)

        attributes = {
            "item_name": [{"value": f"{title} - Baby Boy Girl Clothes Bodysuit Funny Cute"}],
            "brand": [{"value": "NOFO VIBES"}],
            "item_type_keyword": [{"value": "infant-and-toddler-bodysuits"}],
            "product_description": [{"value": DESCRIPTION}],
            "bullet_point": [{"value": b} for b in BULLETS],
            "target_gender": [{"value": "female"}],
            "age_range_description": [{"value": "Infant"}],
            "material": [{"value": "Cotton"}],
            "department": [{"value": "Baby Girls"}],
            "variation_theme": [{"name": "SIZE/COLOR"}],
            "parentage_level": [{"value": "child"}],
            "child_parent_sku_relationship": [{
                "child_relationship_type": "variation",
                "parent_sku": parent_sku
            }],
            "size": [{"value": variation}],
            "style": [{"value": sleeve_type}],
            "color": [{"value": color_map}],
            "list_price": [{"currency": "USD", "value": price_map[variation]}],
            "fulfillment_availability": [{
                "quantity": 999,
                "fulfillment_channel_code": "DEFAULT",
                "marketplace_id": "ATVPDKIKX0DER"
            }]
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
