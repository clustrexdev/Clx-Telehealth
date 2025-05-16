import os
import json
import requests
from modul.const import ATHENA_BASE_URL
from flask import request, jsonify, send_file
from modul.functions import validate_checkin_fields
from modul.utils import get_request, post_request, get_headers


def register_athena_routes(app):

    @app.route("/<practice_id>/appointments/<appointment_id>/checkin", methods = ["GET"])
    def validate_appointment_checkin(practice_id, appointment_id):
        try:
            appt_checkin_url = f"{ATHENA_BASE_URL}/v1/{practice_id}/appointments/{appointment_id}/checkin"
            final_response, status_code = get_request(appt_checkin_url)
            if status_code == 200:
                final_response, status_code = validate_checkin_fields(final_response)
            return final_response, status_code
        except Exception as e:
            print(str(e), flush=True)
            return jsonify({"error": e}), 500


    @app.route("/<practice_id>/appointments/<appointment_id>/checkin", methods = ["POST"])
    def appointment_check_in(practice_id, appointment_id):
        try:
            appointment_check_in_url = f"{ATHENA_BASE_URL}/v1/{practice_id}/appointments/{appointment_id}/checkin"
            return post_request(appointment_check_in_url)
        except Exception as e:
            print(str(e), flush=True)
            return jsonify({"error": e}), 500


    @app.route("/<practice_id>/appointments/<appointment_id>", methods = ["GET"])
    def get_appointment_details(practice_id, appointment_id):
        try:
            get_appt_url = f"{ATHENA_BASE_URL}/v1/{practice_id}/appointments/{appointment_id}"
            return get_request(get_appt_url)
        except Exception as e:
            print(str(e), flush=True)
            return jsonify({"error": e}), 500


    @app.route("/<practice_id>/patients/<patient_id>", methods = ["GET"])
    def get_patient_details(practice_id, patient_id):
        try:
            get_patient_url = f"{ATHENA_BASE_URL}/v1/{practice_id}/patients/{patient_id}"
            return get_request(get_patient_url)
        except Exception as e:
            print(str(e), flush=True)
            return jsonify({"error": e}), 500


    @app.route("/<practice_id>/<patient_id>/encounterdocument", methods = ["POST"])
    def add_encounter_document(practice_id, patient_id):
        try:
            add_encounter_doc_url = f"{ATHENA_BASE_URL}/v1/{practice_id}/patients/{patient_id}/documents/encounterdocument"
            headers = get_headers() | {'Content-Type': 'multipart/form-data'}
            data = request.form.to_dict() | {"documentsubclass": "PROGRESSNOTE"}

            file = request.files.get('attachmentcontents')
            if file is None:
                return jsonify({"Message": "No Documents attached in 'attachmentcontents' to upload!"}), 400
            
            files = {"attachmentcontents": (file.filename, file.stream, file.content_type)}

            response = requests.post(add_encounter_doc_url, headers=headers, data=data, files=files)
            return json.loads(response.text), response.status_code
        except Exception as e:
            print(str(e), flush=True)
            return jsonify({"error": str(e)}), 500


    @app.route('/get-pdf/<session_id>', methods=['GET'])
    def get_pdf(session_id):
        pdf_path = None
        success = False
        try:
            pdf_path = os.path.join(os.path.dirname(__file__), 'files', f'{session_id}.pdf')
            if os.path.exists(pdf_path):
                success = True
                return send_file(pdf_path, mimetype='application/pdf'), 200
            return jsonify({"error": "No file found"}), 404
        except Exception as e:
            print(str(e), flush=True)
            return jsonify({"error": str(e)}), 500
        finally:
            print("Get PDF")
            if success and pdf_path is not None and os.path.exists(pdf_path):
                os.remove(pdf_path)
    

