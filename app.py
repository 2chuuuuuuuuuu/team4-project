import streamlit as st
import google.generativeai as genai

# ==========================================
# 0. API 키 설정 및 Gemini 모델 초기화
# ==========================================
if "GEMINI_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    GOOGLE_API_KEY = ""

genai.configure(api_key=GOOGLE_API_KEY)

@st.cache_resource
def load_gemini_model():
    if not GOOGLE_API_KEY:
        return None
    candidate_models = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.0-flash"]
    for model_name in candidate_models:
        try:
            test_model = genai.GenerativeModel(model_name)
            test_model.generate_content("H", generation_config={"max_output_tokens": 1})
            return test_model
        except Exception:
            continue
    return None

model = load_gemini_model()

# ==========================================
# 1. 페이지 기본 설정 및 스타일 (UI/UX)
# ==========================================
st.set_page_config(page_title="팀 프로젝트 역할 추천 서비스", page_icon="🧩", layout="centered")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght=400;600;700;800&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Pretendard', sans-serif; }
    .main-title { font-size: 28px; font-weight: 800; color: #27AE60 !important; text-align: center; margin-bottom: 8px; }
    .subtitle { font-size: 14px; color: #8A95A5 !important; text-align: center; margin-bottom: 30px; }
    .report-card { background-color: #FFFFFF !important; border-left: 6px solid #27AE60 !important; border-top: 1px solid #E2E8F0 !important; border-right: 1px solid #E2E8F0 !important; border-bottom: 1px solid #E2E8F0 !important; border-radius: 8px !important; padding: 20px !important; margin: 20px 0 !important; }
    .report-card p, .report-card span, .report-card b { color: #1E293B !important; }
    
    /* AI 말풍선 스타일: 가독성을 위해 흰색 배경 테마에서도 글자가 아주 진하고 또렷하게 나오도록 고정 */
    .ai-bubble { background-color: #F4FBF7 !important; border: 1px dashed #27AE60 !important; padding: 18px !important; border-radius: 10px !important; font-size: 14px !important; line-height: 1.6 !important; margin-top: 15px !important; color: #1E293B !important; }
    .ai-bubble p, .ai-bubble span, .ai-bubble div, .ai-bubble li, .ai-bubble b { color: #1E293B !important; }
</style>
""", unsafe_allow_html=True)

questions = [
    {"id": "q1", "category": "analysis", "q": "Q1. 새로운 아이디어를 자주 떠올리는 편이다.", "reverse": False},
    {"id": "q2", "category": "analysis", "q": "Q2. 복잡한 문제를 구조적으로 나누어 생각할 수 있다.", "reverse": False},
    {"id": "q3", "category": "analysis", "q": "Q3. 여러 정보를 비교하고 논리적으로 정리하는 데 익숙하다.", "reverse": False},
    {"id": "q4", "category": "analysis", "q": "Q4. 팀원들의 의견을 조율하고 명확한 방향을 제시할 수 있다.", "reverse": False},
    {"id": "q5", "category": "analysis", "q": "Q5. [역문항] 프로젝트 기획이나 새로운 아이디어를 제안하는 것이 다소 부담스럽다.", "reverse": True},
    {"id": "q6", "category": "coding", "q": "Q6. 파이썬 등 프로그래밍 언어를 사용해본 경험이 있다.", "reverse": False},
    {"id": "q7", "category": "coding", "q": "Q7. 코드나 시스템 오류가 발생했을 때 스스로 해결하려고 끝까지 시도한다.", "reverse": False},
    {"id": "q8", "category": "coding", "q": "Q8. 새로운 소프트웨어 툴이나 최신 기술을 배우는 것이 어렵지 않다.", "reverse": False},
    {"id": "q9", "category": "coding", "q": "Q9. AI 도구(ChatGPT 등)를 개발이나 문제 해결 환경에 적극적으로 활용한다.", "reverse": False},
    {"id": "q10", "category": "coding", "q": "Q10. [역문항] 알고리즘이나 컴퓨터 공학적 개념을 이해하는 것이 어렵게 느껴진다.", "reverse": True},
    {"id": "q11", "category": "design", "q": "Q11. 색상 조합이나 레이아웃 구성을 시각적으로 조화롭게 할 수 있다.", "reverse": False},
    {"id": "q12", "category": "design", "q": "Q12. Figma, Canva, Photoshop 등의 디자인 도구를 다루어 본 적 있다.", "reverse": False},
    {"id": "q13", "category": "design", "q": "Q13. 독창적인 표현이나 추상적인 아이디어를 시각화하여 구현할 수 있다.", "reverse": False},
    {"id": "q14", "category": "design", "q": "Q14. 디자인 요소의 작은 디테일(정렬, 폰트 크기, 간격 등)에 신경 쓰는 편이다.", "reverse": False},
    {"id": "q15", "category": "design", "q": "Q15. [역문항] 발표 자료나 결과물의 시각적인 완성도(디자인)는 크게 중요하지 않다고 생각한다.", "reverse": True},
    {"id": "q16", "category": "presentation", "q": "Q16. 내 의견과 지식을 다른 사람에게 명확하고 조리 있게 설명할 수 있다.", "reverse": False},
    {"id": "q17", "category": "presentation", "q": "Q17. 여러 청중이나 사람들 앞에서 서서 말하는 것이 크게 부담되지 않는다.", "reverse": False},
    {"id": "q18", "category": "presentation", "q": "Q18. 복잡한 발표 자료의 핵심 내용을 논리적으로 요약하여 전달할 수 있다.", "reverse": False},
    {"id": "q19", "category": "presentation", "q": "Q19. 스피치 도중 청중의 실시간 반응을 보면서 템포나 설명을 조절할 수 있다.", "reverse": False},
    {"id": "q20", "category": "presentation", "q": "Q20. [역문항] 팀 프로젝트 등에서 공식적인 발표나 모임 진행을 맡는 것을 피하는 편이다.", "reverse": True}
]

if "page" not in st.session_state:
    st.session_state.page = "start"
if "user_info" not in st.session_state:
    st.session_state.user_info = {}

# ==========================================
# 2. 화면 라우팅 분기 조절
# ==========================================

if st.session_state.page == "start":
    st.markdown("<div class='main-title'>🧩 팀 프로젝트 역할 자동 추천 서비스</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>대학생 맞춤형 팀 빌딩 및 AI 역할 분배 자동화 시스템 (4조)</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("시작하기", use_container_width=True):
            st.session_state.page = "info"
            st.rerun()

elif st.session_state.page == "info":
    st.markdown("<h2 style='text-align: center; color: #2ECC71;'>👤 1단계: 사용자 정보 입력</h2>", unsafe_allow_html=True)
    with st.form("info_form"):
        name = st.text_input("이름", placeholder="예: 홍길동")
        student_id = st.text_input("학번", placeholder="예: 202612345")
        preferred_role = st.selectbox("선호 역할", ["기획", "개발", "디자인", "발표"])
        submit_info = st.form_submit_button("설문 시작하기")
        if submit_info:
            if not name.strip() or not student_id.strip():
                st.error("⚠️ 이름과 학번을 모두 입력해주세요!")
            else:
                st.session_state.user_info = {"name": name, "id": student_id, "preferred_role": preferred_role}
                st.session_state.page = "survey"
                st.rerun()

elif st.session_state.page == "survey":
    st.markdown("<h2 style='text-align: center; color: #2ECC71;'>📋 2단계: 역량 진단 설문</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #8A95A5;'>{st.session_state.user_info['name']}님의 프로젝트 성향을 정밀 분석합니다.</p>", unsafe_allow_html=True)
    
    options = ["선택 안 함", "전혀 아니다", "아니다", "보통이다", "그렇다", "매우 그렇다"]
    
    with st.form("survey_main_form"):
        responses = {}
        for item in questions:
            st.markdown(f"**{item['q']}**")
            responses[item['id']] = st.radio(
                f"label_{item['id']}", 
                options, 
                index=0, 
                horizontal=True, 
                key=f"radio_{item['id']}",
                label_visibility="collapsed"
            )
            st.markdown("<hr style='margin:10px 0; border:none; border-top:1px solid #F1F5F9;'>", unsafe_allow_html=True)
            
        submit_survey = st.form_submit_button("결과 분석하기", use_container_width=True)
        
        if submit_survey:
            raw_answers = [responses[item['id']] for item in questions]
            missing_questions = [item['q'].split('.')[0] for item in questions if responses[item['id']] == "선택 안 함"]
            answered_selections = [ans for ans in raw_answers if ans != "선택 안 함"]
            
            is_all_one = all(ans == "전혀 아니다" for ans in answered_selections) if answered_selections else False
            is_all_five = all(ans == "매우 그렇다" for ans in answered_selections) if answered_selections else False
            
            if missing_questions:
                st.error(f"❌ [필수 응답 오류] 아직 답변하지 않은 문항이 있습니다. ({', '.join(missing_questions)})")
                st.stop()
                
            elif is_all_one or is_all_five:
                st.error("⚠️ 불성실 응답 패턴 감지: 모든 문항에 동일한 극단적 답변('전혀 아니다' 또는 '매우 그렇다')을 마킹하셨습니다. 정확한 AI 분석이 불가능하므로 결과 화면 진입이 완전히 차단되었습니다. 정상적인 답변으로 수정 후 다시 시도해주세요.")
                st.stop()
                
            else:
                score_map = {"전혀 아니다": 1, "아니다": 2, "보통이다": 3, "그렇다": 4, "매우 그렇다": 5}
                reverse_score_map = {"전혀 아니다": 5, "아니다": 4, "보통이다": 3, "그렇다": 2, "매우 그렇다": 1}
                category_scores = {"analysis": [], "coding": [], "design": [], "presentation": []}
                
                for item in questions:
                    val_string = responses[item['id']]
                    if item['reverse']: score = reverse_score_map[val_string]
                    else: score = score_map[val_string]
                    category_scores[item['category']].append(score)
                    
                st.session_state.category_scores = category_scores
                st.session_state.page = "result"
                st.rerun()

elif st.session_state.page == "result":
    if "category_scores" not in st.session_state:
        st.session_state.page = "survey"
        st.rerun()
        
    user = st.session_state.user_info
    cat_scores = st.session_state.category_scores
    
    def get_avg(cat):
        vals = cat_scores.get(cat, [])
        return sum(vals) / len(vals) if vals else 3.0
        
    avg_analysis = get_avg("analysis")
    avg_coding = get_avg("coding")
    avg_design = get_avg("design")
    avg_presentation = get_avg("presentation")
    
    scores = {
        "기획": (avg_analysis * 1.5) + (avg_presentation * 0.5), 
        "개발": (avg_coding * 1.6) + (avg_analysis * 0.4),      
        "디자인": (avg_design * 2.0),                            
        "발표": (avg_presentation * 1.4) + (avg_analysis * 0.6) 
    }
    pure_recommended = max(scores, key=scores.get)
    final_role = user['preferred_role'] 
    
    st.markdown(f"<h2 style='text-align: center; color: #2ECC71;'>🏆 {user['name']}님의 정밀 역할 진단 리포트</h2>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class='report-card'>
        <p>📌 <b>학번:</b> {user['id']}</p>
        <p>📌 <b>선호 역할:</b> {user['preferred_role']}</p>
        <p>📌 <b>데이터 기반 추천 역할:</b> {pure_recommended}</p>
        <hr style='border:none; border-top: 1px solid #E2E8F0; margin: 12px 0;'>
        <p style='font-size: 16px;'>🎯 <b>최종 매칭 팀 역할:</b> <span style='color:#27AE60; font-weight:bold;'>{final_role}</span></p>
    </div>
    """, unsafe_allow_html=True)
    
    loading_placeholder = st.empty()
    loading_placeholder.text("AI 심층적 팀 내 포지셔닝 분석 중...")
    
    if model is None:
        ai_text = f"사용자의 성향과 의지를 종합 분석하여 최종적으로 [{final_role}] 역할을 부여합니다."
    else:
        # 🚨 [질문자님 피드백 완벽 반영]: 뻔한 점수 나열은 초반 도입부에만 팩트로 쾅 박아두고, 본론에서는 '실제 팀 내 협업 행동 패턴' 및 '구체적 조언'을 쏟아내도록 프롬프트 정밀 설계
        prompt = (
            f"대학생 팀 프로젝트 성향 진단 결과에 대해 '실질적인 팀 내 협업 행동 조언'을 담은 전문가 소견서를 작성해라.\n"
            f"사용자 이름: {user['name']}\n"
            f"사용자 선호 역할: {user['preferred_role']}\n"
            f"데이터 분석 추천 역할: {pure_recommended}\n"
            f"최종 매칭된 직무: {final_role}\n\n"
            f"부문별 실제 평점:\n"
            f"- 기획/분석: {avg_analysis:.1f}점, 개발/기술: {avg_coding:.1f}점, 시각디자인: {avg_design:.1f}점, 발표/커뮤니케이션: {avg_presentation:.1f}점\n\n"
            f"작성 구조 지침:\n"
            f"1. 도입부: '{user['name']}님, 평점 분석 결과 ~성향이 {max([avg_analysis, avg_coding, avg_design, avg_presentation]):.1f}점으로 가장 우수하여 최종적으로 [{final_role}] 역할을 맡는 것이 입증되었습니다.' 수준으로 데이터 연동 사실만 깔끔히 짚고 빠르게 넘어갈 것.\n"
            f"2. 핵심 본론 (AI가 반드시 해야 하는 구체적인 팀 플레이 분석):\n"
            f"   - 단순 직무 정의가 아니라, 이 사용자가 '실제 팀 미팅이나 과제 수행 과정에서 어떤 독보적인 무기가 될 수 있는지' 행동 패턴 위주로 조언을 작성해라.\n"
            f"   - 예시: 개발을 원했으나 디자인이 높게 나온 경우 -> '기술적 로직을 이해하는 디자이너이므로 개발팀의 무리한 요구와 기획팀의 추상적인 요구 사이에서 완벽한 가교 역할을 수행하며 팀의 병목현상을 해결할 수 있습니다'와 같은 구체적 조언 덧붙이기.\n"
            f"   - 기획을 원했으나 발표가 높은 경우 -> '논리적 구조화 능력이 탑재된 스피커이므로, 단순히 말만 잘하는 게 아니라 팀원들의 복잡한 아이디어를 명확하게 압축해 교수님과 청중에게 꽂히게 만드는 최종 병기 역할을 해야 합니다'와 같은 조언 덧붙이기.\n"
            f"3. 결론: 해당 역할을 수행할 때 팀 전체의 퀄리티와 시너지가 어떻게 극대화되는지 명확한 비전을 제시하며 4~5줄 수준의 깊이 있고 프로페셔널한 문장으로 결론지을 것."
        )
        try:
            response = model.generate_content(prompt)
            ai_text = f"{response.text}"
        except Exception as e:
            ai_text = f"⚠️ AI 소견서 로드 실패: {e}"
            
    loading_placeholder.empty()
    st.markdown(f"<div class='ai-bubble'>{ai_text}</div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("다시 진단하기", use_container_width=True):
        st.session_state.page = "start"
        st.session_state.user_info = {}
        if "category_scores" in st.session_state:
            del st.session_state.category_scores
        st.rerun()
