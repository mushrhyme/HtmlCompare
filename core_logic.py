"""
HTML 문서 비교를 위한 핵심 로직 모듈 v3
- HTMLDiffHighlighter 클래스를 활용한 새로운 비교 방식
- 기존 HTMLComparator 기능과 통합
- 스트림릿과 독립적인 순수한 로직만 포함
"""

import difflib
from bs4 import BeautifulSoup
import re


ABSOLUTE_THRESHOLD = 0.2

class HTMLComparator:
    """HTML 문서 비교를 위한 통합 클래스"""

    def __init__(self):
        pass


    def load_file(self, uploaded_file):
        """업로드된 파일을 읽어서 문자열로 반환"""
        try:
            return uploaded_file.read().decode('utf-8')
        except Exception as e:
            raise Exception(f"파일 읽기 오류: {str(e)}")


    def analyze_changes(self, before_html, after_html):
        """HTML에서 변경된 부분을 분석하여 반환 (char_word 방식만 지원)"""
        try:
            changes = self._analyze_char_word_changes(before_html, after_html)
            return changes
        except Exception as e:
            raise Exception(f"변경사항 분석 오류: {str(e)}")


    def _extract_clean_text(self, html_content):
        """HTML에서 깔끔한 텍스트 추출"""
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text()
        text = re.sub(r'\s+', ' ', text.replace('\u00a0', ' ')).strip()
        return text


    def _analyze_char_word_changes(self, before_html, after_html):
        """문자/단어 단위 변경사항 분석"""
        before_text = self._extract_clean_text(before_html)
        after_text = self._extract_clean_text(after_html)
        before_words, after_words = before_text.split(), after_text.split()


        matcher = difflib.SequenceMatcher(None, before_words, after_words)
        results = []

        for tag, i1,i2,j1,j2 in matcher.get_opcodes():
            if tag == "equal": continue
            
            before_position = self._calculate_word_position(before_text, before_words, i1, i2)
            after_position = self._calculate_word_position(after_text, after_words, j1, j2)
            
            # 🆕 컨텍스트 정보 추가 (앞뒤 3개 단어씩)
            before_context_before = before_words[max(0, i1-3):i1] if i1 > 0 else []
            before_context_after = before_words[i2:min(len(before_words), i2+3)]
            after_context_before = after_words[max(0, j1-3):j1] if j1 > 0 else []
            after_context_after = after_words[j2:min(len(after_words), j2+3)]
            
            results.append({
                "type": "text",
                "status": tag,
                "before": before_words[i1:i2],
                "after": after_words[j1:j2],
                "before_position": before_position,
                "after_position": after_position,
                # 🆕 컨텍스트 정보 추가
                "before_context_before": before_context_before,
                "before_context_after": before_context_after,
                "after_context_before": after_context_before,
                "after_context_after": after_context_after
            })
        return results
    
    
    def _calculate_word_position(self, full_text, words, start_idx, end_idx):
        """단어 인덱스를 텍스트 위치로 변환 (공백 정규화 통일)"""
        if start_idx >= len(words) or end_idx > len(words):
            return None
        
        full_text_norm = re.sub(r'\s+', ' ', full_text.replace('\u00a0', ' ')).strip()
        
        before_words = words[:start_idx]
        target_words = words[start_idx:end_idx]
        
        before_text = " ".join(before_words)
        start_pos = len(before_text) + (1 if before_text else 0)
        
        target_text = " ".join(target_words)
        end_pos = start_pos + len(target_text)
        
        return (start_pos, end_pos)


    def create_html_with_highlighting(self, before_html, after_html, changes, search_tolerance=50, context_window=50, context_words=3):
        """HTML 구조를 보존하면서 변경사항을 하이라이팅 (컨텍스트 기반 매칭 지원)"""
        
        soup_before = BeautifulSoup(before_html, 'html.parser')
        soup_after = BeautifulSoup(after_html, 'html.parser')
        
        self._apply_highlights_to_html(soup_before, soup_after, changes, search_tolerance, context_window, context_words)
        
        style = """
        <style>
        .html-comparison-container {
            display: flex;
            gap: 20px;
            margin: 20px 0;
        }
        .html-side {
            flex: 1;
            border: 1px solid #ddd;
            padding: 15px;
            border-radius: 5px;
            background: white;
        }
        .html-title {
            font-weight: bold;
            margin-bottom: 10px;
            padding: 8px;
            background-color: #f8f9fa;
            border-radius: 3px;
            color: #333;
        }
        .highlight-added {
            background-color: #d4edda !important;
            border: 3px solid #28a745 !important;
            padding: 4px !important;
            border-radius: 5px !important;
            position: relative !important;
            display: inline-block !important;
            margin: 2px !important;
            font-weight: bold !important;
        }
        .highlight-removed {
            background-color: #f8d7da !important;
            border: 3px solid #dc3545 !important;
            padding: 4px !important;
            border-radius: 5px !important;
            position: relative !important;
            display: inline-block !important;
            margin: 2px !important;
            font-weight: bold !important;
        }
        .highlight-modified {
            background-color: #fff3cd !important;
            border: 3px solid #ffc107 !important;
            padding: 4px !important;
            border-radius: 5px !important;
            position: relative !important;
            display: inline-block !important;
            margin: 2px !important;
            font-weight: bold !important;
        }
        .highlight-tooltip {
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 6px 10px;
            border-radius: 4px;
            font-size: 12px;
            white-space: nowrap;
            z-index: 9999;
            top: -35px;
            left: 0;
            opacity: 0;
            transition: opacity 0.3s;
            pointer-events: none;
        }
        .highlight-added:hover .highlight-tooltip,
        .highlight-removed:hover .highlight-tooltip,
        .highlight-modified:hover .highlight-tooltip {
            opacity: 1;
        }
        </style>
        """
        
        comparison_html = f"""
        {style}
        <div class="html-comparison-container">
            <div class="html-side">
                <div class="html-title">📄 원본 HTML</div>
                <div>{str(soup_before)}</div>
            </div>
            <div class="html-side">
                <div class="html-title">📝 수정된 HTML</div>
                <div>{str(soup_after)}</div>
            </div>
        </div>
        """
        return comparison_html
    
    def _apply_highlights_to_html(self, soup_before, soup_after, changes, search_tolerance=50, context_window=50, context_words=3):
        """HTML 요소에 변경사항 하이라이팅 적용 (컨텍스트 기반 매칭 지원)"""
        original_soup_before = soup_before
        modified_soup_after = soup_after
        
        for i, change in enumerate(changes):
            if change["type"] == "text":
                result = self._highlight_text_in_html(original_soup_before, modified_soup_after, change, i, search_tolerance, context_window, context_words)
                change["highlighting_result"] = result
        
    def _highlight_text_in_html(self, original_soup_before, modified_soup_after, change, change_index, search_tolerance=50, context_window=50, context_words=3):
        """텍스트 변경사항을 HTML에서 하이라이팅 (컨텍스트 고려 매칭)"""
        status = change["status"]
        before_text = " ".join(change.get("before", []))
        after_text = " ".join(change.get("after", []))
        
        # 변경사항의 앞뒤 컨텍스트 추출
        context_before, context_after = self._extract_change_context(change)
        
        result = {
            "before_highlighted": False,
            "after_highlighted": False,
            "before_matched_html": None,
            "after_matched_html": None,
            "debug_info": {
                "status": status,
                "before_text": before_text,
                "after_text": after_text,
                "before_text_length": len(before_text),
                "after_text_length": len(after_text),
                "context_before": context_before,
                "context_after": context_after,
                # 🆕 저장된 컨텍스트 정보 추가
                "stored_before_context_before": " ".join(change.get("before_context_before", [])),
                "stored_before_context_after": " ".join(change.get("before_context_after", [])),
                "stored_after_context_before": " ".join(change.get("after_context_before", [])),
                "stored_after_context_after": " ".join(change.get("after_context_after", []))
            }
        }
        
        if status == "delete" and before_text:
            # 원본 HTML에서 원본 텍스트 찾기 (컨텍스트 고려 매칭)
            success, matched_html, debug_info = self._find_and_highlight_text_by_content(
                original_soup_before, before_text, "highlight-removed", 
                f"변경사항 {change_index+1}: 삭제됨: {before_text}", apply_highlighting=True,
                context_before=context_before, context_after=context_after
            )
            result["before_highlighted"] = success
            result["before_matched_html"] = matched_html
            result["debug_info"]["before_search_success"] = success
            result["debug_info"].update(debug_info)
        
        elif status == "insert" and after_text:
            # 수정된 HTML에서 수정된 텍스트 찾기 (컨텍스트 고려 매칭)
            success, matched_html, debug_info = self._find_and_highlight_text_by_content(
                modified_soup_after, after_text, "highlight-added", 
                f"변경사항 {change_index+1}: 추가됨: {after_text}", apply_highlighting=True,
                context_before=context_before, context_after=context_after
            )
            result["after_highlighted"] = success
            result["after_matched_html"] = matched_html
            result["debug_info"]["after_search_success"] = success
            result["debug_info"]["after_debug_info"] = debug_info
        
        elif status == "replace" and before_text and after_text:
            # 원본 HTML에서 원본 텍스트 찾기 (컨텍스트 고려 매칭)
            success_before, matched_html_before, debug_info_before = self._find_and_highlight_text_by_content(
                original_soup_before, before_text, "highlight-modified", 
                f"변경사항 {change_index+1}: 변경됨: {before_text} → {after_text}", apply_highlighting=True,
                context_before=context_before, context_after=context_after
            )
            # 수정된 HTML에서 수정된 텍스트 찾기 (컨텍스트 고려 매칭)
            success_after, matched_html_after, debug_info_after = self._find_and_highlight_text_by_content(
                modified_soup_after, after_text, "highlight-modified", 
                f"변경사항 {change_index+1}: 변경됨: {before_text} → {after_text}", apply_highlighting=True,
                context_before=context_before, context_after=context_after
            )
            result["before_highlighted"] = success_before
            result["after_highlighted"] = success_after
            result["before_matched_html"] = matched_html_before
            result["after_matched_html"] = matched_html_after
            result["debug_info"]["before_search_success"] = success_before
            result["debug_info"]["after_search_success"] = success_after
            result["debug_info"].update(debug_info_before)
            result["debug_info"]["after_debug_info"] = debug_info_after
        
        return result

    def _extract_change_context(self, change):
        """변경사항에서 앞뒤 컨텍스트 추출 (저장된 컨텍스트 사용)"""
        try:
            # 🆕 저장된 컨텍스트 정보 사용 (우선순위: before > after)
            if change.get("before_context_before") and change.get("before_context_after"):
                context_before = " ".join(change["before_context_before"])
                context_after = " ".join(change["before_context_after"])
                print(f"🔍 컨텍스트 추출 (before): 앞='{context_before[:30]}...', 뒤='{context_after[:30]}...'")
                return context_before, context_after
            elif change.get("after_context_before") and change.get("after_context_after"):
                context_before = " ".join(change["after_context_before"])
                context_after = " ".join(change["after_context_after"])
                print(f"🔍 컨텍스트 추출 (after): 앞='{context_before[:30]}...', 뒤='{context_after[:30]}...'")
                return context_before, context_after
            
            # 폴백: 기존 방식 (HTML에서 동적 추출)
            before_text = " ".join(change.get("before", []))
            after_text = " ".join(change.get("after", []))
            target_text = before_text if before_text else after_text
            
            if target_text:
                # 폴백: 컨텍스트 없음
                print(f"🔍 컨텍스트 추출 (폴백): 컨텍스트 정보 없음")
                return None, None
            
            print(f"🔍 컨텍스트 추출 실패: 컨텍스트 정보 없음")
            return None, None
            
        except Exception as e:
            print(f"🔍 컨텍스트 추출 오류: {str(e)}")
            return None, None


    def _find_and_highlight_text_by_content(self, soup, target_text, css_class, tooltip, apply_highlighting=True, context_before=None, context_after=None):
        """텍스트 내용과 앞뒤 컨텍스트를 고려해서 HTML에서 텍스트를 찾아 하이라이팅"""
        if not target_text.strip():
            return False, None, {"error": "빈 타겟 텍스트"}
            
        target_text = target_text.strip()
        highlighted_elements = set()
        
        # 모든 텍스트 노드에서 타겟 텍스트 검색
        matches_found = 0
        matched_html = None
        all_matches = []
        
        # HTML의 모든 텍스트 노드 검색
        for element in soup.find_all(text=True):
            if element.parent and element.parent.name not in ['script', 'style']:
                text_content = re.sub(r'\s+', ' ', element.replace('\u00a0', ' ').strip())
                
                if text_content and target_text in text_content:
                    # 기본 유사도 계산
                    basic_similarity = self._calculate_text_similarity(text_content, target_text)
                    
                    # 🆕 디버깅: 비교 대상 출력
                    print(f"📊 매칭 발견:")
                    print(f"   🔍 찾는 텍스트 (target_text): {target_text[:50]}... ({len(target_text)}자)")
                    print(f"   📄 HTML 노드 텍스트 (text_content): {text_content[:50]}... ({len(text_content)}자)")
                    print(f"   📈 기본 유사도: {basic_similarity:.3f}")
                    
                    # 컨텍스트 매칭 점수 계산 (상세 정보 포함)
                    context_score = 0.0
                    context_details = None
                    if context_before or context_after:
                        context_score, context_details = self._calculate_context_match_score_with_details(
                            element, target_text, context_before, context_after
                        )
                        print(f"   🎯 컨텍스트 점수: {context_score:.3f}")
                    
                    # 최종 점수 = 기본 유사도 + 컨텍스트 보너스
                    final_score = basic_similarity + (context_score * 0.5)  # 컨텍스트 보너스 50%
                    print(f"   🏆 최종 점수: {final_score:.3f}")
                    
                    all_matches.append({
                        "element": element,
                        "text": text_content,
                        "similarity": basic_similarity,
                        "context_score": context_score,
                        "context_details": context_details,
                        "final_score": final_score,
                        "parent_tag": element.parent.name if element.parent else "None"
                    })
        
        if all_matches:
            # 최종 점수 순으로 정렬하여 가장 좋은 매치 선택
            all_matches.sort(key=lambda x: x["final_score"], reverse=True)
            best_match = all_matches[0]
            
            # 유사도 threshold 확인
            if best_match["final_score"] >= ABSOLUTE_THRESHOLD:
                if apply_highlighting:
                    matches_found, matched_html, _ = self._apply_highlighting(
                        best_match, soup, css_class, tooltip, highlighted_elements
                    )
                else:
                    matches_found = 1
                    matched_html = str(best_match["element"].parent) if best_match["element"].parent else str(best_match["element"])
            else:
                # threshold 미달 시 매칭 실패로 처리
                matches_found = 0
                matched_html = None
        
        # 🆕 [추가] 완전 일치 실패 시: 타겟 텍스트 일부를 포함하는 노드 후보 탐색
        if not all_matches:
            partial_matches = []
            
            for element in soup.find_all(text=True):
                if element and element.parent and element.parent.name not in ['script', 'style']:
                    text_content = re.sub(r'\s+', ' ', element.replace('\u00a0', ' ').strip())
                    if text_content and (text_content in target_text or target_text in text_content):
                        # 부분 매칭에서도 유사도 계산
                        similarity = self._calculate_text_similarity(text_content, target_text)
                        if similarity >= ABSOLUTE_THRESHOLD:
                            partial_matches.append(element)
            
            print(f"🔍 시퀀스 매칭: {len(partial_matches)}개 부분 매칭")

            # 🧩 후보 노드들을 연속성 기준으로 그룹화
            grouped_candidates = []
            current_group = []
            
            for elem in partial_matches:
                if elem is None:
                    continue
                if not current_group:
                    current_group.append(elem)
                    continue
                prev = current_group[-1]
                # 같은 <tr> 내에서 연속된 <td>인지 검사
                if (
                    prev and prev.parent
                    and prev.parent.parent
                    and elem.parent
                    and elem.parent.parent == prev.parent.parent
                ):
                    current_group.append(elem)
                else:
                    grouped_candidates.append(current_group)
                    current_group = [elem]
            if current_group:
                grouped_candidates.append(current_group)
            
            print(f"🔍 {len(grouped_candidates)}개 그룹")

            # 🧩 각 그룹별 컨텍스트 유사도 평가 (개선된 버전)
            best_group = None
            best_score = 0.0
            context_used = False
            context_score = 0.0
            context_details = {}
            
            for i, group in enumerate(grouped_candidates):
                if not group:
                    continue
                # None 요소 필터링
                valid_elements = [g for g in group if g is not None]
                if not valid_elements:
                    continue
                    
                group_text = " ".join(
                    [re.sub(r'\s+', ' ', e.strip()) for e in [g.string or g.get_text() for g in valid_elements]]
                )
                
                base_sim = self._calculate_text_similarity(group_text, target_text)
                context_score = 0.0
                context_used = False
                context_details = {}
                
                # 🆕 개선된 컨텍스트 매칭: 저장된 컨텍스트와 실제 HTML 컨텍스트 비교
                if context_before or context_after:
                    context_used = True
                    
                    # 실제 HTML에서 해당 그룹의 앞뒤 컨텍스트 추출
                    actual_before_context, actual_after_context = self._extract_actual_context_from_group(
                        valid_elements, group_text
                    )
                    
                    # 저장된 컨텍스트와 실제 컨텍스트 매칭 점수 계산
                    before_match_score = 0.0
                    after_match_score = 0.0
                    
                    if context_before and actual_before_context:
                        before_match_score = self._calculate_text_similarity(
                            actual_before_context, context_before
                        )
                    
                    if context_after and actual_after_context:
                        after_match_score = self._calculate_text_similarity(
                            actual_after_context, context_after
                        )
                    
                    # 컨텍스트 매칭 점수 계산 (가중 평균)
                    context_weights = []
                    context_scores = []
                    
                    if before_match_score > 0:
                        context_scores.append(before_match_score)
                        context_weights.append(0.5)
                    
                    if after_match_score > 0:
                        context_scores.append(after_match_score)
                        context_weights.append(0.5)
                    
                    if context_scores:
                        context_score = sum(score * weight for score, weight in zip(context_scores, context_weights))
                        context_score = context_score / sum(context_weights) if context_weights else 0.0
                    
                    # 컨텍스트 디버깅 정보 저장
                    context_details = {
                        'actual_before_context': actual_before_context,
                        'actual_after_context': actual_after_context,
                        'stored_before_context': context_before,
                        'stored_after_context': context_after,
                        'before_match_score': before_match_score,
                        'after_match_score': after_match_score,
                        'context_score': context_score
                    }
                    
                    # 컨텍스트 디버깅 정보 출력 (상위 3개 그룹만)
                    if i < 3:
                        print(f"  🔍 그룹 {i}: '{group_text[:30]}...'")
                        print(f"    기본 유사도: {base_sim:.3f}")
                        print(f"    실제 앞 컨텍스트: '{actual_before_context[:30] if actual_before_context else 'None'}...'")
                        print(f"    저장된 앞 컨텍스트: '{context_before[:30] if context_before else 'None'}...'")
                        print(f"    앞 컨텍스트 매칭: {before_match_score:.3f}")
                        print(f"    실제 뒤 컨텍스트: '{actual_after_context[:30] if actual_after_context else 'None'}...'")
                        print(f"    저장된 뒤 컨텍스트: '{context_after[:30] if context_after else 'None'}...'")
                        print(f"    뒤 컨텍스트 매칭: {after_match_score:.3f}")
                        print(f"    최종 컨텍스트 점수: {context_score:.3f}")
                else:
                    if i < 3:
                        print(f"  🔍 그룹 {i}: '{group_text[:30]}...' (컨텍스트 없음)")
                        print(f"    기본 유사도: {base_sim:.3f}")
                
                # 🆕 개선된 최종 점수 계산: 컨텍스트 매칭에 높은 가중치 부여
                if context_used and context_score > 0:
                    # 컨텍스트 매칭이 있는 경우: 컨텍스트 우선
                    final_score = base_sim * 0.2 + context_score * 0.8
                else:
                    # 컨텍스트 매칭이 없는 경우: 기본 유사도만 사용
                    final_score = base_sim
                
                if final_score > best_score:
                    best_group = valid_elements
                    best_score = final_score
                    print(f"    🏆 새로운 최고 점수: {final_score:.3f} (컨텍스트 사용: {context_used}, 컨텍스트 점수: {context_score:.3f})")
            
            if best_group:
                # 시퀀스 매칭에서도 threshold 확인
                if best_score >= ABSOLUTE_THRESHOLD:
                    group_text = " ".join([e.strip() for e in [g.string or g.get_text() for g in best_group]])
                    print(f"✅ 시퀀스 매칭 성공: {len(best_group)}개 노드, 점수: {best_score:.3f}")
                    print(f"✅ 선택된 텍스트: '{group_text[:50]}...'")
                else:
                    print(f"❌ 시퀀스 매칭 threshold 미달: {best_score:.3f} < {ABSOLUTE_THRESHOLD}")
                    best_group = None
            else:
                print(f"❌ 시퀀스 매칭 실패")
                # 시퀀스 매칭 실패 시에도 debug_info 반환
                return False, None, {
                    "target_text": target_text,
                    "matches_found": 0,
                    "total_candidates": len(partial_matches),
                    "best_similarity": 0.0,
                    "note": "시퀀스 매칭 실패 - 적절한 그룹을 찾지 못함"
                }

            # 🧩 최종 그룹의 각 노드에 하이라이트 적용 (표 구조 유지)
            if best_group and apply_highlighting:
                # 1. 먼저 컨텍스트 생성 (원본 노드 정보 보존)
                first_elem = best_group[0]
                matched_html_context = None
                
                if first_elem and first_elem.parent:
                    if first_elem.parent.parent and first_elem.parent.parent.name == 'tr':
                        target_tr = first_elem.parent.parent
                        # 같은 행의 모든 td 요소들 수집
                        td_elements = [td for td in target_tr.find_all('td')]
                        
                        # 현재 그룹의 td들 찾기
                        group_td_indices = []
                        for elem in best_group:
                            if elem.parent and elem.parent.name == 'td':
                                for i, td in enumerate(td_elements):
                                    if td == elem.parent:
                                        group_td_indices.append(i)
                                        break
                        
                        if group_td_indices and len(td_elements) > 1:
                            # 앞뒤 ±10개 td 요소 수집
                            min_idx = min(group_td_indices)
                            max_idx = max(group_td_indices)
                            start_idx = max(0, min_idx - 10)
                            end_idx = min(len(td_elements), max_idx + 11)
                            context_tds = td_elements[start_idx:end_idx]
                            
                            # HTML 컨텍스트 생성
                            context_html = ""
                            context_html += f"<!-- 📋 시퀀스 매칭 컨텍스트 (총 {len(context_tds)}개 td) -->\n"
                            
                            for i, td in enumerate(context_tds):
                                actual_index = i + start_idx
                                if actual_index in group_td_indices:
                                    # 🎯 시퀀스 매칭된 노드
                                    context_html += f"<!-- 🎯 시퀀스 매칭 노드 {actual_index} -->\n{str(td)}\n<!-- 🎯 시퀀스 매칭 노드 {actual_index} 끝 -->\n"
                                else:
                                    # 앞뒤 컨텍스트
                                    position = "앞" if actual_index < min_idx else "뒤"
                                    distance = min(abs(actual_index - min_idx), abs(actual_index - max_idx))
                                    context_html += f"<!-- {position} 컨텍스트 (거리: {distance}) -->\n{str(td)}\n<!-- {position} 컨텍스트 끝 -->\n"
                            
                            context_html += f"<!-- 📋 시퀀스 매칭 컨텍스트 끝 -->"
                            matched_html_context = context_html.strip()
                        else:
                            matched_html_context = f"<!-- 🎯 시퀀스 매칭 그룹 -->\n{str(first_elem.parent)}\n<!-- 🎯 시퀀스 매칭 그룹 끝 -->"
                    else:
                        matched_html_context = f"<!-- 🎯 시퀀스 매칭 그룹 -->\n{str(first_elem.parent)}\n<!-- 🎯 시퀀스 매칭 그룹 끝 -->"
                else:
                    matched_html_context = f"<!-- 🎯 시퀀스 매칭 그룹 -->\n{str(first_elem)}\n<!-- 🎯 시퀀스 매칭 그룹 끝 -->"
                
                # 2. 그 다음 하이라이팅 적용
                print(f"🎨 하이라이팅 시작: {len(best_group)}개 노드에 {css_class} 적용")
                
                for i, elem in enumerate(best_group):
                    if elem is None:
                        continue
                    
                    # 디버깅 정보 출력
                    elem_text = elem.strip() if isinstance(elem, str) else elem
                    print(f"  🎨 노드 {i+1}: '{elem_text[:30]}...' → {css_class}")
                    
                    # 하이라이팅 span 생성
                    span = soup.new_tag('span', **{'class': css_class})
                    span.string = elem_text
                    
                    # 툴팁 추가 (디버깅 정보 포함)
                    tooltip_text = f"{tooltip} (시퀀스 {i+1}/{len(best_group)})"
                    tooltip_span = soup.new_tag('span', **{'class': 'highlight-tooltip'})
                    tooltip_span.string = tooltip_text
                    span.append(tooltip_span)
                    
                    # 원본 요소를 하이라이팅된 요소로 교체
                    elem.replace_with(span)
                
                print(f"✅ 하이라이팅 완료: {len(best_group)}개 노드 처리됨")
                
                # 안전한 HTML 반환값 생성
                if first_elem and first_elem.parent:
                    if first_elem.parent.parent and first_elem.parent.parent.name == 'tr':
                        matched_html = str(first_elem.parent.parent)
                    else:
                        matched_html = str(first_elem.parent)
                else:
                    matched_html = str(first_elem) if first_elem else "None"
                
                # 시퀀스 매칭 성공 시 all_matches에 추가하여 화면 표시 문제 해결
                group_text = " ".join([e.strip() for e in [g.string or g.get_text() for g in best_group]])
                all_matches.append({
                    "element": first_elem,
                    "text": group_text,
                    "similarity": best_score,
                    "context_score": 0.0,
                    "context_details": None,
                    "final_score": best_score,
                    "parent_tag": first_elem.parent.name if first_elem.parent else "None"
                })
                
                
                # 화면 표시를 위한 올바른 debug_info 생성
                debug_info = {
                    "target_text": target_text,
                    "matches_found": 1,  # 시퀀스 매칭 성공
                    "total_candidates": len(partial_matches),  # 부분 매칭된 노드 수
                    "best_similarity": best_score,
                    "matched_html_node": matched_html,
                    "matched_text_content": group_text,
                    "matched_parent_tag": first_elem.parent.name if first_elem.parent else "None",
                    "matched_html_context": matched_html_context,  # 🆕 시퀀스 매칭 컨텍스트 추가
                    "context_before": context_before,
                    "context_after": context_after,
                    "all_candidates": [],  # 시퀀스 매칭에서는 단순화
                    "note": "시퀀스 매칭 성공 (개선된 컨텍스트 매칭)",
                    "group_size": len(best_group),
                    "group_score": best_score,
                    # 🆕 개선된 컨텍스트 매칭 정보 추가
                    "context_matching_info": {
                        "method": "improved_sequence_matching",
                        "context_used": context_used,
                        "context_score": context_score,
                        "context_details": context_details,
                        "actual_before_context": context_details.get('actual_before_context'),
                        "actual_after_context": context_details.get('actual_after_context'),
                        "before_match_score": context_details.get('before_match_score', 0),
                        "after_match_score": context_details.get('after_match_score', 0)
                    },
                    # 🆕 하이라이팅 디버깅 정보 추가
                    "highlighting_info": {
                        "method": "sequence_matching",
                        "highlighted_nodes": len(best_group),
                        "css_class": css_class,
                        "tooltip": tooltip,
                        "group_text": group_text,
                        "individual_nodes": [
                            {
                                "index": i,
                                "text": elem.strip() if isinstance(elem, str) else str(elem),
                                "parent_tag": elem.parent.name if elem.parent else "None"
                            } for i, elem in enumerate(best_group)
                        ]
                    }
                }
                
                return True, matched_html, debug_info
        
        # 매칭된 노드의 HTML 컨텍스트 정보 수집 (앞뒤 컨텍스트 포함)
        matched_html_context = None
        if all_matches:
            best_element = best_match["element"]
            target_text = best_match["text"]
            
            # 🆕 최종 선택된 후보의 앞뒤 컨텍스트를 포함한 HTML 생성
            if best_element.parent and best_element.parent.name == 'td':
                target_td = best_element.parent
                parent_tr = target_td.parent
                
                if parent_tr and parent_tr.name == 'tr':
                    # 같은 행의 모든 td 요소들 수집
                    td_elements = [td for td in parent_tr.find_all('td')]
                    
                    # 현재 td의 인덱스 찾기
                    current_index = -1
                    for i, td in enumerate(td_elements):
                        if td == target_td:
                            current_index = i
                            break
                    
                    if current_index != -1 and len(td_elements) > 1:
                        # 🆕 앞뒤 ±10개 td 요소 수집 (더 넓은 컨텍스트)
                        start_idx = max(0, current_index - 10)
                        end_idx = min(len(td_elements), current_index + 11)
                        context_tds = td_elements[start_idx:end_idx]
                        
                        # HTML 컨텍스트 생성 (앞뒤 컨텍스트 포함)
                        context_html = ""
                        context_html += f"<!-- 📋 앞뒤 컨텍스트 (총 {len(context_tds)}개 td) -->\n"
                        
                        for i, td in enumerate(context_tds):
                            actual_index = i + start_idx
                            if actual_index == current_index:
                                # 🎯 최종 선택된 후보
                                context_html += f"<!-- 🎯 최종 선택된 후보 (인덱스: {actual_index}) -->\n{str(td)}\n<!-- 🎯 최종 선택된 후보 끝 -->\n"
                            else:
                                # 앞뒤 컨텍스트
                                position = "앞" if actual_index < current_index else "뒤"
                                distance = abs(actual_index - current_index)
                                context_html += f"<!-- {position} 컨텍스트 (거리: {distance}) -->\n{str(td)}\n<!-- {position} 컨텍스트 끝 -->\n"
                        
                        context_html += f"<!-- 📋 앞뒤 컨텍스트 끝 -->"
                        matched_html_context = context_html.strip()
                    else:
                        matched_html_context = f"<!-- 🎯 최종 선택된 후보 -->\n{str(target_td)}\n<!-- 🎯 최종 선택된 후보 끝 -->"
                else:
                    matched_html_context = f"<!-- 🎯 최종 선택된 후보 -->\n{str(target_td)}\n<!-- 🎯 최종 선택된 후보 끝 -->"
            else:
                # td가 아닌 경우 기본 처리
                matched_html_context = f"<!-- 🎯 최종 선택된 후보 -->\n{str(best_element)}\n<!-- 🎯 최종 선택된 후보 끝 -->"
        
        debug_info = {
            "target_text": target_text,
            "matches_found": matches_found,
            "total_candidates": len(all_matches),
            "best_similarity": all_matches[0]["similarity"] if all_matches else 0.0,
            "final_score": all_matches[0]["final_score"] if all_matches else 0.0,  # 🆕 추가: 최종 점수
            "basic_similarity": all_matches[0]["similarity"] if all_matches else 0.0,  # 🆕 추가: 기본 유사도
            "context_score": all_matches[0]["context_score"] if all_matches else 0.0,  # 🆕 추가: 컨텍스트 점수
            "matched_html_node": str(best_match["element"].parent) if all_matches and best_match["element"].parent else str(best_match["element"]) if all_matches else None,
            "matched_text_content": best_match["text"] if all_matches else None,
            "matched_parent_tag": best_match["parent_tag"] if all_matches else None,
            "matched_html_context": matched_html_context,
            "context_before": context_before,
            "context_after": context_after,
            "all_candidates": [
                {
                    "text": match["text"],
                    "similarity": match["similarity"],
                    "context_score": match["context_score"],
                    "context_details": match["context_details"],
                    "final_score": match["final_score"],
                    "parent_tag": match["parent_tag"],
                    "html_node": str(match["element"].parent) if match["element"].parent else str(match["element"]),
                    "html_context": self._get_html_context_with_siblings(match["element"], context_range=3),
                    "row_context": self._get_row_context_for_candidate(match["element"])
                } for match in all_matches
            ]
        }
        
        return matches_found > 0, matched_html, debug_info

    def _calculate_context_match_score_with_details(self, element, target_text, context_before, context_after):
        """앞뒤 컨텍스트를 고려한 매칭 점수 계산 (상세 정보 포함)"""
        try:
            # 🆕 현재 요소 주변 컨텍스트 추출 (테이블 행 또는 일반 요소 모두 지원)
            row_text = ""
            td_elements = []
            context_available = False
            
            # 1. 테이블 행(<tr>)이 있는 경우
            if element.parent and element.parent.parent and element.parent.parent.name == 'tr':
                parent_tr = element.parent.parent
                # 같은 행의 모든 텍스트 수집
                for td in parent_tr.find_all('td'):
                    td_text = re.sub(r'\s+', ' ', td.get_text().replace('\u00a0', ' ').strip())
                    row_text += td_text + " "
                    td_elements.append({
                        'element': td,
                        'text': td_text,
                        'is_target': target_text in td_text
                    })
                context_available = True
            # 2. 일반 요소 (예: <p>, <div>)인 경우
            elif element.parent:
                # 현재 요소의 텍스트만 사용
                current_text = re.sub(r'\s+', ' ', element.string or element.get_text() or '').strip()
                row_text = current_text
                td_elements.append({
                    'element': element.parent,
                    'text': current_text,
                    'is_target': target_text in current_text
                })
                context_available = True
                
                # 🆕 디버깅: 비테이블 요소 처리
                print(f"📝 비테이블 요소 감지 (태그: {element.parent.name if element.parent else 'None'})")
                print(f"   요소 텍스트: {row_text[:50]}...")
            
            if context_available:
                row_text = row_text.strip()
                
                # 컨텍스트 매칭 점수 계산
                score = 0.0
                details = {
                    'row_text': row_text,
                    'td_elements': td_elements,
                    'target_text': target_text,
                    'context_before': context_before,
                    'context_after': context_after,
                    'before_score': 0.0,
                    'after_score': 0.0,
                    'pattern_score': 0.0,
                    'before_weight': 0.3,
                    'after_weight': 0.3,
                    'pattern_weight': 0.4
                }
                
                # 앞 컨텍스트 매칭
                if context_before:
                    before_score = self._calculate_text_similarity(row_text, context_before)
                    score += before_score * 0.3  # 앞 컨텍스트 30% 가중치
                    details['before_score'] = before_score
                    print(f"   🎯 앞 컨텍스트 매칭: {before_score:.3f} (찾는 것: '{context_before[:30]}...', 실제: '{row_text[:50]}...')")
                
                # 뒤 컨텍스트 매칭
                if context_after:
                    after_score = self._calculate_text_similarity(row_text, context_after)
                    score += after_score * 0.3  # 뒤 컨텍스트 30% 가중치
                    details['after_score'] = after_score
                    print(f"   🎯 뒤 컨텍스트 매칭: {after_score:.3f} (찾는 것: '{context_after[:30]}...', 실제: '{row_text[-50:]}...')")
                
                # 타겟 텍스트 주변 패턴 매칭
                if context_before and context_after:
                    # "앞컨텍스트 타겟텍스트 뒤컨텍스트" 패턴 검색
                    pattern = f"{context_before} {target_text} {context_after}"
                    pattern_score = self._calculate_text_similarity(row_text, pattern)
                    score += pattern_score * 0.4  # 패턴 매칭 40% 가중치
                    details['pattern_score'] = pattern_score
                    details['pattern'] = pattern
                    print(f"   🎯 패턴 매칭: {pattern_score:.3f}")
                
                print(f"   🏆 최종 컨텍스트 점수: {score:.3f}")
                
                details['final_score'] = min(score, 1.0)
                return min(score, 1.0), details
                
        except Exception as e:
            print(f"   ❌ 컨텍스트 계산 오류: {e}")
            return 0.0, {'error': str(e)}
        
        print(f"   ❌ 컨텍스트를 찾을 수 없음 (element.parent: {element.parent is not None if element else False})")
        return 0.0, {'error': 'No parent tr found or element is None'}

    def _get_html_context_with_siblings(self, element, context_range=5):
         """매칭된 요소의 앞뒤 형제 요소들을 포함한 HTML 컨텍스트 반환"""
         try:
             if not element:
                 return "None"
             
             # 텍스트 노드인 경우 부모 태그를 기준으로 형제 요소들 찾기
             if hasattr(element, 'parent') and element.parent:
                 # 텍스트 노드의 부모 태그 (예: <td>)
                 parent_tag = element.parent
                 
                 # 부모 태그의 부모에서 형제 태그들 찾기 (예: <tr> 안의 <td>들)
                 if parent_tag.parent and parent_tag.parent.name == 'tr':
                     grandparent = parent_tag.parent
                     siblings = [child for child in grandparent.children if hasattr(child, 'name') and child.name == 'td']
                     
                     # 현재 부모 태그의 인덱스 찾기
                     current_index = -1
                     for i, sibling in enumerate(siblings):
                         if sibling == parent_tag:
                             current_index = i
                             break
                     
                     if current_index != -1 and len(siblings) > 1:
                         # 앞뒤 컨텍스트 범위 계산
                         start_idx = max(0, current_index - context_range)
                         end_idx = min(len(siblings), current_index + context_range + 1)
                         
                         # 컨텍스트 요소들 수집
                         context_elements = siblings[start_idx:end_idx]
                         
                         # HTML 문자열 생성
                         context_html = ""
                         for i, sibling in enumerate(context_elements):
                             if i + start_idx == current_index:
                                 # 현재 매칭된 요소는 하이라이팅
                                 context_html += f"<!-- 🎯 매칭된 요소 -->\n{str(sibling)}\n<!-- 🎯 매칭된 요소 끝 -->\n"
                             else:
                                 context_html += f"{str(sibling)}\n"
                         
                         return context_html.strip()
                 
                 # 형제 요소를 찾지 못한 경우 부모 태그만 반환
                 return str(parent_tag)
             
             # 텍스트 노드가 아닌 경우 요소 자체 반환
             return str(element)
             
         except Exception as e:
             return f"HTML 컨텍스트 추출 오류: {str(e)}"

    def _get_row_context_for_candidate(self, element):
         """후보 요소의 행 전체 컨텍스트를 원본 HTML 상태로 반환 (하이라이팅 적용 전)"""
         try:
             if not element or not hasattr(element, 'parent') or not element.parent:
                 return "None"
             
             # 텍스트 노드의 부모 태그 (예: <td>)
             parent_tag = element.parent
             
             # 부모 태그의 부모에서 형제 태그들 찾기 (예: <tr> 안의 <td>들)
             if parent_tag.parent and parent_tag.parent.name == 'tr':
                 grandparent = parent_tag.parent
                 siblings = [child for child in grandparent.children if hasattr(child, 'name') and child.name == 'td']
                 
                 # 현재 부모 태그의 인덱스 찾기
                 current_index = -1
                 for i, sibling in enumerate(siblings):
                     if sibling == parent_tag:
                         current_index = i
                         break
                 
                 if current_index != -1 and len(siblings) > 1:
                     # 전체 행의 HTML 컨텍스트 생성 (하이라이팅 적용 전)
                     context_html = ""
                     for i, sibling in enumerate(siblings):
                         if i == current_index:
                             # 현재 매칭된 요소는 표시
                             context_html += f"<!-- 🎯 탐색 중인 요소 -->\n{str(sibling)}\n<!-- 🎯 탐색 중인 요소 끝 -->\n"
                         else:
                             context_html += f"{str(sibling)}\n"
                     
                     return context_html.strip()
             
             # 형제 요소를 찾지 못한 경우 부모 태그만 반환
             return str(parent_tag)
             
         except Exception as e:
             return f"행 컨텍스트 추출 오류: {str(e)}"


    def _apply_highlighting(self, best_match, soup, css_class, tooltip, highlighted_elements):
        """하이라이팅 적용 (기존 로직 유지)"""
        element = best_match["element"]
        text_content = best_match["text"]
        
        
        # 하이라이팅된 HTML 요소 생성
        highlighted_span = soup.new_tag('span', **{'class': css_class})
        highlighted_span.string = text_content
        
        # 툴팁 추가
        tooltip_span = soup.new_tag('span', **{'class': 'highlight-tooltip'})
        tooltip_span.string = tooltip
        highlighted_span.append(tooltip_span)
        
        
        # 원본 텍스트 노드를 하이라이팅된 요소로 교체
        element.replace_with(highlighted_span)
        
        
        highlighted_elements.add(element)
        matched_html = str(highlighted_span.parent)  # 매칭된 HTML 요소 저장
        
        return True, matched_html, {}


    def _calculate_text_similarity(self, text1, text2):
        """두 텍스트 간의 유사도 계산 (0.0 ~ 1.0)"""
        if not text1 or not text2:
            return 0.0
        
        # 공백 정규화
        text1_norm = re.sub(r'\s+', ' ', text1.strip())
        text2_norm = re.sub(r'\s+', ' ', text2.strip())
        
        # difflib을 사용한 유사도 계산
        matcher = difflib.SequenceMatcher(None, text1_norm, text2_norm)
        ratio = matcher.ratio()
        
        # 🆕 디버깅: 유사도가 낮을 때 비교 대상 로그 출력
        if ratio > 0 and ratio < 0.3 and len(text1_norm) > 20 and len(text2_norm) > 20:
            print(f"🔍 유사도 계산: {ratio:.3f}")
            print(f"   비교 대상 1 ({len(text1_norm)}자): {text1_norm[:50]}...")
            print(f"   비교 대상 2 ({len(text2_norm)}자): {text2_norm[:50]}...")
        
        return ratio


    def _extract_actual_context_from_group(self, valid_elements, group_text):
        """그룹의 실제 HTML 컨텍스트 추출 (앞뒤 셀 내용)"""
        try:
            if not valid_elements:
                return None, None
            
            # 첫 번째 요소의 부모 행 찾기
            first_element = valid_elements[0]
            if not first_element.parent or not first_element.parent.parent:
                return None, None
            
            parent_tr = first_element.parent.parent
            if parent_tr.name != 'tr':
                return None, None
            
            # 행의 모든 td 요소들 수집
            tds = parent_tr.find_all('td')
            if not tds:
                return None, None
            
            # 그룹의 첫 번째와 마지막 요소가 속한 td의 인덱스 찾기
            first_td_index = -1
            last_td_index = -1
            
            for i, td in enumerate(tds):
                if first_element.parent == td:
                    first_td_index = i
                if valid_elements[-1].parent == td:
                    last_td_index = i
            
            if first_td_index == -1 or last_td_index == -1:
                return None, None
            
            # 앞 컨텍스트 추출 (첫 번째 td 이전)
            before_context = None
            if first_td_index > 0:
                before_td = tds[first_td_index - 1]
                before_text = re.sub(r'\s+', ' ', before_td.get_text().replace('\u00a0', ' ').strip())
                if before_text:
                    before_context = before_text
            
            # 뒤 컨텍스트 추출 (마지막 td 이후)
            after_context = None
            if last_td_index < len(tds) - 1:
                after_td = tds[last_td_index + 1]
                after_text = re.sub(r'\s+', ' ', after_td.get_text().replace('\u00a0', ' ').strip())
                if after_text:
                    after_context = after_text
            
            return before_context, after_context
            
        except Exception as e:
            print(f"🔍 컨텍스트 추출 오류: {str(e)}")
            return None, None
