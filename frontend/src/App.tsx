import React, { useState, useEffect, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Send, Search, Info, Layout, MessageSquare, Database } from 'lucide-react';
import './App.css';

interface Node {
  id: string;
  label: string;
  type: string;
  metadata?: any;
}

interface Edge {
  source: string;
  target: string;
  label: string;
}

interface Message {
  text: string;
  sender: 'user' | 'bot';
  data?: any;
  sql?: string;
}

function App() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [messages, setMessages] = useState<Message[]>([
    { text: "Welcome to Dodge AI. How can I help you trace your Order-to-Cash flows today?", sender: 'bot' }
  ]);
  const [input, setInput] = useState("");
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch('http://localhost:8000/graph')
      .then(res => res.json())
      .then(data => {
        setGraphData({
          nodes: data.nodes,
          links: data.edges.map((e: any) => ({ source: e.source, target: e.target, label: e.label }))
        });
      });
  }, []);

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMsg = input;
    setMessages(prev => [...prev, { text: userMsg, sender: 'user' }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMsg })
      });
      const data = await res.json();
      setMessages(prev => [...prev, { text: data.answer, sender: 'bot', data: data.data, sql: data.sql }]);
    } catch (err) {
      setMessages(prev => [...prev, { text: "Sorry, I'm having trouble connecting to the backend.", sender: 'bot' }]);
    } finally {
      setLoading(false);
    }
  };

  const nodeColor = (node: any) => {
    switch (node.type) {
      case 'SalesOrder': return '#00d2ff';
      case 'Customer': return '#9d50bb';
      case 'Delivery': return '#ff9a9e';
      case 'Billing': return '#f6d365';
      default: return '#ffffff';
    }
  };

  return (
    <div className="app-container">
      <header className="glass-header">
        <div className="logo">
          <Database size={24} className="icon-pulse" />
          <span>DODGE<span className="accent">AI</span></span>
        </div>
        <div className="header-actions">
          <div className="status-badge">
            <span className="dot"></span> Connected
          </div>
        </div>
      </header>

      <main>
        <div className="graph-pane">
          <ForceGraph2D
            graphData={graphData}
            nodeAutoColorBy="type"
            nodeLabel={(node: any) => `${node.type}: ${node.label}`}
            linkColor={() => 'rgba(255, 255, 255, 0.2)'}
            linkDirectionalArrowLength={3.5}
            linkDirectionalArrowRelPos={1}
            onNodeClick={(node: any) => setSelectedNode(node)}
            backgroundColor="#0a0e14"
            nodeCanvasObject={(node: any, ctx, globalScale) => {
              const label = node.label;
              const fontSize = 12 / globalScale;
              ctx.font = `${fontSize}px Inter, sans-serif`;
              const textWidth = ctx.measureText(label).width;
              const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2);

              ctx.fillStyle = nodeColor(node);
              ctx.beginPath();
              ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI, false);
              ctx.fill();

              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';
              ctx.fillStyle = 'white';
              ctx.fillText(label, node.x, node.y + 10);
            }}
          />
          {selectedNode && (
            <div className="node-info glass">
              <div className="info-header">
                <h3>Node Metadata</h3>
                <button onClick={() => setSelectedNode(null)}>✕</button>
              </div>
              <div className="info-body">
                <p><strong>Type:</strong> {selectedNode.type}</p>
                <p><strong>ID:</strong> {selectedNode.id}</p>
                {selectedNode.metadata && Object.entries(selectedNode.metadata).map(([k, v]: any) => (
                  <p key={k}><strong>{k}:</strong> {String(v)}</p>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="chat-pane glass">
          <div className="chat-header">
            <MessageSquare size={20} />
            <h2>Graph Intelligence</h2>
          </div>
          <div className="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`message ${m.sender}`}>
                <div className="bubble">
                  {m.text}
                  {m.sql && (
                    <div className="sql-box">
                      <code>{m.sql}</code>
                    </div>
                  )}
                  {m.data && (
                    <div className="data-table">
                      <table>
                        <thead>
                          <tr>{Object.keys(m.data[0] || {}).map(k => <th key={k}>{k}</th>)}</tr>
                        </thead>
                        <tbody>
                          {m.data.slice(0, 5).map((row: any, j: number) => (
                            <tr key={j}>{Object.values(row).map((v: any, k) => <td key={k}>{String(v)}</td>)}</tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && <div className="message bot"><div className="bubble typing">...</div></div>}
          </div>
          <div className="chat-input-area">
            <input 
              type="text" 
              placeholder="Ask anything about the graph..." 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            />
            <button onClick={handleSend} disabled={loading}>
              <Send size={18} />
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
