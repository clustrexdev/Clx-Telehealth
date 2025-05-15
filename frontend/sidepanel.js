console.log("Sidepanel script is loaded")   // For verifying the sidepanel.js is loaded successfully.

// const appBaseURL = "http://localhost:3000";
const appBaseURL = "https://wpgstw5c32.execute-api.us-east-1.amazonaws.com/dev";
const practiceId = 1959225;
const headers = {
    "authorizationToken": "allow"
}
const apt_id = 3504656; // Kept static appointment ID.
var patientId;
var email = "";

let apiKey, sessionId, token, session, publisher, inviteLink;

const callBtn = document.getElementById('call-button');
const endBtn = document.getElementById('end-call');
const startScreen = document.getElementById('start-screen');
const callScreen = document.getElementById('call-screen');
const waitingMsg = document.getElementById('waiting-msg');
const subscriberContainer = document.getElementById('subscriber');
callBtn.classList.add("disabled");

callBtn.addEventListener('click', startCall);
endBtn.addEventListener('click', endCall);


// Logout Button
document.getElementById("logout").addEventListener("click", () => {
    logout();
});


// Fetch the email from extension's local storage.
chrome.storage.local.get("profile", function(result) {
    email = result.profile.email;
    document.getElementById("email").textContent = email;
    console.log("User email:", result.profile.email);
});


// Logout function
function logout(){
    chrome.identity.getAuthToken({ interactive: false }, function(token) {
        if (chrome.runtime.lastError || !token) return;
    
        chrome.identity.removeCachedAuthToken({ token: token }, function() {
            fetch('https://accounts.google.com/o/oauth2/revoke?token=' + token)
            .then(() => {
                window.location.href = chrome.runtime.getURL("auth.html");
            });
        });
    });
}


// On clicking the recordPatientDataButton it sends a request to background.js file to scrape the data.
document.getElementById("recordPatientDataButton").addEventListener("click", () => {
    chrome.runtime.sendMessage({ action: "scrapeData" });
});


// Checks whether the scraped data is a valid Patient. (must be a proper integer value)
function isValidPatientId(patientId){
    return patientId !== "Not found" && !isNaN(patientId) && patientId.trim() !== "";
}


// On successful scraping of data the call sends the scraped data to show in the extension.
chrome.runtime.onMessage.addListener((message) => {
    if (message.type === "return_data") {
        patientId = message.data.patientId;
        if (isValidPatientId(patientId)){
            callBtn.classList.remove("disabled");
            document.getElementById("recordPatientDataButton").style.display = "none";
            document.getElementById("NoPatientDetails").style.display = "none";
            document.getElementById("patientId").innerText = patientId;
            document.getElementById("firstName").innerText = message.data.firstName;
            document.getElementById("lastName").innerText = message.data.lastName;
            document.getElementById("dob").innerText = message.data.dob;
        }
        else{
            callBtn.classList.add("disabled");
            document.getElementById("recordPatientDataButton").style.display="block";
            document.getElementById("NoPatientDetails").style.display = "block";
        }
    }
});


async function fetchSessionDetails() {
    const res = await fetch(`${appBaseURL}/session`, {method: 'GET', headers: headers});
    if (!res.ok) throw new Error('Failed to fetch session');
    return res.json();
}


function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(screenId).classList.add('active');
}


function copyInviteLink(){
    navigator.clipboard.writeText(inviteLink)
    .then(()=>alert('Link copied to clipboard!'))
    .catch(() => alert('Failed to copy link.'));
}


async function startCall() {
    // if(isValidPatientId(patientId) && await checkin_requirements(apt_id)){
    if(isValidPatientId(patientId)){
        try {
            const data = await fetchSessionDetails();
            apiKey = data.apiKey;
            sessionId = data.sessionId;
            token = data.token;
            inviteLink = data.invite_link;

            document.getElementById("invite-copy-button").addEventListener("click", () => {
                copyInviteLink();
            });

            session = OT.initSession(apiKey, sessionId);

            session.on('streamCreated', event => {
                waitingMsg.style.display = 'none';
                const subscriber = session.subscribe(
                    event.stream,
                    subscriberContainer,
                    { insertMode: 'append', width: '100%' }
                );
                document.getElementById('waiting-msg').style.display = 'none';
                document.getElementById("patient-role").style.display = "block";
            });

            session.connect(token, err => {
                if (err) {
                    alert('Connection error: ' + err.message);
                    return;
                }

                publisher = OT.initPublisher('publisher', {
                    insertMode: 'append',
                    width: '100%'
                });

                // session.publish(publisher);
                session.publish(publisher, async (publishErr) => {
                    if (publishErr) {
                      console.error('Publishing error:', publishErr);
                      return;
                    }
        
                    try {
                      const recordingResponse = await fetch(`${appBaseURL}/start-recording/${sessionId}`, {
                        method: 'POST', headers: headers
                      });
                      
                      const recordingData = await recordingResponse.json();
                      
                      if (!recordingResponse.ok) {
                        console.error('Failed to start recording:', recordingData.error);
                      } else {
                        console.log('Recording started:', recordingData);
                        document.querySelector('.recording-indicator').style.display = 'block';
                      }
                    } catch (recordErr) {
                      console.error('Error starting recording:', recordErr);
                    }
                });
                document.getElementById("provider-role").style.display = "block";
            });

            showScreen('call-screen');
            document.querySelector('.recording-indicator').style.display = 'none';
        } catch (e) {
            alert(e.message);
        }
    }
}


async function endCall() {
    try{
        if (sessionId) {
            const response = await fetch(`${appBaseURL}/end-session/${sessionId}`, {
              method: 'POST', headers: headers
            });
            
            const data = await response.json();
            
            if (!response.ok) {
              throw new Error(data.error || 'Unknown error ending session');
            }
            
        }
    
        if (publisher) {
            session.unpublish(publisher);
            publisher = null;
        }
    
        if (session) {
            session.disconnect();
            session = null;
        }
    
        document.getElementById('subscriber').innerHTML =
        '<div id="waiting-msg" class="status">Waiting for other user to join...</div>';
    
        showScreen('start-screen');
    
        // Check-in after the call is ended. We will get the encounter id after this step.
        // await checkin_appointment(apt_id);
    
        // Get Encounter ID.
        const [encounterId, departmentId] = await get_encounter_details(apt_id);
    
        // Upload document against the encounter ID.
        if (encounterId != null){
            var formData = await get_pdf();
            if (formData.status == "Success"){
                formData = formData.file;
                formData.append("departmentid", departmentId);
                formData.append("encounterid", encounterId);
                
                const result = await add_encounter_document(formData);
                console.log(result);
            }
            else {
                console.log("No document is generated to upload!");
            }
        }
    } catch (error) {
        console.error('Error ending call:', error);
        alert('An error occurred while ending the call: ' + error.message);
      }

}


async function checkin_requirements(apptid){
    const result = await fetch(`${appBaseURL}/${practiceId}/appointments/${apptid}/checkin`, {method: 'GET', headers: headers})
    .then(res => {
        if(!res.ok){
            return res.json().then(res=>{throw new Error(res.error)});
        }
        console.log("Requirements Satisfied!");
        return true;
    })
    .catch(err => {
        console.log(err);
        return false;
    })
    return result;
}


async function checkin_appointment(apptid){
    fetch(`${appBaseURL}/${practiceId}/appointments/${apptid}/checkin`, {method: 'POST', headers: headers})
    console.log("Appointment Checked In!");
}


async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


async function get_encounter_details(apptid){
    // It will take time to complete checkin and get encounter ID. 
    // So here we are retrying 6 times with 3 secs gap.
    for (let attempt = 1; attempt <= 6; attempt++) {
        try{
            const response = await fetch(`${appBaseURL}/${practiceId}/appointments/${apptid}`, {method: 'GET', headers: headers});
            const data = await response.json();
            let encounterId = null;
            if (data != null && data.length){
                encounterId = data[0].encounterid;
                if (encounterId != null){
                    console.log("Fetched Appointment Details!");
                    return [encounterId, data[0].departmentid]
                }
            }
        }
        catch (err) {
            console.error('API call failed:', err);
        }
        await sleep(3000);
    }
    console.warn("No Encounter ID found even after 15 seconds");
    return null;
}


async function get_pdf(){
    try{
        const res = await fetch(`${appBaseURL}/get-pdf`, {method: 'GET', headers: headers});
        if (!res.ok) {
            return res.json().then(res => {throw new Error(res.error)})
        }
        const blob = await res.blob();
        const formData = new FormData();
        formData.append('attachmentcontents', blob, 'source.pdf');
        console.log("File Generated Successfully!");
        return {status: "Success", file: formData};
    }
    catch (error_msg) {
        console.error("get_pdf()", error_msg);
        return {status: "Failed", error: error_msg};
    }
}


async function add_encounter_document(formData){
    const result = await fetch(`${appBaseURL}/${practiceId}/${patientId}/encounterdocument`, {method: 'POST', headers: headers, body: formData})
    .then(res => {
        if(!res.ok){
            return res.json().then(res=>{throw new Error(res.error)});
        }
        console.log("Uploaded the SOAP Document Successfully!");
        return res.json();
    })
    .catch(err => {
        console.log(err);
    })
    return result
}


// Don't remove the below function code.

// async function get_department() {
//     let patient_info = await get_patient_details();
//     console.log(patient_info.departmentid)
//     return patient_info.departmentid
// }

// async function get_patient_details(){
//     try{
//         const response = await fetch(`${appBaseURL}/${practiceId}/patients/${patientId}`, {method: 'GET', headers: headers});
//         if (!response.ok) throw new Error('Failed to fetch departmentId');
//         const data = await response.json();
//         return data[0];
//     }
//     catch (err) {
//         console.error('API call failed:', err);
//     }
// }
