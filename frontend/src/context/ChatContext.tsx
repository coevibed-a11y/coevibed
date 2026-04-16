'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface ChatContextType {
  messages: Message[];
  isChatOpen: boolean;
  setIsChatOpen: (open: boolean) => void;
  // 🌟 페이지 정보와 데이터 유무를 전역에서 관리
  currentPage: string;
  setCurrentPage: (page: string) => void;
  hasData: boolean;
  setHasData: (val: boolean) => void;
  sendMessage: (msg: string) => Promise<void>;
  isLoading: boolean;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: '안녕하세요! Vibe AI 비서입니다. 무엇을 도와드릴까요? 😊' }
  ]);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  // 🌟 전역 상태 추가
  const [currentPage, setCurrentPage] = useState('home');
  const [hasData, setHasData] = useState(false);

  const sendMessage = async (content: string) => {
    const userMsg: Message = { role: 'user', content };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      // 🌟 .env에 설정한 백엔드 주소 혹은 로컬 주소
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

      const response = await fetch(`${backendUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': process.env.NEXT_PUBLIC_VIBE_API_KEY as string,
        },
        body: JSON.stringify({
          message: content,
          current_page: currentPage, // 🌟 저장소에 있는 현재 페이지 전송
          has_data: hasData,         // 🌟 저장소에 있는 데이터 유무 전송
          history: messages.slice(-5) 
        }),
      });

      const data = await response.json();
      if (data.status === 'success') {
        setMessages(prev => [...prev, { role: 'assistant', content: data.reply }]);
      } else {
        throw new Error(data.reply);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: '연결이 잠시 불안정해요. 다시 말씀해 주시겠어요? 😅' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ChatContext.Provider value={{ 
      messages, isChatOpen, setIsChatOpen, 
      currentPage, setCurrentPage, hasData, setHasData, 
      sendMessage, isLoading 
    }}>
      {children}
    </ChatContext.Provider>
  );
}

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) throw new Error('useChat must be used within a ChatProvider');
  return context;
};