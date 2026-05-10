def make_receipt_payload(
    *,
    receipt_total: int = 500,
    date: int = 20260428,
    item: str = "milk",
) -> dict:
    return {
        "receipt_total": receipt_total,
        "items": [
            {
                "item": item,
                "num": 1,
                "amount": receipt_total,
                "total": receipt_total,
                "date": date,
                "ingredients": 1,
            }
        ],
    }


def create_receipt(client, **kwargs) -> dict:
    response = client.post("/receipts", json=make_receipt_payload(**kwargs))
    assert response.status_code == 201
    return response.json()


def test_create_receipt(client):
    response = client.post("/receipts", json=make_receipt_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["receipt_total"] == 500
    assert len(body["items"]) == 1
    assert body["items"][0]["date"] == 20260428


def test_create_receipt_rejects_receipt_total_mismatch(client):
    payload = make_receipt_payload(receipt_total=500)
    payload["receipt_total"] = 999

    response = client.post("/receipts", json=payload)

    assert response.status_code == 400


def test_create_receipt_rejects_item_total_mismatch(client):
    payload = make_receipt_payload(receipt_total=200)
    payload["items"][0]["num"] = 2

    response = client.post("/receipts", json=payload)

    assert response.status_code == 400


def test_create_receipt_rejects_empty_items(client):
    payload = make_receipt_payload()
    payload["items"] = []

    response = client.post("/receipts", json=payload)

    assert response.status_code == 422


def test_create_receipt_rejects_invalid_date(client):
    payload = make_receipt_payload(date=20260230)

    response = client.post("/receipts", json=payload)

    assert response.status_code == 422


def test_get_receipt(client):
    created = create_receipt(client, receipt_total=700, item="bread")

    response = client.get(f"/receipts/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_receipt_returns_404_for_missing_id(client):
    response = client.get("/receipts/999")

    assert response.status_code == 404


def test_list_receipts(client):
    first = create_receipt(client, receipt_total=100, item="milk")
    second = create_receipt(client, receipt_total=200, item="bread")

    response = client.get("/receipts")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": first["id"],
            "receipt_total": 100,
            "item_count": 1,
            "date_min": 20260428,
            "date_max": 20260428,
        },
        {
            "id": second["id"],
            "receipt_total": 200,
            "item_count": 1,
            "date_min": 20260428,
            "date_max": 20260428,
        },
    ]


def test_list_receipts_uses_skip_and_limit(client):
    create_receipt(client, receipt_total=100, item="milk")
    second = create_receipt(client, receipt_total=200, item="bread")
    create_receipt(client, receipt_total=300, item="eggs")

    response = client.get("/receipts?skip=1&limit=1")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == second["id"]


def test_list_receipts_uses_date_filter(client):
    create_receipt(client, receipt_total=100, date=20260401, item="milk")
    matched = create_receipt(client, receipt_total=200, date=20260415, item="bread")
    create_receipt(client, receipt_total=300, date=20260501, item="eggs")

    response = client.get("/receipts?date_from=20260410&date_to=20260430")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == matched["id"]
    assert body[0]["date_min"] == 20260415
    assert body[0]["date_max"] == 20260415


def test_delete_receipt(client):
    created = create_receipt(client)

    response = client.delete(f"/receipts/{created['id']}")

    assert response.status_code == 200
    assert response.json() == {"deleted": True, "id": created["id"]}

    get_response = client.get(f"/receipts/{created['id']}")
    assert get_response.status_code == 404


def test_delete_receipt_returns_404_for_missing_id(client):
    response = client.delete("/receipts/999")

    assert response.status_code == 404
