from pymongo import MongoClient
from faker import Faker
import random

fake = Faker()
client = MongoClient("mongodb://localhost:27017/")

client.drop_database("cdc_system")
db = client["cdc_system"]

# Banks
banks = [
    {"bank_code": "7171", "bank_name": "DBS Bank Ltd", "branch_code": "001",
     "branch_name": "Main Branch", "swift_code": "DBSSSGSG", "remarks": "FAST/GIRO Enabled"},
    {"bank_code": "7339", "bank_name": "OCBC Bank", "branch_code": "501",
     "branch_name": "Tampines Branch", "swift_code": "OCBCSGSG", "remarks": "FAST/GIRO Enabled"},
    {"bank_code": "7761", "bank_name": "UOB Bank", "branch_code": "001",
     "branch_name": "Raffles Place", "swift_code": "UOVBSGSG", "remarks": "FAST/GIRO Enabled"},
    {"bank_code": "7091", "bank_name": "Maybank Singapore", "branch_code": "001",
     "branch_name": "Main Branch", "swift_code": "MBBESGSG", "remarks": "FAST/GIRO Enabled"},
    {"bank_code": "7302", "bank_name": "Standard Chartered Bank", "branch_code": "001",
     "branch_name": "Main Branch", "swift_code": "SCBLSGSG", "remarks": "FAST/GIRO Enabled"},
    {"bank_code": "7375", "bank_name": "HSBC Singapore", "branch_code": "146",
     "branch_name": "Orchard Branch", "swift_code": "HSBCSGSG", "remarks": "FAST/GIRO Enabled"},
    {"bank_code": "7171", "bank_name": "POSB Bank", "branch_code": "081",
     "branch_name": "Toa Payoh Branch", "swift_code": "DBSSSGSG", "remarks": "FAST/GIRO Enabled"},
    {"bank_code": "9465", "bank_name": "Citibank Singapore", "branch_code": "001",
     "branch_name": "Main Branch", "swift_code": "CITISGSG", "remarks": "FAST/GIRO Enabled"},
    {"bank_code": "7083", "bank_name": "RHB Bank Berhad", "branch_code": "001",
     "branch_name": "Main Branch", "swift_code": "RHBBSGSG", "remarks": "FAST/GIRO Enabled"},
    {"bank_code": "7012", "bank_name": "Bank of China Singapore", "branch_code": "001",
     "branch_name": "Main Branch", "swift_code": "BKCHSGSG", "remarks": "FAST/GIRO Enabled"}
]
db.banks.insert_many(banks)
bank_codes = list({b["bank_code"] for b in banks})

# PostalDistrict
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
        "district": d["district"],
        "bankcode": random.choice(bank_codes)
    })
db.merchants.insert_many(merchants)

# Households
households = []
for i in range(2000):
    # postal code still generated, but no district field stored
    households.append({
        "_id": f"H{i:05}",
        "postal_code": fake.postcode()
    })
db.households.insert_many(households)

# Tranches & Vouchers
denoms = {"2": 60, "5": 24, "10": 6}

tranches = []
vouchers = []

for h in households:
    tranches.append({
        "_id": f"{h['_id']}_JAN2025",
        "household_id": h["_id"],
        "tranche_id": "JAN2025",
        "total_amount": 300,
        "vouchers": denoms
    })

    for denom, count in denoms.items():
        for _ in range(count):
            vouchers.append({
                "_id": fake.uuid4(),
                "household_id": h["_id"],
                "tranche_id": "JAN2025",
                "denomination": int(denom),
                "used": False
            })

db.tranches.insert_many(tranches)
db.vouchers.insert_many(vouchers)

print("====== CDC Database Rebuilt (Household district removed) ======")
print("banks:", db.banks.count_documents({}))
print("postaldistricts:", db.postaldistricts.count_documents({}))
print("merchants:", db.merchants.count_documents({}))
print("households:", db.households.count_documents({}))
print("tranches:", db.tranches.count_documents({}))
print("vouchers:", db.vouchers.count_documents({}))
print("transactions: NOT USED")
