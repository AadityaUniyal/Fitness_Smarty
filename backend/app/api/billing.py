from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import JSONResponse
import os
import stripe
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from datetime import datetime

router = APIRouter(prefix="/api/billing", tags=["billing"]) 

# Initialize Stripe
STRIPE_SECRET = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
if STRIPE_SECRET:
    stripe.api_key = STRIPE_SECRET
else:
    # Running without Stripe key will allow local testing flow but block real checkout
    stripe.api_key = None


@router.post("/create-checkout-session")
def create_checkout_session(payload: dict, db: Session = Depends(get_db)):
    """Create a Stripe Checkout Session for a subscription plan.
    Expects payload: {"plan_id": <int>, "success_url": "<url>", "cancel_url": "<url>"}
    """
    plan_id = payload.get("plan_id")
    success_url = payload.get("success_url", os.getenv("FRONTEND_URL", "http://localhost:5173") + "/billing/success")
    cancel_url = payload.get("cancel_url", os.getenv("FRONTEND_URL", "http://localhost:5173") + "/billing/cancel")

    if not STRIPE_SECRET:
        raise HTTPException(status_code=400, detail="Stripe secret key not configured on server")

    plan = db.query(models.SubscriptionPlan).filter_by(id=plan_id).first()
    if not plan or not plan.stripe_price_id:
        raise HTTPException(status_code=404, detail="Subscription plan not found or not configured with Stripe Price ID")

    try:
        session = stripe.checkout.Session.create(
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            mode="subscription",
            line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
        )
        return {"url": session.url, "id": session.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not STRIPE_WEBHOOK_SECRET:
        # If webhook secret not configured, accept but log warning
        try:
            event = stripe.Event.construct_from(request.json(), stripe.api_key)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid webhook payload: {e}")
    else:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Webhook signature verification failed: {e}")

    # Handle relevant events
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # subscription id is available when mode=subscription
        stripe_subscription_id = session.get('subscription')
        client_reference_id = session.get('client_reference_id')
        customer_id = session.get('customer')

        # Try to link to local user via metadata or client_reference_id if set
        user = None
        if client_reference_id:
            user = db.query(models.EnhancedUser).filter_by(id=client_reference_id).first()

        # If subscription id present, fetch subscription details
        if stripe_subscription_id:
            try:
                sub = stripe.Subscription.retrieve(stripe_subscription_id)
                # Create or update user subscription
                if user:
                    us = db.query(models.UserSubscription).filter_by(user_id=user.id).first()
                    if not us:
                        us = models.UserSubscription(user_id=user.id, plan_id=None, stripe_subscription_id=stripe_subscription_id)
                        db.add(us)
                    us.stripe_subscription_id = stripe_subscription_id
                    us.status = sub.status
                    us.current_period_start = datetime.fromtimestamp(sub.current_period_start) if sub.current_period_start else None
                    us.current_period_end = datetime.fromtimestamp(sub.current_period_end) if sub.current_period_end else None
                    db.commit()
            except Exception:
                pass

    elif event['type'].startswith('invoice.') or event['type'].startswith('customer.subscription.'):
        # Handle invoices and subscription lifecycle events (paid, failed, updated, cancelled)
        obj = event['data']['object']
        # Minimal handling: record invoice/payments
        try:
            stripe_invoice_id = obj.get('id')
            amount_due = obj.get('amount_due') or obj.get('amount') or obj.get('total')
            customer = obj.get('customer')
            # No direct mapping to user - skip unless metadata present
            db.add(models.Invoice(stripe_invoice_id=stripe_invoice_id, amount_due_cents=amount_due or 0, paid=(obj.get('paid') is True)))
            db.commit()
        except Exception:
            db.rollback()

    return JSONResponse(status_code=200, content={"received": True})
