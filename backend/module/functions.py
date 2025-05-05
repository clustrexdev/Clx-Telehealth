from flask import jsonify

def validate_checkin_fields(data):
    try:
        for row in data:
            if row.get("required") is True and row.get("complete") is False:
                return jsonify({
                    "message": f"{row.get('name')} is missing!"
                }), 400
        return jsonify({"message": "Ready for check-in"}), 200
    except Exception as e:
        print(str(e), flush=True)
        return jsonify({"error": str(e)}), 500

