class Household:
    def __init__(self, hid, postal_code):
        self.household_id = hid
        self.postal_code = postal_code
        self.tranches = {}   # tranche_id -> Tranche


class Tranche:
    def __init__(self, tranche_id, vouchers):
        self.tranche_id = tranche_id
        self.vouchers = vouchers  # {"2":60,"5":24,"10":6}
