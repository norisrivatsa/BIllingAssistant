import requests

ACCESS_TOKEN = "EAAIust0R5WMBOy55fZBqrF3mL7YjTFfztllNxo1FFkPs4rZBh17GaVZANlkGs3ZB86blZAwF89PZCZAy7SDx3cb6nYHXRXTOEjGa0VkWnDgRAtmghP0t9nnz6ICWNkDVAdEFn8pCG4KOZB05jfHQc1sgYVBVIk9W4ZBNVZBZBxdJD3hq0MfyearkG83VAhnaKcYUKOEHTXoedt3sxjqz9B1GsYa8y6iRWgZD"
PHONE_NUMBER_ID = "536195642919681"
# PHONE_NUMBER_ID = "9154400224"

url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

data = {
    "messaging_product": "whatsapp",
    "to": "919154400224",
    "type": "text",
    "text": {"body": "Hello! This is a test message from WhatsApp API."}
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
