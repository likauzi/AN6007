from pymongo import MongoClient
from models import Household, Tranche

client = MongoClient("mongodb://localhost:27017/")
db = client["cdc_system"]

#save
def save_household(h):
    db.households.update_one(
        {"_id": h.household_id},
        {"$set": {
            "postal_code": h.postal_code,
        }},
        upsert=True
    )

def save_tranche(hid, t):
    db.tranches.update_one(
        {"_id": f"{hid}_{t.tranche_id}"},
        {"$set": {
            "household_id": hid,
            "tranche_id": t.tranche_id,
            "total_amount": 300,
            "vouchers": t.vouchers
        }},
        upsert=True
    )

# Restart Recovery
def load_all_households():
    households = {}

    for d in db.households.find():
        h = Household(d["_id"], d["postal_code"],)
        households[h.household_id] = h

    for d in db.tranches.find():
        t = Tranche(d["tranche_id"], d["vouchers"])
        households[d["household_id"]].tranches[t.tranche_id] = t

    return households
