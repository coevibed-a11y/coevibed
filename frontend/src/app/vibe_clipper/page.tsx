'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { TARGET_DICTIONARY } from './constants/targetDictionary';

export default function Home() {
  // === 상태 관리 ===
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [startTime, setStartTime] = useState('00:00:00');
  const [endTime, setEndTime] = useState('00:01:00');
  
  const [displayTarget, setDisplayTarget] = useState('');
  const [actualTarget, setActualTarget] = useState(''); 
  const [suggestions, setSuggestions] = useState<typeof TARGET_DICTIONARY>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [backendUrl, setBackendUrl] = useState('');

  // 🌟 챗봇 UI 상태
  const [isChatOpen, setIsChatOpen] = useState(false);

  const autocompleteRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (autocompleteRef.current && !autocompleteRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleTargetChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setDisplayTarget(value);
    setActualTarget(value);
    
    if (value.length > 0) {
      const filtered = TARGET_DICTIONARY.filter(item => 
        item.keywords.some(keyword => keyword.toLowerCase().includes(value.toLowerCase()))
      );
      setSuggestions(filtered);
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
  };

  const selectTarget = (label: string, text: string) => {
    setDisplayTarget(text);
    setActualTarget(label);
    setShowSuggestions(false);
  };

  const parseTimeToSeconds = (timeStr: string) => {
    const parts = timeStr.split(':').reverse();
    let seconds = 0;
    for (let i = 0; i < parts.length; i++) {
      seconds += parseInt(parts[i] || '0') * Math.pow(60, i);
    }
    return seconds;
  };

  // 🌟 파일명에서 Track ID 추출 및 그룹화
  const groupFilesByTrack = (files: string[]) => {
    const groups: { [key: string]: string[] } = {};
    files.forEach(file => {
      const match = file.match(/_tr(\d+)_/);
      const trackId = match ? match[1] : 'unknown';
      if (!groups[trackId]) groups[trackId] = [];
      groups[trackId].push(file);
    });
    return groups;
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setResult(null);

    const startSec = parseTimeToSeconds(startTime);
    const endSec = parseTimeToSeconds(endTime);
    
    if (isNaN(startSec) || isNaN(endSec)) {
      setError('시간 형식이 잘못되었습니다. (예: 01:20)');
      return;
    }
    if (startSec >= endSec) {
      setError('🚨 시작 시간이 종료 시간보다 같거나 늦을 수 없습니다!');
      return;
    }
    if (!actualTarget) {
      setError('수확할 타겟을 입력해 주세요.');
      return;
    }

    setIsLoading(true);

    try {
      let currentBackendUrl = backendUrl;
      if (!currentBackendUrl) {
        // 🌟 [수정 완료] Firebase URL 404 에러 해결 (/server_status.json 추가)
        const firebaseUrl = `${process.env.NEXT_PUBLIC_FIREBASE_URL}/server_status.json?t=${Date.now()}`;
        const firebaseRes = await fetch(firebaseUrl, { cache: 'no-store' });
        const firebaseData = await firebaseRes.json();
        
        currentBackendUrl = firebaseData?.backend_url; 
        setBackendUrl(currentBackendUrl);
        
        if (!currentBackendUrl) {
          throw new Error("AI 엔진(백엔드)이 오프라인 상태입니다. 엔진을 켜주세요.");
        }
      }

      const response = await fetch(`${currentBackendUrl}/api/mine`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': process.env.NEXT_PUBLIC_VIBE_API_KEY as string,
          'ngrok-skip-browser-warning': '69420',
        },
        body: JSON.stringify({
          youtube_url: youtubeUrl,
          target_label: actualTarget,
          max_crops: 50,
          start_time: startTime,
          end_time: endTime,
        }),
      });

      const data = await response.json();
      if (response.ok) {
        setResult(data);
      } else {
        throw new Error(data.detail || data.message || '수확 중 오류가 발생했습니다.');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // 🌟 트랙 삭제 API 호출
  const handleDeleteTrack = async (trackId: string) => {
    if (trackId === 'unknown') return;
    
    try {
      const response = await fetch(`${backendUrl}/api/delete-track`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': process.env.NEXT_PUBLIC_VIBE_API_KEY as string,
        },
        body: JSON.stringify({ track_id: parseInt(trackId) }),
      });

      const data = await response.json();
      if (response.ok) {
        // 🌟 [수정 완료] 삭제 성공 시, 남은 파일과 "필터링된 ZIP URL"을 업데이트!
        setResult((prev: any) => ({
          ...prev,
          message: data.message,
          files: data.files,
          filtered_zip_url: data.filtered_zip_url 
        }));
      } else {
        alert("삭제 중 오류가 발생했습니다.");
      }
    } catch (err) {
      alert("서버 연결에 실패했습니다.");
    }
  };

  return (
    <main className="min-h-screen bg-gray-950 text-white p-8 font-sans relative">
      
      {/* 🌟 좌측 상단 홈 버튼 */}
      <Link href="/" className="absolute top-8 left-8 flex items-center gap-2 text-gray-400 hover:text-white transition-colors bg-gray-900/50 px-4 py-2 rounded-full border border-gray-800">
        <span className="text-xl">🏠</span>
        <span className="font-semibold text-sm">Back to Hub</span>
      </Link>

      <div className="max-w-4xl mx-auto space-y-8 mt-12">
        <header className="text-center space-y-4">
          <h1 className="text-4xl font-extrabold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Vibe-Clipper V2
          </h1>
          <p className="text-gray-400">객체 추적 기반 스마트 선별 수확 시스템</p>
        </header>

        {/* --- 폼 영역 --- */}
        <form onSubmit={handleSubmit} className="bg-gray-900 p-6 rounded-2xl shadow-xl border border-gray-800 space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-semibold text-gray-300">📺 유튜브 URL</label>
            <input
              type="text"
              required
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500 transition-all"
              placeholder="https://www.youtube.com/..."
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 relative" ref={autocompleteRef}>
            <div className="space-y-2 relative">
              <label className="text-sm font-semibold text-gray-300">🎯 수확할 타겟 (자유 입력)</label>
              <input
                type="text"
                required
                value={displayTarget}
                onChange={handleTargetChange}
                onFocus={() => displayTarget && setShowSuggestions(true)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-purple-500 transition-all"
                placeholder="예: 빨간 모자를 쓴 사람..."
              />
              <p className="text-xs text-gray-500 mt-1 pl-1">
                💡 한국어로 입력하면 AI가 문맥을 파악해 정확히 타겟팅합니다.
              </p>
              
              {showSuggestions && suggestions.length > 0 && (
                <ul className="absolute z-10 w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-2xl overflow-hidden">
                  {suggestions.map((item) => (
                    <li 
                      key={item.label}
                      onClick={() => selectTarget(item.label, item.text)}
                      className="p-3 hover:bg-gray-700 cursor-pointer text-sm transition-colors"
                    >
                      {item.text}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-300">⏱️ 시작 시간</label>
                <input
                  type="text"
                  required
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500"
                  placeholder="00:00:00"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-300">⏳ 종료 시간</label>
                <input
                  type="text"
                  required
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500"
                  placeholder="00:01:00"
                />
              </div>
            </div>
          </div>

          {error && <div className="p-4 bg-red-900/50 border border-red-500/50 text-red-200 rounded-lg text-sm">{error}</div>}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold rounded-lg shadow-lg transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <span className="animate-pulse">⏳ AI 분석 및 픽셀 필터링 중... (수십 초 소요)</span>
            ) : (
              <span>🚀 스마트 수확 시작</span>
            )}
          </button>
        </form>

        {/* --- 결과 표시 영역 (그룹화, 이중 다운로드 버튼 적용) --- */}
        {result && (
          <div className="bg-gray-900 p-6 rounded-2xl shadow-xl border border-gray-800 space-y-6 animate-fade-in-up">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4 border-b border-gray-800 pb-4">
              <h2 className="text-xl font-bold text-green-400">✨ {result.message}</h2>
              
              <div className="flex gap-3">
                {/* 🌟 원본 전체 다운로드 버튼 */}
                {result.zip_url && (
                  <a 
                    href={`${backendUrl}/${result.zip_url}`}
                    download
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm font-bold rounded-lg transition-all"
                  >
                    📦 원본 전체 ZIP
                  </a>
                )}
                
                {/* 🌟 필터링된 ZIP 다운로드 버튼 (오탐지 삭제를 한 번이라도 했을 때만 나타남!) */}
                {result.filtered_zip_url && (
                  <a 
                    href={`${backendUrl}/${result.filtered_zip_url}`}
                    download
                    className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white text-sm font-bold rounded-lg shadow-lg transition-all animate-fade-in-up"
                  >
                    🎯 필터링 완료 ZIP
                  </a>
                )}
              </div>
            </div>

            {result.files && result.files.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {/* 파일을 Track ID별로 그룹화하여 렌더링 */}
                {Object.entries(groupFilesByTrack(result.files)).map(([trackId, filesArr]) => (
                  <div key={trackId} className="relative group bg-gray-800 rounded-xl overflow-hidden border border-gray-700">
                    
                    {/* 대표 이미지 1장만 표시 */}
                    <div className="h-40 relative">
                      <img 
                        src={`${backendUrl}/${filesArr[0]}?t=${Date.now()}`} 
                        alt={`Track ${trackId}`} 
                        className="w-full h-full object-contain"
                      />
                      <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                        <button 
                          onClick={() => handleDeleteTrack(trackId)}
                          className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white text-sm font-bold rounded-lg shadow-lg transform translate-y-4 group-hover:translate-y-0 transition-all"
                        >
                          🗑️ 오탐지 일괄 삭제
                        </button>
                      </div>
                    </div>
                    
                    <div className="p-3 bg-gray-800 flex justify-between items-center border-t border-gray-700">
                      <span className="text-xs font-mono text-purple-400 bg-purple-900/30 px-2 py-1 rounded">ID: {trackId}</span>
                      <span className="text-xs text-gray-400">{filesArr.length}장 수확됨</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-12 flex flex-col items-center justify-center bg-gray-800/50 rounded-xl border border-gray-700 border-dashed">
                <span className="text-5xl mb-4">🪹</span>
                <p className="text-gray-300 font-semibold">저장된 데이터가 없습니다.</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 🌟 우측 하단 챗봇 플로팅 UI */}
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

    </main>
  );
}