import os
import time
import uuid
import boto3
import tempfile
import requests
import shutil
import json
import re
import openai
from pydub import AudioSegment
from flask import jsonify
from modul.const import VONAGE_APPLICATION_ID,VONAGE_PRIVATE_KEY_PATH, S3_BUCKET_NAME ,OPENAI_API_KEY , AWS_REGION
from vonage import Auth , Vonage
from vonage_video import ListArchivesFilter
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from weasyprint import HTML


s3 = boto3.client("s3",region_name = AWS_REGION)
transcribe = boto3.client("transcribe", region_name= AWS_REGION)
client = boto3.client('ses', region_name=AWS_REGION)


openai.api_key = OPENAI_API_KEY


vonage_client = Vonage(
    Auth(
        application_id=VONAGE_APPLICATION_ID,
        private_key=VONAGE_PRIVATE_KEY_PATH,
    )
)


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


def download_and_transcribe_mp4(url, session_id):
    """Download .mp4 archive, convert to .mp3, transcribe via AWS, save to S3 and generate SOAP"""
    
    temp_dir = tempfile.mkdtemp()
    print(f"Created temporary directory: {temp_dir}")
    
    try:
        print(f"Downloading video for session {session_id}...")
        response = requests.get(url, stream=True)
        if response.status_code != 200:
            return f"Failed to download file: HTTP status code {response.status_code}"

        mp4_path = os.path.join(temp_dir, f"{session_id}.mp4")
        with open(mp4_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Convert to MP3
        mp3_path = os.path.join(temp_dir, f"{session_id}.mp3")
        AudioSegment.from_file(mp4_path, format="mp4").export(mp3_path, format="mp3")
        
        # Upload to S3
        mp3_filename = os.path.basename(mp3_path)
        s3_key = f"sessions/{session_id}/audio/{mp3_filename}"
        s3.upload_file(mp3_path, S3_BUCKET_NAME, s3_key)
        
        # Start transcription job
        job_name = f"transcribe-{session_id}-{uuid.uuid4()}"
        media_uri = f"s3://{S3_BUCKET_NAME}/{s3_key}"

        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={"MediaFileUri": media_uri},
            MediaFormat="mp3",
            LanguageCode="en-US",
            OutputBucketName=S3_BUCKET_NAME,
        )
        
        print(f"Started transcription job: {job_name}")
        while True:
            status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            job_status = status["TranscriptionJob"]["TranscriptionJobStatus"]
            if job_status in ["COMPLETED", "FAILED"]:
                break
            time.sleep(5)
        
        if job_status == "FAILED":
            return f"Transcription failed for session {session_id}"
        
        # Download transcript JSON
        transcript_key = f"{job_name}.json"
        local_json_path = os.path.join(temp_dir, transcript_key)
        s3.download_file(S3_BUCKET_NAME, transcript_key, local_json_path)
        
        with open(local_json_path, "r") as f:
            result = json.load(f)
            transcript_text = result["results"]["transcripts"][0]["transcript"]
        
        # Save transcript text file and upload
        final_transcription_path = os.path.join(temp_dir, f"{session_id}.txt")
        with open(final_transcription_path, "w") as f:
            f.write(transcript_text)
        
        s3.upload_file(final_transcription_path, S3_BUCKET_NAME, f"sessions/{session_id}/{session_id}.txt")
        
        # Generate SOAP + PDF
        soap_json = convertToSOAP(transcript_text, session_id)
        soap_to_pdf(soap_json, session_id)
        
        return soap_json
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def convertToSOAP(text, sessionID):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages = [
            {
                "role": "system",
                "content": """You are a clinical assistant AI that converts natural language conversations between a doctor and a patient into a structured SOAP note.

                You will receive a **continuous, unlabeled transcription** of a conversation. The roles of the doctor and patient are not marked — you must infer speaker identity based on the language:
                - Clinical language, explanations, or treatment suggestions → doctor.
                - Symptoms, complaints, feelings → patient.

                Your task is to:
                1. Analyze the full conversation.
                2. Identify relevant information for each SOAP section.
                3. Output a valid JSON object with **nested dictionaries** for each section:
                - `subjective`: symptoms and experiences reported by the patient.
                - `objective`: doctor's findings, questions, and observations.
                - `assessment`: doctor's diagnosis or impressions.
                - `plan`: prescribed treatment, investigations, follow-up, etc.

                Rules:
                - Each section must be a JSON object (use `{}` if no data is available).
                - Ensure JSON is syntactically correct and parsable.
                - Do not include explanations or markdown — return only the JSON object.

                Now process the following doctor-patient conversation transcript:
                """
            },
            {
                "role": "user",
                "content": text
            }
        ]
    )

    raw_response = response.choices[0].message["content"].strip()
    print("Raw response:", raw_response)  # for debugging

    # Try to extract JSON part, ignoring ```json or ``` wrappers
    cleaned_response = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_response, flags=re.DOTALL).strip()

    try:
        soap_data = raw_response
    except json.JSONDecodeError as e:
        print("JSON decoding error:", e)
        print("Cleaned response:", cleaned_response)
        return None  # or raise error, or log

    # Save to file
    soap_json_path = f"/tmp/{sessionID}_summary.json"
    with open(soap_json_path, "w") as json_file:
        json.dump(soap_data, json_file, indent=4)

    # Upload to S3
    s3_key = f"sessions/{sessionID}/{sessionID}_summary.json"
    s3.upload_file(soap_json_path, S3_BUCKET_NAME, s3_key)

    result = {
        "response" : response['choices'][0]['message']['content']
    }

    return result  # optionally return for use in other parts of app


def send_session_email(session_url):
    """Send a session URL as an email message to recipients using AWS SES."""
    try:


        # AWS SES Configuration
        SENDER_EMAIL = "tkarthik@clustrex.com"
        RECIPIENT_EMAILS = ["tkarthik@clustrex.com"]

        # Email content
        subject = "Video Session Link"
        html_body = f"""
        <html>
        <head></head>
        <body>
          <p>Hello,</p>
          <p>You have been invited to a video session. Click the link below to join:</p>
          <p><a href="{session_url}">{session_url}</a></p>
        </body>
        </html>
        """


        # Send email to each recipient
        for recipient in RECIPIENT_EMAILS:
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = SENDER_EMAIL
            message['To'] = recipient
            message.attach(MIMEText(html_body, 'html'))

            response = client.send_raw_email(
                Source=SENDER_EMAIL,
                Destinations=[recipient],
                RawMessage={'Data': message.as_string()}
            )
            print(f"Email sent to {recipient}. Message ID: {response['MessageId']}")

    except Exception as e:
        print(f"Error sending session email: {str(e)}")


def soap_to_pdf(soap_notes, session_id):
    try:
        doc_path = f"/tmp/{session_id}.pdf"

        soap_notes = soap_notes.get("response")
        
        if soap_notes is not None:
            soap_notes = json.loads(soap_notes)

            soap_content = ""
            for field, content in soap_notes.items():
                soap_content += f"<p><b>{field}:</b></p>"
                for key, value in content.items():
                    soap_content += f"<p><b>{key}:</b> {value}</p>"

            text_content = f"""
            <html>
                <head></head>
                <body>
                    <h1 style="text-align:center;">SOAP Notes Document</h1>
                    {soap_content}
                </body>
            </html>
            """

            # Save PDF
            HTML(string=text_content).write_pdf(doc_path)
            print("PDF generated successfully")

    except Exception as e:
        print(f"Error generating SOAP document: {str(e)}") 


def fetch_archive(session_id):
    """ Function to fetch archive URL for the given session_id """
    try:
        # List archives to find the matching one
        filter = ListArchivesFilter(offset=0)
        archives, count, _ = vonage_client.video.list_archives(filter)

        # Find the active archive that corresponds to the session_id
        matching_archive = next(
            (a for a in archives if a.session_id == session_id),
            None
        )
        if not matching_archive:
            print(f"No active archive found for session {session_id}")
            return

        archive_id = matching_archive.id

        # Poll the archive status until it's 'available' or 20 seconds have passed
        max_retries = 20
        interval = 2  # Check every 2 seconds
        for _ in range(max_retries):
            archive = vonage_client.video.get_archive(archive_id)
            if archive.status == "available":
                print(f"Archive for session {session_id} is available. URL: {archive.url}")
                # You can return or store the URL as needed
                return archive.url
            time.sleep(interval)

        # If archive is still not available after 20 seconds
        print(f"Archive for session {session_id} is still pending after 20 seconds.")
        return None

    except Exception as e:
        print(f"Error fetching archive for session {session_id}: {str(e)}")


def poll_for_matching_archive(session_id, timeout=60, interval=2):
    """
    Polls for an archive related to the given session_id.
    - Stops archive if paused.
    - Waits until archive is available or paused after timeout.
    """
    try:
        max_retries = timeout // interval
        matching_archive = None

        for attempt in range(max_retries):
            filter = ListArchivesFilter(offset=0)
            archives, count, _ = vonage_client.video.list_archives(filter)

            for archive in archives:
                if archive.session_id == session_id:
                    matching_archive = archive
                    print(f"[{attempt}] Found archive ID {archive.id} — status: {archive.status}")

                    if archive.status == "available":
                        print(f"✅ Archive is ready: {archive.id}")
                        print(f"URL: {archive.url}")
                        soap=download_and_transcribe_mp4(session_id=session_id,url=archive.url)
                        print(soap)
                        return archive  # Archive is available — return immediately

            time.sleep(interval)

        # Final check after polling
        if matching_archive:
            archive = vonage_client.video.get_archive(matching_archive.id)
            if archive.status == "paused":
                print(f"⏹️ Final status: Archive is still paused after polling.")
                return "paused"
            elif archive.status == "available":
                print(f"✅ Final status: Archive is available.")
                return archive

        print(f"⏰ No matching available archive found for session {session_id}.")
        return None

    except Exception as e:
        print(f"❌ Error during archive polling: {str(e)}")
        return None

