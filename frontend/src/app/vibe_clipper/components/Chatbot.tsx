'use client';

interface ChatbotProps {
  isChatOpen: boolean;
  setIsChatOpen: (v: boolean) => void;
}

export default function Chatbot({ isChatOpen, setIsChatOpen }: ChatbotProps) {
  return (
    <div className="fixed bottom-8 right-8 z-50 flex flex-col items-end">
      {isChatOpen && (
        <div className="mb-4 w-80 h-96 bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl overflow-hidden flex flex-col animate-fade-in-up">
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4 text-white font-bold flex justify-between items-center">
            <span>💬 Vibe AI 비서</span>
            <button onClick={() => setIsChatOpen(false)} className="hover:text-gray-200">✕</button>
          </div>
          <div className="flex-1 p-4 bg-gray-800/50 overflow-y-auto">
            <div className="bg-gray-700 p-3 rounded-lg text-sm text-gray-200 w-5/6 mb-2">
              안녕하세요! 데이터 수확 중 도움이 필요하신가요? 😊 (현재 UI 데모 버전입니다)
            </div>
          </div>
          <div className="p-3 border-t border-gray-700 bg-gray-900 flex gap-2">
            <input type="text" placeholder="메시지를 입력하세요..." className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500" />
            <button className="bg-purple-600 px-3 py-2 rounded-lg text-white hover:bg-purple-500 font-bold">→</button>
          </div>
        </div>
      )}
      
      <button 
        onClick={() => setIsChatOpen(!isChatOpen)}
        className="w-14 h-14 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full shadow-lg hover:shadow-xl hover:scale-105 transition-all flex items-center justify-center text-2xl text-white border-2 border-gray-800"
      >
        {isChatOpen ? '✕' : '🤖'}
      </button>
    </div>
  );
}