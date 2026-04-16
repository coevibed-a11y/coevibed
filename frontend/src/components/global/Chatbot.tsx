'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useChat } from '../../context/ChatContext';

export default function Chatbot() {
  const { messages, isChatOpen, setIsChatOpen, sendMessage, isLoading } = useChat();
  const [input, setInput] = useState('');
  
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null); // 🌟 높이 조절을 위한 Ref

  // 메시지가 추가될 때마다 자동으로 하단 스크롤
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // 🌟 AI 응답에서 마크다운 기호(**, *, #, _ 등)를 제거하는 함수
  const removeMarkdown = (text: string) => {
    return text.replace(/[*#_`~]/g, '');
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    const msg = input;
    setInput('');
    
    // 🌟 전송 후 입력창 높이 초기화
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    
    await sendMessage(msg);
  };

  // 🌟 텍스트 입력 시 높이 자동 조절 함수
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'; // 먼저 초기화
      // scrollHeight를 기준으로 하되, 96px(약 4줄)을 최대치로 고정
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 96)}px`;
    }
  };

  // 🌟 Enter는 전송, Shift+Enter는 줄바꿈
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // 한글 입력 시 Enter 키 이벤트가 두 번 발생하는 현상(IME) 방지
    if (e.nativeEvent.isComposing) return;

    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // 기본 줄바꿈 방지
      handleSend();
    }
  };

  return (
    <div className="fixed bottom-8 right-8 z-[9999] flex flex-col items-end">
      {isChatOpen && (
        <div className="mb-4 w-80 h-96 bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl overflow-hidden flex flex-col animate-fade-in-up">
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4 text-white font-bold flex justify-between items-center shadow-lg">
            <span>💬 Vibe AI 비서</span>
            <button onClick={() => setIsChatOpen(false)} className="hover:text-gray-200">✕</button>
          </div>
          
          <div ref={scrollRef} className="flex-1 p-4 bg-gray-800/50 overflow-y-auto space-y-4">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] p-3 rounded-2xl text-sm shadow-sm whitespace-pre-wrap ${
                  msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-none' : 'bg-gray-700 text-gray-100 rounded-tl-none'
                }`}>
                  {/* 🌟 마크다운을 제거하고 줄바꿈이 정상 적용되도록 렌더링 */}
                  {msg.role === 'assistant' ? removeMarkdown(msg.content) : msg.content}
                </div>
              </div>
            ))}
            {isLoading && <div className="text-xs text-gray-500 animate-pulse ml-1">AI 비서가 답변을 작성 중입니다...</div>}
          </div>
          
          {/* 🌟 버튼이 입력창 하단에 맞춰지도록 items-end 추가 */}
          <div className="p-3 border-t border-gray-700 bg-gray-900 flex items-end gap-2">
            {/* 🌟 input 대신 자동 확장 textarea 적용 */}
            <textarea
              ref={textareaRef}
              value={input}
              rows={1}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              placeholder="궁금한 점을 물어보세요!"
              className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-purple-500 transition-colors resize-none overflow-y-auto"
              style={{
                minHeight: '40px', // 1줄 기본 높이
                maxHeight: '96px'  // 약 4줄 최대 높이
              }}
            />
            {/* 버튼 크기 고정(h-10)으로 textarea가 늘어나도 모양 유지 */}
            <button 
              onClick={handleSend} 
              className="bg-purple-600 w-10 h-10 rounded-lg text-white hover:bg-purple-500 font-bold transition-transform active:scale-95 flex items-center justify-center"
            >
              →
            </button>
          </div>
        </div>
      )}
      
      <button 
        onClick={() => setIsChatOpen(!isChatOpen)} 
        className="w-14 h-14 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full shadow-2xl flex items-center justify-center text-white text-2xl border-2 border-gray-800 hover:scale-105 transition-all"
      >
        {isChatOpen ? '✕' : '🤖'}
      </button>
    </div>
  );
}