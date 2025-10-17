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
    "🎨 High-Quality Ink Printing: Our Baby Bodysuit features vibrant, long-lasting colors thanks to direct-to-garment printing.",
    "🎖️ Proudly Veteran-Owned: Show your support for our heroes while dressing your little one in style.",
    "👶 Comfort and Convenience: Crafted from soft, breathable materials for maximum comfort and easy diaper changes.",
    "🎁 Perfect Baby Shower Gift: A thoughtful and adorable present for new parents.",
    "📏 Versatile Sizing & Colors: Available in multiple colors and sizes for the perfect fit."
]

VARIATIONS = [
    "Newborn White Short Sleeve", "0-3M White Short Sleeve", "3-6M White Short Sleeve",
    "6-9M White Short Sleeve", "12M White Short Sleeve", "18M White Short Sleeve", "24M White Short Sleeve",
    "0-3M Natural Short Sleeve", "3-6M Natural Short Sleeve", "6-9M Natural Short Sleeve", "12M Natural Short Sleeve",
    "0-3M Pink Short Sleeve", "3-6M Pink Short Sleeve", "6-9M Pink Short Sleeve",
    "0-3M Blue Short Sleeve", "3-6M Blue Short Sleeve", "6-9M Blue Short Sleeve",
    "Newborn White Long Sleeve", "0-3M White Long Sleeve", "3-6M White Long Sleeve",
    "6-9M White Long Sleeve", "12M White Long Sleeve", "18M White Long Sleeve", "24M White Long Sleeve"
]

def upload_and_create_shopify_product(uploaded_file, title_slug, title_full):
    uploaded_file.seek(0)
    imgbb_url = "https://api.imgbb.com/1/upload"
    files = {"key": (None, IMGBB_API_KEY), "name": (None, title_slug), "image": uploaded_file}
    response = requests.post(imgbb_url, files=files)
    response.raise_for_status()
    image_url = response.json()["data"]["url"]

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
    slug = ''.join([w[0] for w in title.split() if w]).upper()[:3] + f"-{random.randint(1000,9999)}"

    def extract_color_sleeve_size(variation):
        parts = variation.split()
        size_token = next(p for p in parts if p == "Newborn" or "M" in p)
        sleeve_type = "Short Sleeve" if "Short" in variation else "Long Sleeve"
        size_with_sleeve = f"{size_token} - {sleeve_type}"
        color_token = next(p for p in parts if p.lower() in ["white", "pink", "blue", "natural"])
        color_value = {"white": "White", "natural": "Beige", "pink": "Light Pink", "blue": "Light Blue"}[color_token.lower()]
        return color_value, sleeve_type, size_with_sleeve

    price_map = {
        "Newborn White Short Sleeve": 29.99, "0-3M White Short Sleeve": 29.99, "3-6M White Short Sleeve": 29.99,
        "6-9M White Short Sleeve": 29.99, "12M White Short Sleeve": 29.99, "18M White Short Sleeve": 29.99,
        "24M White Short Sleeve": 29.99, "0-3M Natural Short Sleeve": 33.99, "3-6M Natural Short Sleeve": 33.99,
        "6-9M Natural Short Sleeve": 33.99, "12M Natural Short Sleeve": 33.99, "0-3M Pink Short Sleeve": 33.99,
        "3-6M Pink Short Sleeve": 33.99, "6-9M Pink Short Sleeve": 33.99, "0-3M Blue Short Sleeve": 33.99,
        "3-6M Blue Short Sleeve": 33.99, "6-9M Blue Short Sleeve": 33.99, "Newborn White Long Sleeve": 30.99,
        "0-3M White Long Sleeve": 30.99, "3-6M White Long Sleeve": 30.99, "6-9M White Long Sleeve": 30.99,
        "12M White Long Sleeve": 30.99, "18M White Long Sleeve": 30.99, "24M White Long Sleeve": 30.99
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
            "variation_theme": [{"attributes": ["color", "size"]}],
            "parentage_level": [{"value": "parent"}]
        }
    }]

    for i, variation in enumerate(VARIATIONS, start=2):
        color_value, sleeve_type, size_with_sleeve = extract_color_sleeve_size(variation)
        sku = f"{slug}-{i:03d}"
        attributes = {
            "item_name": [{"value": f"{title} - Baby Boy Girl Clothes Bodysuit Funny Cute"}],
            "brand": [{"value": "NOFO VIBES"}],
            "variation_theme": [{"attributes": ["color", "size"]}],
            "parentage_level": [{"value": "child"}],
            "child_parent_sku_relationship": [{"child_relationship_type": "variation", "parent_sku": parent_sku}],
            "color": [{"value": color_value}],
            "color_name": [{"value": color_value}],
            "size": [{"value": size_with_sleeve}],
            "style": [{"value": sleeve_type}],
            "list_price": [{"currency": "USD", "value": price_map[variation]}],
            "main_product_image_locator": [{"media_location": image_url, "marketplace_id": "ATVPDKIKX0DER"}]
        }
        messages.append({"messageId": i, "sku": sku, "operationType": "UPDATE", "productType": "LEOTARD", "attributes": attributes})

    return json.dumps({"header": {"sellerId": SELLER_ID, "version": "2.0"}, "messages": messages}, indent=2)

def get_amazon_access_token():
    r = requests.post("https://api.amazon.com/auth/o2/token", data={
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": LWA_CLIENT_ID,
        "client_secret": LWA_CLIENT_SECRET
    })
    r.raise_for_status()
    return r.json()["access_token"]

def submit_amazon_json_feed(json_feed, token):
    doc = requests.post("https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/documents",
        headers={"x-amz-access-token": token, "Content-Type": "application/json"},
        json={"contentType": "application/json"}).json()
    requests.put(doc["url"], data=json_feed.encode("utf-8"), headers={"Content-Type": "application/json"})
    res = requests.post("https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/feeds",
        headers={"x-amz-access-token": token, "Content-Type": "application/json"},
        json={"feedType": "JSON_LISTINGS_FEED", "marketplaceIds": [MARKETPLACE_ID], "inputFeedDocumentId": doc["feedDocumentId"]})
    return res.json()["feedId"]

uploaded_files = st.file_uploader("Upload PNG Files", type="png", accept_multiple_files=True)
if uploaded_files:
    for f in uploaded_files:
        name = os.path.splitext(f.name)[0]
        st.image(Image.open(f), caption=name)
        url = upload_and_create_shopify_product(f, name, name + " - Baby Bodysuit")
        token = get_amazon_access_token()
        feed = generate_amazon_json_feed(name, url)
        feed_id = submit_amazon_json_feed(feed, token)
        st.success(f"✅ Submitted to Amazon — Feed ID: {feed_id}")

