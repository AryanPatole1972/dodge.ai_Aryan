# Dodge AI - Context Graph System

Dodge AI is an LLM-powered context graph system that unifies fragmented SAP Order-to-Cash (O2C) data into a single interactive intelligence platform.

## Architecture Decisions

### 1. Data Layer: SQLite & JSONL
- **Storage**: Used SQLite for the primary data store. Why? Because the dataset is inherently relational (Orders, Items, Deliveries), and LLMs are exceptionally good at generating SQL.
- **Ingestion**: A custom Python script (`ingest.py`) processes raw SAP JSONL files, stringifies nested structures, and normalizes types for efficient querying.

### 2. Graph Modeling
- **Nodes**: Sales Orders, Customers, Deliveries, Billing Documents, and Journal Entries.
- **Edges**: Modeled based on the O2C flow:
  - `Customer` --[Ordered]--> `SalesOrder`
  - `SalesOrder` --[Delivered]--> `OutboundDelivery`
  - `SalesOrder` --[Billed]--> `BillingDocument`
  - `BillingDocument` --[Recorded]--> `JournalEntry`
- **Engine**: The graph is constructed dynamically in the backend and visualized using `react-force-graph-2d`.

### 3. LLM Strategy: Natural Language to SQL
- **Flow**: User → Natural Language → LLM → SQL → SQLite → Results → Natural Language Response.
- **Grounding**: The system explicitly returns the SQL executed and the raw data rows, ensuring "hallucination-free" answers.
- **Prompting**: The system prompt includes the exact database schema and relationship mapping to ensure accurate JOINs across fragmented O2C tables.

### 4. Guardrails
- **Domain Restriction**: The LLM is instructed to reject queries outside the O2C domain with a standardized message.
- **Data Privacy**: No authentication is implemented as per requirements, but the system restricts operations to `SELECT` only.

## Setup Instructions

### Backend
1. Install dependencies: `pip install fastapi uvicorn sqlite3`
2. Run ingestion: `python ingest.py`
3. Start backend: `python backend/main.py`

### Frontend
1. Install dependencies: `npm install`
2. Start dev server: `npm run dev`

## Bonus Features Implemented
- **NL to SQL Translation**: Dynamic query generation.
- **Metadata Inspection**: Click any node in the graph to see its full SAP metadata.
- **Visual Grounding**: Relationship-based graph exploration.
