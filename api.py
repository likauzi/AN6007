from models import Household, Tranche
from db import save_household, save_tranche

# In-memory store (injected)
households = {}

def init(household_store):
    global households
    households = household_store


def register_household(hid, postal, district):
    if hid in households:
        raise ValueError("Household already exists")

    h = Household(hid, postal)
    households[hid] = h
    save_household(h)
    return h


def claim_tranche(hid, tranche_id="JAN2025"):
    if hid not in households:
        raise ValueError("Household not registered")

    t = Tranche(tranche_id, {"2":60,"5":24,"10":6})
    households[hid].tranches[tranche_id] = t
    save_tranche(hid, t)
    return t

