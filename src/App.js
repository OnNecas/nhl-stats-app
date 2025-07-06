// src/App.js
import { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [question, setQuestion] = useState('');
  const [summary, setSummary] = useState('');
  const [results, setResults] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSummary('Loading...');
    const res = await axios.post('http://localhost:8000/ask', { question });
    setSummary(res.data.summary);
    setResults(res.data.data);
  };

  return (
    <div className="App">
      <h1>🏒 NHL Stats Assistant</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Ask a hockey question..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button type="submit">Ask</button>
      </form>

      <div className="summary">
        <h2>🧠 Summary</h2>
        <p>{summary}</p>
      </div>

      {results.length > 0 && (
        <div className="results">
          <h2>📊 Results</h2>
          <table>
            <thead>
              <tr>
                {Object.keys(results[0]).map((col) => (
                  <th key={col}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {results.map((row, idx) => (
                <tr key={idx}>
                  {Object.values(row).map((cell, i) => (
                    <td key={i}>{cell}</td>
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
