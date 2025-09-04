# D:\Hackathon\backend\service.py
import os
import pandas as pd
from backend.pipeline import VIPDetectionPipeline

# Path to your real dataset
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "real_vip_accounts.csv")

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"VIP dataset not found at {DATA_PATH}")

# Load VIP names from dataset
df = pd.read_csv(DATA_PATH)
OFFICIAL_VIPS = df["Name"].dropna().astype(str).str.lower().tolist()

# Initialize pipeline with official names
pipeline = VIPDetectionPipeline(official_usernames=OFFICIAL_VIPS)

def check_text_service(text: str):
    return pipeline.check_text(text or "")

def check_account_service(name: str):
    return pipeline.check_account({"Name": (name or "").strip()})

def check_username_service(username: str):
    return pipeline.check_username((username or "").strip())
