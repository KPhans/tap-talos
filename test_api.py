import requests
import datetime
import hmac
import hashlib
import base64
import json

# ====== Configuration ======
api_key = "SHAM9PQH040Z"
api_secret = "fwcou0bwvtmq4ck3sx32vn5xj9f2a9tb"
host = "tal-295.sandbox.talostrading.com"
path = "/v1/balances"
query = ""  # No filters for now; get all balances
body = ""   # GET request, no body

# ====== Build Authentication Headers ======
utc_now = datetime.datetime.utcnow()
utc_datetime = utc_now.strftime("%Y-%m-%dT%H:%M:%S.000000Z")

params = [
    "GET",
    utc_datetime,
    host,
    path,
]

endpoint = f"https://{host}{path}"
if query:
    endpoint += f"?{query}"
    params.append(query)
if body:
    params.append(body)

payload = "\n".join(params)
hashvalue = hmac.new(
    api_secret.encode('ascii'), payload.encode('ascii'), hashlib.sha256
)
signature = base64.urlsafe_b64encode(hashvalue.digest()).decode()

headers = {
    "TALOS-KEY": api_key,
    "TALOS-SIGN": signature,
    "TALOS-TS": utc_datetime,
}

# ====== Make the Request ======
response = requests.get(url=endpoint, headers=headers)

# ====== Check Response ======
if response.status_code == 200:
    resp_json = response.json()
    print(json.dumps(resp_json.get("data", {}), indent=2))
else:
    print(f"Failed to fetch balances. Status Code: {response.status_code}")
    print(response.text)
