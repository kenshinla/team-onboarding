from fastapi import FastAPI, HTTPException

app = FastAPI(title="HOL Day2 Business API")

CUSTOMERS = {
    "C001": {"customer_id": "C001", "name": "김민수", "product": "인터넷 500M"},
    "C002": {"customer_id": "C002", "name": "이서연", "product": "인터넷 1G"},
}
BILLING = {
    "C001": {"customer_id": "C001", "previous": 33000, "current": 39000},
    "C002": {"customer_id": "C002", "previous": 45000, "current": 45000},
}
INCIDENTS = {
    "서울": {"region": "서울", "status": "정상", "message": "현재 등록된 장애가 없습니다."},
    "부산": {"region": "부산", "status": "점검", "message": "일부 지역 점검 중입니다."},
}

@app.get("/customers/{customer_id}")
def get_customer(customer_id: str) -> dict:
    customer = CUSTOMERS.get(customer_id.upper())
    if customer is None:
        raise HTTPException(status_code=404, detail="고객을 찾을 수 없습니다.")
    return customer

@app.get("/billing/{customer_id}")
def get_billing(customer_id: str) -> dict:
    billing = BILLING.get(customer_id.upper())
    if billing is None:
        raise HTTPException(status_code=404, detail="요금 정보를 찾을 수 없습니다.")
    return billing


@app.get("/incidents/{region}")
def get_incident(region: str) -> dict:
    incident = INCIDENTS.get(region)
    if incident is None:
        raise HTTPException(status_code=404, detail="지역 정보를 찾을 수 없습니다.")
    return incident


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8555)
    