import React, { useState, useRef, useEffect } from 'react';
import { Send, Menu, Plus, MessageSquare, User, Bot } from 'lucide-react';
import MermaidChart from './components/MermaidChart';

// --- Types ---
interface Message {
  role: 'user' | 'assistant';
  content: string;
}

// --- INTELLIGENT PARSER (The Fix) ---
const parseMessage = (content: string) => {
  // 1. Try to find a formal Markdown block (```mermaid ... ```)
  const codeBlockRegex = /```mermaid([\s\S]*?)```/;
  const matchBlock = content.match(codeBlockRegex);

  if (matchBlock) {
    return {
      text: content.replace(codeBlockRegex, '').trim(),
      chartCode: matchBlock[1].trim()
    };
  }

  // 2. Fallback: If AI forgets the ``` block, look for raw "graph TD" or "mindmap"
  // This detects "graph TD" or "mindmap" if it appears after a newline
  const rawGraphRegex = /(\n\s*graph TD[\s\S]*|\n\s*mindmap[\s\S]*)/;
  const matchRaw = content.match(rawGraphRegex);

  if (matchRaw) {
    return {
      text: content.replace(rawGraphRegex, '').trim(),
      chartCode: matchRaw[0].trim()
    };
  }

  // 3. No graph found
  return { text: content, chartCode: null };
};

function App() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Hello! I am PathFinder. Ready to plan your learning journey?' }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user' as const, content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // REPLACE with your actual Backend URL
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input }),
      });

      const data = await response.json();

      // Handle the response
      const botContent = data.response || data.message || JSON.stringify(data);

      setMessages((prev) => [...prev, { role: 'assistant', content: botContent }]);

    } catch (error) {
      console.error("API Error:", error);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: "⚠️ Error: Could not connect to backend. Is it running?" }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50 text-gray-800 font-sans">

      {/* Sidebar */}
      <aside className="w-64 bg-white border-r hidden md:flex flex-col">
        <div className="p-4 border-b flex items-center justify-between">
          <h1 className="font-bold text-xl text-blue-600">PathFinder</h1>
          <button className="p-1 hover:bg-gray-100 rounded">
            <Menu size={20} />
          </button>
        </div>
        <div className="p-4">
          <button
            className="w-full flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors"
            onClick={() => setMessages([{ role: 'assistant', content: 'Hello! What should we learn next?' }])}
          >
            <Plus size={18} />
            <span>New Session</span>
          </button>
        </div>
      </aside>

      {/* Main Chat */}
      <main className="flex-1 flex flex-col max-w-5xl mx-auto w-full bg-white shadow-sm">
        <header className="p-4 border-b md:hidden flex items-center justify-between">
          <span className="font-bold text-blue-600">PathFinder AI</span>
          <Menu size={20} />
        </header>

        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {messages.map((msg, idx) => {
            const isBot = msg.role === 'assistant';
            const { text, chartCode } = parseMessage(msg.content);

            return (
              <div key={idx} className={`flex gap-4 ${isBot ? 'justify-start' : 'justify-end'}`}>
                {isBot && (
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                    <Bot size={18} className="text-blue-600" />
                  </div>
                )}

                <div className={`max-w-[85%] rounded-2xl p-4 shadow-sm ${
                  isBot ? 'bg-white border border-gray-100 text-gray-800' : 'bg-blue-600 text-white'
                }`}>
                  <div className="whitespace-pre-wrap leading-relaxed">{text}</div>

                  {/* Render Diagram if detected */}
                  {isBot && chartCode && (
                    <div className="mt-4 pt-4 border-t border-gray-100">
                      <p className="text-xs font-bold text-gray-400 uppercase mb-2">Visual Roadmap</p>
                      <MermaidChart chartCode={chartCode} />
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {isLoading && (
            <div className="flex gap-4">
               <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center"><Bot size={18} /></div>
               <div className="bg-white border p-4 rounded-2xl"><span className="animate-pulse">Generating Roadmap...</span></div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="p-4 border-t bg-white">
          <div className="flex items-center gap-2 bg-gray-50 border rounded-xl p-2 px-4">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Type your topic here..."
              className="flex-1 bg-transparent outline-none"
              disabled={isLoading}
            />
            <button onClick={handleSend} disabled={isLoading} className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              <Send size={18} />
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;