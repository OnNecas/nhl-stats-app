import React, { useState } from 'react';
import axios from 'axios';
import './App.css'; // we'll style this next

function App() {
  const [question, setQuestion] = useState('');
  const [summary, setSummary] = useState('');
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);

  const askQuestion = async () => {
    if (!question.trim()) return;
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/ask', { question });
      setSummary(response.data.summary);
      setData(response.data.data);
    } catch (err) {
      setSummary("❌ Error: " + err.message);
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <h1 className="title">🏒 NHL Stats AI</h1>
      <div className="input-group">
        <input
          className="question-input"
          type="text"
          placeholder="Ask about NHL players..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && askQuestion()}
        />
        <button className="ask-button" onClick={askQuestion}>Ask</button>
      </div>

      {loading && <div className="loading">⏳ Working on your request...</div>}

      {summary && (
        <div className="summary-box">
          <strong>Summary:</strong> {summary}
        </div>
      )}

      {data.length > 0 && (
        <div className="table-wrapper">
          <table className="stats-table">
            <thead>
              <tr>
                {Object.keys(data[0]).map((key) => (
                  <th key={key}>{key}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, idx) => (
                <tr key={idx}>
                  {Object.values(row).map((val, i) => (
                    <td key={i}>{val}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default App;
