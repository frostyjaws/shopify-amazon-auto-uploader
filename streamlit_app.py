Thanks for the screenshot — that helps.

The blank screen is happening because the code you’re running right now is **not a full Streamlit app anymore.** The version I last sent only included the top half (definitions, functions) but not the actual UI code at the bottom that renders widgets and runs the workflow. So Streamlit boots, installs deps, and then… nothing to draw → black screen.

I’m going to give you the **entire full app.py / streamlit_app.py** in one copy box, start to finish:

* keeps all your original logic (multi-file uploader, Shopify upload, Amazon feed submit, status check, etc.)
* uses the updated VARIATIONS and price_map you wanted
* includes the UI block so Streamlit actually renders

👉 Replace your whole file with this:

```python
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

# UPDATED VARIATIONS MASTER LIST (the only combos you actually sell)
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
    # upload PNG to imgbb
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

    # create product in Shopify
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

    # use same global list
    variations = VARIATIONS

    def format_slug(title):
        # short SKU base like ABC-1234
        slug = ''.join([w[0] for w in title.split() if w]).upper()[:3]
        return f"{slug}-{random.randint(1000, 9999)}"

    def format_variation_sku(slug, variation):
        # turn "0-3M White Short Sleeve" -> "03M-W-SS"
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
        # "0-3M Blue Short Sleeve" -> ("Blue", "Short Sleeve")
        color_map = "White"
        sleeve_type = "Short Sleeve" if "Short" in variation else "Long Sleeve"
        for word in variation.split():
            if word.lower() in ["white", "pink", "blue", "natural"]:
                color_map = word.capitalize()
        return color_map, sleeve_type

    slug = format_slug(title)

    # UPDATED PRICE MAP FROM YOUR CHART
    price_map = {
        # White Short Sleeve ($29.99)
        "Newborn White Short Sleeve": 29.99,
        "0-3M White Short Sleeve": 29.99,
        "3-6M White Short Sleeve": 29.99,
        "6-9M White Short Sleeve": 29.99,
        "12M White Short Sleeve": 29.99,
        "18M White Short Sleeve": 29.99,
        "24M White Short Sleeve": 29.99,

        # Natural Short Sleeve ($33.99)
        "0-3M Natural Short Sleeve": 33.99,
        "3-6M Natural Short Sleeve": 33.99,
        "6-9M Natural Short Sleeve": 33.99,
        "12M Natural Short Sleeve": 33.99,

        # Pink Short Sleeve ($33.99)
        "0-3M Pink Short Sleeve": 33.99,
        "3-6M Pink Short Sleeve": 33.99,
        "6-9M Pink Short Sleeve": 33.99,

        # Blue Short Sleeve ($33.99)
        "0-3M Blue Short Sleeve": 33.99,
        "3-6M Blue Short Sleeve": 33.99,
        "6-9M Blue Short Sleeve": 33.99,

        # White Long Sleeve ($30.99)
        "Newborn White Long Sleeve": 30.99,
        "0-3M White Long Sleeve": 30.99,
        "3-6M White Long Sleeve": 30.99,
        "6-9M White Long Sleeve": 30.99,
        "12M White Long Sleeve": 30.99,
        "18M White Long Sleeve": 30.99,
        "24M White Long Sleeve": 30.99,
    }

    parent_sku = f"{slug}-PARENT"

    # parent message
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

    # each child variation row
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
            "sleeve": [{"value": sleeve_type}],
            "color": [{"value": color_map}],
            "list_price": [{"currency": "USD", "value": price_map[variation]}],
            "fulfillment_availability": [{
                "quantity": 999,
                "fulfillment_channel_code": "DEFAULT",
                "marketplace_id": "ATVPDKIKX0DER"
            }],
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
    r = requests.post(
        "https://api.amazon.com/auth/o2/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
            "client_id": LWA_CLIENT_ID,
            "client_secret": LWA_CLIENT_SECRET,
        },
    )
    r.raise_for_status()
    return r.json()["access_token"]


def submit_amazon_json_feed(json_feed, access_token):
    # 1. create feed document (where we're supposed to upload the JSON)
    doc_res = requests.post(
        "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/documents",
        headers={
            "x-amz-access-token": access_token,
            "Content-Type": "application/json",
        },
        json={"contentType": "application/json"},
    )
    doc_res.raise_for_status()
    doc = doc_res.json()

    # 2. upload feed body to that pre-signed URL
    upload = requests.put(
        doc["url"],
        data=json_feed.encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    upload.raise_for_status()

    # 3. tell Amazon "process that doc as a JSON_LISTINGS_FEED"
    feed_res = requests.post(
        "https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/feeds",
        headers={
            "x-amz-access-token": access_token,
            "Content-Type": "application/json",
        },
        json={
            "feedType": "JSON_LISTINGS_FEED",
            "marketplaceIds": [MARKETPLACE_ID],
            "inputFeedDocumentId": doc["feedDocumentId"],
        },
    )
    feed_res.raise_for_status()
    return feed_res.json()["feedId"]


def check_amazon_feed_status(feed_id, access_token):
    res = requests.get(
        f"https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/feeds/{feed_id}",
        headers={
            "x-amz-access-token": access_token,
            "Content-Type": "application/json",
        },
    )
    res.raise_for_status()
    return res.json()


def download_amazon_processing_report(feed_status, access_token):
    doc_id = feed_status.get("resultFeedDocumentId")
    if not doc_id:
        return "Processing report not available yet."

    doc_info = requests.get(
        f"https://sellingpartnerapi-na.amazon.com/feeds/2021-06-30/documents/{doc_id}",
        headers={"x-amz-access-token": access_token},
    ).json()

    report = requests.get(doc_info["url"])
    report.raise_for_status()
    return report.text


# === UI ===

st.set_page_config(page_title="Shopify + Amazon Uploader", page_icon="🍼", layout="wide")
st.title("🍼 Shopify + Amazon Auto Uploader")
st.caption("Upload PNG → Create Shopify product → Build + Submit Amazon feed with all variations.")

uploaded_files = st.file_uploader(
    "Upload PNG Files (Hold Ctrl or Shift to select multiple)",
    type="png",
    accept_multiple_files=True,
)

if uploaded_files:
    all_messages = []
    all_skus = []

    for uploaded_file in uploaded_files:
        st.markdown(f"---\n### 📦 Processing: `{uploaded_file.name}`")

        try:
            # derive title + handle from filename
            file_stem = os.path.splitext(uploaded_file.name)[0]
            title_full = file_stem.replace("-", " ").replace("_", " ").title() + " - Baby Bodysuit"
            handle = (
                file_stem.lower()
                .replace(" ", "-")
                .replace("_", "-")
                + "-baby-bodysuit"
            )

            # preview image
            image = Image.open(uploaded_file)
            st.image(image, caption=title_full, use_container_width=True)

            st.info("Uploading to ImgBB + Creating product on Shopify...")
            uploaded_file.seek(0)
            shopify_image_url = upload_and_create_shopify_product(
                uploaded_file, handle, title_full
            )
            st.success("✅ Shopify Product Created")

            st.info("Generating Amazon Feed for this design...")
            json_feed_for_this_file = json.loads(
                generate_amazon_json_feed(file_stem, shopify_image_url)
            )

            # stash messages for later combined submit
            all_messages.extend(json_feed_for_this_file["messages"])

            for msg in json_feed_for_this_file["messages"]:
                if msg.get("sku"):
                    all_skus.append(msg["sku"])

            st.code(json.dumps(json_feed_for_this_file, indent=2), language="json")

        except Exception as e:
            st.error(f"❌ Error processing {uploaded_file.name}: {e}")

    # after loop, allow submit of combined feed
    if all_messages:
        st.markdown("## 📡 Submit Combined Feed to Amazon")

        # de-dupe messageId so Amazon doesn't freak
        for idx, msg in enumerate(all_messages, start=1):
            msg["messageId"] = idx

        full_feed_payload = {
            "header": {
                "sellerId": SELLER_ID,
                "version": "2.0",
                "issueLocale": "en_US",
            },
            "messages": all_messages,
        }

        if st.button("🚀 Submit Feed to Amazon"):
            try:
                token = get_amazon_access_token()
                feed_id = submit_amazon_json_feed(
                    json.dumps(full_feed_payload), token
                )
                st.success(f"✅ Feed Submitted to Amazon — Feed ID: {feed_id}")

                st.info("Checking Feed Status...")
                status = check_amazon_feed_status(feed_id, token)
                st.code(json.dumps(status, indent=2), language="json")

                if status.get("processingStatus") == "DONE":
                    st.info("Downloading Processing Report...")
                    report = download_amazon_processing_report(status, token)
                    st.code(report)
                else:
                    st.warning("⚠️ Feed not processed yet. Check again later.")
            except Exception as e:
                st.error(f"❌ Error submitting combined feed: {e}")

st.markdown("------")
st.caption("USE SIZE CHART / VARIATION MATRIX ABOVE FOR ALL LISTINGS.")
```
