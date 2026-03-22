from datetime import datetime

import pytest
import requests


BASE_URL = "http://127.0.0.1:8080/api/v1"
ADMIN_URL = f"{BASE_URL}/admin"
ROLL_NUMBER = "2024114004"


def headers(user_id=1, roll=ROLL_NUMBER):
    request_headers = {}
    if roll is not None:
        request_headers["X-Roll-Number"] = str(roll)
    if user_id is not None:
        request_headers["X-User-ID"] = str(user_id)
    return request_headers


def assert_json_response(response):
    assert "application/json" in response.headers.get("content-type", "")


def parse_json(response):
    assert_json_response(response)
    return response.json()


def get_admin_products():
    response = requests.get(f"{ADMIN_URL}/products", headers=headers(user_id=None))
    assert response.status_code == 200
    data = parse_json(response)
    assert isinstance(data, list)
    return data


def get_active_products():
    response = requests.get(f"{BASE_URL}/products", headers=headers())
    assert response.status_code == 200
    data = parse_json(response)
    assert isinstance(data, list)
    return data


def get_any_address_id():
    response = requests.get(f"{BASE_URL}/addresses", headers=headers())
    assert response.status_code == 200
    addresses = parse_json(response)
    assert isinstance(addresses, list)
    assert addresses, "Expected at least one address for user 1"
    return addresses[0]["address_id"]


def add_item_to_cart(product_id, quantity):
    response = requests.post(
        f"{BASE_URL}/cart/add",
        headers=headers(),
        json={"product_id": product_id, "quantity": quantity},
    )
    return response


def place_card_order(product_id=1, quantity=1):
    requests.delete(f"{BASE_URL}/cart/clear", headers=headers())
    add_response = add_item_to_cart(product_id, quantity)
    assert add_response.status_code == 200
    address_id = get_any_address_id()
    checkout_response = requests.post(
        f"{BASE_URL}/checkout",
        headers=headers(),
        json={"payment_method": "CARD", "address_id": address_id},
    )
    assert checkout_response.status_code == 200
    checkout_data = parse_json(checkout_response)
    return checkout_data["order_id"], checkout_data


@pytest.fixture(autouse=True)
def clear_cart_before_each_test():
    requests.delete(f"{BASE_URL}/cart/clear", headers=headers())
    yield


def test_auth_missing_roll():
    response = requests.get(f"{BASE_URL}/profile", headers={"X-User-ID": "1"})
    assert response.status_code == 401


def test_auth_invalid_roll():
    response = requests.get(
        f"{BASE_URL}/profile",
        headers={"X-Roll-Number": "abc", "X-User-ID": "1"},
    )
    assert response.status_code == 400


def test_auth_missing_user_id():
    response = requests.get(f"{BASE_URL}/profile", headers={"X-Roll-Number": ROLL_NUMBER})
    assert response.status_code == 400


def test_auth_invalid_user_id_type():
    response = requests.get(
        f"{BASE_URL}/profile",
        headers={"X-Roll-Number": ROLL_NUMBER, "X-User-ID": "not_an_int"},
    )
    assert response.status_code == 400


def test_profile_get_structure():
    response = requests.get(f"{BASE_URL}/profile", headers=headers())
    assert response.status_code == 200
    data = parse_json(response)
    required = {"user_id", "name", "email", "phone", "wallet_balance", "loyalty_points"}
    assert required.issubset(data.keys())


def test_profile_update_valid_and_verify():
    payload = {"name": "Alice Bob", "phone": "1234567890"}
    update_response = requests.put(f"{BASE_URL}/profile", headers=headers(), json=payload)
    assert update_response.status_code == 200
    get_response = requests.get(f"{BASE_URL}/profile", headers=headers())
    assert get_response.status_code == 200
    profile = parse_json(get_response)
    assert profile["name"] == payload["name"]
    assert profile["phone"] == payload["phone"]


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "A", "phone": "1234567890"},
        {"name": "A" * 51, "phone": "1234567890"},
        {"name": "Alice Bob", "phone": "12345"},
        {"name": "Alice Bob", "phone": "12345abcde"},
    ],
)
def test_profile_update_invalid_inputs(payload):
    response = requests.put(f"{BASE_URL}/profile", headers=headers(), json=payload)
    assert response.status_code == 400


def test_addresses_list_structure():
    response = requests.get(f"{BASE_URL}/addresses", headers=headers())
    assert response.status_code == 200
    data = parse_json(response)
    assert isinstance(data, list)
    if data:
        required = {"address_id", "label", "street", "city", "pincode", "is_default"}
        assert required.issubset(data[0].keys())


@pytest.mark.parametrize(
    "payload",
    [
        {"street": "123 Main St", "city": "Cityville", "pincode": "123456", "is_default": False},
        {"label": "INVALID", "street": "123 Main St", "city": "Cityville", "pincode": "123456", "is_default": False},
        {"label": "HOME", "street": "12", "city": "Cityville", "pincode": "123456", "is_default": False},
        {"label": "HOME", "street": "123 Main St", "city": "C", "pincode": "123456", "is_default": False},
        {"label": "HOME", "street": "123 Main St", "city": "Cityville", "pincode": "12345", "is_default": False},
        {"label": "HOME", "street": "123 Main St", "city": "Cityville", "pincode": 123456, "is_default": False},
    ],
)
def test_address_add_invalid_inputs(payload):
    response = requests.post(f"{BASE_URL}/addresses", headers=headers(), json=payload)
    assert response.status_code == 400


def test_address_add_valid_and_verify_immutable_fields_on_update():
    create_payload = {
        "label": "OTHER",
        "street": "123 Valid Street Name",
        "city": "ValidCity",
        "pincode": "654321",
        "is_default": False,
    }
    create_response = requests.post(f"{BASE_URL}/addresses", headers=headers(), json=create_payload)
    assert create_response.status_code == 200
    created = parse_json(create_response)

    address_id = created["address_id"]
    update_payload = {
        "label": "OFFICE",
        "street": "456 Updated Street Name",
        "city": "ChangedCity",
        "pincode": "111111",
        "is_default": True,
    }
    update_response = requests.put(
        f"{BASE_URL}/addresses/{address_id}",
        headers=headers(),
        json=update_payload,
    )
    assert update_response.status_code == 200
    updated = parse_json(update_response)
    assert updated["street"] == "456 Updated Street Name"
    assert updated["label"] == "OTHER"
    assert updated["city"] == "ValidCity"
    assert updated["pincode"] == "654321"


def test_address_only_one_default_after_setting_new_default():
    list_response = requests.get(f"{BASE_URL}/addresses", headers=headers())
    assert list_response.status_code == 200
    addresses = parse_json(list_response)
    if len(addresses) < 2:
        pytest.skip("Need at least two existing addresses to verify default switching")

    first_id = addresses[0]["address_id"]
    second_id = addresses[1]["address_id"]

    first_update = requests.put(
        f"{BASE_URL}/addresses/{first_id}",
        headers=headers(),
        json={"street": addresses[0]["street"], "is_default": True},
    )
    assert first_update.status_code == 200

    second_update = requests.put(
        f"{BASE_URL}/addresses/{second_id}",
        headers=headers(),
        json={"street": addresses[1]["street"], "is_default": True},
    )
    assert second_update.status_code == 200

    list_response = requests.get(f"{BASE_URL}/addresses", headers=headers())
    assert list_response.status_code == 200
    refreshed_addresses = parse_json(list_response)
    defaults = [address for address in refreshed_addresses if address.get("is_default") is True]
    assert len(defaults) == 1


def test_address_delete_missing_returns_404():
    response = requests.delete(f"{BASE_URL}/addresses/99999", headers=headers())
    assert response.status_code == 404


def test_products_list_active_only():
    admin_products = get_admin_products()
    user_products = get_active_products()
    admin_inactive_ids = {product["product_id"] for product in admin_products if not product.get("is_active", True)}
    user_ids = {product["product_id"] for product in user_products}
    assert admin_inactive_ids.isdisjoint(user_ids)
    assert all(product.get("is_active") is True for product in user_products)


def test_product_missing_returns_404():
    response = requests.get(f"{BASE_URL}/products/99999", headers=headers())
    assert response.status_code == 404


def test_product_get_single_structure():
    products = get_active_products()
    product_id = products[0]["product_id"]
    response = requests.get(f"{BASE_URL}/products/{product_id}", headers=headers())
    assert response.status_code == 200
    data = parse_json(response)
    required = {"product_id", "name", "category", "price", "stock_quantity", "is_active"}
    assert required.issubset(data.keys())


def test_products_filter_by_category():
    products = get_active_products()
    category = products[0]["category"]
    response = requests.get(f"{BASE_URL}/products", headers=headers(), params={"category": category})
    assert response.status_code == 200
    filtered = parse_json(response)
    assert filtered
    assert all(product["category"] == category for product in filtered)


def test_products_search_by_name():
    products = get_active_products()
    name_fragment = products[0]["name"].split()[0]
    response = requests.get(f"{BASE_URL}/products", headers=headers(), params={"search": name_fragment})
    assert response.status_code == 200
    filtered = parse_json(response)
    assert filtered
    assert all(name_fragment.lower() in product["name"].lower() for product in filtered)


def test_products_sort_by_price_ascending():
    response = requests.get(f"{BASE_URL}/products", headers=headers(), params={"sort": "price_asc"})
    assert response.status_code == 200
    products = parse_json(response)
    prices = [product["price"] for product in products]
    assert prices == sorted(prices)


def test_products_sort_by_price_descending():
    response = requests.get(f"{BASE_URL}/products", headers=headers(), params={"sort": "price_desc"})
    assert response.status_code == 200
    products = parse_json(response)
    prices = [product["price"] for product in products]
    assert prices == sorted(prices, reverse=True)


def test_cart_get_empty_after_clear():
    clear_response = requests.delete(f"{BASE_URL}/cart/clear", headers=headers())
    assert clear_response.status_code == 200
    cart_response = requests.get(f"{BASE_URL}/cart", headers=headers())
    assert cart_response.status_code == 200
    cart = parse_json(cart_response)
    assert cart.get("items") == []
    assert cart.get("total") == 0


@pytest.mark.parametrize("quantity", [0, -1])
def test_cart_add_non_positive_quantity_rejected(quantity):
    response = add_item_to_cart(product_id=1, quantity=quantity)
    assert response.status_code == 400


def test_cart_add_invalid_product_returns_404():
    response = add_item_to_cart(product_id=99999, quantity=1)
    assert response.status_code == 404


def test_cart_add_insufficient_stock_returns_400():
    products = get_active_products()
    product = next(product for product in products if product["stock_quantity"] > 0)
    response = add_item_to_cart(product_id=product["product_id"], quantity=product["stock_quantity"] + 1)
    assert response.status_code == 400


def test_cart_add_accumulates_quantity_and_item_math():
    product_id = 1
    assert add_item_to_cart(product_id=product_id, quantity=2).status_code == 200
    assert add_item_to_cart(product_id=product_id, quantity=3).status_code == 200
    cart_response = requests.get(f"{BASE_URL}/cart", headers=headers())
    assert cart_response.status_code == 200
    cart = parse_json(cart_response)
    item = next(entry for entry in cart["items"] if entry["product_id"] == product_id)
    assert item["quantity"] == 5
    assert item["subtotal"] == item["quantity"] * item["unit_price"]
    assert cart["total"] == sum(entry["subtotal"] for entry in cart["items"])


def test_cart_update_quantity_non_positive_rejected():
    assert add_item_to_cart(product_id=1, quantity=1).status_code == 200
    response = requests.post(
        f"{BASE_URL}/cart/update",
        headers=headers(),
        json={"product_id": 1, "quantity": 0},
    )
    assert response.status_code == 400


def test_cart_update_missing_product_returns_404():
    response = requests.post(
        f"{BASE_URL}/cart/update",
        headers=headers(),
        json={"product_id": 99999, "quantity": 1},
    )
    assert response.status_code == 404


def test_cart_remove_missing_returns_404():
    response = requests.post(f"{BASE_URL}/cart/remove", headers=headers(), json={"product_id": 99999})
    assert response.status_code == 404


def test_coupon_apply_missing_code_rejected():
    response = requests.post(f"{BASE_URL}/coupon/apply", headers=headers(), json={})
    assert response.status_code == 400


def test_coupon_apply_expired_coupon_rejected():
    coupons_response = requests.get(f"{ADMIN_URL}/coupons", headers=headers(user_id=None))
    assert coupons_response.status_code == 200
    coupons = parse_json(coupons_response)
    expired_coupon = next(
        (coupon for coupon in coupons if datetime.fromisoformat(coupon["expiry_date"].replace("Z", "+00:00")) < datetime.now().astimezone()),
        None,
    )
    if expired_coupon is None:
        pytest.skip("No expired coupon available in fixture data")
    assert add_item_to_cart(product_id=1, quantity=1).status_code == 200
    response = requests.post(
        f"{BASE_URL}/coupon/apply",
        headers=headers(),
        json={"code": expired_coupon["coupon_code"]},
    )
    assert response.status_code == 400


def test_coupon_apply_below_minimum_cart_value_rejected():
    coupons_response = requests.get(f"{ADMIN_URL}/coupons", headers=headers(user_id=None))
    assert coupons_response.status_code == 200
    coupons = parse_json(coupons_response)
    coupon = next((entry for entry in coupons if entry.get("min_cart_value", 0) >= 500), None)
    if coupon is None:
        pytest.skip("No suitable coupon found")
    assert add_item_to_cart(product_id=1, quantity=1).status_code == 200
    response = requests.post(
        f"{BASE_URL}/coupon/apply",
        headers=headers(),
        json={"code": coupon["coupon_code"]},
    )
    assert response.status_code == 400


def test_coupon_apply_and_remove_valid_coupon():
    coupons_response = requests.get(f"{ADMIN_URL}/coupons", headers=headers(user_id=None))
    assert coupons_response.status_code == 200
    coupons = parse_json(coupons_response)
    valid_coupon = next(
        (
            coupon
            for coupon in coupons
            if coupon.get("is_active") is True
            and datetime.fromisoformat(coupon["expiry_date"].replace("Z", "+00:00")) > datetime.now().astimezone()
            and coupon.get("min_cart_value", 0) <= 200
        ),
        None,
    )
    if valid_coupon is None:
        pytest.skip("No active valid coupon with low minimum cart value found")

    product = next(product for product in get_active_products() if product["price"] >= valid_coupon.get("min_cart_value", 0))
    assert add_item_to_cart(product_id=product["product_id"], quantity=1).status_code == 200

    apply_response = requests.post(
        f"{BASE_URL}/coupon/apply",
        headers=headers(),
        json={"code": valid_coupon["coupon_code"]},
    )
    assert apply_response.status_code == 200
    apply_data = parse_json(apply_response)
    assert "discount" in apply_data

    remove_response = requests.post(f"{BASE_URL}/coupon/remove", headers=headers())
    assert remove_response.status_code == 200


def test_checkout_invalid_method_returns_400():
    address_id = get_any_address_id()
    response = requests.post(
        f"{BASE_URL}/checkout",
        headers=headers(),
        json={"payment_method": "BITCOIN", "address_id": address_id},
    )
    assert response.status_code == 400


def test_checkout_empty_cart_returns_400():
    address_id = get_any_address_id()
    response = requests.post(
        f"{BASE_URL}/checkout",
        headers=headers(),
        json={"payment_method": "COD", "address_id": address_id},
    )
    assert response.status_code == 400


def test_checkout_invalid_address_returns_400():
    assert add_item_to_cart(product_id=1, quantity=1).status_code == 200
    response = requests.post(
        f"{BASE_URL}/checkout",
        headers=headers(),
        json={"payment_method": "CARD", "address_id": 99999},
    )
    assert response.status_code == 400


def test_checkout_card_success_status_fields():
    order_id, checkout_data = place_card_order(product_id=1, quantity=1)
    assert order_id is not None
    assert checkout_data["payment_status"] == "PAID"
    assert checkout_data["order_status"] == "PLACED"


def test_checkout_cod_over_limit_rejected():
    products = sorted(get_active_products(), key=lambda item: item["price"], reverse=True)
    chosen = products[0]
    quantity = max(1, int(5001 / max(chosen["price"], 1)) + 1)
    quantity = min(quantity, chosen["stock_quantity"])
    if chosen["price"] * quantity <= 5000:
        pytest.skip("Unable to create cart total above COD limit with available stock")
    assert add_item_to_cart(product_id=chosen["product_id"], quantity=quantity).status_code == 200
    address_id = get_any_address_id()
    response = requests.post(
        f"{BASE_URL}/checkout",
        headers=headers(),
        json={"payment_method": "COD", "address_id": address_id},
    )
    assert response.status_code == 400


def test_order_invoice_math_from_checkout():
    order_id, checkout_data = place_card_order(product_id=1, quantity=2)
    invoice_response = requests.get(f"{BASE_URL}/orders/{order_id}/invoice", headers=headers())
    assert invoice_response.status_code == 200
    invoice = parse_json(invoice_response)
    assert invoice["subtotal"] + invoice["gst_amount"] == invoice["total_amount"]
    assert checkout_data["total_amount"] == invoice["total_amount"]


def test_wallet_get_structure():
    response = requests.get(f"{BASE_URL}/wallet", headers=headers())
    assert response.status_code == 200
    data = parse_json(response)
    assert "wallet_balance" in data


@pytest.mark.parametrize("amount", [-100, 0, 100001])
def test_wallet_add_out_of_bounds_rejected(amount):
    response = requests.post(f"{BASE_URL}/wallet/add", headers=headers(), json={"amount": amount})
    assert response.status_code == 400


def test_wallet_pay_insufficient_balance_rejected():
    second_user_headers = headers(user_id=2)
    wallet_response = requests.get(f"{BASE_URL}/wallet", headers=second_user_headers)
    assert wallet_response.status_code == 200
    wallet = parse_json(wallet_response)
    balance = wallet.get("wallet_balance", 0)
    pay_response = requests.post(
        f"{BASE_URL}/wallet/pay",
        headers=second_user_headers,
        json={"amount": balance + 1},
    )
    assert pay_response.status_code == 400


def test_loyalty_get_structure():
    response = requests.get(f"{BASE_URL}/loyalty", headers=headers())
    assert response.status_code == 200
    data = parse_json(response)
    assert "loyalty_points" in data


def test_loyalty_redeem_zero_rejected():
    response = requests.post(f"{BASE_URL}/loyalty/redeem", headers=headers(), json={"points": 0})
    assert response.status_code == 400


def test_loyalty_redeem_insufficient_rejected():
    points_response = requests.get(f"{BASE_URL}/loyalty", headers=headers())
    assert points_response.status_code == 200
    points = parse_json(points_response).get("loyalty_points", 0)
    response = requests.post(f"{BASE_URL}/loyalty/redeem", headers=headers(), json={"points": points + 1})
    assert response.status_code == 400


def test_orders_list_structure():
    response = requests.get(f"{BASE_URL}/orders", headers=headers())
    assert response.status_code == 200
    data = parse_json(response)
    assert isinstance(data, list)
    if data:
        required = {"order_id", "total_amount", "payment_status", "order_status"}
        assert required.issubset(data[0].keys())


def test_order_cancel_missing_returns_404():
    response = requests.post(f"{BASE_URL}/orders/99999/cancel", headers=headers())
    assert response.status_code == 404


def test_order_cancel_restores_stock_quantity():
    product = next(entry for entry in get_active_products() if entry["stock_quantity"] >= 3)
    product_id = product["product_id"]
    before_admin = requests.get(f"{ADMIN_URL}/products", headers=headers(user_id=None))
    before_stock = next(item for item in parse_json(before_admin) if item["product_id"] == product_id)["stock_quantity"]

    order_id, _ = place_card_order(product_id=product_id, quantity=2)
    cancel_response = requests.post(f"{BASE_URL}/orders/{order_id}/cancel", headers=headers())
    assert cancel_response.status_code == 200

    after_admin = requests.get(f"{ADMIN_URL}/products", headers=headers(user_id=None))
    after_stock = next(item for item in parse_json(after_admin) if item["product_id"] == product_id)["stock_quantity"]
    assert after_stock == before_stock


def test_reviews_get_structure():
    product_id = get_active_products()[0]["product_id"]
    response = requests.get(f"{BASE_URL}/products/{product_id}/reviews", headers=headers())
    assert response.status_code == 200
    data = parse_json(response)
    assert "reviews" in data
    assert "average_rating" in data


@pytest.mark.parametrize("rating", [0, 6])
def test_review_rating_out_of_bounds_rejected(rating):
    response = requests.post(
        f"{BASE_URL}/products/1/reviews",
        headers=headers(),
        json={"rating": rating, "comment": "invalid rating"},
    )
    assert response.status_code == 400


@pytest.mark.parametrize("comment", ["", "x" * 201])
def test_review_comment_length_invalid(comment):
    response = requests.post(
        f"{BASE_URL}/products/1/reviews",
        headers=headers(),
        json={"rating": 5, "comment": comment},
    )
    assert response.status_code == 400


def test_support_ticket_create_and_list_structure():
    create_response = requests.post(
        f"{BASE_URL}/support/ticket",
        headers=headers(),
        json={"subject": "Valid Subject", "message": "Valid Message"},
    )
    assert create_response.status_code == 200
    created = parse_json(create_response)
    assert "ticket_id" in created
    list_response = requests.get(f"{BASE_URL}/support/tickets", headers=headers())
    assert list_response.status_code == 200
    tickets = parse_json(list_response)
    assert isinstance(tickets, list)
    assert any(ticket["ticket_id"] == created["ticket_id"] for ticket in tickets)


@pytest.mark.parametrize(
    "payload",
    [
        {"subject": "abcd", "message": "hello"},
        {"subject": "x" * 101, "message": "hello"},
        {"subject": "Valid Subject", "message": ""},
        {"subject": "Valid Subject", "message": "x" * 501},
    ],
)
def test_support_ticket_creation_validation(payload):
    response = requests.post(f"{BASE_URL}/support/ticket", headers=headers(), json=payload)
    assert response.status_code == 400


def test_support_ticket_status_transition_rules():
    create_response = requests.post(
        f"{BASE_URL}/support/ticket",
        headers=headers(),
        json={"subject": "Transition Subject", "message": "Transition Message"},
    )
    assert create_response.status_code == 200
    ticket_id = parse_json(create_response)["ticket_id"]

    open_to_closed = requests.put(
        f"{BASE_URL}/support/tickets/{ticket_id}",
        headers=headers(),
        json={"status": "CLOSED"},
    )
    assert open_to_closed.status_code == 400

    open_to_in_progress = requests.put(
        f"{BASE_URL}/support/tickets/{ticket_id}",
        headers=headers(),
        json={"status": "IN_PROGRESS"},
    )
    assert open_to_in_progress.status_code == 200

    in_progress_to_open = requests.put(
        f"{BASE_URL}/support/tickets/{ticket_id}",
        headers=headers(),
        json={"status": "OPEN"},
    )
    assert in_progress_to_open.status_code == 400

    in_progress_to_closed = requests.put(
        f"{BASE_URL}/support/tickets/{ticket_id}",
        headers=headers(),
        json={"status": "CLOSED"},
    )
    assert in_progress_to_closed.status_code == 200


def test_admin_users_list_structure():
    response = requests.get(f"{ADMIN_URL}/users", headers=headers(user_id=None))
    assert response.status_code == 200
    users = parse_json(response)
    assert isinstance(users, list)
    assert users
    required = {"user_id", "name", "wallet_balance", "loyalty_points"}
    assert required.issubset(users[0].keys())
