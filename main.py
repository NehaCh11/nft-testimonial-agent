import os
import re
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request

# --------- Gemini API Setup ---------
import google.generativeai as genai

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("⚠️ Please set your GEMINI_API_KEY in .env")

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# --------- Flask Setup ---------
app = Flask(__name__)

# --------- Algorand Logic Only ---------
def fetch_algorand_assets(wallet_address):
    url = f"https://mainnet-idx.algonode.cloud/v2/accounts/{wallet_address}/assets"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("assets", [])
    except Exception as e:
        print(f"❌ Algorand fetch error: {e}")
        return []

def clip_to_sentences(text, max_sentences=2):
    text = re.sub(r"(?i)(testimonial[:\-]*|nft name:.*|description:.*)", "", text)
    sentences = re.split(r"(?<=[.!?])\s+", text.strip().strip('"').strip("'"))
    clipped = " ".join(sentences[:max_sentences]).strip()
    return clipped if clipped.endswith(('.', '!', '?')) else clipped + '.'

def generate_testimonial(nft_name, nft_description):
    prompt = (
        f"You are a proud NFT collector. Write a short 2-sentence testimonial expressing excitement or personal value of owning this NFT.\n\n"
        f"NFT Name: {nft_name}\nDescription: {nft_description}\nTestimonial:"
    )
    try:
        response = gemini_model.generate_content(prompt)
        return clip_to_sentences(response.text)
    except Exception as e:
        return f"[Error generating testimonial: {e}]"

# --------- Web Routes ---------
@app.route("/", methods=["GET", "POST"])
def index():
    testimonials = []
    if request.method == "POST":
        wallet = request.form.get("wallet")
        assets = fetch_algorand_assets(wallet)
        for asset in assets:
            asset_id = asset.get("asset-id")
            amount = asset.get("amount")
            name = f"Algorand ASA #{asset_id}"
            desc = f"Algorand asset ID {asset_id}, holding amount: {amount}."
            testimonial = generate_testimonial(name, desc)
            testimonials.append({"name": name, "desc": desc, "testimonial": testimonial})
    return render_template("index.html", testimonials=testimonials)

# --------- Main Entry ---------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use Render's PORT env variable
    app.run(host="0.0.0.0", port=port, debug=True)

# ---------------------------------------------------------------------
# ❌ COMMENTED OUT: Multi-chain support, Falcon model, Covalent client
# ---------------------------------------------------------------------
# import torch
# from transformers import pipeline
# from covalent import CovalentClient

# API_KEY = os.getenv("COVALENT_API_KEY")
# client = CovalentClient(API_KEY)

# generator = pipeline(
#     "text-generation",
#     model="tiiuae/falcon-rw-1b",
#     device=0 if torch.cuda.is_available() else -1,
#     do_sample=True,
#     max_new_tokens=80,
#     top_p=0.9,
#     temperature=0.9
# )

# CHAIN_OPTIONS = {
#     1: ("Ethereum Mainnet", "eth-mainnet"),
#     ...
#     20: ("Scroll Sepolia", "scroll-sepolia-testnet"),
# }

# def select_chain():
#     ...
# def get_wallet_address():
#     ...
# def fetch_multichain_nfts():
#     ...
