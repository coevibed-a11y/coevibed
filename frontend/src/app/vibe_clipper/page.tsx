'use client';

import { useState, useRef, useEffect } from 'react';
import { TARGET_DICTIONARY } from './constants/targetDictionary';

export default function Home() {
  // === 상태 관리 ===
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [startTime, setStartTime] = useState('00:00:00');
  const [endTime, setEndTime] = useState('00:01:00');
  
  // 🌟 스마트 타겟 상태 (자유 입력 지원)
  const [displayTarget, setDisplayTarget] = useState('');
  const [actualTarget, setActualTarget] = useState(''); 
  const [suggestions, setSuggestions] = useState<typeof TARGET_DICTIONARY>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [backendUrl, setBackendUrl] = useState('');

  const autocompleteRef = useRef<HTMLDivElement>(null);

  // 화면 밖 클릭 시 드롭다운 닫기
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (autocompleteRef.current && !autocompleteRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // 🌟 타겟 검색 로직 (자유 입력 허용)
  const handleTargetChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setDisplayTarget(value);
    setActualTarget(value); // 사용자가 입력한 값 그대로를 일단 실제 타겟으로 설정!
    
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
    setActualTarget(label); // 사전에 있는 걸 고르면 영어 라벨(bird 등)로 덮어씀
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

  // 수확 시작!
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setResult(null);

    const startSec = parseTimeToSeconds(startTime);
    const endSec = parseTimeToSeconds(endTime);
    
    if (isNaN(startSec) || isNaN(endSec)) {
      setError('시간 형식이 잘못되었습니다. (예: 01:20 또는 00:01:20)');
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
    
    // 🌟 족쇄 해제: 사전에 없는 단어라도 에러를 띄우지 않고 그대로 통과시킵니다!
    // 사용자가 'white bird'라고 치면 그 값을 finalTarget으로 사용합니다.
    const finalTarget = actualTarget; 

    setIsLoading(true);

    try {
      let currentBackendUrl = backendUrl;
      if (!currentBackendUrl) {
        const firebaseRes = await fetch(process.env.NEXT_PUBLIC_FIREBASE_URL as string);
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
          target_label: finalTarget, // YOLO-World로 향하는 자유 텍스트!
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

  return (
    <main className="min-h-screen bg-gray-950 text-white p-8 font-sans">
      <div className="max-w-4xl mx-auto space-y-8">
        
        <header className="text-center space-y-4">
          <h1 className="text-4xl font-extrabold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Vibe-Clipper V2
          </h1>
          <p className="text-gray-400">Open-Vocabulary AI 에셋 수확 파이프라인</p>
        </header>

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
            {/* 🌟 수정된 타겟 입력기: 자유 입력 강조 */}
            <div className="space-y-2 relative">
              <label className="text-sm font-semibold text-gray-300">🎯 수확할 타겟 (자유 입력)</label>
              <input
                type="text"
                required
                value={displayTarget}
                onChange={handleTargetChange}
                onFocus={() => displayTarget && setShowSuggestions(true)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-purple-500 transition-all placeholder-gray-500"
                placeholder="예: 예: 빨간 모자를 쓴 사람, 하얀 자동차..."
              />
              {/* 🌟 사용자 경험(UX)을 위한 영어 권장 팁 추가 */}
              <p className="text-xs text-gray-500 mt-1 pl-1">
                💡 팁: 한국어로 입력하면 AI 에이전트가 문맥을 파악해 타겟을 찾아냅니다.
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
            className="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold rounded-lg shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <span className="animate-pulse">⏳ 프롬프트 분석 및 에셋 수확 중... (최대 수십 초 소요)</span>
            ) : (
              <span>🚀 AI 수확 시작</span>
            )}
          </button>
        </form>

        {result && (
          <div className="bg-gray-900 p-6 rounded-2xl shadow-xl border border-gray-800 space-y-6 animate-fade-in-up">
            
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <h2 className="text-2xl font-bold text-green-400">✨ {result.message}</h2>
              
              {result.zip_url && result.files.length > 0 && (
                <a 
                  href={`${backendUrl}/${result.zip_url}`}
                  download
                  className="px-6 py-3 bg-green-600 hover:bg-green-500 text-white font-bold rounded-full shadow-lg transition-all flex items-center gap-2"
                >
                  📦 전체 다운로드 (ZIP)
                </a>
              )}
            </div>

            {result.files && result.files.length > 0 ? (
              <>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="md:col-span-2 h-64 md:h-96 relative rounded-xl overflow-hidden bg-gray-800 group">
                    <img 
                      src={`${backendUrl}/${result.files[0]}?t=${Date.now()}`} 
                      alt="Main Crop" 
                      className="w-full h-full object-contain group-hover:scale-105 transition-transform duration-500"
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 md:col-span-1">
                    {result.files.slice(1, 5).map((file: string, index: number) => (
                      <div key={index} className="h-32 md:h-44 relative rounded-xl overflow-hidden bg-gray-800 group">
                        <img 
                          src={`${backendUrl}/${file}?t=${Date.now()}`} 
                          alt={`Crop ${index + 1}`} 
                          className="w-full h-full object-contain group-hover:scale-110 transition-transform duration-500"
                        />
                      </div>
                    ))}
                  </div>
                </div>
                
                {result.files.length > 5 && (
                  <div className="text-center space-y-1 mt-4">
                    <p className="text-gray-400 text-sm font-medium">
                      * 서버 안정성을 위해 회당 최대 수확량은 50장으로 제한됩니다.
                    </p>
                    <p className="text-gray-500 text-xs">
                      위 이미지는 미리보기이며, 전체 50장의 데이터는 ZIP 파일로 확인하세요.
                    </p>
                  </div>
                )}
              </>
            ) : (
              <div className="py-12 flex flex-col items-center justify-center bg-gray-800/50 rounded-xl border border-gray-700 border-dashed">
                <span className="text-5xl mb-4">🪹</span>
                <p className="text-gray-300 font-semibold">해당 구간에서 타겟을 발견하지 못했습니다.</p>
                <p className="text-gray-500 text-sm mt-2">다른 유튜브 영상이나, 타겟이 더 명확히 등장하는 시간대를 설정해 보세요.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}