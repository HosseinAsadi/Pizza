import requests
import base64

'''
    {
        "transaction": {
            "currency": "GBP",
            "amount": "0.5",
            "description": "",
            "commerceType": "MOTO",
            "channel": "MOBILE"
        },
        "paymentMethod": {
            "card": {
                "pan": "4596640141217047",
                "cv2": "052",
                "expiryDate": "0725",
                "cardType": "VISA_DEBIT",
                "nickname": "",
                "cardHolderName": "",
                "defaultCard": "false"
            },
            "billingAddress": {
                "city": "",
                "postcode": "",
                "countryCode": ""
            }
        },
        "customer": {
            "merchantRef": "mer_cust_131241413",
            "displayName": "Mr O Whatasillyname",
            "billingAddress": {
                "city": "",
                "postcode": "",
                "countryCode": ""
            }
        }
    }
'''


def pay(info):
    body = {
        "transaction": {
            "currency": "GBP",
            "amount": info['amount'],
            "description": "",
            "commerceType": "MOTO",
            "channel": "MOBILE"
        },
        "paymentMethod": {
            "card": {
                "pan": info['pan'],
                "cv2": info['cv2'],
                "expiryDate": info['expiryDate'],
                "cardType": info['cardType'],
                "nickname": info['nickname'],
                "cardHolderName": info['cardHolderName'],
                "defaultCard": "false"
            },
            "billingAddress": {
                "city": info['city'],
                "postcode": info['postcode'],
                "countryCode": info['countryCode']
            }
        },
        "customer": {
            "merchantRef": info['merchantRef'],
            "displayName": info['displayName'],
            "billingAddress": {
                "city": info['city'],
                "postcode": info['postcode'],
                "countryCode": info['countryCode']
            }
        }
    }

    url = 'https://api.pay360.com/acceptor/rest/transactions/8000738/payment'
    auth = 'MP5WS5KVRVAEFLXEUPU7WBW6FA:Nq+5LnRY0IVSTSdtdj7GdQ=='
    auth = base64.b64encode(auth.encode('utf-8'))
    auth = str(auth, 'utf-8')
    auth = "Basic {}".format(auth)
    r = requests.post(url, data=body, headers={"authorization": auth, 'Content-Type': 'application/json'})
    if r.status_code == 200:
        return r.json()
    else:
        return None
