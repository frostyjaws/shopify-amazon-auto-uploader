import streamlit as st
import requests
import json

# === CREDENTIALS ===
SHOPIFY_TOKEN = st.secrets["SHOPIFY_TOKEN"]
SHOPIFY_STORE = st.secrets["SHOPIFY_STORE"]
IMGBB_API_KEY = st.secrets["IMGBB_API_KEY"]
LWA_CLIENT_ID = st.secrets["LWA_CLIENT_ID"]
LWA_CLIENT_SECRET = st.secrets["LWA_CLIENT_SECRET"]
REFRESH_TOKEN = st.secrets["REFRESH_TOKEN"]
MARKETPLACE_ID = st.secrets["MARKETPLACE_ID"]
SELLER_ID = st.secrets["SELLER_ID"]

PRODUCT_TYPE = "LEOTARD"  # ✅ Works for your node

DESCRIPTION = """
<p>Celebrate the arrival of your little one with our adorable Custom Baby onesie&reg;, the perfect baby shower gift...</p>
"""

BULLETS = [
    "🎨 High-Quality Ink Printing: Our Baby Bodysuit features vibrant, long-lasting colors...",
    "🎖️ Proudly Veteran-Owned: Show your support for our heroes...",
    "👶 Comfort and Convenience: Crafted from soft, breathable materials...",
    "🎁 Perfect Baby Shower Gift: This funny Baby Bodysuit makes for an excellent gift...",
    "📏Versatile Sizing & Colors: Available in a range of sizes and colors..."
]

# === COLOR IMAGE MAPS ===
COLOR_MAIN_IMAGE = {
    "Light Blue": "https://m.media-amazon.com/images/I/31ysQw3KbCL.jpg",
    "Pink": "https://m.media-amazon.com/images/I/213KeA4UkeL.jpg",
    "White": "https://m.media-amazon.com/images/I/310VhqCvvCL.jpg",
    "Beige": "https://m.media-amazon.com/images/I/51B7bnNK0nL.jpg"
}

COLOR_SWATCH_IMAGE = {
    "Light Blue": "https://m.media-amazon.com/images/I/31ysQw3KbCL.jpg",
    "Pink": "https://m.media-amazon.com/images/I/213KeA4UkeL.jpg",
    "White": "https://m.media-amazon.com/images/I/310VhqCvvCL.jpg",
    "Beige": "https://m.media-amazon.com/images/I/51B7bnNK0nL.jpg"
}

# === PRICING TABLE ===
PRICE_TABLE = {
    ("Newborn - Short Sleeve", "White"): 29.99,
    ("0–3M - Short Sleeve", "White"): 29.99,
    ("3–6M - Short Sleeve", "White"): 29.99,
    ("6–9M - Short Sleeve", "White"): 29.99,
    ("12M - Short Sleeve", "White"): 29.99,
    ("18M - Short Sleeve", "White"): 29.99,
    ("24M - Short Sleeve", "White"): 29.99,

    ("0–3M - Short Sleeve", "Beige"): 33.99,
    ("3–6M - Short Sleeve", "Beige"): 33.99,
    ("6–9M - Short Sleeve", "Beige"): 33.99,
    ("12M - Short Sleeve", "Beige"): 33.99,

    ("0–3M - Short Sleeve", "Pink"): 33.99,
    ("3–6M - Short Sleeve", "Pink"): 33.99,
    ("6–9M - Short Sleeve", "Pink"): 33.99,
    ("12M - Short Sleeve", "Pink"): 33.99,

    ("0–3M - Short Sleeve", "Light Blue"): 33.99,
    ("3–6M - Short Sleeve", "Light Blue"): 33.99,
    ("6–9M - Short Sleeve", "Light Blue"): 33.99,
    ("12M - Short Sleeve", "Light Blue"): 33.99,

    ("Newborn - Long Sleeve", "White"): 30.99,
    ("0–3M - Long Sleeve", "White"): 30.99,
    ("3–6M - Long Sleeve", "White"): 30.99,
    ("6–9M - Long Sleeve", "White"): 30.99,
    ("12M - Long Sleeve", "White"): 30.99,
    ("18M - Long Sleeve", "White"): 30.99,
    ("24M - Long Sleeve", "White"): 30.99
}

# === GENERATE FEED ===
def generate_amazon_json_feed(title, base_image_url):
    parent_sku = title.replace(" ", "") + "-Parent"
    messages = []

    # Parent
    messages.append({
        "sku": parent_sku,
        "productType": PRODUCT_TYPE,
        "attributes": {
            "item_name": [{"value": f"{title} - Baby Boy Girl Clothes Bodysuit Funny Cute"}],
            "brand": [{"value": "NOFO VIBES"}],
            "product_description": [{"value": DESCRIPTION}],
            "bullet_point": [{"value": b} for b in BULLETS],
            "variation_theme": [{"name": "SIZE/COLOR"}],
        }
    })

    # Children
    for (size, color), price in PRICE_TABLE.items():
        child_sku = f"{title.replace(' ', '')}-{size.replace(' ', '')}-{color.replace(' ', '')}"
        main_image = COLOR_MAIN_IMAGE.get(color, base_image_url)
        swatch_image = COLOR_SWATCH_IMAGE.get(color, main_image)

        attributes = {
            "parentage": [{"value": "child"}],
            "parent_sku": [{"value": parent_sku}],
            "relationship_type": [{"value": "variation"}],
            "variation_theme": [{"name": "SIZE/COLOR"}],
            "item_name": [{"value": f"{title} - Baby Boy Girl Clothes Bodysuit Funny Cute"}],
            "brand": [{"value": "NOFO VIBES"}],
            "size": [{"value": size}],
            "color": [{"value": color}],
            "standard_price": [{"currency": "USD", "value_with_tax": price}],
            "bullet_point": [{"value": b} for b in BULLETS],
            "product_description": [{"value": DESCRIPTION}],
            "main_product_image_locator": [{
                "media_location": main_image,
                "marketplace_id": MARKETPLACE_ID
            }],
            "other_images": [
                {
                    "image_type": "SWATCH",
                    "media_location": swatch_image,
                    "marketplace_id": MARKETPLACE_ID
                },
                {
                    "image_type": "MAIN",
                    "media_location": main_image,
                    "marketplace_id": MARKETPLACE_ID
                }
            ]
        }

        messages.append({
            "sku": child_sku,
            "productType": PRODUCT_TYPE,
            "attributes": attributes
        })

    feed = {"header": {"sellerId": SELLER_ID, "version": "2.0"}, "messages": messages}
    return json.dumps(feed, indent=2)

# === STREAMLIT UI ===
st.title("Amazon SP-API Feed Generator with Swatches")

title = st.text_input("Product Title")
uploaded_image = st.file_uploader("Upload Base Image (optional)")

if st.button("Generate Feed"):
    base_image_url = "https://yourfallbackimageurl.com/placeholder.jpg"
    if uploaded_image:
        base_image_url = base_image_url  # Or upload to CDN if you want dynamic
    
    feed_json = generate_amazon_json_feed(title, base_image_url)
    st.download_button("Download JSON Feed", feed_json, "amazon_feed.json")
    st.code(feed_json, language="json")
