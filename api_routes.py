from flask import request, jsonify
import api  # 业务层模块

def register_api_routes(app, households):
    def json_error(message: str, status: int = 400):
        return jsonify({"error": message}), status

    # ---------------- Households ----------------
    @app.route("/api/v1/households", methods=["POST"])
    def api_v1_register_household():
        data = request.get_json(silent=True) or {}
        postal = data.get("postal_code")
        if not postal:
            return json_error("postal_code is required", 400)

        try:
            h = api.register_household(postal)
            return jsonify({
                "household_id": h.household_id,
                "postal_code": h.postal_code,
                "tranches": list(h.tranches.keys())
            }), 201
        except ValueError as e:
            return json_error(str(e), 400)
        except Exception:
            return json_error("internal server error", 500)

    @app.route("/api/v1/households/<hid>/tranches", methods=["POST"])
    def api_v1_claim_tranche(hid):
        data = request.get_json(silent=True) or {}
        tranche_id = data.get("tranche_id")  # optional

        try:
            if tranche_id:
                t = api.claim_tranche(hid, tranche_id=tranche_id)
            else:
                t = api.claim_tranche(hid)

            return jsonify({
                "household_id": hid,
                "tranche_id": t.tranche_id,
                "vouchers": t.vouchers
            }), 201
        except ValueError as e:
            return json_error(str(e), 400)
        except Exception:
            return json_error("internal server error", 500)

    @app.route("/api/v1/households/<hid>", methods=["GET"])
    def api_v1_get_household(hid):
        h = households.get(hid)
        if not h:
            return json_error("household not found", 404)

        return jsonify({
            "household_id": h.household_id,
            "postal_code": h.postal_code,
            "tranches": list(h.tranches.keys())
        }), 200

    # ---------------- Redeem & Balance ----------------
    @app.route("/api/v1/redeem", methods=["POST"])
    def api_v1_redeem():
        data = request.get_json(silent=True) or {}
        try:
            tx = api.redeem_transaction(
                household_id=data.get("household_id"),
                merchant_id=data.get("merchant_id"),
                voucher_ids=data.get("voucher_ids"),
                tranche_id=data.get("tranche_id")  # optional
            )
            return jsonify(tx), 201
        except ValueError as e:
            return json_error(str(e), 400)
        except Exception:
            return json_error("internal server error", 500)

    @app.route("/api/v1/households/<hid>/vouchers", methods=["GET"])
    def api_v1_household_vouchers(hid):
        tranche_id = request.args.get("tranche_id")  # optional
        try:
            vouchers = api.list_available_vouchers(hid, tranche_id=tranche_id)
            return jsonify({
                "household_id": hid,
                "tranche_id": tranche_id,
                "vouchers": vouchers
            }), 200
        except ValueError as e:
            return json_error(str(e), 400)
        except Exception:
            return json_error("internal server error", 500)

    @app.route("/api/v1/households/<hid>/balance", methods=["GET"])
    def api_v1_household_balance(hid):
        tranche_id = request.args.get("tranche_id")  # optional
        mode = request.args.get("mode", "summary")   # summary | list
        try:
            if mode == "list":
                vouchers = api.get_available_vouchers_list(hid, tranche_id=tranche_id)
                return jsonify({
                    "household_id": hid,
                    "tranche_id": tranche_id,
                    "vouchers": vouchers
                }), 200
            else:
                data = api.get_balance_summary(hid, tranche_id=tranche_id)
                return jsonify(data), 200
        except ValueError as e:
            return json_error(str(e), 400)
        except Exception:
            return json_error("internal server error", 500)

