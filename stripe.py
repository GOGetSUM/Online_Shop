# Set your secret key. Remember to switch to your live secret key in production.
# See your keys here: https://dashboard.stripe.com/apikeys
import stripe
stripe.api_key = "sk_test_4eC39HqLyjWDarjtT1zdp7dc"

stripe.PaymentIntent.create(
  amount=1099,
  currency="eur",
  automatic_payment_methods={"enabled": True},
)


from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/secret')
def secret():
  intent = # ... Create or retrieve the PaymentIntent
  return jsonify(client_secret=intent.client_secret)