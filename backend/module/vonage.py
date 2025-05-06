from module import app
from flask import jsonify
from vonage import Auth, Vonage
from vonage_video.models import SessionOptions
from vonage_video import TokenOptions
from module.const import VONAGE_APPLICATION_ID, VONAGE_PRIVATE_KEY_PATH


vonage_client = Vonage(
	Auth(
    	application_id=VONAGE_APPLICATION_ID,
    	private_key=VONAGE_PRIVATE_KEY_PATH,
	)
)

@app.route("/session", methods=["GET"])
def create_session():
    try:
        options = SessionOptions(media_mode='relayed')
        session = vonage_client.video.create_session(options)
        sessionId = session.session_id

        token_options = TokenOptions(session_id=sessionId, role='publisher')
        token = vonage_client.video.generate_client_token(token_options)
        token_str = token.decode('utf-8')
        invite_link = f"http://localhost:5500/backend/module/templates/index-final-copy.html?session={sessionId}&token={token_str}"

        return jsonify({
            "apiKey": VONAGE_APPLICATION_ID,
            "sessionId": sessionId,
            "token": token_str,
            "inviteLink": invite_link
        })
    except Exception as e:
        print("Error creating session:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200


