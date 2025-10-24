import streamlit as st
import requests
import os
import json
from PIL import Image

# === CREDENTIALS ===
SHOPIFY_TOKEN = st.secrets["SHOPIFY_TOKEN"]
SHOPIFY_STORE = st.secrets["SHOPIFY_STORE"]
IMGBB_API_KEY = st.secrets["IMGBB_API_KEY"]
LWA_CLIENT_ID = st.secrets["LWA_CLIENT_ID"]
LWA_CLIENT_SECRET = st.secrets["LWA_CLIENT_SECRET"]
REFRESH_TOKEN = st.secrets["REFRESH_TOKEN"]
MARKETPLACE_ID = st.secrets["MARKETPLACE_ID"]  # e.g. "ATVPDKIKX0DER" for US
SELLER_ID = st.secrets["SELLER_ID"]

# we'll keep using LEOTARD since that already worked for you
PRODUCT_TYPE = "LEOTARD"

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

# color names that shoppers should see
# we are standardizing on these exact color labels
DISPLAY_COLOR = {
    "White": "White",
    "Beige": "Beige",
    "Pink": "Pink",
    "Light Blue": "Light Blue",
}

# swatch / main image for each color
COLOR_MAIN_IMAGE = {
    "Light Blue": "https://m.media-amazon.com/images/I/31ysQw3KbCL.jpg",
    "Pink":       "https://m.media-amazon.com/images/I/213KeA4UkeL.jpg",
    "White":      "https://m.media-amazon.com/images/I/310VhqCvvCL.jpg",
    "Beige":      "https://m.media-amazon.com/images/I/51B7bnNK0nL.jpg",
}

# Explicit list of ALL 26 combos you want:
# size_text = what shows in the Size dropdown (includes sleeve)
# color_label = what shows in the Color swatch selector
# price = retail price
VARIATION_COMBOS = [
    # Short Sleeve White ($29.99)
    ("Newborn - Short Sleeve", "White",      29.99),
    ("0-3M - Short Sleeve",    "White",      29.99),
    ("3-6M - Short Sleeve",    "White",      29.99),
    ("6-9M - Short Sleeve",    "White",      29.99),
    ("12M - Short Sleeve",     "White",      29.99),
    ("18M - Short Sleeve",     "White",      29.99),
    ("24M - Short Sleeve",     "White",      29.99),

    # Short Sleeve Beige ($33.99)
    ("0-3M - Short Sleeve",    "Beige",      33.99),
    ("3-6M - Short Sleeve",    "Beige",      33.99),
    ("6-9M - Short Sleeve",    "Beige",      33.99),
    ("12M - Short Sleeve",     "Beige",      33.99),

    # Short Sleeve Pink ($33.99)
    ("0-3M - Short Sleeve",    "Pink",       33.99),
    ("3-6M - Short Sleeve",    "Pink",       33.99),
    ("6-9M - Short Sleeve",    "Pink",       33.99),
    ("12M - Short Sleeve",     "Pink",       33.99),

    # Short Sleeve Light Blue ($33.99)
    ("0-3M - Short Sleeve",    "Light Blue", 33.99),
    ("3-6M - Short Sleeve",    "Light Blue", 33.99),
    ("6-9M - Short Sleeve",    "Light Blue", 33.99),
    ("12M - Short Sleeve",     "Light Blue", 33.99),

    # Long Sleeve White ($30.99)
    ("Newborn - Long Sleeve",  "White",      30.99),
    ("0-3M - Long Sleeve",     "White",      30.99),
    ("3-6M - Long Sleeve",     "White",      30.99),
    ("6-9M - Long Sleeve",     "White",      30.99),
    ("12M - Long Sleeve",      "White",      30.99),
    ("18M - Long Sleeve",      "White",      30.99),
    ("24M - Long Sleeve",      "White",      30.99),
]

# ---------------------------------
# SHOPIFY IMAGE UPLOAD PER DESIGN
# ---------------------------------
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
    shopify_product = r.json()
    shopify_image_url = shopify_product["product"]["images"][0]["src"]
    return shopify_image_url

# ---------------------------------
# AMAZON AUTH / FEED SUBMIT HELPERS
# ---------------------------------
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

def submit_amazon_json_feed(json_feed, access_token):
    # Step 1: request a document slot
    doc_res = requests.post(
        "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/documents",
        headers={
            "x-amz-access-token": access_token,
            "Content-Type": "application/json"
        },
        json={"contentType": "application/json"}
    )
    doc_res.raise_for_status()
    doc = doc_res.json()

    # Step 2: upload the feed body
    upload = requests.put(
        doc["url"],
        data=json_feed.encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    upload.raise_for_status()

    # Step 3: tell Amazon to process it
    feed_res = requests.post(
        "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/feeds",
        headers={
            "x-amz-access-token": access_token,
            "Content-Type": "application/json"
        },
        json={
            "feedType": "JSON_LISTINGS_FEED",
            "marketplaceIds": [MARKETPLACE_ID],
            "inputFeedDocumentId": doc["feedDocumentId"]
        }
    )
    feed_res.raise_for_status()
    return feed_res.json()["feedId"]

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
    ).json()
    report = requests.get(doc_info["url"])
    report.raise_for_status()
    return report.text

# ---------------------------------
# FEED GENERATION FOR ONE DESIGN
# ---------------------------------
def generate_amazon_json_feed(title, default_image_url):
    """
    Build feed payload (parent + 26 children) for ONE design/image.
    """
    import random

    def slugify_title(t):
        # short stable-ish SKU stem: first letters of up to 3 words
        initials = ''.join([w[0] for w in t.split() if w]).upper()[:3] or "SKU"
        return f"{initials}-{random.randint(1000, 9999)}"

    def build_child_sku(slug, size_text, color_label):
        # Make a deterministic SKU like SLUG-03M-W-SS
        # extract leading size chunk before " - "
        size_token = size_text.split(" - ")[0]  # e.g. "0-3M"
        size_code = (size_token
                     .replace("Newborn", "NB")
                     .replace("0-3M", "03M")
                     .replace("3-6M", "36M")
                     .replace("6-9M", "69M")
                     .replace("12M", "12M")
                     .replace("18M", "18M")
                     .replace("24M", "24M"))

        sleeve_code = "SS" if "Short Sleeve" in size_text else "LS"

        # color code first letter
        color_code = color_label[0].upper() if color_label else "X"

        return f"{slug}-{size_code}-{color_code}-{sleeve_code}"

    slug = slugify_title(title)
    parent_sku = f"{slug}-PARENT"

    messages = []

    # -------------------
    # PARENT MESSAGE
    # -------------------
    parent_msg = {
        "messageId": 1,
        "sku": parent_sku,
        "operationType": "UPDATE",
        "productType": PRODUCT_TYPE,
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
            "supplier_declared_has_product_identifier_exemption": [{"value": True}],

            # parent just needs *an* image – we can use the uploaded design
            "main_product_image_locator": [{
                "media_location": default_image_url,
                "marketplace_id": "ATVPDKIKX0DER"
            }],
        }
    }
    messages.append(parent_msg)

    # -------------------
    # CHILD MESSAGES
    # -------------------
    msg_id_counter = 2

    for (size_text, color_label, price) in VARIATION_COMBOS:
        display_color = DISPLAY_COLOR[color_label]  # ensure clean label
        sleeve_value = "Short Sleeve" if "Short Sleeve" in size_text else "Long Sleeve"

        child_sku = build_child_sku(slug, size_text, display_color)

        # color-specific hero image (swatch image / main image for that child)
        child_main_image = COLOR_MAIN_IMAGE.get(display_color, default_image_url)

        child_attributes = {
            "item_name": [{"value": f"{title} - {size_text} - {display_color}"}],
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

            # shopper-facing selectable attrs
            "size":  [{"value": size_text}],       # ex: "6-9M - Short Sleeve"
            "color": [{"value": display_color}],   # ex: "Light Blue"

            # extra style details
            "style":  [{"value": sleeve_value}],
            "sleeve": [{"value": sleeve_value}],

            "model_number": [{"value": "NBV"}],
            "model_name": [{"value": "Crew Neck Bodysuit"}],
            "import_designation": [{"value": "Made in USA"}],
            "country_of_origin": [{"value": "US"}],
            "condition_type": [{"value": "new_new"}],
            "batteries_required": [{"value": False}],
            "fabric_type": [{"value": "100% cotton"}],
            "supplier_declared_dg_hz_regulation": [{"value": "not_applicable"}],
            "supplier_declared_has_product_identifier_exemption": [{"value": True}],
            "care_instructions": [{"value": "Machine Wash"}],

            # catalog price block
            "list_price": [{
                "currency": "USD",
                "value": price
            }],

            # <-- THIS MAKES IT BUYABLE -->
            "purchasable_offer": [{
                "currency": "USD",
                "our_price": [{
                    "schedule": [{
                        "value_with_tax": price
                    }]
                }],
                "marketplace_id": MARKETPLACE_ID
            }],

            # <-- THIS MAKES IT IN STOCK -->
            "fulfillment_availability": [{
                "quantity": 999,
                "fulfillment_channel_code": "DEFAULT",
                "marketplace_id": MARKETPLACE_ID
            }],

            # shipping/box info
            "item_package_dimensions": [{
                "length": {"value": 3, "unit": "inches"},
                "width":  {"value": 3, "unit": "inches"},
                "height": {"value": 1, "unit": "inches"}
            }],
            "item_package_weight": [{
                "value": 0.19,
                "unit": "kilograms"
            }],

            # main image per color child (drives swatch preview)
            "main_product_image_locator": [{
                "media_location": child_main_image,
                "marketplace_id": MARKETPLACE_ID
            }]
        }

        child_msg = {
            "messageId": msg_id_counter,
            "sku": child_sku,
            "operationType": "UPDATE",
            "productType": PRODUCT_TYPE,
            "requirements": "LISTING",
            "attributes": child_attributes
        }
        messages.append(child_msg)
        msg_id_counter += 1

    # whole feed doc for THIS design
    feed_body = {
        "header": {
            "sellerId": SELLER_ID,
            "version": "2.0",
            "issueLocale": "en_US"
        },
        "messages": messages
    }
    return feed_body


# ---------------------------------
# STREAMLIT UI
# ---------------------------------
st.title("Shopify + Amazon Feed Uploader (Multi PNG ➜ Parent + 26 Variations)")

uploaded_files = st.file_uploader(
    "Upload PNG Files (Hold Ctrl/Shift to select multiple)",
    type=["png"],
    accept_multiple_files=True
)

if uploaded_files:
    all_messages = []

    for uploaded_file in uploaded_files:
        st.markdown(f"---\n### 📦 Processing: `{uploaded_file.name}`")
        try:
            # derive title from filename
            file_stem = os.path.splitext(uploaded_file.name)[0]
            title_full = file_stem.replace("-", " ").replace("_", " ").title() + " - Baby Bodysuit"
            handle = file_stem.lower().replace(" ", "-").replace("_", "-") + "-baby-bodysuit"

            # preview uploaded art
            img = Image.open(uploaded_file)
            st.image(img, caption=title_full, use_container_width=True)

            st.info("Uploading to ImgBB + Creating product on Shopify...")
            uploaded_file.seek(0)
            shopify_img_url = upload_and_create_shopify_product(uploaded_file, handle, title_full)
            st.success("✅ Shopify Product Created")

            st.info("Generating Amazon messages for this design...")
            feed_fragment = generate_amazon_json_feed(file_stem, shopify_img_url)

            # merge its parent + 26 children into global feed
            all_messages.extend(feed_fragment["messages"])

        except Exception as e:
            st.error(f"❌ Error processing {uploaded_file.name}: {e}")

    if all_messages:
        st.markdown("## 🛰️ Submitting Combined Feed to Amazon...")

        try:
            # make sure messageIds are unique & sequential across ALL designs
            for idx, msg in enumerate(all_messages, start=1):
                msg["messageId"] = idx

            final_feed = {
                "header": {
                    "sellerId": SELLER_ID,
                    "version": "2.0",
                    "issueLocale": "en_US"
                },
                "messages": all_messages
            }

            token = get_amazon_access_token()

            st.info("Submitting feed to Amazon SP-API…")
            feed_id = submit_amazon_json_feed(json.dumps(final_feed), token)
            st.success(f"✅ Feed Submitted — Feed ID: {feed_id}")

            st.info("Checking feed status…")
            status = check_amazon_feed_status(feed_id, token)
            st.code(json.dumps(status, indent=2))

            if status.get("processingStatus") == "DONE":
                st.info("Downloading processing report…")
                report = download_amazon_processing_report(status, token)
                st.code(report)
            else:
                st.warning("⚠️ Feed not processed yet. Please check again later.")

        except Exception as e:
            st.error(f"❌ Error submitting to Amazon: {e}")
