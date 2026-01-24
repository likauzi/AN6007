from models import Household, Tranche
from db import save_household, save_tranche, get_next_household_id, create_vouchers_for_tranche
from datetime import datetime
from db import db
import random
import os
import csv

# In-memory store (injected)
households = {}

def init(household_store):
    global households
    households = household_store

#原lx代码，zn进行修改
# def register_household(hid, postal):
#     if hid in households:
#         raise ValueError("Household already exists")

#     h = Household(hid, postal)
#     households[hid] = h
#     save_household(h)
#     return h

#zn：修改household 注册逻辑为用户只需输入postal code，系统自动分配household_id，household_id和postal code再一起存储至MongoDB数据库中
def register_household(postal: str):
    if not postal or len(postal) < 2:
        raise ValueError("postal_code is required")

    hid = get_next_household_id()

    # 保险：如果内存里恰好已有同名（极少见，通常不会发生）
    if hid in households:
        raise ValueError("Generated household_id already exists (unexpected)")

    h = Household(hid, postal)
    households[hid] = h
    save_household(h)
    return h


#zn:用户点击claim领券后成功生成vouchers
def claim_tranche(hid, tranche_id="JAN2026"):
    if hid not in households:
        raise ValueError("Household not registered")

    # 防止同一个 tranche 重复 claim 导致重复 vouchers
    if tranche_id in households[hid].tranches:
        raise ValueError("Tranche already claimed")

    t = Tranche(tranche_id, {"2":60,"5":24,"10":6})
    households[hid].tranches[tranche_id] = t
    save_tranche(hid, t)

    # 关键：生成并写入 vouchers collection
    create_vouchers_for_tranche(hid, tranche_id, t.vouchers)

    return t

#=====================bai==========================
# --- Redemption CSV writer ---
REDEEM_DIR = "redemptions"  

def _ensure_redeem_dir():
    os.makedirs(REDEEM_DIR, exist_ok=True)

def _redeem_filename(dt: datetime) -> str:
    # RedeemYYYYMMDDHH.csv
    return f"Redeem{dt.strftime('%Y%m%d%H')}.csv"

def _append_redemption_rows(tx_id: str, household_id: str, merchant_id: str, ts_full: str, vouchers: list, total_amount: int):
    """
    for each voucher write into RedeemYYYYMMDDHH.csv as a row
    including: Transaction_ID,Household_ID,Merchant_ID,Transaction_Date,Voucher_id,Denomination_Used,Amount_Redeemed
    """
    _ensure_redeem_dir()
    dt = datetime.now()
    filename = _redeem_filename(dt)
    path = os.path.join(REDEEM_DIR, filename)

    header = [
        "Transaction_ID",
        "Household_ID",
        "Merchant_ID",
        "Transaction_Date",
        "Voucher_id",
        "Denomination_Used",
        "Amount_Redeemed"
    ]

    file_exists = os.path.exists(path)

    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not file_exists:
            w.writerow(header)

        for v in vouchers:
            # v: mongo voucher doc
            denom = int(v.get("denomination", 0))
            w.writerow([
                tx_id,
                household_id,
                merchant_id,
                ts_full,          # YYYYMMDDhhmmss
                v["_id"],         # voucher_id（uuid）
                denom,            # Denomination_Used
                total_amount      # Amount_Redeemed
            ])



def _next_tx_id():
    # TX2026_YYYYMMDDhhmmss + 3ranmodom digits
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"TX2026_{now}{random.randint(0, 999):03d}"



def redeem_transaction(household_id: str, merchant_id: str, voucher_ids: list, tranche_id: str = None):
    """
    one transaction = one tx document (written to db.transactions)
    Multiple vouchers can be redeemed in one tx
    After redemption: the corresponding vouchers.used is set to True
    """

    if not isinstance(voucher_ids, list) or len(voucher_ids) == 0:
        raise ValueError("voucher_ids must be a non-empty list")

    # 1) Validate that merchant / household exists
    if db.merchants.find_one({"_id": merchant_id}) is None:
        raise ValueError("Merchant not registered")

    if db.households.find_one({"_id": household_id}) is None:
        raise ValueError("Household not registered")

    # 2) Fetch vouchers 
    vouchers = list(db.vouchers.find({"_id": {"$in": voucher_ids}}))
    if len(vouchers) != len(voucher_ids):
        raise ValueError("Some voucher_id(s) not found")

    # 3) Validate: ownership, tranche, and unused status
    for v in vouchers:
        if v.get("household_id") != household_id:
            raise ValueError("Some voucher(s) do not belong to this household")
        if tranche_id is not None and v.get("tranche_id") != tranche_id:
            raise ValueError("Some voucher(s) do not belong to the specified tranche")
        if v.get("used") is True:
            raise ValueError("Some voucher(s) have already been used")

    # 4) Update used=True (to avoid duplicate redemption)
    update_filter = {
        "_id": {"$in": voucher_ids},
        "household_id": household_id,
        "used": False
    }
    if tranche_id is not None:
        update_filter["tranche_id"] = tranche_id

    res = db.vouchers.update_many(update_filter, {"$set": {"used": True}})
    if res.modified_count != len(voucher_ids):
        raise ValueError("Redeem failed: some voucher(s) are no longer available")

    # 5) Generate tx document
    ts_full = datetime.now().strftime("%Y%m%d%H%M%S")
    tx_id = _next_tx_id()

    total = 0
    for v in vouchers:
        total += int(v.get("denomination", 0))

    tx_doc = {
        "tx_id": tx_id,
        "household_id": household_id,
        "merchant_id": merchant_id,
        "timestamp": ts_full,
        "voucher_ids": [v["_id"] for v in vouchers],
        "total_amount": total
    }

    # 6) Write to Redemption CSV (hourly files)
    _append_redemption_rows(
        tx_id=tx_id,
        household_id=household_id,
        merchant_id=merchant_id,
        ts_full=ts_full,
        vouchers=vouchers,
        total_amount=total
    )

    return tx_doc


# balance checking
def list_available_vouchers(household_id: str, tranche_id: str = None):
    # to check whether household exists
    if db.households.find_one({"_id": household_id}) is None:
        raise ValueError("Household not registered")

    query = {"household_id": household_id, "used": False}
    if tranche_id:
        query["tranche_id"] = tranche_id

    vouchers = list(db.vouchers.find(query, {"_id": 1, "denomination": 1, "tranche_id": 1}))

    return [
        {
            "voucher_id": v["_id"],
            "denomination": v["denomination"],
            "tranche_id": v.get("tranche_id")
        }
        for v in vouchers
    ]

#bai：balance summary
def get_balance_summary(household_id: str, tranche_id: str = None):
    if db.households.find_one({"_id": household_id}) is None:
        raise ValueError("Household not registered")

    match = {"household_id": household_id, "used": False}
    if tranche_id:
        match["tranche_id"] = tranche_id

    pipeline = [
        {"$match": match},
        {"$group": {"_id": "$denomination", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    rows = list(db.vouchers.aggregate(pipeline))

    summary = {int(r["_id"]): int(r["count"]) for r in rows}
    total_count = sum(summary.values())
    total_amount = sum(k * v for k, v in summary.items())

    return {
        "household_id": household_id,
        "tranche_id": tranche_id,
        "summary": summary,
        "total_vouchers": total_count,
        "total_amount": total_amount
    }

def get_available_vouchers_list(household_id: str, tranche_id: str = None):
    if db.households.find_one({"_id": household_id}) is None:
        raise ValueError("Household not registered")

    q = {"household_id": household_id, "used": False}
    if tranche_id:
        q["tranche_id"] = tranche_id


    vouchers = list(db.vouchers.find(q, {"_id": 1, "denomination": 1, "tranche_id": 1}).sort("denomination", 1))
    return [
        {"voucher_id": v["_id"], "denomination": int(v["denomination"]), "tranche_id": v.get("tranche_id")}
        for v in vouchers
    ]
#=====================bai==========================