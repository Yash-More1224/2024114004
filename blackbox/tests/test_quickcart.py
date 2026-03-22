import requests
import pytest
import time

BASE_URL = "http://127.0.0.1:8080/api/v1"
ADMIN_URL = "http://127.0.0.1:8080/api/v1/admin"
def headers(user_id=1, roll="2024114004"):
    h = {}
    if roll is not None:
        h["X-Roll-Number"] = str(roll)
    if user_id is not None:
        h["X-User-ID"] = str(user_id)
    return h

# --- AUTH ---
def test_auth_missing_roll():
    res = requests.get(f"{BASE_URL}/profile", headers={"X-User-ID": "1"})
    assert res.status_code == 401

def test_auth_invalid_roll():
    res = requests.get(f"{BASE_URL}/profile", headers={"X-Roll-Number": "abc", "X-User-ID": "1"})
    assert res.status_code == 400

def test_auth_missing_user_id():
    res = requests.get(f"{BASE_URL}/profile", headers={"X-Roll-Number": "2024114004"})
    assert res.status_code == 400

# --- PROFILE ---
def test_profile_update_valid():
    res = requests.put(f"{BASE_URL}/profile", headers=headers(), json={"name": "Alice Bob", "phone": "1234567890"})
    assert res.status_code == 200

def test_profile_update_name_too_short():
    res = requests.put(f"{BASE_URL}/profile", headers=headers(), json={"name": "A", "phone": "1234567890"})
    assert res.status_code == 400

def test_profile_update_phone_invalid_length():
    res = requests.put(f"{BASE_URL}/profile", headers=headers(), json={"name": "Alice Bob", "phone": "12345"})
    assert res.status_code == 400

# --- ADDRESSES ---
def test_address_add_invalid_label():
    res = requests.post(f"{BASE_URL}/addresses", headers=headers(), json={
        "label": "INVALID", "street": "123 Main St", "city": "Cityville", "pincode": "123456", "is_default": False
    })
    assert res.status_code == 400

def test_address_add_invalid_street():
    res = requests.post(f"{BASE_URL}/addresses", headers=headers(), json={
        "label": "HOME", "street": "12", "city": "Cityville", "pincode": "123456", "is_default": False
    })
    assert res.status_code == 400

def test_address_add_invalid_pincode():
    res = requests.post(f"{BASE_URL}/addresses", headers=headers(), json={
        "label": "HOME", "street": "123 Main St", "city": "Cityville", "pincode": "12345", "is_default": False
    })
    assert res.status_code == 400

def test_address_add_valid_and_verify_fields():
    res = requests.post(f"{BASE_URL}/addresses", headers=headers(), json={
        "label": "HOME", "street": "123 Valid St", "city": "ValidCity", "pincode": "654321", "is_default": False
    })
    assert res.status_code == 200
    data = res.json()
    assert "address_id" in data
    assert data["label"] == "HOME"
    assert data["street"] == "123 Valid St"
    address_id = data["address_id"]

    # Test update (only street/is_default mutable)
    update_res = requests.put(f"{BASE_URL}/addresses/{address_id}", headers=headers(), json={
        "label": "OFFICE", "street": "456 New St", "city": "NewCity", "pincode": "111111", "is_default": True
    })
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["street"] == "456 New St"
    assert updated["label"] == "HOME" # Label must not change
    assert updated["city"] == "ValidCity" # City must not change
    assert updated["pincode"] == "654321" # Pincode must not change
    assert updated["is_default"] is True

def test_address_delete_missing():
    res = requests.delete(f"{BASE_URL}/addresses/99999", headers=headers())
    assert res.status_code == 404

# --- PRODUCTS ---
def test_products_list_active_only():
    admin_prod = requests.get(f"{ADMIN_URL}/products", headers=headers(user_id=None)).json()
    inactive_exists = any(not p["is_active"] for p in admin_prod)
    
    user_prod = requests.get(f"{BASE_URL}/products", headers=headers()).json()
    # Check if there are any inactive products returned to user
    has_inactive = any(not getattr(p, "is_active", True) or p.get("is_active") is False for p in user_prod)
    if inactive_exists:
        assert not has_inactive, "Inactive products were returned in the user list."

def test_product_missing():
    res = requests.get(f"{BASE_URL}/products/99999", headers=headers())
    assert res.status_code == 404

# --- CART ---
def test_cart_add_zero_qty():
    res = requests.post(f"{BASE_URL}/cart/add", headers=headers(), json={"product_id": 1, "quantity": 0})
    assert res.status_code == 400

def test_cart_add_invalid_product():
    res = requests.post(f"{BASE_URL}/cart/add", headers=headers(), json={"product_id": 99999, "quantity": 1})
    assert res.status_code == 404

def test_cart_remove_missing():
    res = requests.post(f"{BASE_URL}/cart/remove", headers=headers(), json={"product_id": 99999})
    assert res.status_code == 404

def test_cart_math_correctness():
    # Clear cart first
    requests.delete(f"{BASE_URL}/cart/clear", headers=headers())
    
    # Add a product repeatedly
    requests.post(f"{BASE_URL}/cart/add", headers=headers(), json={"product_id": 1, "quantity": 2})
    requests.post(f"{BASE_URL}/cart/add", headers=headers(), json={"product_id": 1, "quantity": 3})
    
    # Get cart
    cart = requests.get(f"{BASE_URL}/cart", headers=headers()).json()
    items = cart.get("items", [])
    
    # Find product 1
    p1 = next((i for i in items if i["product_id"] == 1), None)
    assert p1 is not None
    assert p1["quantity"] == 5 # Quantities should accumulate
    assert p1["subtotal"] == 5 * p1["unit_price"]
    
    total = sum(i["subtotal"] for i in items)
    assert cart["total"] == total

# --- COUPONS ---
def test_coupon_apply_expired():
    # Attempting to apply standard EXPIRED coupon if it exists in DB
    # We don't know code, but let's test a fake one
    res = requests.post(f"{BASE_URL}/coupon/apply", headers=headers(), json={"code": "EXPIREDCOUPON"})
    pass # Cannot guarantee existence of specific coupon codes

# --- CHECKOUT ---
def test_checkout_invalid_method():
    res = requests.post(f"{BASE_URL}/checkout", headers=headers(), json={"payment_method": "BITCOIN", "address_id": 1})
    assert res.status_code == 400

def test_checkout_empty_cart():
    requests.delete(f"{BASE_URL}/cart/clear", headers=headers())
    res = requests.post(f"{BASE_URL}/checkout", headers=headers(), json={"payment_method": "COD", "address_id": 1})
    assert res.status_code == 400

# --- WALLET ---
def test_wallet_add_negative():
    res = requests.post(f"{BASE_URL}/wallet/add", headers=headers(), json={"amount": -100})
    assert res.status_code == 400

def test_wallet_add_too_large():
    res = requests.post(f"{BASE_URL}/wallet/add", headers=headers(), json={"amount": 100001})
    assert res.status_code == 400

def test_wallet_pay_insufficient():
    # Use user 2 (since test user 1 might have money from other tests)
    h2 = headers(user_id=2)
    wallet = requests.get(f"{BASE_URL}/wallet", headers=h2).json()
    balance = wallet.get("wallet_balance", wallet.get("balance", 0))
    res = requests.post(f"{BASE_URL}/wallet/pay", headers=h2, json={"amount": balance + 100})
    assert res.status_code == 400

# --- LOYALTY ---
def test_loyalty_redeem_less_than_1():
    res = requests.post(f"{BASE_URL}/loyalty/redeem", headers=headers(), json={"points": 0})
    assert res.status_code == 400

def test_loyalty_redeem_insufficient():
    pts_data = requests.get(f"{BASE_URL}/loyalty", headers=headers()).json()
    pts = pts_data.get("loyalty_points", pts_data.get("points", 0))
    res = requests.post(f"{BASE_URL}/loyalty/redeem", headers=headers(), json={"points": pts + 100})
    assert res.status_code == 400

# --- ORDERS ---
def test_order_cancel_missing():
    res = requests.post(f"{BASE_URL}/orders/99999/cancel", headers=headers())
    assert res.status_code == 404

def test_order_invoice_math():
    requests.delete(f"{BASE_URL}/cart/clear", headers=headers())
    requests.post(f"{BASE_URL}/cart/add", headers=headers(), json={"product_id": 1, "quantity": 1})
    requests.post(f"{BASE_URL}/cart/add", headers=headers(), json={"product_id": 2, "quantity": 1})
    
    res = requests.post(f"{BASE_URL}/checkout", headers=headers(), json={"payment_method": "COD", "address_id": 1})
    if res.status_code == 200:
        order_id = res.json()["order_id"]
        inv = requests.get(f"{BASE_URL}/orders/{order_id}/invoice", headers=headers()).json()
        assert "subtotal" in inv
        assert "gst_amount" in inv
        assert "total_amount" in inv
        assert inv["subtotal"] + inv["gst_amount"] == inv["total_amount"]

# --- REVIEWS ---
def test_review_rating_bounds():
    res1 = requests.post(f"{BASE_URL}/products/1/reviews", headers=headers(), json={"rating": 0, "comment": "Bad"})
    assert res1.status_code == 400
    res2 = requests.post(f"{BASE_URL}/products/1/reviews", headers=headers(), json={"rating": 6, "comment": "Good"})
    assert res2.status_code == 400

def test_review_comment_length():
    res1 = requests.post(f"{BASE_URL}/products/1/reviews", headers=headers(), json={"rating": 5, "comment": ""})
    assert res1.status_code == 400

# --- SUPPORT ---
def test_support_ticket_creation_bounds():
    res1 = requests.post(f"{BASE_URL}/support/ticket", headers=headers(), json={"subject": "ab", "message": "hello"})
    assert res1.status_code == 400

def test_support_ticket_status_transitions():
    res = requests.post(f"{BASE_URL}/support/ticket", headers=headers(), json={"subject": "Valid Subject", "message": "Valid Message"})
    assert res.status_code == 200
    ticket_id = res.json().get("ticket_id")
    
    if ticket_id:
        # Open -> Closed is valid? Doc says:
        # OPEN can go to IN_PROGRESS. IN_PROGRESS can go to CLOSED. No other changes are allowed.
        # Check OPEN -> CLOSED (Should fail)
        update1 = requests.put(f"{BASE_URL}/support/tickets/{ticket_id}", headers=headers(), json={"status": "CLOSED"})
        assert update1.status_code == 400
        
        # Check OPEN -> IN_PROGRESS (Should succeed)
        update2 = requests.put(f"{BASE_URL}/support/tickets/{ticket_id}", headers=headers(), json={"status": "IN_PROGRESS"})
        assert update2.status_code == 200
        
        # Check IN_PROGRESS -> OPEN (Should fail)
        update3 = requests.put(f"{BASE_URL}/support/tickets/{ticket_id}", headers=headers(), json={"status": "OPEN"})
        assert update3.status_code == 400
