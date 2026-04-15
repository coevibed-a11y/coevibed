// constants/targetDictionary.ts

export const TARGET_DICTIONARY = [
  // === 🧍 사람 및 교통수단 (Person & Vehicles) ===
  { label: 'person', text: '🧍 사람 (person)', keywords: ['사람', '인물', '남자', '여자', '인간', '보행자', 'person', 'man', 'woman', 'human'] },
  { label: 'bicycle', text: '🚲 자전거 (bicycle)', keywords: ['자전거', '자전차', '사이클', 'bicycle', 'bike', 'cycle'] },
  { label: 'car', text: '🚗 자동차 (car)', keywords: ['차', '자동차', '승용차', '차량', 'car', 'auto', 'vehicle'] },
  { label: 'motorcycle', text: '🏍️ 오토바이 (motorcycle)', keywords: ['오토바이', '모터사이클', '바이크', 'motorcycle', 'bike'] },
  { label: 'airplane', text: '✈️ 비행기 (airplane)', keywords: ['비행기', '항공기', '여객기', 'airplane', 'plane', 'aircraft'] },
  { label: 'bus', text: '🚌 버스 (bus)', keywords: ['버스', '대중교통', 'bus'] },
  { label: 'train', text: '🚆 기차 (train)', keywords: ['기차', '열차', '전철', '지하철', 'train', 'subway'] },
  { label: 'truck', text: '🚚 트럭 (truck)', keywords: ['트럭', '화물차', '트레일러', 'truck', 'lorry'] },
  { label: 'boat', text: '⛵ 배 (boat)', keywords: ['배', '보트', '선박', '요트', 'boat', 'ship', 'yacht'] },

  // === 🚦 실외 및 도로 시설물 (Outdoor) ===
  { label: 'traffic light', text: '🚥 신호등 (traffic light)', keywords: ['신호등', '교통신호', 'traffic light', 'signal'] },
  { label: 'fire hydrant', text: '🚒 소화전 (fire hydrant)', keywords: ['소화전', 'fire hydrant'] },
  { label: 'stop sign', text: '🛑 정지 표지판 (stop sign)', keywords: ['정지', '표지판', '정지 표지판', 'stop sign', 'sign'] },
  { label: 'parking meter', text: '🅿️ 주차 요금기 (parking meter)', keywords: ['주차', '요금기', '정산기', 'parking meter'] },
  { label: 'bench', text: '🪑 벤치 (bench)', keywords: ['벤치', '의자', '공원 의자', 'bench'] },

  // === 🐾 동물 (Animals) ===
  { label: 'bird', text: '🦅 새 (bird)', keywords: ['새', '참새', '독수리', '비둘기', '까마귀', '조류', 'bird', 'eagle', 'sparrow'] },
  { label: 'cat', text: '🐱 고양이 (cat)', keywords: ['고양이', '야옹이', '반려묘', 'cat', 'kitty', 'feline'] },
  { label: 'dog', text: '🐶 개 (dog)', keywords: ['개', '강아지', '멍멍이', '반려견', 'dog', 'puppy', 'hound'] },
  { label: 'horse', text: '🐴 말 (horse)', keywords: ['말', '조랑말', 'horse', 'pony'] },
  { label: 'sheep', text: '🐑 양 (sheep)', keywords: ['양', 'sheep', 'lamb'] },
  { label: 'cow', text: '🐮 소 (cow)', keywords: ['소', '얼룩소', '황소', 'cow', 'bull', 'cattle'] },
  { label: 'elephant', text: '🐘 코끼리 (elephant)', keywords: ['코끼리', 'elephant'] },
  { label: 'bear', text: '🐻 곰 (bear)', keywords: ['곰', '북극곰', '불곰', 'bear'] },
  { label: 'zebra', text: '🦓 얼룩말 (zebra)', keywords: ['얼룩말', 'zebra'] },
  { label: 'giraffe', text: '🦒 기린 (giraffe)', keywords: ['기린', 'giraffe'] },

  // === 🎒 소지품 및 액세서리 (Accessories) ===
  { label: 'backpack', text: '🎒 백팩 (backpack)', keywords: ['가방', '배낭', '백팩', '책가방', 'backpack', 'bag'] },
  { label: 'umbrella', text: '☔ 우산 (umbrella)', keywords: ['우산', '양산', 'umbrella', 'parasol'] },
  { label: 'handbag', text: '👜 핸드백 (handbag)', keywords: ['핸드백', '가방', '여성가방', 'handbag', 'purse', 'bag'] },
  { label: 'tie', text: '👔 넥타이 (tie)', keywords: ['넥타이', '타이', 'tie', 'necktie'] },
  { label: 'suitcase', text: '🧳 캐리어 (suitcase)', keywords: ['캐리어', '여행가방', '슈트케이스', 'suitcase', 'luggage'] },

  // === ⚽ 스포츠 용품 (Sports) ===
  { label: 'frisbee', text: '🥏 원반 (frisbee)', keywords: ['원반', '프리스비', 'frisbee', 'disc'] },
  { label: 'skis', text: '🎿 스키 (skis)', keywords: ['스키', 'skis', 'ski'] },
  { label: 'snowboard', text: '🏂 스노우보드 (snowboard)', keywords: ['스노우보드', '보드', 'snowboard', 'board'] },
  { label: 'sports ball', text: '⚽ 스포츠 공 (sports ball)', keywords: ['공', '축구공', '농구공', '야구공', 'ball', 'sports ball'] },
  { label: 'kite', text: '🪁 연 (kite)', keywords: ['연', '방패연', '가오리연', 'kite'] },
  { label: 'baseball bat', text: '🏏 야구 빠따 (baseball bat)', keywords: ['야구 방망이', '배트', '빠따', 'baseball bat', 'bat'] },
  { label: 'baseball glove', text: '🧤 야구 글러브 (baseball glove)', keywords: ['글러브', '야구 장갑', 'baseball glove', 'glove'] },
  { label: 'skateboard', text: '🛹 스케이트보드 (skateboard)', keywords: ['스케이트보드', '보드', 'skateboard'] },
  { label: 'surfboard', text: '🏄 서핑보드 (surfboard)', keywords: ['서핑보드', '서프보드', 'surfboard'] },
  { label: 'tennis racket', text: '🎾 테니스 라켓 (tennis racket)', keywords: ['테니스 라켓', '라켓', '채', 'tennis racket', 'racket'] },

  // === 🍽️ 주방 및 식기 (Kitchen & Dining) ===
  { label: 'bottle', text: '🍾 병 (bottle)', keywords: ['병', '물병', '술병', '페트병', 'bottle', 'flask'] },
  { label: 'wine glass', text: '🍷 와인잔 (wine glass)', keywords: ['와인잔', '유리잔', 'wine glass', 'glass'] },
  { label: 'cup', text: '☕ 컵 (cup)', keywords: ['컵', '머그컵', '종이컵', 'cup', 'mug'] },
  { label: 'fork', text: '🍴 포크 (fork)', keywords: ['포크', 'fork'] },
  { label: 'knife', text: '🔪 칼 (knife)', keywords: ['칼', '나이프', '식도', 'knife'] },
  { label: 'spoon', text: '🥄 숟가락 (spoon)', keywords: ['숟가락', '스푼', 'spoon'] },
  { label: 'bowl', text: '🥣 그릇 (bowl)', keywords: ['그릇', '대접', '사발', '볼', 'bowl', 'dish'] },

  // === 🍔 음식 (Food) ===
  { label: 'banana', text: '🍌 바나나 (banana)', keywords: ['바나나', 'banana'] },
  { label: 'apple', text: '🍎 사과 (apple)', keywords: ['사과', 'apple'] },
  { label: 'sandwich', text: '🥪 샌드위치 (sandwich)', keywords: ['샌드위치', 'sandwich'] },
  { label: 'orange', text: '🍊 오렌지 (orange)', keywords: ['오렌지', '귤', 'orange', 'tangerine'] },
  { label: 'broccoli', text: '🥦 브로콜리 (broccoli)', keywords: ['브로콜리', 'broccoli'] },
  { label: 'carrot', text: '🥕 당근 (carrot)', keywords: ['당근', 'carrot'] },
  { label: 'hot dog', text: '🌭 핫도그 (hot dog)', keywords: ['핫도그', 'hot dog'] },
  { label: 'pizza', text: '🍕 피자 (pizza)', keywords: ['피자', 'pizza'] },
  { label: 'donut', text: '🍩 도넛 (donut)', keywords: ['도넛', '도나쓰', 'donut', 'doughnut'] },
  { label: 'cake', text: '🍰 케이크 (cake)', keywords: ['케이크', '케익', 'cake'] },

  // === 🛋️ 가구 (Furniture) ===
  { label: 'chair', text: '🪑 의자 (chair)', keywords: ['의자', 'chair', 'seat'] },
  { label: 'couch', text: '🛋️ 소파 (couch)', keywords: ['소파', '쇼파', '카우치', 'couch', 'sofa'] },
  { label: 'potted plant', text: '🪴 화분 (potted plant)', keywords: ['화분', '식물', '화초', 'potted plant', 'plant'] },
  { label: 'bed', text: '🛏️ 침대 (bed)', keywords: ['침대', 'bed'] },
  { label: 'dining table', text: '🍽️ 식탁 (dining table)', keywords: ['식탁', '테이블', '책상', 'dining table', 'table', 'desk'] },
  { label: 'toilet', text: '🚽 변기 (toilet)', keywords: ['변기', '화장실', '좌변기', 'toilet', 'restroom'] },

  // === 💻 전자기기 (Electronics) ===
  { label: 'tv', text: '📺 TV (tv)', keywords: ['티비', '텔레비전', '모니터', 'tv', 'television', 'monitor'] },
  { label: 'laptop', text: '💻 노트북 (laptop)', keywords: ['노트북', '랩탑', '컴퓨터', 'laptop', 'computer', 'pc'] },
  { label: 'mouse', text: '🖱️ 마우스 (mouse)', keywords: ['마우스', 'mouse'] },
  { label: 'remote', text: '🎛️ 리모컨 (remote)', keywords: ['리모컨', '리모콘', 'remote', 'controller'] },
  { label: 'keyboard', text: '⌨️ 키보드 (keyboard)', keywords: ['키보드', '자판', 'keyboard'] },
  { label: 'cell phone', text: '📱 스마트폰 (cell phone)', keywords: ['핸드폰', '스마트폰', '휴대폰', '전화기', '폰', 'cell phone', 'mobile', 'phone', 'smartphone'] },

  // === 🏠 가전 및 실내 물품 (Appliances & Indoor) ===
  { label: 'microwave', text: '🍱 전자레인지 (microwave)', keywords: ['전자레인지', '전자렌지', 'microwave'] },
  { label: 'oven', text: '🍳 오븐 (oven)', keywords: ['오븐', 'oven'] },
  { label: 'toaster', text: '🍞 토스터 (toaster)', keywords: ['토스터', '토스트기', 'toaster'] },
  { label: 'sink', text: '🚰 싱크대 (sink)', keywords: ['싱크대', '개수대', '세면대', 'sink', 'washbasin'] },
  { label: 'refrigerator', text: '🧊 냉장고 (refrigerator)', keywords: ['냉장고', 'refrigerator', 'fridge'] },
  { label: 'book', text: '📖 책 (book)', keywords: ['책', '도서', '서적', 'book'] },
  { label: 'clock', text: '⏰ 시계 (clock)', keywords: ['시계', '벽시계', '손목시계', 'clock', 'watch'] },
  { label: 'vase', text: '🏺 꽃병 (vase)', keywords: ['꽃병', '화병', 'vase'] },
  { label: 'scissors', text: '✂️ 가위 (scissors)', keywords: ['가위', 'scissors'] },
  { label: 'teddy bear', text: '🧸 곰인형 (teddy bear)', keywords: ['곰인형', '테디베어', '인형', 'teddy bear', 'doll'] },
  { label: 'hair drier', text: '💨 헤어 드라이어 (hair drier)', keywords: ['드라이기', '헤어 드라이어', 'hair drier', 'dryer'] },
  { label: 'toothbrush', text: '🪥 칫솔 (toothbrush)', keywords: ['칫솔', '양치', 'toothbrush'] }
];