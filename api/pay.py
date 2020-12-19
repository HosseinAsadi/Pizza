import json

import requests
import base64

from django.utils.crypto import get_random_string

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


def pay_level1(info):
    merchant_ref = get_random_string(32)
    body = {
        "transaction": {
            "currency": "GBP",
            "amount": info['amount'],
            "description": "",
            "commerceType": "ECOM",
            "merchantRef": merchant_ref,
            "channel": "MOBILE"
        },
        "paymentMethod": {
            "card": {
                "pan": info['pan'],
                "cv2": info['cv2'],
                "expiryDate": info['expiryDate'],
                "cardType": info['cardType'],
                "cardHolderName": info['cardHolderName'],
                "defaultCard": "false"
            },
            "billingAddress": {
                "line1": info['line1'],
                "city": info['city'],
                "postcode": info['postcode'],
                "countryCode": info['countryCode']
            }
        },
        "customer": {
            "registered": False
        }
    }

    url = 'https://api.pay360.com/acceptor/rest/transactions/8000738/payment'
    auth = 'MP5WS5KVRVAEFLXEUPU7WBW6FA:Nq+5LnRY0IVSTSdtdj7GdQ=='
    auth = base64.b64encode(auth.encode('utf-8'))
    auth = str(auth, 'utf-8')
    auth = "Basic {}".format(auth)
    r = requests.post(url, data=json.dumps(body), headers={"Authorization": auth, 'Content-Type': 'application/json'})

    res_json = r.json()
    if r.status_code == 201:
        if res_json['outcome']['status'] == 'SUCCESS':
            return {
                'url': res_json['clientRedirect']['url'],
                'pareq': res_json['clientRedirect']['pareq'],
                'transaction': res_json['transaction']
            }
        else:
            return res_json['outcome']['status']['reasonMessage']
    else:
        return res_json['outcome']['status']['reasonMessage']


def pay_level2(request):
    body = {
        "threeDSecureResponse": {"pares": request.POST.get('PaRes')}
    }
    url = 'https://api.pay360.com/acceptor/rest/transactions/8000738/'+str(request.POST.get('MD'))+'/resume'
    auth = 'MP5WS5KVRVAEFLXEUPU7WBW6FA:Nq+5LnRY0IVSTSdtdj7GdQ=='
    auth = base64.b64encode(auth.encode('utf-8'))
    auth = str(auth, 'utf-8')
    auth = "Basic {}".format(auth)
    r = requests.post(url, data=json.dumps(body), headers={"Authorization": auth, 'Content-Type': 'application/json'})

    res_json = r.json()
    if r.status_code == 200:
        return res_json
    else:
        return res_json['outcome']['status']['reasonMessage']
