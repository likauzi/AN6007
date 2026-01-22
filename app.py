from flask import Flask, request, render_template, redirect
import api
from db import load_all_households

app = Flask(__name__)

# -------- System Restart --------
households = load_all_households()
api.init(households)

# -------- Routes --------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/register", methods=["POST"])
def register():
    api.register_household(
        request.form["hid"],
        request.form["postal"]
    )
    return redirect("/dashboard")

@app.route("/api/claim", methods=["POST"])
def claim():
    api.claim_tranche(request.form["hid"])
    return redirect("/dashboard")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", households=households)

if __name__ == "__main__":
    app.run(debug=True)


