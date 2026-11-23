import base64
import json
import os
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

def provider(endpoint,fields):
    account=os.environ['TWILIO_ACCOUNT_SID']
    service=os.environ['TWILIO_VERIFY_SERVICE_SID']
    if not re.fullmatch('VA[0-9a-fA-F]{32}',service):
        raise ValueError('Verify Service SID xato')
    authorization=base64.b64encode((account+':'+os.environ['TWILIO_AUTH_TOKEN']).encode()).decode()
    request=Request('https://verify.twilio.com/v2/Services/'+service+'/'+endpoint,
                    data=urlencode(fields).encode(),headers={'Authorization':'Basic '+authorization})
    with urlopen(request,timeout=25) as response:
        return json.load(response)

def verify_owner(phone,email):
    for destination,channel in [(phone,'sms'),(email,'email')]:
        provider('Verifications',{'To':destination,'Channel':channel})
        code=input(channel+' orqali kelgan kod: ').strip()
        if provider('VerificationCheck',{'To':destination,'Code':code}).get('status')!='approved':
            raise ValueError('Kod tasdiqlanmadi')
