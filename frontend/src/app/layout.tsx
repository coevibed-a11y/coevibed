import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

// 🌟 추가된 임포트 (경로를 사용자님의 폴더 구조에 맞췄습니다)
import { ChatProvider } from "../context/ChatContext";
import Chatbot from "../components/global/Chatbot";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "COEVIBED AI",
  description: "Vibe-Clipper & AI Assistant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="ko"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        {/* 🌟 1. ChatProvider로 전체 페이지(children)를 감싸줍니다. */}
        <ChatProvider>
          {children}
          {/* 🌟 2. 전역 챗봇을 Provider 안에 배치하여 기능을 활성화합니다. */}
          <Chatbot />
        </ChatProvider>
      </body>
    </html>
  );
}