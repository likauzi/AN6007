# app_final.py
# Purpose: Web pages for manual testing (HTML forms/pages only).
# All JSON APIs are registered via api_routes.py under /api/v1/...

from flask import Flask, request, render_template, redirect
import api
from db import load_all_households
from api_routes import register_api_routes

app = Flask(__name__)

# -------- System Restart --------
households = load_all_households()
api.init(households)

# -------- JSON API routes (for frontend/mobile, all under /api/v1/...) --------
register_api_routes(app, households)

# -------- Web pages (manual testing) --------
@app.route("/")
def index():
    # Requires templates/index.html
    # This page typically contains: register household form + claim form + links to other test pages
    return render_template("index.html")


# Household register (HTML form submission)
@app.route("/api/register", methods=["POST"])
def register_household_form():
    postal = request.form.get("postal", "").strip()
    api.register_household(postal)
    return redirect("/dashboard")


# Claim tranche (HTML form submission)
@app.route("/api/claim", methods=["POST"])
def claim_tranche_form():
    hid = request.form.get("hid", "").strip()
    api.claim_tranche(hid)  # default tranche_id = JAN2026 in your api.py
    return redirect("/dashboard")


# Dashboard page (shows in-memory households + their tranches)
@app.route("/dashboard")
def dashboard():
    # Requires templates/dashboard.html
    return render_template("dashboard.html", households=households)


# Optional: Redeem test page (web UI)
@app.route("/redeem_page")
def redeem_page():
    # Requires templates/redeem.html
    # In your redeem.html, make sure it calls the JSON API endpoint /api/v1/redeem (not /api/redeem)
    return render_template("redeem.html")


# Optional: Balance test page (web UI)
@app.route("/balance_page")
def balance_page():
    # Requires templates/balance.html
    # In your balance.html, make sure it calls:
    #   GET /api/v1/households/<hid>/balance?mode=summary|list&tranche_id=...
    #   GET /api/v1/households/<hid>/vouchers?tranche_id=...
    return render_template("balance.html")


if __name__ == "__main__":
    app.run(debug=True)


