# adiFit Demo Video Script

Target length: within 3 minutes

## 0:00-0:20 Opening

안녕하세요. 제가 구현한 솔루션은 `adiFit`입니다.

adiFit은 adidas eCommerce 상품 리뷰를 AI로 분석해 사이즈, 착용감, 색상/디자인, 사용 용도, VOC 이슈를 구조화하고, 이를 소비자용 핏 어드바이저와 내부 머천다이저 대시보드로 보여주는 리뷰 인텔리전스 프로토타입입니다.

## 0:20-0:40 App Overview

앱은 Streamlit으로 구현했습니다.

왼쪽에서 상품을 선택할 수 있고, 현재 데모 데이터는 Ultraboost Light, Samba OG, Adizero Adios Pro 3의 직접 정의한 리뷰 24건입니다.

백엔드는 Gemini structured output과 Gemini embedding을 사용합니다.

## 0:40-1:20 Fit Advisor Demo

먼저 소비자 관점의 핏 어드바이저를 보겠습니다.

상품은 `Samba OG`를 선택하고, 평소 사이즈는 `260`, 발볼은 `넓음`으로 입력합니다.

질문은 다음과 같이 넣겠습니다.

> 평소 260 신고 발볼 넓은데 정사이즈로 사도 될까요?

결과를 보면, 앱은 단순히 일반적인 답변을 생성하지 않고 검색된 리뷰 근거에 기반해 사이즈 업을 추천합니다.

아래에는 실제로 근거가 된 review_id와 원문 인용이 표시됩니다.

핵심은 LLM이 임의로 추측하지 않도록 검색된 리뷰 안에서만 답하게 하고, 모든 핵심 판단에 citation을 붙이도록 제한했다는 점입니다.

## 1:20-1:55 Merchandiser Dashboard

다음은 내부 머천다이저 대시보드입니다.

여기서는 리뷰 수, 평균 평점, 사이즈 결론, 발볼 결론을 볼 수 있습니다.

Samba OG의 경우 사이즈 관련 리뷰가 대부분 사이즈 업을 권장하고, 발볼이 좁다는 신호도 함께 나타납니다.

아래 실행 제안에서는 PDP 사이즈 영역에 `정사이즈보다 반 치수 크게` 안내를 노출하라는 액션이 생성됩니다.

이렇게 리뷰 분석 결과를 단순 요약에서 끝내지 않고, 실제 PDP 개선이나 반품 감소 액션으로 연결했습니다.

## 1:55-2:15 Product Comparison

상품 비교 탭에서는 세 상품을 나란히 비교할 수 있습니다.

어떤 상품이 정사이즈인지, 어떤 상품에서 사이즈 업 비중이 높은지, 평균 평점과 대표 이슈가 무엇인지 한눈에 볼 수 있습니다.

## 2:15-2:45 Segment & Trend

다음은 제 연구 강점을 반영한 세그먼트와 트렌드 분석입니다.

리뷰 embedding을 KMeans로 클러스터링하고 PCA로 시각화했습니다.

LLM이 추출한 사용 용도, 착용감, 디자인/색상, VOC 태그를 사용해 세그먼트를 해석합니다.

예를 들어 `Comfort-driven Buyers`, `Wide-foot Fit Risk`, `Performance Runners` 같은 고객 사용 맥락 그룹이 생성됩니다.

아래 시계열 차트는 월별 VOC 이슈와 사용 맥락 태그 변화를 보여줍니다.

현재는 데모 샘플이라 규모가 작지만, 실제 운영 리뷰 수천 건에 연결하면 VOC spike나 고객 세그먼트 drift를 추적하는 구조로 확장할 수 있습니다.

## 2:45-3:00 Validation & Closing

마지막으로 검증 탭입니다.

직접 라벨링한 24개 리뷰 기준 size signal 추출 정확도는 95.8%입니다.

또한 어드바이저 답변은 인용한 review_id가 실제 검색 근거에 있는지 citation coverage를 계산합니다.

정리하면, adiFit은 단순 리뷰 요약이 아니라 리뷰를 구조화하고, 근거 기반 답변과 내부 VOC 액션, 세그먼트/트렌드 분석까지 연결하는 working AI prototype입니다.
