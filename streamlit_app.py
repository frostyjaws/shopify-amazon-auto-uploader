import streamlit as st
import requests
import os
import json
from PIL import Image
from io import BytesIO
import random
from datetime import datetime

# =========================
# CREDENTIALS / CONSTANTS
# =========================
SHOPIFY_TOKEN = st.secrets["SHOPIFY_TOKEN"]
SHOPIFY_STORE = st.secrets["SHOPIFY_STORE"]
IMGBB_API_KEY = st.secrets["IMGBB_API_KEY"]
LWA_CLIENT_ID = st.secrets["LWA_CLIENT_ID"]
LWA_CLIENT_SECRET = st.secrets["LWA_CLIENT_SECRET"]
REFRESH_TOKEN = st.secrets["REFRESH_TOKEN"]
MARKETPLACE_ID = st.secrets["MARKETPLACE_ID"]  # e.g. "ATVPDKIKX0DER"
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

# Swatch dots (color chips)
COLOR_SWATCHES = {
    "White": "https://m.media-amazon.com/images/I/310VhqCvvCL.jpg",
    "Pink": "https://m.media-amazon.com/images/I/213KeA4UkeL.jpg",
    "Light Blue": "https://m.media-amazon.com/images/I/31ysQw3KbCL.jpg",
    "Beige": "https://m.media-amazon.com/images/I/51B7bnNK0nL.jpg"
}

# =========================
# OFFER MATRIX (26 ROWS)
# =========================
# size_text = what's shown in Amazon size dropdown (we include sleeve type here)
# color     = simple color for swatch and color picker
# price     = list price / offer price
VARIATION_COMBOS = [
    # White Short Sleeve
    {"size_text": "Newborn - Short Sleeve", "color": "White", "price": 29.99},
    {"size_text": "0-3M - Short Sleeve",    "color": "White", "price": 29.99},
    {"size_text": "3-6M - Short Sleeve",    "color": "White", "price": 29.99},
    {"size_text": "6-9M - Short Sleeve",    "color": "White", "price": 29.99},
    {"size_text": "12M - Short Sleeve",     "color": "White", "price": 29.99},
    {"size_text": "18M - Short Sleeve",     "color": "White", "price": 29.99},
    {"size_text": "24M - Short Sleeve",     "color": "White", "price": 29.99},

    # Natural/Beige Short Sleeve (you called this Beige in swatch)
    {"size_text": "0-3M - Short Sleeve",    "color": "Beige", "price": 33.99},
    {"size_text": "3-6M - Short Sleeve",    "color": "Beige", "price": 33.99},
    {"size_text": "6-9M - Short Sleeve",    "color": "Beige", "price": 33.99},
    {"size_text": "12M - Short Sleeve",     "color": "Beige", "price": 33.99},

    # Pink Short Sleeve
    {"size_text": "0-3M - Short Sleeve",    "color": "Pink", "price": 33.99},
    {"size_text": "3-6M - Short Sleeve",    "color": "Pink", "price": 33.99},
    {"size_text": "6-9M - Short Sleeve",    "color": "Pink", "price": 33.99},
    {"size_text": "12M - Short Sleeve",     "color": "Pink", "price": 33.99},

    # Light Blue Short Sleeve
    {"size_text": "0-3M - Short Sleeve",    "color": "Light Blue", "price": 33.99},
    {"size_text": "3-6M - Short Sleeve",    "color": "Light Blue", "price": 33.99},
    {"size_text": "6-9M - Short Sleeve",    "color": "Light Blue", "price": 33.99},
    {"size_text": "12M - Short Sleeve",     "color": "Light Blue", "price": 33.99},

    # White Long Sleeve
    {"size_text": "Newborn - Long Sleeve",  "color": "White", "price": 30.99},
    {"size_text": "0-3M - Long Sleeve",     "color": "White", "price": 30.99},
    {"size_text": "3-6M - Long Sleeve",     "color": "White", "price": 30.99},
    {"size_text": "6-9M - Long Sleeve",     "color": "White", "price": 30.99},
    {"size_text": "12M - Long Sleeve",      "color": "White", "price": 30.99},
    {"size_text": "18M - Long Sleeve",      "color": "White", "price": 30.99},
    {"size_text": "24M - Long Sleeve",      "color": "White", "price": 30.99},
]

# NOTE: 7 white SS + 4 beige SS + 4 pink SS + 4 light blue SS + 7 white LS = 26
# total children is 26. Parent is +1 = 27 messages in feed.

# =========================
# HELPERS
# =========================

def upload_and_create_shopify_product(uploaded_file, title_slug, title_full):
    """
    1. Upload image to ImgBB  (to get a CDN URL for the mockup)
    2. Create product in Shopify with that image
    3. Return the Shopify image URL for use as MAIN image in Amazon
    """
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
    shopify_product = r.json()
    shopify_image_url = shopify_product["product"]["images"][0]["src"]
    return shopify_image_url  # the mockup main image for Amazon child MAIN

def get_amazon_access_token():
    r = requests.post(
        "https://api.amazon.com/auth/o2/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
            "client_id": LWA_CLIENT_ID,
            "client_secret": LWA_CLIENT_SECRET
        }
    )
    r.raise_for_status()
    return r.json()["access_token"]

def submit_amazon_json_feed(json_feed_str, access_token):
    # 1. Create feed document
    doc_res = requests.post(
        "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/documents",
        headers={
            "x-amz-access-token": access_token,
            "Content-Type": "application/json"
        },
        json={"contentType": "application/json"}
    )
    doc_res.raise_for_status()
    doc_info = doc_res.json()

    # 2. Upload actual feed body
    upload = requests.put(
        doc_info["url"],
        data=json_feed_str.encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    upload.raise_for_status()

    # 3. Finalize feed
    feed_res = requests.post(
        "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/feeds",
        headers={
            "x-amz-access-token": access_token,
            "Content-Type": "application/json"
        },
        json={
            "feedType": "JSON_LISTINGS_FEED",
            "marketplaceIds": [MARKETPLACE_ID],
            "inputFeedDocumentId": doc_info["feedDocumentId"]
        }
    )
    feed_res.raise_for_status()
    feed_id = feed_res.json()["feedId"]
    return feed_id

def check_amazon_feed_status(feed_id, access_token):
    res = requests.get(
        f"https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/feeds/{feed_id}",
        headers={
            "x-amz-access-token": access_token,
            "Content-Type": "application/json"
        }
    )
    res.raise_for_status()
    return res.json()

def download_amazon_processing_report(feed_status, access_token):
    doc_id = feed_status.get("resultFeedDocumentId")
    if not doc_id:
        return "Processing report not available yet."

    doc_info = requests.get(
        f"https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/documents/{doc_id}",
        headers={"x-amz-access-token": access_token}
    )
    doc_info.raise_for_status()
    doc_info = doc_info.json()

    report = requests.get(doc_info["url"])
    report.raise_for_status()
    return report.text

def slug_from_title(title):
    # Simple short SKU root like "SP-8510"
    base = "".join([w[0] for w in title.split() if w]).upper()
    if len(base) < 3:
        base = (base + "XXX")[:3]
    return f"{base}-{random.randint(1000,9999)}"

def sku_from_combo(parent_slug, size_text, color):
    # Create deterministic-ish child SKU text
    # size_text ex: "6-9M - Short Sleeve"
    # color ex: "Light Blue"
    # We'll compress to codes to keep SKU short-ish:
    # size_code: remove spaces and dash -> "6-9MShort"
    size_code = (
        size_text
        .replace(" ", "")
        .replace("–", "-")
        .replace("—", "-")
        .replace("--", "-")
        .replace("/", "")
        .replace("-ShortSleeve", "-SS")
        .replace("-LongSleeve", "-LS")
        .replace("ShortSleeve", "SS")
        .replace("LongSleeve", "LS")
        .replace("Short", "Short")
        .replace("Sleeve", "S")
    )
    # little cleanup: "ShortS" => "SS"
    size_code = size_code.replace("ShortS", "SS")
    size_code = size_code.replace("LongS", "LS")

    color_code = (
        color.upper()
        .replace(" ", "")
        .replace("LIGHTBLUE", "LB")
        .replace("WHITE", "W")
        .replace("PINK", "P")
        .replace("BEIGE", "B")
    )

    # random tail so we don't collide
    tail = random.randint(100,999)

    return f"{parent_slug}-{size_code}-{color_code}-{tail}"

def generate_feed_messages(title, mockup_image_url):
    """
    Build:
    - 1 parent message
    - 26 child messages
    Each child gets:
      - size_text in "size"
      - color in "color"
      - PRICE in list_price + purchasable_offer
      - swatch_image_locator for swatch
      - main_product_image_locator for main
    """
    parent_slug = slug_from_title(title)
    parent_sku = f"{parent_slug}-PARENT"

    # Parent message
    messages = [{
        "messageId": 1,
        "sku": parent_sku,
        "operationType": "UPDATE",
        "productType": "LEOTARD",  # keep using what worked historically
        "requirements": "LISTING",
        "attributes": {
            "item_name": [{
                "value": f"{title} - Baby Boy Girl Clothes Bodysuit Funny Cute"
            }],
            "brand": [{"value": "NOFO VIBES"}],
            "item_type_keyword": [{"value": "infant-and-toddler-bodysuits"}],
            "product_description": [{"value": DESCRIPTION}],
            "bullet_point": [{"value": b} for b in BULLETS],

            # static attrs that worked for you
            "target_gender": [{"value": "female"}],
            "age_range_description": [{"value": "Infant"}],
            "material": [{"value": "Cotton"}],
            "department": [{"value": "Baby Girls"}],

            # VARIATION THEME
            # We are telling Amazon that children vary by Size + Color
            "variation_theme": [{"name": "SIZE/COLOR"}],

            "parentage_level": [{"value": "parent"}],

            "model_number": [{"value": title}],
            "model_name": [{"value": title}],

            "import_designation": [{"value": "Imported"}],
            "country_of_origin": [{"value": "US"}],
            "condition_type": [{"value": "new_new"}],
            "batteries_required": [{"value": False}],
            "fabric_type": [{"value": "100% cotton"}],
            "supplier_declared_dg_hz_regulation": [{"value": "not_applicable"}],
            "supplier_declared_has_product_identifier_exemption": [{"value": True}],

            # Give Amazon something for main product image on parent
            "main_product_image_locator": [{
                "media_location": mockup_image_url,
                "marketplace_id": MARKETPLACE_ID
            }]
        }
    }]

    # Child messages
    message_id_counter = 2
    for combo in VARIATION_COMBOS:
        size_text = combo["size_text"]
        color_name = combo["color"]
        price_val = combo["price"]

        # SKU unique per size/color
        child_sku = sku_from_combo(parent_slug, size_text, color_name)

        # Swatch image URL
        swatch_url = COLOR_SWATCHES[color_name]

        # We reuse main mockup image for listing photo for now.
        # (Later you could map different mockups per color if you want)
        main_image_url = mockup_image_url

        attributes = {
            "item_name": [{
                "value": f"{title} - {color_name} / {size_text}"
            }],
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

            # connect to parent SKU
            "child_parent_sku_relationship": [{
                "child_relationship_type": "variation",
                "parent_sku": parent_sku
            }],

            # Variation dimensions:
            # We bake sleeve length into size_text, like "6-9M - Short Sleeve"
            "size": [{"value": size_text}],
            "color": [{"value": color_name}],

            # Compliance / detail
            "model_number": [{"value": "CrewNeckBodysuit"}],
            "model_name": [{"value": "Crew Neck Bodysuit"}],
            "import_designation": [{"value": "Made in USA"}],
            "country_of_origin": [{"value": "US"}],
            "condition_type": [{"value": "new_new"}],
            "batteries_required": [{"value": False}],
            "fabric_type": [{"value": "100% cotton"}],
            "supplier_declared_dg_hz_regulation": [{"value": "not_applicable"}],
            "supplier_declared_has_product_identifier_exemption": [{"value": True}],
            "care_instructions": [{"value": "Machine Wash"}],

            # Images:
            # main image = product mockup
            "main_product_image_locator": [{
                "media_location": main_image_url,
                "marketplace_id": MARKETPLACE_ID
            }],
            # swatch image = color chip (goes in that SWATCH column in UI)
            "swatch_image_locator": [{
                "media_location": swatch_url,
                "marketplace_id": MARKETPLACE_ID
            }],

            # Offer / price / stock
            "list_price": [{
                "currency": "USD",
                "value": price_val
            }],
            "purchasable_offer": [{
                "currency": "USD",
                "our_price": [{
                    "schedule": [{
                        "value_with_tax": price_val
                    }]
                }],
                "marketplace_id": MARKETPLACE_ID
            }],
            "fulfillment_availability": [{
                "quantity": 999,
                "fulfillment_channel_code": "DEFAULT",
                "marketplace_id": MARKETPLACE_ID
            }],

            # package details (unchanged from before)
            "item_package_dimensions": [{
                "length": {"value": 3, "unit": "inches"},
                "width": {"value": 3, "unit": "inches"},
                "height": {"value": 1, "unit": "inches"}
            }],
            "item_package_weight": [{
                "value": 0.19,
                "unit": "kilograms"
            }],
        }

        messages.append({
            "messageId": message_id_counter,
            "sku": child_sku,
            "operationType": "UPDATE",
            "productType": "LEOTARD",  # keep same productType as what Amazon already accepted
            "requirements": "LISTING",
            "attributes": attributes
        })
        message_id_counter += 1

    feed = {
        "header": {
            "sellerId": SELLER_ID,
            "version": "2.0",
            "issueLocale": "en_US"
        },
        "messages": messages
    }

    return feed


# =========================
# UI (MULTI UPLOAD MODE)
# =========================

st.set_page_config(
    page_title="Amazon SP-API Feed Generator",
    page_icon="🍼",
    layout="wide",
)

st.title("Amazon SP-API Feed Generator")

uploaded_files = st.file_uploader(
    "Upload PNG Files (you can select multiple)",
    type=["png"],
    accept_multiple_files=True
)

if uploaded_files:
    all_messages = []
    # we will collect feed messages from each uploaded design,
    # then merge all into one big submission

    st.write("Processing uploads...")

    for uploaded_file in uploaded_files:
        try:
            file_stem = os.path.splitext(uploaded_file.name)[0]

            # make readable title and Shopify handle
            title_full = file_stem.replace("-", " ").replace("_", " ").title() + " - Baby Bodysuit"
            handle = file_stem.lower().replace(" ", "-").replace("_", "-") + "-baby-bodysuit"

            # preview image
            image = Image.open(uploaded_file)
            st.image(image, caption=title_full, use_container_width=True)

            # STEP 1: Upload to ImgBB + Create product on Shopify
            st.info("Uploading to ImgBB + Creating product on Shopify...")
            uploaded_file.seek(0)
            mockup_image_url = upload_and_create_shopify_product(uploaded_file, handle, title_full)
            st.success("✅ Shopify Product Created")

            # STEP 2: Build feed messages (parent + 26 kids)
            st.info("Generating Amazon Feed messages...")
            feed_dict = generate_feed_messages(file_stem, mockup_image_url)

            # extend all messages
            all_messages.extend(feed_dict["messages"])

        except Exception as e:
            st.error(f"❌ Error processing {uploaded_file.name}: {e}")

    if all_messages:
        # Before submit: reassign messageId across EVERYTHING so they are unique 1..N
        for idx, msg in enumerate(all_messages, start=1):
            msg["messageId"] = idx

        full_feed = {
            "header": {
                "sellerId": SELLER_ID,
                "version": "2.0",
                "issueLocale": "en_US"
            },
            "messages": all_messages
        }

        st.markdown("### 🛰 Submitting Combined Feed to Amazon...")
        try:
            token = get_amazon_access_token()

            # Submit feed
            feed_id = submit_amazon_json_feed(json.dumps(full_feed), token)
            st.success(f"✅ Feed Submitted to Amazon — Feed ID: {feed_id}")

            # Check status immediately (it'll usually be IN_QUEUE or PROCESSING)
            st.info("Checking Feed Status...")
            status = check_amazon_feed_status(feed_id, token)
            st.code(json.dumps(status, indent=2))

            proc_state = status.get("processingStatus", "")
            if proc_state == "DONE":
                st.info("Downloading Processing Report...")
                report = download_amazon_processing_report(status, token)
                st.code(report)
            else:
                st.warning("⚠️ Feed not processed yet. Please check again later.")

        except Exception as e:
            st.error(f"❌ Error submitting feed to Amazon: {e}")
