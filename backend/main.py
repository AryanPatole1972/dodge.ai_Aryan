from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json
import os
from pydantic import BaseModel
from typing import List, Optional
from nlp import nl_to_sql, execute_query

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(__file__), "../o2c.db")

class QueryRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    data: Optional[list] = None
    sql: Optional[str] = None

@app.get("/graph")
def get_graph(limit: int = 100):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    nodes = []
    edges = []
    
    # 1. Sales Orders
    orders = cursor.execute(f"SELECT salesOrder, soldToParty, totalNetAmount FROM sales_order_headers LIMIT {limit}").fetchall()
    for o in orders:
        nodes.append({
            "id": f"SO_{o['salesOrder']}",
            "label": f"SO {o['salesOrder']}",
            "type": "SalesOrder",
            "metadata": dict(o)
        })
        if o['soldToParty']:
            nodes.append({
                "id": f"CUST_{o['soldToParty']}",
                "label": f"Customer {o['soldToParty']}",
                "type": "Customer"
            })
            edges.append({
                "id": f"SO_CUST_{o['salesOrder']}",
                "source": f"CUST_{o['soldToParty']}",
                "target": f"SO_{o['salesOrder']}",
                "label": "Ordered By"
            })

    # 2. Deliveries
    deliveries = cursor.execute(f"SELECT deliveryDocument, referenceSdDocument FROM outbound_delivery_items LIMIT {limit}").fetchall()
    for d in deliveries:
        nodes.append({
            "id": f"DEL_{d['deliveryDocument']}",
            "label": f"Del {d['deliveryDocument']}",
            "type": "Delivery",
            "metadata": dict(d)
        })
        if d['referenceSdDocument']:
            edges.append({
                "id": f"SO_DEL_{d['deliveryDocument']}",
                "source": f"SO_{d['referenceSdDocument']}",
                "target": f"DEL_{d['deliveryDocument']}",
                "label": "Delivered"
            })

    # 3. Billing
    billing = cursor.execute(f"SELECT billingDocument, referenceSdDocument FROM billing_document_items LIMIT {limit}").fetchall()
    for b in billing:
        nodes.append({
            "id": f"BILL_{b['billingDocument']}",
            "label": f"Bill {b['billingDocument']}",
            "type": "Billing",
            "metadata": dict(b)
        })
        if b['referenceSdDocument']:
            edges.append({
                "id": f"DEL_BILL_{b['billingDocument']}",
                "source": f"DEL_{b['referenceSdDocument']}",
                "target": f"BILL_{b['billingDocument']}",
                "label": "Billed"
            })

    # Deduplicate nodes
    unique_nodes = {n['id']: n for n in nodes}.values()
    
    conn.close()
    return {"nodes": list(unique_nodes), "edges": edges}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: QueryRequest):
    sql = nl_to_sql(request.query)
    
    if sql == "OFF_TOPIC":
        return ChatResponse(answer="This system is designed to answer questions related to the provided dataset only.")
    
    if sql:
        results = execute_query(sql, DB_PATH)
        if isinstance(results, str): # Error message
            return ChatResponse(answer=f"Error executing query: {results}", sql=sql)
            
        # Ground the response in data
        if not results:
            return ChatResponse(answer="I found no data matching that query in the system.", sql=sql)
            
        # Construct natural language answer based on data
        answer = f"Found {len(results)} records matching your query."
        if "highest" in request.query.lower():
            p = results[0].get('product', results[0].get('product_id'))
            c = results[0].get('count')
            answer = f"The product with the highest billed documents is {p} with {c} documents."
        
        return ChatResponse(answer=answer, data=results, sql=sql)

    return ChatResponse(answer="I'm here to help you analyze the Order-to-Cash process. Please ask about Sales Orders, Deliveries, or Invoices.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
