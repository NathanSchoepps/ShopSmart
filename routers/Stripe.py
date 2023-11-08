from fastapi import APIRouter, Header, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
import stripe
from firebase_admin import auth
from database.firebase import db
from routers.Auth import get_current_user

# from dotenv import dotenv_values

router = APIRouter(prefix="/stripe", tags=["Stripe"])

stripe.api_key = "sk_test_51O4jrjGwPzvmtN7SduawL5IUCTQw7CS7i7O4xs4cNvS3vtPCBcgjMdns23lASZGzfAbKruD4z64DJlvRsGWAfWX500iqiNvjqu"

YOUR_DOMAIN = "http://localhost"


@router.get("/subscribe")
async def get_checkout(user_data: dict = Depends(get_current_user)):
    # Vérifiez d'abord si l'utilisateur est déjà abonné dans la base de données
    query_result = db.child("users").child(user_data["uid"]).child("stripe").get().val()
    if query_result:
        raise HTTPException(status_code=400, detail="user already subscribed")

    # Créez une session de paiement avec Stripe
    checkout_session = stripe.checkout.Session.create(
        success_url=YOUR_DOMAIN + "/html/success.html",
        cancel_url=YOUR_DOMAIN + "/html/cancel.html",
        line_items=[
            {
                "price": "price_1O5214GwPzvmtN7SOroWjJe7",
                "quantity": 1,
            }
        ],
        mode="subscription",
        payment_method_types=["card"],
        customer_email=user_data["email"],
    )

    # Après avoir créé la session de paiement, enregistrez les informations de souscription dans la base de données
    subscription_data = {
        "subscription_id": checkout_session["subscription"],
        "status": "active",  # Vous pouvez initialiser l'état de la souscription selon vos besoins
    }
    db.child("users").child(user_data["uid"]).child("stripe").set(subscription_data)

    return checkout_session["url"]


@router.post("/webhook")
async def retreive_webhook(request: Request, STRIPE_SIGNATURE: str = Header()):
    event = None
    payload = await request.body()
    sig_header = STRIPE_SIGNATURE

    # constructing webhook event
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            "whsec_56ca131466c9589d65e8341d35fae97b6b7eb4e58ef10911c7bf074d675b19a1",
        )
    except ValueError as e:
        print("Invalid payload in POST /stripe/webhook response-body")
        raise e
    except stripe.error.SignatureVerificationError as e:
        print("Invalid signature in POST /stripe/webhook response-header")
        raise e
    # event handler
    if event["type"] == "checkout.session.completed":
        print("Checkout session completed")
    elif event["type"] == "invoice.paid":
        print("Invoice paid")
        email = event["data"]["object"]["customer_email"]
        firebase_user = auth.get_user_by_email(email)
        customer_id = event["data"]["object"]["customer"]
        subscription_id = event["data"]["object"]["subscription"]
        db.child("users").child(firebase_user.uid).child("stripe").set(
            data={"subscription_id": subscription_id, "customer_id": customer_id}
        )
    elif event["type"] == "invoice.payment_failed":
        print("Invoice payment failed")
    else:
        print("Unhandled event type {}".format(event["type"]))


@router.get("/usage")
async def stripe_usage(userData: int = Depends(get_current_user)):
    fireBase_user = auth.get_user(userData["uid"])
    stripe_data = db.child("users").child(fireBase_user.uid).child("stripe").get().val()
    cust_id = stripe_data["cust_id"]
    return stripe.Invoice.upcoming(customer=cust_id)
