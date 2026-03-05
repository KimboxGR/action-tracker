import requests
from bs4 import BeautifulSoup
import json
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

URL = "https://www.action.com/nl-nl/nieuw/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_products():
    response = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    products = []

    for item in soup.select("a[href*='/p/']"):

        name = item.get_text(strip=True)
        link = "https://www.action.com" + item["href"]

        img_tag = item.select_one("img")
        image = img_tag["src"] if img_tag else ""

        price_tag = item.select_one("[class*=price]")
        price = price_tag.get_text(strip=True) if price_tag else ""

        if name:
            products.append({
                "name": name,
                "url": link,
                "image": image,
                "price": price
            })

    return list({p["url"]: p for p in products}.values())


def load_seen():
    if not os.path.exists("products_seen.json"):
        return []
    with open("products_seen.json", "r") as f:
        return json.load(f)


def save_seen(products):
    with open("products_seen.json", "w") as f:
        json.dump(products, f, indent=2)


def generate_html(products):

    today = datetime.now().strftime("%d %B")

    html = f"""
    <html>
    <body style="margin:0;background:#f4f6f8;font-family:Arial,sans-serif;">

    <div style="background:#003A8F;color:white;padding:20px;text-align:center;">
    <h2 style="margin:0;">🛒 Nieuw bij Action – {today}</h2>
    <p style="margin:5px 0 0 0;">Vandaag zijn er {len(products)} nieuwe producten gevonden</p>
    </div>

    <div style="padding:20px;">
    <table width="100%" style="max-width:800px;margin:auto;">
    <tr>
    """

    for i, product in enumerate(products):

        html += f"""
        <td style="width:50%;padding:10px;">
        <div style="background:white;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.08);padding:15px;text-align:center;">

        <img src="{product['image']}" style="width:100%;max-width:250px;border-radius:8px;"><br><br>

        <div style="font-weight:bold;color:#222;margin-bottom:5px;">
        {product['name']}
        </div>

        <div style="font-size:18px;color:#003A8F;font-weight:bold;margin-bottom:12px;">
        {product['price']}
        </div>

        <a href="{product['url']}" style="
        display:inline-block;
        background:#003A8F;
        color:white;
        padding:10px 16px;
        border-radius:6px;
        text-decoration:none;
        font-size:14px;
        ">
        Bekijk product →
        </a>

        </div>
        </td>
        """

        if i % 2 == 1:
            html += "</tr><tr>"

    html += """
    </tr>
    </table>
    </div>

    <div style="text-align:center;color:#666;font-size:13px;padding:30px 20px;">
    Automatisch gegenereerd door jouw schatje,<br>
    omdat ik zoveel van je hou ❤️<br><br>

    Hopelijk zit er weer iets leuks tussen.<br><br>

    Bron: action.com
    </div>

    </body>
    </html>
    """

    return html


def send_email(new_products):

    sender = os.environ["EMAIL_ADDRESS"]
    password = os.environ["EMAIL_PASSWORD"]
    receiver = os.environ["EMAIL_RECEIVER"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{len(new_products)} nieuwe Action producten 🛒"
    msg["From"] = sender
    msg["To"] = receiver

    html = generate_html(new_products)

    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())


def main():

    current_products = get_products()
    seen_products = load_seen()

    seen_urls = {p["url"] for p in seen_products}

    new_products = [p for p in current_products if p["url"] not in seen_urls]

    if new_products:
        send_email(new_products)
        save_seen(current_products)
        print(f"{len(new_products)} nieuwe producten gevonden en gemaild.")
    else:
        print("Geen nieuwe producten.")


if __name__ == "__main__":
    main()
