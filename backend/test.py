from modul import handler 
import json # assuming handler is defined in module/__init__.py

test_event = {
    "httpMethod": "GET",
    "headers": {
        "Content-Type": "application/json"
    },
    "path": "/session",
    "isBase64Encoded": False,
    "body" :json.dumps( {
        "object_name": "1746713216362.mp3"
    })
}

response = handler(test_event, None)
print(response)
