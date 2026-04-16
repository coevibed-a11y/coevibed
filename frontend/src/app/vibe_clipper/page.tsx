'use client';

import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { TARGET_DICTIONARY } from './constants/targetDictionary';

// 🌟 전역 챗봇 저장소(Context) 연결
import { useChat } from '../../context/ChatContext'; 

// 🌟 분리된 UI 컴포넌트 불러오기
import ClipperForm from './components/ClipperForm';
import ClipperResult from './components/ClipperResult';

export default function Home() {
  // 🌟 챗봇에게 현재 페이지 상태를 보고하기 위한 함수들
  const { setCurrentPage, setHasData } = useChat();

  // === 1. 수확 엔진 관련 상태 관리 ===
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

  // 폼의 자동완성 바깥 클릭 감지용 Ref
  const autocompleteRef = useRef<HTMLDivElement>(null);

  // === 2. 챗봇 상태 동기화 (useEffect) ===
  
  // 페이지 진입 시 챗봇에게 위치 보고
  useEffect(() => {
    setCurrentPage('vibe_clipper');
    // 페이지를 나갈 때 상태를 기본값으로 되돌림
    return () => setCurrentPage('home');
  }, [setCurrentPage]);

  // 수확 결과 유무를 챗봇에게 보고
  useEffect(() => {
    const hasFiles = !!result && result.files?.length > 0;
    setHasData(hasFiles);
  }, [result, setHasData]);

  // === 3. 사용자 인터랙션 로직 ===

  // 바깥 클릭 시 자동완성 목록 닫기
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
    
    if (value.trim().length > 0) {
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
    setShowSuggestions(false); // 명시적으로 드롭다운 닫기
  };

  const parseTimeToSeconds = (timeStr: string) => {
    const parts = timeStr.split(':').reverse();
    let seconds = 0;
    for (let i = 0; i < parts.length; i++) {
      seconds += parseInt(parts[i] || '0') * Math.pow(60, i);
    }
    return seconds;
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setShowSuggestions(false); // 검색(Enter) 시 드롭다운 무조건 닫기
    setError('');
    setResult(null);

    // 🌟 QA 로직: 시간 형식 검사 및 마이너스(-) 기호 정제
    const cleanStart = startTime.replace(/-/g, "").trim();
    const cleanEnd = endTime.replace(/-/g, "").trim();
    const timeRegex = /^(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d$/;

    if (!timeRegex.test(cleanStart) || !timeRegex.test(cleanEnd)) {
      setError('⚠️ 시간 형식을 정확히 지켜주세요. (예: 00:00:00 ~ 00:01:20)');
      return;
    }

    setStartTime(cleanStart);
    setEndTime(cleanEnd);

    if (parseTimeToSeconds(cleanStart) >= parseTimeToSeconds(cleanEnd)) {
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
        // Firebase 등에서 백엔드 URL 가져오기
        const firebaseUrl = `${process.env.NEXT_PUBLIC_FIREBASE_URL}/server_status.json?t=${Date.now()}`;
        const firebaseRes = await fetch(firebaseUrl, { cache: 'no-store' });
        const firebaseData = await firebaseRes.json();
        currentBackendUrl = firebaseData?.backend_url; 
        setBackendUrl(currentBackendUrl);
      }

      if (!currentBackendUrl) throw new Error("AI 엔진(백엔드)이 오프라인 상태입니다.");

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
          start_time: cleanStart,
          end_time: cleanEnd,
        }),
      });

      const data = await response.json();
      if (response.ok) setResult(data);
      else throw new Error(data.detail || data.message || '수확 중 오류가 발생했습니다.');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteTrack = async (trackId: string) => {
    if (trackId === 'unknown') return;
    try {
      const response = await fetch(`${backendUrl}/api/delete-track`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json', 
          'x-api-key': process.env.NEXT_PUBLIC_VIBE_API_KEY as string 
        },
        body: JSON.stringify({ track_id: parseInt(trackId) }),
      });
      const data = await response.json();
      if (response.ok) {
        setResult((prev: any) => ({ 
          ...prev, 
          message: data.message, 
          files: data.files, 
          filtered_zip_url: data.filtered_zip_url 
        }));
      } else alert("삭제 중 오류가 발생했습니다.");
    } catch (err) {
      alert("서버 연결에 실패했습니다.");
    }
  };

  // === 4. UI 렌더링 부 ===
  return (
    <main className="min-h-screen bg-gray-950 text-white p-8 font-sans relative">
      {/* 홈 버튼 */}
      <Link href="/" className="absolute top-8 left-8 flex items-center gap-2 text-gray-400 hover:text-white transition-colors bg-gray-900/50 px-4 py-2 rounded-full border border-gray-800">
        <span className="text-xl">🏠</span>
        <span className="font-semibold text-sm">Back to Hub</span>
      </Link>

      <div className="max-w-4xl mx-auto space-y-8 mt-12">
        <header className="text-center space-y-4">
          <h1 className="text-4xl font-extrabold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Vibe-Clipper V2
          </h1>
          <p className="text-gray-400">자연어 기반 이미지 크롭 시스템</p>
        </header>

        {/* 🌟 1. 입력 폼 컴포넌트 */}
        <ClipperForm 
          youtubeUrl={youtubeUrl} setYoutubeUrl={setYoutubeUrl}
          startTime={startTime} setStartTime={setStartTime}
          endTime={endTime} setEndTime={setEndTime}
          displayTarget={displayTarget} handleTargetChange={handleTargetChange}
          suggestions={suggestions} showSuggestions={showSuggestions}
          selectTarget={selectTarget} autocompleteRef={autocompleteRef}
          error={error} isLoading={isLoading} handleSubmit={handleSubmit}
        />

        {/* 🌟 2. 결과 출력 컴포넌트 */}
        {result && (
          <ClipperResult 
            result={result} 
            backendUrl={backendUrl} 
            handleDeleteTrack={handleDeleteTrack} 
          />
        )}
      </div>
    </main>
  );
}