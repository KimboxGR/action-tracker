import requests
from bs4 import BeautifulSoup
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

URL = "https://www.action.com/nl-nl/nieuw/"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def get_products():
    response = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    products = []

    # Selecteer elk productblok (controleer HTML van Action)
    for item in soup.select("a[href*='/p/']"):
        name = item.get_text(strip=True)
        link = "https://www.action.com" + item["href"]

        # Afbeelding ophalen
        img_tag = item.select_one("img")
        image = img_tag['src'] if img_tag else ""

        # Prijs ophalen
        price_tag = item.select_one(".product-price")  # pas selector aan als nodig
        price = price_tag.get_text(strip=True) if price_tag else ""

        if name:
            products.append({
                "name": name,
                "url": link,
                "image": image,
                "price": price
            })

    # Verwijder duplicates op URL
    return list({p["url"]: p for p in products}.values())

def load_seen():
    if not os.path.exists("products_seen.json"):
        return []
    with open("products_seen.json", "r") as f:
        return json.load(f)

def save_seen(products):
    with open("products_seen.json", "w") as f:
        json.dump(products, f, indent=2)

def send_email(new_products):
    sender = os.environ["EMAIL_ADDRESS"]
    password = os.environ["EMAIL_PASSWORD"]
    receiver = os.environ["EMAIL_RECEIVER"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{len(new_products)} nieuwe Action producten 🛒"
    msg["From"] = sender
    msg["To"] = receiver

    # HTML e-mail (mobiel-vriendelijk, tabel layout)
    html = """
    <html>
    <head>
      <style>
        body { font-family: Arial, sans-serif; }
        table { border-collapse: collapse; width: 100%; }
        td { padding: 8px; vertical-align: middle; }
        img { width: 80px; height: auto; display: block; }
        a { text-decoration: none; color: #1a73e8; }
        @media only screen and (max-width: 600px) {
            td { display: block; width: 100%; }
            img { margin-bottom: 8px; }
        }
      </style>
    </head>
    <body>
      <h2>Nieuwe producten bij Action</h2>
      <table>
    """

    for product in new_products:
        html += "<tr>"
        html += f"<td><img src='{product['image']}'></td>" if product['image'] else "<td></td>"
        html += "<td>"
        html += f"<a href='{product['url']}'><strong>{product['name']}</strong></a><br>"
        if product['price']:
            html += f"<span>{product['price']}</span>"
        html += "</td>"
        html += "</tr>"

    html += """
      </table>
    </body>
    </html>
    """

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
