# adiFit Demo Video Script

Target length: 2:45-3:00

Demo URL: `http://localhost:8521`

Recommended demo input:

- Product: `삼바 OG`
- Usual size: `260`
- Width: `넓음`
- Question: `평소 260 신고 발볼 넓은데 정사이즈로 사도 될까요?`

## 0:00-0:15 Opening

Action: show the app header and sidebar.

Narration:

안녕하세요. 제가 구현한 솔루션은 `adiFit`입니다.

adiFit은 상품 리뷰를 AI로 분석해 사이즈, 착용감, 색상/디자인, 사용 용도, VOC 이슈를 구조화하고, 소비자용 핏 어드바이저와 내부 대시보드로 보여주는 리뷰 인텔리전스 프로토타입입니다.

## 0:15-0:35 Data and System Overview

Action: point to sidebar product selector and backend caption.

Narration:

현재 데모는 Ultraboost Light, Samba OG, Adizero Adios Pro 3의 리뷰 24건을 사용합니다.

백엔드는 Gemini structured output으로 리뷰를 구조화하고, Gemini embedding으로 검색과 클러스터링을 수행합니다.

## 0:35-1:15 Fit Advisor

Action:

1. Select `삼바 OG`.
2. Enter usual size `260`.
3. Select width `넓음`.
4. Enter the recommended demo question.
5. Click `사이즈 추천 받기`.

Narration:

먼저 소비자 관점의 핏 어드바이저입니다.

평소 260을 신고 발볼이 넓은 고객이 Samba OG를 정사이즈로 사도 되는지 질문해 보겠습니다.

결과를 보면 앱은 일반적인 답변을 생성하는 것이 아니라, 검색된 리뷰 근거를 바탕으로 사이즈 조언을 제공합니다.

아래에는 답변에 사용된 review_id와 원문 인용이 표시됩니다. 이 구조를 통해 LLM이 근거 밖 내용을 추측하지 않도록 제한했습니다.

## 1:15-1:50 Merchandiser Dashboard

Action: open `머천다이저 대시보드` tab.

Narration:

다음은 내부 머천다이저 대시보드입니다.

상품별 리뷰 수, 평균 평점, 사이즈 결론, 발볼 결론을 확인할 수 있고, 속성별 감성과 사이즈 신호 분포도 함께 볼 수 있습니다.

Samba OG의 경우 사이즈 업과 발볼 리스크가 반복적으로 나타나기 때문에, PDP에 반 치수 크게 신으라는 안내를 노출하라는 액션이 생성됩니다.

즉, 리뷰 분석 결과가 단순 요약에서 끝나지 않고 실제 상품 페이지 개선 액션으로 연결됩니다.

## 1:50-2:10 Product Comparison

Action: open `상품 비교` tab.

Narration:

상품 비교 탭에서는 세 상품의 사이즈 신호와 평균 평점, 대표 이슈를 나란히 비교할 수 있습니다.

어떤 상품이 정사이즈에 가까운지, 어떤 상품에서 사이즈 업 리스크가 높은지 빠르게 판단할 수 있습니다.

## 2:10-2:40 Segments and Trend

Action: open `세그먼트 & 트렌드` tab.

Narration:

다음은 리뷰 세그먼트와 VOC 트렌드입니다.

리뷰 embedding을 KMeans로 클러스터링하고, LLM이 추출한 사용 용도, 착용감, 디자인/색상, VOC 태그를 사용해 각 세그먼트를 해석합니다.

예를 들어 Comfort-driven Buyers, Wide-foot Fit Risk, Performance Runners처럼 고객 사용 맥락별 그룹을 볼 수 있습니다.

아래 월별 차트는 fit risk, durability, delivery, price resistance 같은 VOC 이슈가 시간에 따라 어떻게 움직이는지 보여줍니다.

## 2:40-3:00 Validation and Close

Action: open `검증` tab.

Narration:

마지막으로 검증 탭입니다.

직접 라벨링한 24개 리뷰 기준 size signal 추출 정확도는 95.8%입니다.

또한 답변이 실제 검색 근거 안의 review_id를 인용하는지 citation coverage를 계산합니다.

정리하면, adiFit은 리뷰를 구조화하고, 근거 기반 답변과 내부 VOC 액션, 고객 세그먼트와 트렌드 분석까지 연결하는 working AI prototype입니다.
