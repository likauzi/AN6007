from pymongo import MongoClient
from faker import Faker
import random


fake = Faker()
client = MongoClient("mongodb://localhost:27017/")

# Drop and recreate database
client.drop_database("cdc_system")
db = client["cdc_system"]

# PostalDistrict (master data)
postal_districts = []
for i in range(1, 29):
    postal_districts.append({
        "_id": f"{i:02}",
        "district": f"D{i:02}",
        "location": fake.city()
    })
db.postaldistricts.insert_many(postal_districts)

# Merchants
merchants = []
for i in range(300):
    d = random.choice(postal_districts)
    merchants.append({
        "_id": f"M{i:05}",
        "status": "active",
        "district": d["district"]
    })
db.merchants.insert_many(merchants)

# Households
households = []
for i in range(2000):
    d = random.choice(postal_districts)
    households.append({
        "_id": f"H{i:05}",
        "postal_code": d["_id"] + fake.postcode()[2:]
    })
db.households.insert_many(households)

# Tranches & Vouchers
denoms = {"2": 60, "5": 24, "10": 6}  # total = 300

tranches = []
vouchers = []

for h in households:
    tranches.append({
        "_id": f"{h['_id']}_JAN2026",
        "household_id": h["_id"],
        "tranche_id": "JAN2026",
        "total_amount": 300,
        "vouchers": denoms
    })

    for denom, count in denoms.items():
        for _ in range(count):
            vouchers.append({
                "_id": fake.uuid4(),
                "household_id": h["_id"],
                "tranche_id": "JAN2026",
                "denomination": int(denom),
                "used": False
            })

db.tranches.insert_many(tranches)
db.vouchers.insert_many(vouchers)

# Transactions
"""
from datetime import datetime

NUM_TX = 100

unused_vouchers = list(db.vouchers.find({"used": False}))
selected_vouchers = random.sample(unused_vouchers, NUM_TX)

transactions = []

for i, v in enumerate(selected_vouchers):
    tx = {
        "tx_id": f"TX2025_{i:05}",
        "household_id": v["household_id"],
        "merchant_id": random.choice(merchants)["_id"],
        "voucher_id": v["_id"],
        "amount": v["denomination"],
        "timestamp": datetime(
            year=2025, month=random.randint(1, 6),
            day=random.randint(1, 28),
            hour=random.randint(8, 22),
            minute=random.randint(0, 59),
            second=random.randint(0, 59)
        ).strftime("%Y%m%d%H%M%S")
    }

    transactions.append(tx)

    # Mark voucher as used
    db.vouchers.update_one(
        {"_id": v["_id"]},
        {"$set": {"used": True}}
    )

db.transactions.insert_many(transactions)
"""

print("====== CDC Database Rebuilt (Merchant District Added) ======")
print("households:", db.households.count_documents({}))
print("postaldistricts:", db.postaldistricts.count_documents({}))
print("merchants:", db.merchants.count_documents({}))
print("tranches:", db.tranches.count_documents({}))
print("vouchers:", db.vouchers.count_documents({}))
print("transactions: NOT USED")
