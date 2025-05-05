
chrome.runtime.onMessage.addListener((message) => {
    if (message.action === "scrapeData") {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (!tabs.length) return;
            const tab = tabs[0];

            // To exclude adding scripts to chrome default pages
            // if (tab.url.startsWith('chrome://') || tab.url.startsWith('chrome-extension://')) {
            //     console.warn("Restricted page. Skipping script injection.");
            //     return;
            // }

            chrome.scripting.executeScript({
                target: { tabId: tab.id, allFrames: true },
                func: extractData
            });
        });
    }
});


function extractData() {
    const patientId = document.getElementsByName("PATIENTID")[0].value || 'Not found';
    const firstName = document.querySelector('#FIRSTNAME')?.value || 'Not found';
    const lastName = document.querySelector('#LASTNAME')?.value || 'Not found';
    const dob = document.querySelector('#dob')?.value || 'Not found';

    chrome.runtime.sendMessage({
        type: 'return_data',
        data: {
            patientId: patientId,
            firstName: firstName,
            lastName: lastName,
            dob: dob
        }
    });
}
