from pymongo import MongoClient
from models import Household, Tranche
import uuid

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


#zn: 用户注册领券后新生成vouchers
def create_vouchers_for_tranche(hid: str, tranche_id: str, voucher_plan: dict):
    """
    voucher_plan e.g. {"2":60, "5":24, "10":6} 代表每种面额的张数
    """
    # 防重复：如果已经存在该家庭该tranche的voucher，就不要再生成（避免重复claim导致重复插入）
    existing = db.vouchers.count_documents({"household_id": hid, "tranche_id": tranche_id})
    if existing > 0:
        raise ValueError("Vouchers already exist for this tranche")

    docs = []
    for denom_str, cnt in voucher_plan.items():
        denom = int(denom_str)
        for _ in range(int(cnt)):
            docs.append({
                "_id": str(uuid.uuid4()),   # voucher_id
                "household_id": hid,
                "tranche_id": tranche_id,
                "denomination": denom,
                "used": False
            })

    if docs:
        db.vouchers.insert_many(docs)
    return len(docs)



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

#zn:新增“自动生成下一个 household_id”，并确保 save/load 只处理 postal_code
def get_next_household_id():
    last = db.households.find_one(sort=[("_id", -1)], projection={"_id": 1})
    if not last:
        # 库里还没有家庭时，从 H00000 开始（也可改成 H00001，按你们组约定）
        return "H00000"

    num = int(last["_id"][1:])  # 去掉 'H'
    return f"H{num + 1:05}"

