import React, { useState, useRef, useEffect } from 'react';
import { Send, Menu, Plus, MessageSquare, User, Bot } from 'lucide-react';
import MermaidChart from './components/MermaidChart';

// Types
interface Message {
  role: 'user' | 'assistant';
  content: string;
}

// Helper
const parseMessage = (content: string) => {
  // Regex to find content between ```mermaid and ```
  const mermaidRegex = /```mermaid([\s\S]*?)```/;
  const match = content.match(mermaidRegex);

  if (match) {
    return {
      text: content.replace(mermaidRegex, '').trim(), // The normal text
      chartCode: match[1].trim() // The diagram code
    };
  }
  return { text: content, chartCode: null };
};

function App() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Hello! I am PathFinder. What topic do you want to master today?' }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // --- Handle Sending Message ---
  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user' as const, content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('https://pathfinder-swgh.onrender.com', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input }),
      });

      const data = await response.json();

      // Assuming backend returns { response: "..." } or similar
      const botMessage = {
        role: 'assistant' as const,
        content: data.response || data.message || "I received your message but got no text back."
      };

      setMessages((prev) => [...prev, botMessage]);

    } catch (error) {
      console.error("API Error:", error);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: "⚠️ Server Error: Could not connect to the backend." }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50 text-gray-800 font-sans">

      {/* --- Sidebar --- */}
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

        <div className="flex-1 overflow-y-auto p-4">
          <div className="text-xs font-semibold text-gray-400 mb-2 uppercase">Recent</div>
          <div className="flex items-center gap-2 p-2 hover:bg-gray-100 rounded cursor-pointer text-sm">
            <MessageSquare size={16} />
            <span className="truncate">Python Roadmap</span>
          </div>
        </div>
      </aside>

      {/* --- Main Chat Area --- */}
      <main className="flex-1 flex flex-col max-w-5xl mx-auto w-full bg-white shadow-sm">

        {/* Header (Mobile) */}
        <header className="p-4 border-b md:hidden flex items-center justify-between bg-white">
          <span className="font-bold text-blue-600">PathFinder AI</span>
          <Menu size={20} />
        </header>

        {/* Messages List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {messages.map((msg, idx) => {
            const isBot = msg.role === 'assistant';

            // Split Text
            const { text, chartCode } = parseMessage(msg.content);

            return (
              <div key={idx} className={`flex gap-4 ${isBot ? 'justify-start' : 'justify-end'}`}>

                {/* Bot Icon */}
                {isBot && (
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                    <Bot size={18} className="text-blue-600" />
                  </div>
                )}

                {/* Message Bubble */}
                <div className={`max-w-[85%] rounded-2xl p-4 shadow-sm ${
                  isBot ? 'bg-white border border-gray-100 text-gray-800' : 'bg-blue-600 text-white'
                }`}>

                  {/* 1. Render Text */}
                  <div className="whitespace-pre-wrap leading-relaxed">
                    {text}
                  </div>

                  {/* 2. Render Mermaid Chart (Only for Bot) */}
                  {isBot && chartCode && (
                    <div className="mt-4 pt-4 border-t border-gray-100">
                      <p className="text-xs font-bold text-gray-400 uppercase mb-2">Visual Roadmap</p>
                      {/* THIS IS YOUR NEW COMPONENT */}
                      <MermaidChart chartCode={chartCode} />
                    </div>
                  )}

                </div>

                {/* User Icon */}
                {!isBot && (
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
                    <User size={18} className="text-gray-600" />
                  </div>
                )}
              </div>
            );
          })}

          {isLoading && (
            <div className="flex gap-4">
               <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                  <Bot size={18} className="text-blue-600" />
               </div>
               <div className="bg-white border p-4 rounded-2xl">
                 <span className="animate-pulse">Thinking...</span>
               </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t bg-white">
          <div className="flex items-center gap-2 bg-gray-50 border rounded-xl p-2 px-4 focus-within:ring-2 focus-within:ring-blue-100 transition-all">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask anything (e.g., 'Plan for learning Java')..."
              className="flex-1 bg-transparent outline-none text-gray-700"
              disabled={isLoading}
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send size={18} />
            </button>
          </div>
          <p className="text-center text-xs text-gray-400 mt-2">
            PathFinder can make mistakes. Please check important info.
          </p>
        </div>
      </main>
    </div>
  );
}

export default App;