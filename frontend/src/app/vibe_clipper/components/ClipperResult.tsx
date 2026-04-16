'use client';

interface ClipperResultProps {
  result: any;
  backendUrl: string;
  handleDeleteTrack: (trackId: string) => void;
}

export default function ClipperResult({ result, backendUrl, handleDeleteTrack }: ClipperResultProps) {
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

  return (
    <div className="bg-gray-900 p-6 rounded-2xl shadow-xl border border-gray-800 space-y-6 animate-fade-in-up">
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 border-b border-gray-800 pb-4">
        <h2 className="text-xl font-bold text-green-400">✨ {result.message}</h2>
        <div className="flex gap-3">
          {result.zip_url && <a href={`${backendUrl}/${result.zip_url}`} download className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm font-bold rounded-lg transition-all">📦 원본 전체 ZIP</a>}
          {result.filtered_zip_url && <a href={`${backendUrl}/${result.filtered_zip_url}`} download className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white text-sm font-bold rounded-lg shadow-lg transition-all animate-fade-in-up">🎯 필터링 완료 ZIP</a>}
        </div>
      </div>

      {result.files && result.files.length > 0 ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(groupFilesByTrack(result.files)).map(([trackId, filesArr]) => (
            <div key={trackId} className="relative group bg-gray-800 rounded-xl overflow-hidden border border-gray-700">
              <div className="h-40 relative">
                <img src={`${backendUrl}/${filesArr[0]}?t=${Date.now()}`} alt={`Track ${trackId}`} className="w-full h-full object-contain" />
                
                {/* 🌟 UX 개선: 회색 X 힌트 버튼 */}
                <div className="absolute top-2 right-2 w-6 h-6 flex items-center justify-center bg-gray-500/80 text-white/90 rounded-full text-sm font-bold shadow-lg z-0">
                  ✕
                </div>

                <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center z-10">
                  <button onClick={() => handleDeleteTrack(trackId)} className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white text-sm font-bold rounded-lg shadow-lg transform translate-y-4 group-hover:translate-y-0 transition-all">
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
  );
}