from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import get_current_user
from backend.core.stripe_client import stripe_client
from backend.db.models import User
from backend.db.session import get_db

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/subscription")
async def get_subscription_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get user's subscription information."""
    return {
        "user_id": str(current_user.id),
        "tier": current_user.tier.value,
        "credits_remaining": current_user.credits_remaining,
        "stripe_customer_id": current_user.stripe_customer_id,
        "stripe_subscription_id": current_user.stripe_subscription_id,
        "subscription_status": current_user.subscription_status,
        "created_at": current_user.created_at.isoformat(),
    }


@router.post("/checkout")
async def create_checkout_session(
    plan: str,  # pro or agency
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create Stripe checkout session."""
    if plan not in ["pro", "agency"]:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    try:
        from backend.core.config import settings
        
        price_id_map = {
            "pro": settings.stripe_pro_price_id,
            "agency": settings.stripe_agency_price_id,
        }
        
        price_id = price_id_map[plan]
        if not price_id:
            raise HTTPException(status_code=500, detail="Stripe price not configured")
        
        # Create or get Stripe customer
        customer_id = current_user.stripe_customer_id
        if not customer_id:
            customer = stripe_client.create_customer(
                email=current_user.email,
                metadata={"user_id": str(current_user.id)},
            )
            customer_id = customer.id
            current_user.stripe_customer_id = customer_id
            await db.commit()
        
        # Create checkout session
        session = stripe_client.create_checkout_session(
            customer_id=customer_id,
            price_id=price_id,
            success_url=f"{settings.frontend_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.frontend_url}/billing/cancel",
        )
        
        return {
            "checkout_session_id": session.id,
            "checkout_url": session.url,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")


@router.get("/portal")
async def create_billing_portal_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create Stripe billing portal session."""
    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer found")
    
    try:
        from backend.core.config import settings
        
        session = stripe_client.create_billing_portal_session(
            customer_id=current_user.stripe_customer_id,
            return_url=f"{settings.frontend_url}/account/billing",
        )
        
        return {
            "billing_portal_url": session.url,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")


@router.post("/webhook")
async def handle_stripe_webhook(
    request_body: bytes,
    signature: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle Stripe webhook events."""
    try:
        event = stripe_client.verify_webhook(request_body, signature)
        
        # Queue webhook event for processing
        from backend.workers.celery_app import celery_app
        celery_app.send_task(
            "backend.workers.tasks.process_stripe_webhook",
            args=[event.type, event.id],
        )
        
        return {"received": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")


@router.get("/invoices")
async def list_invoices(
    current_user: User = Depends(get_current_user),
) -> dict:
    """List invoices for the user's Stripe account."""
    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer found")
    
    try:
        invoices = stripe_client.list_customer_invoices(current_user.stripe_customer_id)
        
        return {
            "invoices": [
                {
                    "id": invoice.id,
                    "number": invoice.number,
                    "status": invoice.status,
                    "amount_paid": invoice.amount_paid,
                    "amount_due": invoice.amount_due,
                    "currency": invoice.currency,
                    "created": invoice.created,
                    "paid": invoice.paid,
                    "invoice_pdf": invoice.invoice_pdf,
                }
                for invoice in invoices
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")
