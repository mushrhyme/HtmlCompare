import streamlit as st
from core_logic import HTMLComparator
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def create_file_upload_section():
    """파일 업로드 섹션 UI 생성"""
    col1, col2 = st.columns(2)
    with col1:
        before_file = st.file_uploader("📄 원본 HTML", type=["html","htm"], key="before")
    with col2:
        after_file = st.file_uploader("📄 수정된 HTML", type=["html","htm"], key="after")
    
    return before_file, after_file

def html_to_pdf(html_content):
    """HTML 콘텐츠를 PDF로 변환"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(html_content, wait_until="networkidle")
            pdf_bytes = page.pdf(
                format="A4",
                print_background=True,  # 배경색 포함 (하이라이팅 색상 표시)
                margin={"top": "20mm", "right": "20mm", "bottom": "20mm", "left": "20mm"}
            )
            browser.close()
            return pdf_bytes
    except Exception as e:
        raise Exception(f"PDF 변환 오류: {str(e)}")

def display_changes_summary(changes, show_highlighting_results=False):
    """변경사항 요약을 표로 표시 (디버깅용)"""
    if show_highlighting_results:
        st.subheader("📊 변경사항 요약 (매핑 후)")
    else:
        st.subheader("📊 변경사항 요약 (매핑 전)")
    
    if not changes:
        st.info("변경사항이 없습니다.")
        return
    
    # 통계 정보
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("총 변경사항", len(changes))
    with col2:
        deleted = sum(1 for c in changes if c.get("status") == "delete")
        st.metric("삭제", deleted, delta=None)
    with col3:
        inserted = sum(1 for c in changes if c.get("status") == "insert")
        st.metric("추가", inserted, delta=None)
    with col4:
        replaced = sum(1 for c in changes if c.get("status") == "replace")
        st.metric("변경", replaced, delta=None)
    with col5:
        if show_highlighting_results:
            highlighted = sum(1 for c in changes if c.get("highlighting_result", {}).get("before_highlighted") or c.get("highlighting_result", {}).get("after_highlighted"))
            st.metric("하이라이팅 성공", highlighted, delta=None)
    
    # 변경사항 상세 표
    st.write("---")
    st.write("### 📋 변경사항 상세")
    
    # 확장 가능한 섹션으로 각 변경사항 표시
    for idx, change in enumerate(changes):
        status = change.get("status", "unknown")
        before_text = " ".join(change.get("before", []))
        after_text = " ".join(change.get("after", []))
        
        # 상태별 색상 및 아이콘
        status_info = {
            "delete": ("🔴 삭제됨", "red"),
            "insert": ("🟢 추가됨", "green"),
            "replace": ("🟡 변경됨", "orange")
        }
        status_label, status_color = status_info.get(status, ("❓ 알 수 없음", "gray"))
        
        with st.expander(f"{idx+1}. {status_label} - 변경사항 #{idx+1}", expanded=(idx < 3)):  # 처음 3개는 기본 확장
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**원본 텍스트:**")
                if before_text:
                    st.code(before_text, language=None)
                else:
                    st.info("(비어있음)")
                
                # 컨텍스트 정보
                if change.get("before_context_before") or change.get("before_context_after"):
                    st.markdown("**앞뒤 컨텍스트:**")
                    context_before = " ".join(change.get("before_context_before", []))
                    context_after = " ".join(change.get("before_context_after", []))
                    if context_before:
                        st.caption(f"앞: ...{context_before}")
                    if context_after:
                        st.caption(f"뒤: {context_after}...")
            
            with col2:
                st.markdown(f"**수정된 텍스트:**")
                if after_text:
                    st.code(after_text, language=None)
                else:
                    st.info("(비어있음)")
                
                # 컨텍스트 정보
                if change.get("after_context_before") or change.get("after_context_after"):
                    st.markdown("**앞뒤 컨텍스트:**")
                    context_before = " ".join(change.get("after_context_before", []))
                    context_after = " ".join(change.get("after_context_after", []))
                    if context_before:
                        st.caption(f"앞: ...{context_before}")
                    if context_after:
                        st.caption(f"뒤: {context_after}...")
            
            # 위치 정보
            if change.get("before_position") or change.get("after_position"):
                st.markdown("**위치 정보:**")
                pos_info = []
                if change.get("before_position"):
                    pos_info.append(f"원본: {change['before_position']}")
                if change.get("after_position"):
                    pos_info.append(f"수정본: {change['after_position']}")
                st.caption(" | ".join(pos_info))
            
            # 🆕 하이라이팅 결과 시각화
            if show_highlighting_results and change.get("highlighting_result"):
                highlighting_result = change["highlighting_result"]
                debug_info = highlighting_result.get("debug_info", {})
                
                st.write("---")
                st.markdown("### 🎯 매칭 결과")
                
                # 원본 매칭 결과
                if change.get("status") in ["delete", "replace"]:
                    st.markdown("#### 📄 원본 HTML 매칭")
                    before_success = highlighting_result.get("before_highlighted", False)
                    before_debug = debug_info
                    
                    if before_success:
                        st.success(f"✅ 매칭 성공")
                        
                        # 매칭된 텍스트
                        matched_text = before_debug.get("matched_text_content")
                        if matched_text:
                            st.markdown("**매칭된 텍스트:**")
                            st.code(matched_text[:200] + ("..." if len(matched_text) > 200 else ""), language=None)
                        
                        # 점수 정보
                        col_score1, col_score2, col_score3 = st.columns(3)
                        with col_score1:
                            basic_sim = before_debug.get("basic_similarity", 0)
                            st.metric("기본 유사도", f"{basic_sim:.3f}")
                        with col_score2:
                            context_score = before_debug.get("context_score", 0)
                            st.metric("컨텍스트 점수", f"{context_score:.3f}")
                        with col_score3:
                            final_score = before_debug.get("final_score", 0)
                            st.metric("최종 점수", f"{final_score:.3f}")
                        
                        # 찾는 컨텍스트 vs 실제 컨텍스트
                        st.markdown("**컨텍스트 비교:**")
                        context_before = before_debug.get("context_before")
                        context_after = before_debug.get("context_after")
                        
                        # validation 정보가 있으면 표시
                        validation = before_debug.get("validation")
                        if validation:
                            col_ctx1, col_ctx2 = st.columns(2)
                            with col_ctx1:
                                st.markdown("**앞 컨텍스트:**")
                                if context_before:
                                    st.caption(f"🔍 찾는 것: ...{context_before[:50]}")
                                actual_before = validation.get("actual_before_context", "")
                                if actual_before:
                                    before_match = validation.get("before_match")
                                    match_icon = "✅" if before_match else "❌"
                                    before_score = validation.get("before_score", 0)
                                    st.caption(f"{match_icon} 실제 것: ...{actual_before[-50:]}")
                                    st.caption(f"   점수: {before_score:.3f} {'(통과)' if before_match else '(실패)'}")
                            
                            with col_ctx2:
                                st.markdown("**뒤 컨텍스트:**")
                                if context_after:
                                    st.caption(f"🔍 찾는 것: {context_after[:50]}...")
                                actual_after = validation.get("actual_after_context", "")
                                if actual_after:
                                    after_match = validation.get("after_match")
                                    match_icon = "✅" if after_match else "❌"
                                    after_score = validation.get("after_score", 0)
                                    st.caption(f"{match_icon} 실제 것: {actual_after[:50]}...")
                                    st.caption(f"   점수: {after_score:.3f} {'(통과)' if after_match else '(실패)'}")
                        else:
                            # validation 정보가 없으면 기본 컨텍스트만 표시
                            if context_before:
                                st.caption(f"앞: ...{context_before[:50]}")
                            if context_after:
                                st.caption(f"뒤: {context_after[:50]}...")
                        
                        # 매칭된 HTML 컨텍스트
                        matched_html_ctx = before_debug.get("matched_html_context")
                        if matched_html_ctx:
                            with st.expander("📋 매칭된 HTML 컨텍스트", expanded=False):
                                st.code(matched_html_ctx[:500] + ("..." if len(matched_html_ctx) > 500 else ""), language="html")
                    else:
                        st.error("❌ 매칭 실패")
                        error_info = before_debug.get("error")
                        if error_info:
                            st.caption(f"**오류:** {error_info}")
                            
                            # 🆕 컨텍스트 검증 실패인 경우 상세 정보 표시
                            if error_info == "컨텍스트 검증 실패":
                                validation = before_debug.get("validation", {})
                                if validation:
                                    st.markdown("**🔍 컨텍스트 검증 상세 정보:**")
                                    
                                    col_err1, col_err2 = st.columns(2)
                                    
                                    with col_err1:
                                        st.markdown("**앞 컨텍스트:**")
                                        context_before = before_debug.get("context_before")
                                        if context_before:
                                            st.caption(f"🔍 찾는 것: ...{context_before[:80]}")
                                        actual_before = validation.get("actual_before_context", "")
                                        if actual_before:
                                            before_match = validation.get("before_match", False)
                                            before_score = validation.get("before_score", 0)
                                            match_icon = "✅" if before_match else "❌"
                                            st.caption(f"{match_icon} 실제 것: ...{actual_before[-80:]}")
                                            st.caption(f"   점수: {before_score:.3f} / 0.5 (필요) {'✅ 통과' if before_match else '❌ 실패'}")
                                    
                                    with col_err2:
                                        st.markdown("**뒤 컨텍스트:**")
                                        context_after = before_debug.get("context_after")
                                        if context_after:
                                            st.caption(f"🔍 찾는 것: {context_after[:80]}...")
                                        actual_after = validation.get("actual_after_context", "")
                                        if actual_after:
                                            after_match = validation.get("after_match", False)
                                            after_score = validation.get("after_score", 0)
                                            match_icon = "✅" if after_match else "❌"
                                            st.caption(f"{match_icon} 실제 것: {actual_after[:80]}...")
                                            st.caption(f"   점수: {after_score:.3f} / 0.5 (필요) {'✅ 통과' if after_match else '❌ 실패'}")
                                    
                                    # 매칭된 텍스트 정보
                                    matched_text = before_debug.get("matched_text_content")
                                    if matched_text:
                                        st.markdown("**매칭된 텍스트:**")
                                        st.code(matched_text[:200] + ("..." if len(matched_text) > 200 else ""), language=None)
                                    
                                    # 점수 정보
                                    col_score1, col_score2, col_score3 = st.columns(3)
                                    with col_score1:
                                        basic_sim = before_debug.get("basic_similarity", 0)
                                        st.metric("기본 유사도", f"{basic_sim:.3f}")
                                    with col_score2:
                                        context_score = before_debug.get("context_score", 0)
                                        st.metric("컨텍스트 점수", f"{context_score:.3f}")
                                    with col_score3:
                                        final_score = before_debug.get("final_score", 0)
                                        st.metric("최종 점수", f"{final_score:.3f}")
                
                # 수정본 매칭 결과
                if change.get("status") in ["insert", "replace"]:
                    st.markdown("#### 📝 수정본 HTML 매칭")
                    after_success = highlighting_result.get("after_highlighted", False)
                    after_debug = debug_info.get("after_debug_info", {}) if change.get("status") == "replace" else debug_info
                    
                    if after_success:
                        st.success(f"✅ 매칭 성공")
                        
                        # 매칭된 텍스트
                        matched_text = after_debug.get("matched_text_content")
                        if matched_text:
                            st.markdown("**매칭된 텍스트:**")
                            st.code(matched_text[:200] + ("..." if len(matched_text) > 200 else ""), language=None)
                        
                        # 점수 정보
                        col_score1, col_score2, col_score3 = st.columns(3)
                        with col_score1:
                            basic_sim = after_debug.get("basic_similarity", 0)
                            st.metric("기본 유사도", f"{basic_sim:.3f}")
                        with col_score2:
                            context_score = after_debug.get("context_score", 0)
                            st.metric("컨텍스트 점수", f"{context_score:.3f}")
                        with col_score3:
                            final_score = after_debug.get("final_score", 0)
                            st.metric("최종 점수", f"{final_score:.3f}")
                        
                        # 찾는 컨텍스트 vs 실제 컨텍스트
                        st.markdown("**컨텍스트 비교:**")
                        context_before = after_debug.get("context_before")
                        context_after = after_debug.get("context_after")
                        
                        # validation 정보가 있으면 표시
                        validation = after_debug.get("validation")
                        if validation:
                            col_ctx1, col_ctx2 = st.columns(2)
                            with col_ctx1:
                                st.markdown("**앞 컨텍스트:**")
                                if context_before:
                                    st.caption(f"🔍 찾는 것: ...{context_before[:50]}")
                                actual_before = validation.get("actual_before_context", "")
                                if actual_before:
                                    before_match = validation.get("before_match")
                                    match_icon = "✅" if before_match else "❌"
                                    before_score = validation.get("before_score", 0)
                                    st.caption(f"{match_icon} 실제 것: ...{actual_before[-50:]}")
                                    st.caption(f"   점수: {before_score:.3f} {'(통과)' if before_match else '(실패)'}")
                            
                            with col_ctx2:
                                st.markdown("**뒤 컨텍스트:**")
                                if context_after:
                                    st.caption(f"🔍 찾는 것: {context_after[:50]}...")
                                actual_after = validation.get("actual_after_context", "")
                                if actual_after:
                                    after_match = validation.get("after_match")
                                    match_icon = "✅" if after_match else "❌"
                                    after_score = validation.get("after_score", 0)
                                    st.caption(f"{match_icon} 실제 것: {actual_after[:50]}...")
                                    st.caption(f"   점수: {after_score:.3f} {'(통과)' if after_match else '(실패)'}")
                        else:
                            # validation 정보가 없으면 기본 컨텍스트만 표시
                            if context_before:
                                st.caption(f"앞: ...{context_before[:50]}")
                            if context_after:
                                st.caption(f"뒤: {context_after[:50]}...")
                        
                        # 매칭된 HTML 컨텍스트
                        matched_html_ctx = after_debug.get("matched_html_context")
                        if matched_html_ctx:
                            with st.expander("📋 매칭된 HTML 컨텍스트", expanded=False):
                                st.code(matched_html_ctx[:500] + ("..." if len(matched_html_ctx) > 500 else ""), language="html")
                    else:
                        st.error("❌ 매칭 실패")
                        error_info = after_debug.get("error")
                        if error_info:
                            st.caption(f"**오류:** {error_info}")
                            
                            # 🆕 컨텍스트 검증 실패인 경우 상세 정보 표시
                            if error_info == "컨텍스트 검증 실패":
                                validation = after_debug.get("validation", {})
                                if validation:
                                    st.markdown("**🔍 컨텍스트 검증 상세 정보:**")
                                    
                                    col_err1, col_err2 = st.columns(2)
                                    
                                    with col_err1:
                                        st.markdown("**앞 컨텍스트:**")
                                        context_before = after_debug.get("context_before")
                                        if context_before:
                                            st.caption(f"🔍 찾는 것: ...{context_before[:80]}")
                                        actual_before = validation.get("actual_before_context", "")
                                        if actual_before:
                                            before_match = validation.get("before_match", False)
                                            before_score = validation.get("before_score", 0)
                                            match_icon = "✅" if before_match else "❌"
                                            st.caption(f"{match_icon} 실제 것: ...{actual_before[-80:]}")
                                            st.caption(f"   점수: {before_score:.3f} / 0.5 (필요) {'✅ 통과' if before_match else '❌ 실패'}")
                                    
                                    with col_err2:
                                        st.markdown("**뒤 컨텍스트:**")
                                        context_after = after_debug.get("context_after")
                                        if context_after:
                                            st.caption(f"🔍 찾는 것: {context_after[:80]}...")
                                        actual_after = validation.get("actual_after_context", "")
                                        if actual_after:
                                            after_match = validation.get("after_match", False)
                                            after_score = validation.get("after_score", 0)
                                            match_icon = "✅" if after_match else "❌"
                                            st.caption(f"{match_icon} 실제 것: {actual_after[:80]}...")
                                            st.caption(f"   점수: {after_score:.3f} / 0.5 (필요) {'✅ 통과' if after_match else '❌ 실패'}")
                                    
                                    # 매칭된 텍스트 정보
                                    matched_text = after_debug.get("matched_text_content")
                                    if matched_text:
                                        st.markdown("**매칭된 텍스트:**")
                                        st.code(matched_text[:200] + ("..." if len(matched_text) > 200 else ""), language=None)
                                    
                                    # 점수 정보
                                    col_score1, col_score2, col_score3 = st.columns(3)
                                    with col_score1:
                                        basic_sim = after_debug.get("basic_similarity", 0)
                                        st.metric("기본 유사도", f"{basic_sim:.3f}")
                                    with col_score2:
                                        context_score = after_debug.get("context_score", 0)
                                        st.metric("컨텍스트 점수", f"{context_score:.3f}")
                                    with col_score3:
                                        final_score = after_debug.get("final_score", 0)
                                        st.metric("최종 점수", f"{final_score:.3f}")
            
            # 원시 데이터 (디버깅용)
            with st.expander("🔧 원시 데이터 (디버깅)", expanded=False):
                st.json(change)

def display_html_structure_highlighting(comparator, before, after, changes, context_window=50, search_tolerance=50):
    """HTML 구조 보존 하이라이팅 모드 표시"""
    st.write("💡 원본 HTML과 수정된 HTML을 나란히 표시하고, 변경된 부분을 색상으로 구분합니다.")
    
    # 하이라이팅 실행 및 결과 표시
    with st.spinner("변경사항을 탐색 중입니다..."):
        html_with_highlighting = comparator.create_html_with_highlighting(before, after, changes, search_tolerance, context_window)
    
    st.components.v1.html(html_with_highlighting, height=800, scrolling=True)
    
    # 개별 PDF 다운로드 버튼
    if html_with_highlighting:
        try:
            with st.spinner("PDF 생성 중..."):
                # 원본과 수정본 HTML 각각 생성
                before_html_individual, after_html_individual = comparator.create_individual_html_with_highlighting(
                    before, after, changes, search_tolerance, context_window
                )
                
                # 각각 PDF로 변환
                before_pdf_bytes = html_to_pdf(before_html_individual)
                after_pdf_bytes = html_to_pdf(after_html_individual)
            
            # 두 개의 다운로드 버튼을 나란히 배치
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 원본 PDF 다운로드",
                    data=before_pdf_bytes,
                    file_name="원본_HTML.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
            with col2:
                st.download_button(
                    label="📥 수정본 PDF 다운로드",
                    data=after_pdf_bytes,
                    file_name="수정된_HTML.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"PDF 생성 중 오류가 발생했습니다: {str(e)}")

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
                
                # 🆕 변경사항 요약 표시 (매핑 전)
                display_changes_summary(changes, show_highlighting_results=False)
                
                st.write("---")
                
                # 하이라이팅 결과를 changes에 추가
                with st.spinner("하이라이팅을 적용하고 있습니다..."):
                    # 하이라이팅 실행
                    soup_before = BeautifulSoup(before, 'html.parser')
                    soup_after = BeautifulSoup(after, 'html.parser')
                    comparator._apply_highlights_to_html(soup_before, soup_after, changes, search_tolerance, context_window)
                
                # 🆕 변경사항 요약 표시 (매핑 후 - 매칭 결과 포함)
                st.write("---")
                display_changes_summary(changes, show_highlighting_results=True)
                
                st.write("---")
                
                display_html_structure_highlighting(comparator, before, after, changes, context_window, search_tolerance)
                    
        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")


if __name__ == "__main__":
    HTML_COMPARE()