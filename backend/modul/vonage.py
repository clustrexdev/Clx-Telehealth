import os
import time
from threading import Thread
from vonage import Auth, Vonage
from vonage_video.models import SessionOptions
from vonage_video import TokenOptions
from flask import request, jsonify, render_template, abort
from modul.functions import poll_for_matching_archive , send_session_email
from modul.const import VONAGE_APPLICATION_ID, VONAGE_PRIVATE_KEY_PATH, APPLICATION_BASE_URL


def register_routes(app):
    vonage_client = Vonage(
        Auth(
            application_id=VONAGE_APPLICATION_ID,
            private_key=VONAGE_PRIVATE_KEY_PATH,
        )
    )
    print(APPLICATION_BASE_URL)

    active_sessions = {}

    @app.route("/session", methods=["GET"])
    def create_session():
        try:
            options = SessionOptions(media_mode='routed',archive_mode="always")
            session = vonage_client.video.create_session(options)
            session_id = session.session_id

            token_options = TokenOptions(session_id=session_id, role='publisher')
            token = vonage_client.video.generate_client_token(token_options)
            token_str = token.decode('utf-8')

            active_sessions[session_id] = {"created_at": time.time()}

            invitelink = f"{APPLICATION_BASE_URL}/subscriber?session={session_id}&token={token_str}"

            send_session_email(session_url=invitelink)

            return jsonify({
                "apiKey": VONAGE_APPLICATION_ID,
                "sessionId": session_id,
                "token": token_str,
                "invite_link": invitelink
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500


    @app.route("/end-session/<session_id>", methods=["POST"])
    def end_session(session_id):
        try:
            del active_sessions[session_id]

            Thread(target=poll_for_matching_archive, args=(session_id,)).start()

            return jsonify({
                "message": f"Session {session_id} ended. Archive fetching triggered."
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 500
        

    @app.route("/subscriber")
    def subscriber():
        session_id = request.args.get("session")
        token = request.args.get("token")
        
        if not session_id or not token:
            abort(400, description="Missing required query parameters: session and token")
        
        return render_template("subscriber.html")

