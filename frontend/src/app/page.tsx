import Link from 'next/link';

// Vercel Re-build test

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-gray-950 text-white p-8 font-sans">
      <div className="text-center space-y-8 animate-fade-in-up">
        
        {/* 🌟 메인 타이틀 */}
        <div className="space-y-4">
          <h1 className="text-6xl font-extrabold tracking-tight">
            <span className="bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
              COEVIBED
            </span>
            <span className="text-gray-100"> AI Hub</span>
          </h1>
          <p className="text-xl text-gray-400 font-medium">
            통합 인공지능 에이전트 플랫폼
          </p>
        </div>

        {/* 🌟 프로젝트로 이동하는 포털 버튼들 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12 max-w-4xl mx-auto">
          
          {/* 1번 프로젝트: Vibe-Clipper */}
          <Link 
            href="/vibe_clipper"
            className="group flex flex-col items-center justify-center p-8 bg-gray-900 border border-gray-800 rounded-2xl hover:border-blue-500/50 hover:bg-gray-800 transition-all shadow-lg hover:shadow-blue-500/10 cursor-pointer"
          >
            <span className="text-5xl mb-4 group-hover:scale-110 transition-transform duration-300">✂️</span>
            <h2 className="text-2xl font-bold text-gray-200 group-hover:text-blue-400 transition-colors">Vibe-Clipper</h2>
            <p className="text-sm text-gray-500 mt-2 text-center">
              자연어 기반 이미지 크롭 파이프라인
            </p>
          </Link>

          {/* 2번 프로젝트: (나중을 위한 빈자리) */}
          <div className="flex flex-col items-center justify-center p-8 bg-gray-900/50 border border-gray-800 border-dashed rounded-2xl text-gray-600">
            <span className="text-4xl mb-4 opacity-50">🔒</span>
            <h2 className="text-xl font-bold">Project 2</h2>
            <p className="text-sm mt-2 text-center">Coming Soon</p>
          </div>

          {/* 3번 프로젝트: (나중을 위한 빈자리) */}
          <div className="flex flex-col items-center justify-center p-8 bg-gray-900/50 border border-gray-800 border-dashed rounded-2xl text-gray-600">
            <span className="text-4xl mb-4 opacity-50">🔒</span>
            <h2 className="text-xl font-bold">Project 3</h2>
            <p className="text-sm mt-2 text-center">Coming Soon</p>
          </div>

        </div>
      </div>
    </main>
  );
}