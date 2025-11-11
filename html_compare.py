import streamlit as st
from .core_logic import HTMLComparator


def create_file_upload_section():
    """파일 업로드 섹션 UI 생성"""
    col1, col2 = st.columns(2)
    with col1:
        before_file = st.file_uploader("📄 원본 HTML", type=["html","htm"], key="before")
    with col2:
        after_file = st.file_uploader("📄 수정된 HTML", type=["html","htm"], key="after")
    
    return before_file, after_file

def display_html_structure_highlighting(comparator, before, after, changes, context_window=50, search_tolerance=50):
    """HTML 구조 보존 하이라이팅 모드 표시"""
    st.write("💡 원본 HTML과 수정된 HTML을 나란히 표시하고, 변경된 부분을 색상으로 구분합니다.")
    
    # 하이라이팅 실행 및 결과 표시
    with st.spinner("변경사항을 탐색 중입니다..."):
        html_with_highlighting = comparator.create_html_with_highlighting(before, after, changes, search_tolerance, context_window)
    
    st.components.v1.html(html_with_highlighting, height=800, scrolling=True)

def HTML_COMPARE():
    """메인 스트림릿 애플리케이션"""
    # 페이지 설정
    st.set_page_config(page_title="HTML 문서 비교 도구", layout="wide")
    st.title("🔧 HTML 문서 비교 도구")
    
    # 하드코딩된 설정 값
    context_window = 400  # 컨텍스트 시각화 범위 (±문자)
    search_tolerance = 400  # 위치 필터링 허용 오차 (±문자)
    
    # HTMLComparator 인스턴스 생성
    comparator = HTMLComparator()
    
    # 파일 업로드 섹션
    before_file, after_file = create_file_upload_section()
    
    # 파일이 모두 업로드된 경우 처리
    if before_file and after_file:
        try:
            # 파일 로드
            before = comparator.load_file(before_file)
            after = comparator.load_file(after_file)
                    
            # 비교 실행 버튼
            if st.button("🔍 비교 실행", type="primary"):
                with st.spinner("문서를 분석하고 있습니다..."):
                    changes = comparator.analyze_changes(before, after)
                
                # 하이라이팅 결과를 changes에 추가
                with st.spinner("하이라이팅을 적용하고 있습니다..."):
                    # 하이라이팅은 display_html_structure_highlighting에서 한 번만 실행
                    pass
                
                display_html_structure_highlighting(comparator, before, after, changes, context_window, search_tolerance)
                    
        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")


