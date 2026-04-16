'use client';

import React from 'react';

interface ClipperFormProps {
  youtubeUrl: string; setYoutubeUrl: (v: string) => void;
  startTime: string; setStartTime: (v: string) => void;
  endTime: string; setEndTime: (v: string) => void;
  displayTarget: string; handleTargetChange: (e: any) => void;
  suggestions: any[]; showSuggestions: boolean;
  selectTarget: (label: string, text: string) => void;
  autocompleteRef: React.RefObject<HTMLDivElement | null>;
  error: string; isLoading: boolean;
  handleSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
}

export default function ClipperForm(props: ClipperFormProps) {
  return (
    <form onSubmit={props.handleSubmit} className="bg-gray-900 p-6 rounded-2xl shadow-xl border border-gray-800 space-y-6">
      {/* 1층: 유튜브 URL */}
      <div className="space-y-2">
        <label className="text-sm font-semibold text-gray-300">📺 유튜브 URL</label>
        <input 
          type="text" 
          required 
          value={props.youtubeUrl} 
          onChange={(e) => props.setYoutubeUrl(e.target.value)} 
          className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500 transition-all" 
          placeholder="https://www.youtube.com/..." 
        />
      </div>

      {/* 2층: 타겟 및 시간 입력 (Grid) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 relative" ref={props.autocompleteRef}>
        
        {/* 타겟 입력 부분 */}
        <div className="space-y-2">
          <label className="text-sm font-semibold text-gray-300">🎯 수확할 타겟 (자유 입력)</label>
          
          {/* 🌟 핵심 해결 포인트 1: Input과 드롭다운을 하나로 묶는 전용 relative 컨테이너 */}
          <div className="relative z-50">
            <input 
              type="text" 
              required 
              value={props.displayTarget} 
              onChange={props.handleTargetChange} 
              className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-purple-500 transition-all" 
              placeholder="예: 빨간 모자를 쓴 사람..." 
            />

            {/* 🌟 핵심 해결 포인트 2: h-0 속성을 가진 래퍼로 감싸서 패널 확장을 원천 차단 */}
            {props.showSuggestions && props.suggestions.length > 0 && (
                <div className="absolute top-full left-0 w-full mt-1 h-0 z-[100]">
                  <ul className="bg-gray-800 border border-gray-700 rounded-lg shadow-2xl overflow-hidden max-h-60 overflow-y-auto">
                    {props.suggestions.map((item) => (
                        <li 
                          key={item.label} 
                          onClick={() => props.selectTarget(item.label, item.text)} 
                          className="p-3 hover:bg-gray-700 cursor-pointer text-sm transition-colors border-b border-gray-700 last:border-none"
                        >
                        {item.text}
                        </li>
                    ))}
                  </ul>
                </div>
            )}
          </div>
        </div>

        {/* 시간 입력 부분 */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-semibold text-gray-300">⏱️ 시작 시간</label>
            <input 
              type="text" 
              required 
              value={props.startTime} 
              onChange={(e) => props.setStartTime(e.target.value)} 
              className={`w-full bg-gray-800 border ${props.error.includes('시간 형식') ? 'border-red-500' : 'border-gray-700'} rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500`} 
              placeholder="00:00:00" 
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-semibold text-gray-300">⏳ 종료 시간</label>
            <input 
              type="text" 
              required 
              value={props.endTime} 
              onChange={(e) => props.setEndTime(e.target.value)} 
              className={`w-full bg-gray-800 border ${props.error.includes('시간 형식') ? 'border-red-500' : 'border-gray-700'} rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500`} 
              placeholder="00:01:00" 
            />
          </div>
        </div>
      </div>

      {/* 3층: 안내 문구 */}
      <div className="px-1 -mt-2 space-y-1">
        {/* 🌟 팁 문구 추가 부분 */}
        <p className="text-sm text-gray-400 opacity-90">
          💡 팁: '빨간 옷을 입은', '라켓을 들고 있는' 처럼 구체적인 조건을 추가하면 정확도가 올라갑니다!
        </p>
      </div>

      {props.error && (
        <div className="p-4 bg-red-900/50 border border-red-500/50 text-red-200 rounded-lg text-sm">
          {props.error}
        </div>
      )}

      {/* 4층: 수확 버튼 */}
      <button 
        type="submit" 
        disabled={props.isLoading} 
        className="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold rounded-lg shadow-lg transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed mt-2"
      >
        {props.isLoading ? <span className="animate-pulse">⏳ AI 분석 및 픽셀 필터링 중...</span> : <span>🚀 스마트 수확 시작</span>}
      </button>
    </form>
  );
}