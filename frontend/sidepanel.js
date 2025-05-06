const practiceId = 1959225;
const apt_id = 3504656; // Kept static appointment ID.
var patientId;

document.getElementById("recordPatientDataButton").addEventListener("click", () => {
    chrome.runtime.sendMessage({ action: "scrapeData" });
});

chrome.runtime.onMessage.addListener((message) => {
    if (message.type === "return_data") {
        patientId = message.data.patientId;
        // if (isValidPatientId(patientId)){}
        document.getElementById("patientId").innerText = patientId;
        document.getElementById("firstName").innerText = message.data.firstName;
        document.getElementById("lastName").innerText = message.data.lastName;
        document.getElementById("dob").innerText = message.data.dob;
    }
});

function isValidPatientId(patientId){
    return patientId !== "Not found" && !isNaN(patientId) && patientId.trim() !== "";
}

// async function get_department() {
//     let patient_info = await get_patient_details();
//     console.log(patient_info.departmentid)
//     return patient_info.departmentid
// }


let apiKey, sessionId, token, session, publisher, inviteLink;
        
const callBtn = document.getElementById('call-button');
const endBtn = document.getElementById('end-call');
const startScreen = document.getElementById('start-screen');
const callScreen = document.getElementById('call-screen');
const waitingMsg = document.getElementById('waiting-msg');
const subscriberContainer = document.getElementById('subscriber');

async function fetchSessionDetails() {
    const res = await fetch('http://localhost:3000/session');
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
    if(await checkin_requirements(apt_id)){
    // if(true){
        try {
            const data = await fetchSessionDetails();
            apiKey = data.apiKey;
            sessionId = data.sessionId;
            token = data.token;
            inviteLink = data.inviteLink;

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

                session.publish(publisher);
            });

            showScreen('call-screen');
        } catch (e) {
            alert(e.message);
        }
    }
}

async function endCall() {
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

    // Check-in after the end call
    await checkin_appointment(apt_id);

    // Get Encounter ID.
    const [encounterId, departmentId] = await get_encounter_details(apt_id);

    // Upload document against the encounter ID.
    if (encounterId != null){
        const formData = await get_pdf();
        formData.append("departmentid", departmentId);
        formData.append("encounterid", encounterId);
        
        const result = await add_encounter_document(formData);
        console.log(result);
    }

}

callBtn.addEventListener('click', startCall);
endBtn.addEventListener('click', endCall);


async function checkin_requirements(apptid){
    const result = await fetch(`http://localhost:3000/${practiceId}/appointments/${apptid}/checkin`)
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
    fetch(`http://localhost:3000/${practiceId}/appointments/${apptid}/checkin`, {method: 'POST'})
    console.log("Appointment Checked In!");
}

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function get_encounter_details(apptid){
    for (let attempt = 1; attempt <= 6; attempt++) {
        try{
            const response = await fetch(`http://localhost:3000/${practiceId}/appointments/${apptid}`);
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

async function get_patient_details(){
    try{
        const response = await fetch(`http://localhost:3000/${practiceId}/patients/${patientId}`);
        if (!response.ok) throw new Error('Failed to fetch departmentId');
        const data = await response.json();
        return data[0];
    }
    catch (err) {
        console.error('API call failed:', err);
    }
}

async function get_pdf(){
    const res = await fetch('http://localhost:3000/get-pdf');
    const blob = await res.blob();
    const formData = new FormData();
    formData.append('attachmentcontents', blob, 'source.pdf');
    console.log("File Generated Successfully!");
    return formData;
}

async function add_encounter_document(formData){
    const result = await fetch(`http://localhost:3000/${practiceId}/${patientId}/encounterdocument`, {method: 'POST', body: formData})
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

