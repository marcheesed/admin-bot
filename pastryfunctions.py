import requests
from bs4 import BeautifulSoup
import urllib3
import re
import os
from dotenv import load_dotenv

load_dotenv()
UN = os.getenv("PASTRY_UN")
TOKEN = os.getenv("PASTRY_TOKEN")

# Disable SSL warnings (you're using a self-signed cert on .diy domain)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create a session to persist cookies
session = requests.Session()

# Step 1: Get login page
login_url = "https://pastry.diy/login"
login_page = session.get(login_url, verify=False)

# Step 2: Parse CSRF token
soup = BeautifulSoup(login_page.text, 'html.parser')
csrf_element = soup.find('input', {'name': 'csrf_token'})
if csrf_element is None:
    print("ERROR: Could not find CSRF token on login page")
    csrf_token = None
else:
    # Safely get the value attribute using try-except
    try:
        csrf_token = csrf_element['value']  # type: ignore
    except (KeyError, TypeError):
        print("ERROR: CSRF token element found but no value attribute")
        csrf_token = None

# Step 3: Prepare login payload
if csrf_token is None:
    print("WARNING: Proceeding without CSRF token - login may fail")
    payload = {
        'username': UN,
        'user_token': TOKEN
    }
else:
    payload = {
        'csrf_token': csrf_token,
        'username': UN,
        'user_token': TOKEN
    }

# Optional: Headers to mimic browser
headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": login_url
}

# Step 4: Submit login form
response = session.post(login_url, data=payload, headers=headers, verify=False)

# Step 5: Confirm login worked
if "Welcome, guest!" in response.text:
    print("LOGIN FAILED YOU BLATHERING APE!!!")

# Optional: Access a protected page
admin_page = session.get("https://pastry.diy/admin/pastes", verify=False)

txt = admin_page.text

rows = re.findall(r'<tr>.*?</tr>', txt, re.DOTALL)

arr = [[]]


arr = []

rows = re.findall(r'<tr>.*?</tr>', txt, re.DOTALL)
for row in rows:
    url_match = re.search(r'<a href="([^"]+)">[^<]+</a>', row)
    username_match = re.search(r'<a href="/profile/([^"]+)">([^<]+)</a>', row)

    url = url_match.group(1) if url_match else ""
    username = username_match.group(1) if username_match else ""

    arr.append([url, username])


    #print(f"URL: {url}, Username: {username}")

#for i in range(len(username_matches)):
    #url = url_matches[i] if i < len(url_matches) else None
    #username = username_matches[i][0]  # group 1: username in href




def searchURL(username):
    arrayofurls = []
    for j in range(len(arr)):

        if username in arr[j][1]:
            arrayofurls.append(arr[j][0])
    output = "User "+username+" owns the urls "
    for i in arrayofurls:
        output += i + ", "
    output = output[:-2]
    if output == "User "+username+" owns the url":
        output = "This user either doesn't exist, or doesn't own any URLs. TRY AGAIN BUCKO!!!"
    return output

def searchOwner(url):
    Found = False
    output = "This user doesn't own any URLs. TRY AGAIN!!!"  # Initialize output
    for j in range(len(arr)):
        if url in arr[j][0]:
            output = arr[j][1] + " owns the url " + arr[j][0] + "!"
            Found = True
            break  # Exit loop once found
    return output