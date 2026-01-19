import difflib
import re
import json


def create_tabbed_comparison_html(clause_data):
    """
    조항별 탭을 제공하는 HTML 비교 페이지 생성 함수

    Args:
        clause_data (dict): 조항별, 시군구별, 문단별 데이터가 담긴 중첩 딕셔너리

    Returns:
        str: 비교 결과를 담은 HTML 문서
    """
    # 조항 목록 (탭으로 표시될 항목들)
    clause_titles = list(clause_data.keys())

    # HTML 문서의 기본 구조와 스타일 설정
    html_output = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>시군구별 조례 비교</title>
        <style>
            body { 
                font-family: 'Malgun Gothic', Arial, sans-serif; 
                padding: 20px; 
                line-height: 1.6; 
                max-width: 1200px;
                margin: 0 auto;
                color: #333;
            }
            h1 {
                color: #2c3e50;
                text-align: center;
                margin-bottom: 20px;
            }
            .subtitle {
                color: #555;
                text-align: center;
                margin-top: -15px;
                margin-bottom: 30px;
                font-size: 16px;
            }

            /* 탭 스타일 */
            .tabs {
                display: flex;
                flex-wrap: wrap;
                margin-bottom: 20px;
                border-bottom: 2px solid #4a6ea9;
            }
            .tab-button {
                padding: 10px 20px;
                background-color: #f0f5ff;
                border: none;
                border-radius: 5px 5px 0 0;
                margin-right: 5px;
                cursor: pointer;
                font-weight: bold;
                color: #2c3e50;
                font-size: 16px;
            }
            .tab-button:hover {
                background-color: #d0e0ff;
            }
            .tab-button.active {
                background-color: #4a6ea9;
                color: white;
            }

            /* 탭 내용 영역 */
            .tab-content {
                display: none;
            }
            .tab-content.active {
                display: block;
            }

            /* 비교 테이블 스타일 */
            .paragraph-section {
                border: 1px solid #ddd;
                border-radius: 8px;
                overflow: hidden;
                margin-bottom: 20px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            }
            .paragraph-title {
                background-color: #e0e7f7;
                padding: 8px 15px;
                font-weight: bold;
                color: #2c3e50;
                border-bottom: 1px solid #ccd7f0;
            }
            .diff-row { 
                display: flex;
                flex-direction: row;
                border-bottom: 1px solid #e4e4e4;
            }
            .diff-row:last-child {
                border-bottom: none;
            }
            .city-column {
                width: 120px;
                padding: 15px;
                background-color: #f0f5ff;
                font-weight: bold;
                color: #2c3e50;
                display: flex;
                align-items: center;
                border-right: 1px solid #ddd;
            }
            .content-column {
                flex: 1;
                padding: 15px;
                background-color: #f9f9f9;
                line-height: 1.7;
            }
            .diff { 
                background-color: #ffcccc; 
                padding: 2px 4px;
                border-radius: 3px;
                display: inline-block;
            }
            .item-num {
                font-weight: bold;
                margin-right: 5px;
            }

            /* 반응형 디자인 */
            @media (max-width: 768px) {
                .city-column {
                    width: 80px;
                    font-size: 14px;
                    padding: 10px;
                }
                .content-column {
                    padding: 10px;
                    font-size: 14px;
                }
                .tab-button {
                    padding: 8px 12px;
                    font-size: 14px;
                }
            }
        </style>
    </head>
    <body>
        <h1>시군구별 조례 비교</h1>
        <p class="subtitle">조항별 내용 비교 및 차이점 분석</p>

        <!-- 탭 버튼 영역 -->
        <div class="tabs">
    """

    # 탭 버튼 생성
    for i, title in enumerate(clause_titles):
        active_class = "active" if i == 0 else ""
        html_output += f'<button class="tab-button {active_class}" onclick="openTab(event, \'{title}\')">{title}</button>\n'

    html_output += """
        </div>

        <!-- 탭 내용 영역 -->
    """

    # 각 탭의 내용 생성
    for i, title in enumerate(clause_titles):
        active_class = "active" if i == 0 else ""
        html_output += f'<div id="{title}" class="tab-content {active_class}">\n'

        # 조항 데이터 가져오기
        paragraph_labels = clause_data[title]['paragraphs']
        cities_data = clause_data[title]['cities']
        city_names = list(cities_data.keys())

        # 각 문단별로 비교 섹션 생성
        for p_idx, p_label in enumerate(paragraph_labels):
            # 문단 제목 설정
            if p_label == 'title' or p_idx == 0:
                paragraph_title = "조항 제목"
            else:
                paragraph_title = f"항목 {p_idx}"

            html_output += f"""
            <div class="paragraph-section">
                <div class="paragraph-title">{paragraph_title}</div>
            """

            # 기준 텍스트 (첫 번째 시군구)
            base_city = city_names[0]
            base_text = cities_data[base_city][p_idx] if p_idx < len(cities_data[base_city]) else ""

            # 각 시군구별 내용 추가
            for city_name in city_names:
                # 해당 시군구의 문단 텍스트 가져오기
                city_text = cities_data[city_name][p_idx] if p_idx < len(cities_data[city_name]) else ""

                # 첫 번째 시군구가 아닌 경우 차이점 강조
                if city_name != base_city and city_text and base_text:
                    city_text_highlighted = highlight_differences(base_text, city_text)
                else:
                    city_text_highlighted = city_text

                # 조항 번호 강조 (예: "1.", "2." 등)
                item_num_match = re.match(r'^(\d+\.)', city_text_highlighted)
                if item_num_match:
                    item_num = item_num_match.group(1)
                    city_text_highlighted = city_text_highlighted.replace(item_num,
                                                                          f'<span class="item-num">{item_num}</span>',
                                                                          1)

                html_output += f"""
                <div class="diff-row">
                    <div class="city-column">{city_name}</div>
                    <div class="content-column">{city_text_highlighted}</div>
                </div>
                """

            html_output += """
            </div>
            """

        html_output += "</div>\n"

    # JavaScript 함수 추가
    html_output += """
        <script>
        function openTab(evt, tabName) {
            // 모든 탭 내용을 숨김
            var tabContents = document.getElementsByClassName("tab-content");
            for (var i = 0; i < tabContents.length; i++) {
                tabContents[i].className = tabContents[i].className.replace(" active", "");
            }

            // 모든 탭 버튼에서 active 클래스 제거
            var tabButtons = document.getElementsByClassName("tab-button");
            for (var i = 0; i < tabButtons.length; i++) {
                tabButtons[i].className = tabButtons[i].className.replace(" active", "");
            }

            // 선택한 탭 내용을 표시하고 버튼을 활성화
            document.getElementById(tabName).className += " active";
            evt.currentTarget.className += " active";
        }
        </script>
    </body>
    </html>
    """

    return html_output


def highlight_differences(base_text, compare_text):
    """
    두 텍스트 간의 차이점을 강조 표시하는 함수

    Args:
        base_text (str): 기준 텍스트
        compare_text (str): 비교할 텍스트

    Returns:
        str: 차이점이 강조 표시된, 비교 텍스트의 HTML
    """
    # 단어 단위로 비교하여 차이점 강조 표시
    s = difflib.SequenceMatcher(None, base_text, compare_text)
    result = ""

    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag == 'equal':  # 동일한 부분
            result += compare_text[j1:j2]
        elif tag in ['replace', 'insert']:  # 대체되거나 삽입된 부분
            result += f'<span class="diff">{compare_text[j1:j2]}</span>'
        # 'delete' 태그는 비교 텍스트에 없는 부분이므로 처리하지 않음

    return result


# 테스트 데이터: 여러 시군구의 조례 내용을 담은 구조화된 딕셔너리
clause_data = {
    '목적': {
        'paragraphs': ['paragraph1'],  # 목적 조항은 보통 단일 문단
        'cities': {
            '경상북도 구미시': [
                '이 조례는 구미시 공용차량을 취약계층 등과 공유하여 이를 이동수단으로 활용하거나 여가활동에 이용할 수 있게 함으로써 해당 구미시민의 생활편의와 삶의 질을 증진시킴과 더불어 유휴 자원 활용이라는 공유경제 정책을 실천하는 것을 목적으로 한다.'],
            '경기도 과천시': [
                '이 조례는 「공유재산 및 물품관리법 시행령」제75조제4호에 따라 과천시 공용차량을 과천시민과 공유하여 이를 이동수단으로 활용하거나 여가활동에 이용할 수 있게 함으로써 과천시민의 생활편의와 삶의 질을 증진시킴과 더불어 유휴 자원 활용이라는 공유경제 정책을 실천하는 것을 목적으로 한다.']
        }
    },
    '정의': {
        'paragraphs': ['title', 'definition1', 'definition2', 'definition3', 'definition4'],  # 정의 조항은 여러 문단으로 구성
        'cities': {
            '경상북도 구미시': [
                '제2조(정의) 이 조례에서 사용하는 용어의 뜻은 다음과 같다.',  # title
                '1. "공용차량"이란 구미시 본청, 직속기관, 사업소, 의회사무국이 소유하고 있는 승용자동차, 12인승 이하의 승합자동차 또는 1톤 이하의 화물차를 말한다.',
                # definition1
                '2. "공용차량 공유사업"이란 「관공서의 공휴일에 관한 규정」 제2조에 따른 공휴일, 같은 규정 제3조에 따른 대체공휴일 또는 토요일(이하 "공휴일 등"이라 한다)에 공무에 사용하지 아니하는 공용차량을 이 조례에 따라 구미시민(이하 "시민"이라 한다)에게 무상으로 이용할 수 있게 하는 사업을 말한다.',
                # definition2
                '3. "이용대상자"란 공용차량 공유사업에 따라 공휴일 등에 공용차량을 직접 운전하거나 자신을 위하여 다른 사람에게 운전하도록 지정하여 이용할 수 있는 제3조에 따른 시민을 말한다.',
                # definition3
                '4. "이용자"란 이용대상자 중에서 구미시장(이하"시장"이라 한다)의 승인을 받아 공휴일 등에 공용차량을 이용하는 사람을 말한다.'  # definition4
            ],
            '경기도 과천시': [
                '제2조(정의) 이 조례에서 사용하는 용어의 뜻은 다음과 같다.',
                '1. "공용차량"이란 과천시청 및 그 소속기관이 소유하고 있는 승용자동차 또는 12인승 이하의 승합자동차를 말한다.',
                '2. "공용차량 공유사업"이란 「관공서의 공휴일에 관한 규정」제2조 또는 제3조에 따른 공휴일 또는 대체공휴일이나 토요일(이하 "공휴일 등"이라 한다)에 공무에 사용하지 않는 공용차량을 이 조례에 따라 과천시민(이하 "시민"이라 한다)에게 무상으로 이용할 수 있게 하는 사업을 말한다.',
                '3. "이용대상자"란 공용차량 공유사업에 따라 공휴일등에 공용차량을 자신이 직접 운전하거나 자신을 위하여 다른 사람에게 운전하도록 지정하는 방법으로 이용할 수 있는 자격을 가진 시민을 말한다.',
                '4. "이용자"란 이용대상자 중에서 과천시장(이하 "시장"이라 한다)의 승인을 얻어 공휴일 등에 공용차량을 이용하는 자를 말한다.'
            ]
        }
    }
}

# HTML 비교 결과 생성
html_result = create_tabbed_comparison_html(clause_data)

# HTML 파일로 저장 (필요한 경우)
with open("조례비교결과_탭형식.html", "w", encoding="utf-8") as f:
    f.write(html_result)

print("HTML 비교 결과가 생성되었습니다.")

# 생성된 HTML 출력
html_result