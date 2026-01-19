import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import urllib.parse
import json
from ttkwidgets import CheckboxTreeview
import ast
import webbrowser
from collections import Counter  # 요소의 개수를 쉽게 계산할 수 있는 Counter 모듈 불러오기
import xlwrite


def url_to_search(administrative_code, search_keyword):
    """
    검색할 URL 주소 만들기
    :param administrative_code: 시군구 코드 dictionary
    :param search_keyword: 검색할 키워드
    :return: URL주소
    """
    # 한글을 URL 인코딩(퍼센트 인코딩, Percent Encoding) 방식으로 변환
    encoded_search_keyword = urllib.parse.quote(search_keyword)

    url = ('https://www.elis.go.kr/main/totSrchList?'
           f'ctpvCd={administrative_code[0]}'
           f'&sggCd={administrative_code[1]}'
           '&curPage=1'
           '&category=LAW'
           f'&srchKwd={encoded_search_keyword}')

    return url


def get_ordinance_link(administrative_code, search_keyword):
    """
    시군구 코드로 자치법규정보시스템에서 정보 가져오기
    :param administrative_code: 시군구코드(search_parameter) ex) [47, 920]
    :param search_keyword: 검색 키워드 ex) [공무원 출장]
    :return: (1.조례제목 2.제개정일 3.조례관리담당부서 4.조례페이지파라미터) 딕셔너리자료
    """

    ###############################################################################
    # 1.검색준비
    ###############################################################################
    # 한글을 URL 인코딩(퍼센트 인코딩, Percent Encoding) 방식으로 변환
    encoded_search_keyword = urllib.parse.quote(search_keyword.replace(' ', '+'))
    # url주소 작성
    url = ('https://www.elis.go.kr/main/totSrchList?'
           f'ctpvCd={administrative_code[0]}'
           f'&sggCd={administrative_code[1]}'
           '&curPage=1'
           '&category=LAW'
           f'&srchKwd={encoded_search_keyword}')

    # 요청 헤더 설정
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    #################################################
    # 2.requests로 요청하여 beautifulsoup로 크롤링
    #################################################
    # 웹페이지 요청
    req = requests.get(url, headers=headers)
    # BeautifulSoup로 파싱
    soup = BeautifulSoup(req.text, "html.parser")
    # 조례 제목 불러오기 조회가 안될경우 None retrun
    ordinance_element = soup.select_one('#container > div.inner > div > div.search-result-list > div > a > strong')
    if ordinance_element is None:
        return None
    ordinance_title = ordinance_element.get_text()[367:-12]
    # 조례에 관한 정보 불러오기
    ordinance_info = soup.select_one('#container > div.inner > div > div.search-result-list > div > a > span').get_text()
    # 조례 제개정일 불러오기
    ordinance_update_date = ordinance_info.split(' ')[2]
    # 조례 관리담당부서 불러오기
    ordinance_department = ' '.join(ordinance_info.split(' ')[3:])
    # 조례 페이지 파라미터 불러오기
    ordinance_page_parameters = soup.select_one('#container > div.inner > div > div.search-result-list > div > div > a').get('onclick')
    # 원하는 파라미터 추출
    ordinance_page_parameters = (
        ordinance_page_parameters[ordinance_page_parameters.find("s('") + 3:
                                  ordinance_page_parameters.find("', ")],
        ordinance_page_parameters[ordinance_page_parameters.find("', '") + 4:
                                  ordinance_page_parameters.find("');")])
    ordinance_page = (f"https://www.elis.go.kr/allalr/"
                      f"selectAlrBdtOne?alrNo={ordinance_page_parameters[0]}"
                      f"&histNo={ordinance_page_parameters[1]}&menuNm=main")

    #################################################
    # 3.조례 명에 키워드가 있는지 확인 없으면 None으로 리턴
    # 유사 검색으로 다른 조례가 검색되지 않도록 하기 위함
    #################################################
    for word in search_keyword.split(' '):
        if word not in ordinance_title:
            return None

    #################################################
    # 4.조회된 결과값 딕셔너리화
    #################################################
    result_dict = {
        'title': ordinance_title,
        'update_date': ordinance_update_date,
        'department': ordinance_department,
        'page_address': ordinance_page
    }

    # print(ordinance_title, ordinance_update_date, ordinance_department, ordinance_page_parameters)
    return result_dict


def get_text_excluding_child_p(element):
    """
    부모 <p>에서 자식 <p> 태그(중첩) 내용을 제외하고,
    순수하게 부모 자신이 가진 텍스트만 추출한다.
    """
    text_parts = []
    for child in element.children:
        # child.name 이 None이면 텍스트 노드이므로 그대로 사용
        if child.name is None:
            # 공백/줄바꿈 정리
            text_parts.append(child.strip())
        # 자식이 <p>면(즉 중첩된 p) 부모 텍스트에서는 제외
        elif child.name == 'p':
            continue
        # 그 이외 태그(<strong> 등)는 내부 텍스트만 추출
        else:
            text_parts.append(child.get_text(strip=True))
    return " ".join(t for t in text_parts if t).strip()


def parse_paragraph(p_tag):
    """
    1) 현재 <p> 태그가 가진 텍스트(자식 <p> 제외)를 추출
    2) 자식 <p>를 순회하며 재귀적으로 같은 작업을 수행
    3) 각 결과를 줄바꿈을 넣어 리스트로 반환
    """
    lines = []
    # 1) 우선 부모 <p> 자체 텍스트
    parent_text = get_text_excluding_child_p(p_tag)
    if parent_text:
        lines.append(parent_text)

    # 2) 자식 <p>들에 대해 재귀 파싱
    #    recursive=False 로 해야 '직계 자식'만 순회 (손자 이상의 <p> 중복 방지)
    for child_p in p_tag.find_all('p', recursive=False):
        lines.extend(parse_paragraph(child_p))

    return lines


def get_ordinance_clause_titles(ordinance_url):
    """
    주어진 조례(ordinance) 웹페이지에서 조 제목과 조항 번호에 해당하는 URL 정보를 추출합니다.

    Args:
        ordinance_url (str): 조례 페이지의 URL.

    Returns:
        tuple: 두 개의 딕셔너리로 구성된 튜플을 반환합니다.
            - clause_title_to_url (dict): 조 제목(문자열) -> URL 경로(문자열) 매핑.
            - article_number_to_url (dict): 조항 번호(정수) -> URL 경로(문자열) 매핑.
    """

    # 브라우저처럼 보이도록 요청 헤더를 설정합니다.
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    # 지정한 URL에 GET 요청을 보내 웹페이지의 HTML을 가져옵니다.
    response = requests.get(ordinance_url, headers=headers)

    # BeautifulSoup를 사용해 HTML 텍스트를 파싱합니다.
    soup = BeautifulSoup(response.text, "html.parser")

    # CSS 선택자를 사용해 네비게이션 내의 조 항목(a 태그) 요소들을 찾습니다.
    clause_link_elements = soup.select('#cms-lnb > ul > li.curr > ul > li.curr > ul > li > a')

    # 조 제목과 조항 번호에 대응하는 URL 정보를 저장할 딕셔너리를 초기화합니다.
    clause_title_to_url = {}
    article_number_to_url = {}

    # 찾은 각 a 태그 요소에 대해 텍스트와 href 속성에서 필요한 정보를 추출합니다.
    for link in clause_link_elements:
        link_text = link.get_text()  # 예: "제3조 (사례)"
        href_value = link.get('href')  # 예: "/some/path"

        # href 속성이 없는 경우 건너뜁니다.
        if not href_value:
            continue

        # -- 조 제목 추출 --
        # 텍스트 내에서 '(' 문자의 위치 바로 다음부터 뒤에서 두 번째 문자까지를 조 제목으로 간주합니다.
        # 예: "제3조 (사례)" 에서 '(' 뒤부터 ')' 직전까지 "사례"가 추출됩니다.
        title_start_idx = link_text.find('(') + 1
        clause_title = link_text[title_start_idx:-2]

        # -- 조항 번호 추출 --
        # 텍스트 내에서 '제'와 '조' 사이의 숫자를 추출하여 정수로 변환합니다.
        # 예: "제3조 (사례)" 에서 '제' 뒤부터 '조' 직전까지 "3"을 추출합니다.
        article_start_idx = link_text.find('제') + 1
        article_end_idx = link_text.find('조')
        article_number_str = link_text[article_start_idx:article_end_idx]

        try:
            article_number = int(article_number_str)
        except ValueError:
            # 숫자 변환에 실패하면 해당 항목은 건너뜁니다.
            continue

        # href의 첫 번째 문자는 불필요한 문자(예: '/')로 가정하여 제거합니다.
        clean_href = href_value[1:]

        # 추출한 정보를 딕셔너리에 저장합니다.
        clause_title_to_url[clause_title] = clean_href
        article_number_to_url[article_number] = clean_href

    return clause_title_to_url, article_number_to_url


class OrdinanceCompareApp(tk.Tk):
    """
    메인 애플리케이션 클래스.
    tkinter.Tk를 상속받아 프로그램 전체의 윈도우 창 역할을 함.
    """

    def __init__(self):
        super().__init__()

        self.title("자치법규 조례 비교 시스템")
        self.geometry("1000x600")  # 윈도우 크기 설정

        # json파일에서 시군구 코드 딕셔너리 불러오기
        with open('administrative_code.json', 'r', encoding='utf-8') as file:
            self.admin_code_dict = json.load(file)  # 시군구 코드 불러오기

        # 각종 변수 초기화
        self.selected_regions = []  # 시/군/구 선택 목록
        self.ordinance_search_keyword = tk.StringVar()  # 조례 검색 키워드
        self.ordinance_clause_keyword = tk.StringVar()  # 조례 검색 키워드
        self.admin_code_dict_to_compare = None  # 비교할 시군구 초기 변수선언
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }  # 요청 헤더 설정
        self.entry_search_keyword = None  # 검색할 키워드 선언
        self.result_view = None  # 결과 뷰 선언
        self.adm_select_tree = None  # 시군구 선택 트리뷰 선언
        self.admin_ordinance_clause = None  # 조례조항 선언
        self.xlwrite = None

        # 비교 모드 선택(조례비교 / 세부조항 비교)를 위한 변수
        self.compare_mode = tk.StringVar(value="조례비교")

        # 날짜 필터 범위(예시)
        self.start_date = tk.StringVar()
        self.end_date = tk.StringVar()

        # GUI 구성
        self.create_widgets()

    def create_widgets(self):
        """
        프로그램에 필요한 모든 위젯을 생성하고 배치(Layout)하는 메서드.
        """

        # ------------------------------ 좌측 시군구 선택 트리뷰 ------------------------------
        left_frame = ttk.Frame(self, padding="5 5 5 5")
        left_frame.pack(side=tk.LEFT, fill=tk.Y)

        # 스타일 변경 (폰트 크기 조정)
        style = ttk.Style()
        style.configure("Treeview", font=("Arial", 14))  # 트리뷰 텍스트 크기 조정
        style.configure("Treeview.Heading", font=("Arial", 14))  # 헤더 텍스트 크기 조정

        # 시군구 선택 트리뷰 위젯
        def administrative_select_tree():
            # ------------------------------ 시군구 선택 영역 ------------------------------
            self.adm_select_tree = CheckboxTreeview(left_frame)
            self.adm_select_tree.heading("#0", text="지역 목록")
            self.adm_select_tree.pack(fill=tk.BOTH, expand=True)

            # 행정구역 데이터 추가
            for region_name, admin_dict in self.admin_code_dict.items():
                # 광역시도(최상위 노드) 추가
                self.adm_select_tree.insert("", "end", region_name, text=region_name)
                # 해당 광역시도의 시군구(하위 노드) 추가
                for admin_name, code in admin_dict.items():
                    self.adm_select_tree.insert(region_name, "end", {admin_name: code}, text=admin_name.split(' ')[-1])

            # 전체 선택 버튼 추가
            select_all_button = tk.Button(left_frame, text="전체 선택", command=self.select_all)
            select_all_button.pack(side="left", expand=True)

            # 전체 선택 해제 버튼
            deselect_all_button = tk.Button(left_frame, text="전체 해제", command=self.deselect_all)
            deselect_all_button.pack(side="left", expand=True)

        # ------------------------------ 우측 조례명 검색 및 비교 모드 선택 영역 ------------------------------
        right_frame = ttk.Frame(self, padding="5 5 5 5")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        def search_keyword_widget():
            # 조례명 검색 키워드
            search_frame = ttk.Frame(right_frame)
            search_frame.pack(fill=tk.X)

            tk.Label(search_frame, text="조례명 검색 : ", width=15).pack(side=tk.LEFT, padx=(0, 5), pady=(0, 5))
            self.entry_search_keyword = ttk.Entry(search_frame, textvariable=self.ordinance_search_keyword, width=20)
            self.entry_search_keyword.pack(side=tk.LEFT, fill='both', padx=(0, 10), pady=(0, 5), expand=True)

            btn_search = ttk.Button(search_frame, text="조례검색", command=self.on_search)
            btn_search.pack(side=tk.LEFT, padx=(0, 10), pady=(0, 5))

            # # 조항 검색 키워드
            # search_frame = ttk.Frame(right_frame)
            # search_frame.pack(fill=tk.X)
            #
            # tk.Label(search_frame, text="세부조항 검색 : ", width=15).pack(side=tk.LEFT, padx=(0, 5), pady=(0, 5))
            # self.entry_clause_keyword = ttk.Entry(search_frame, textvariable=self.ordinance_clause_keyword, width=20)
            # self.entry_clause_keyword.pack(side=tk.LEFT, fill='both', padx=(0, 10), pady=(0, 5), expand=True)
            # btn_search = ttk.Button(search_frame, text="검색", command=self.on_search)
            # btn_search.pack(side=tk.LEFT, padx=(0, 10), pady=(0, 5))

        def compare_select_widget():
            # 비교 모드 선택
            mode_frame = ttk.Frame(right_frame, padding="5 5 5 5")
            mode_frame.pack(fill=tk.X)

            btn_search = ttk.Button(mode_frame, text="시군별 조항비교", command=self.compare_clause_titles)
            btn_search.pack(side=tk.LEFT, padx=(0, 10), pady=(0, 5))

            btn_search = ttk.Button(mode_frame, text="시군별 세부조항비교", command=self.compare_clause_titles)
            btn_search.pack(side=tk.LEFT, padx=(0, 10), pady=(0, 5))

        def print_result_view():
            # ------------------------------ 결과 표시 영역 ------------------------------
            result_frame = ttk.Frame(right_frame, padding="5 5 5 5")
            result_frame.pack(fill=tk.BOTH, expand=True)

            # Treeview 컬럼 정의
            columns = ("시군구", "조례제목", "제개정일", "담당부서")
            self.result_view = ttk.Treeview(result_frame, columns=columns, show="headings")

            # 각 컬럼별 설정 (헤더 및 정렬 방식 지정)
            column_settings = {
                "시군구": {"width": 100, "anchor": tk.CENTER},
                "조례제목": {"width": 300, "anchor": tk.CENTER},
                "제개정일": {"width": 100, "anchor": tk.CENTER},
                "담당부서": {"width": 100, "anchor": tk.CENTER}
            }

            for col, settings in column_settings.items():
                self.result_view.heading(col, text=col)
                self.result_view.column(col, **settings)

            # 더블클릭 이벤트 바인딩 (조례 페이지로 이동)
            self.result_view.bind("<Double-1>", self.goto_ordinance_page)

            # 수직 스크롤바 추가
            vsb = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_view.yview)
            self.result_view.configure(yscrollcommand=vsb.set)

            # Treeview 및 Scrollbar 배치
            self.result_view.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            vsb.pack(side=tk.LEFT, fill=tk.Y)

        administrative_select_tree()
        search_keyword_widget()
        compare_select_widget()
        print_result_view()

    def on_search(self):
        """체크된 항목들의 ID 리스트를 반환"""
        checked_items = self.adm_select_tree.get_checked()
        checked_admin = {k: v for item in checked_items for k, v in ast.literal_eval(item).items()}
        keyword = self.entry_search_keyword.get()

        self.verify_and_fetch(checked_admin, keyword)

    def select_all(self):
        """
        모든 항목을 'checked' 상태로 변경하는 함수.
        트리뷰 내 모든 항목과 하위 항목을 재귀적으로 선택 상태로 변경합니다.
        """

        def change_state_recursive(item, state):
            """주어진 항목과 모든 하위 항목의 상태를 변경"""
            self.adm_select_tree.change_state(item, state)  # 현재 항목의 상태 변경
            for child in self.adm_select_tree.get_children(item):  # 하위 항목 순회
                change_state_recursive(child, state)

        # 최상위 항목부터 전체 선택
        for root_item in self.adm_select_tree.get_children():
            change_state_recursive(root_item, "checked")

    def deselect_all(self):
        """
        모든 항목을 'unchecked' 상태로 변경하는 함수.
        트리뷰 내 모든 항목과 하위 항목을 재귀적으로 선택 해제합니다.
        """

        def change_state_recursive(item, state):
            """주어진 항목과 모든 하위 항목의 상태를 변경"""
            self.adm_select_tree.change_state(item, state)  # 현재 항목의 상태 변경
            for child in self.adm_select_tree.get_children(item):  # 하위 항목 순회
                change_state_recursive(child, state)

        # 최상위 항목부터 전체 선택 해제
        for root_item in self.adm_select_tree.get_children():
            change_state_recursive(root_item, "unchecked")

    def treeview_clear(self):
        pass

    def verify_and_fetch(self, dict_to_search, search_keyword):
        """
        시군구별 조례를 조회하여 각 정보를 딕셔너리 형태로 반환하는 함수.

        1. 주어진 행정구역 딕셔너리(dict_to_search)에서 시군구별 조례 정보를 조회합니다.
        2. 조회된 정보를 UI(Treeview)에 추가하며, 조회된 조례가 없을 경우 '조례 없음'을 표시합니다.
        3. 조회 결과를 딕셔너리(self.admin_code_dict_to_compare)에 저장하고 출력합니다.

        :param dict_to_search: 조회할 시군구 딕셔너리 (예: {"경북 봉화군": {"region_code": "47", "district_code": "920"}})
        :param search_keyword: 검색할 키워드 (예: "실종자 수색")
        :return: 조회된 조례 정보를 포함하는 딕셔너리
                 예: {"경북 봉화군": {"title": "실종자 수색 지원 조례",  # 조례 제목
                                    "update_date": "2024.12.01",    # 제개정일
                                    "department": "안전건설과",      # 담당 부서
                                    "page_parameters": "[]"         # 조례 페이지 파라미터
                                    }}
        """

        # 비교할 시군구 데이터를 저장할 딕셔너리 초기화
        self.admin_code_dict_to_compare = {}

        # 기존 결과 리스트뷰 초기화
        self.result_view.delete(*self.result_view.get_children())

        for region_name, codes in dict_to_search.items():
            # 시군구별 조례 정보 조회
            ordinance_info = get_ordinance_link(codes, search_keyword)

            # 조회된 정보가 없을 경우 '조례 없음'으로 표시
            if ordinance_info is None:
                self.result_view.insert("", "end", values=[region_name, '조례 없음'])
                print(region_name, '조례 없음')
            else:
                self.result_view.insert("", "end", values=[
                    region_name,
                    ordinance_info.get('title', '제목 없음'),
                    ordinance_info.get('update_date', '날짜 없음'),
                    ordinance_info.get('department', '부서 없음')
                ])
                print(region_name, ordinance_info['title'])

            # UI 업데이트 (즉시 반영)
            self.result_view.update()

            # 조회된 조례 정보를 저장
            self.admin_code_dict_to_compare[region_name] = ordinance_info

        # 최종 조회된 딕셔너리 출력
        print(self.admin_code_dict_to_compare)

        # 엑셀 작성
        self.xlwrite = xlwrite.XlWrite()
        self.xlwrite.create_admin_search_resurlt(self.admin_code_dict_to_compare)




    def goto_ordinance_page(self, event):
        """더블클릭 시 해당 조례 제목의 웹페이지로 이동"""
        item = self.result_view.selection()[0]  # 선택된 항목 가져오기
        values = self.result_view.item(item, "values")  # 해당 행의 값 가져오기
        administration = values[0]  # 두 번째 열 (조례제목)

        print(self.admin_code_dict_to_compare[administration], administration)

        if self.admin_code_dict_to_compare[administration] is not None:
            page_address = self.admin_code_dict_to_compare[administration]['page_address']
            webbrowser.open(page_address)  # 브라우저에서 URL 열기
        else:
            print("URL이 등록되지 않은 조례입니다.")

    def apply_date_filter(self):
        """
        날짜 필터 적용 버튼 클릭 시.
        이미 표시된 결과를 다시 필터링하거나,
        새 검색을 요청할 수 있음.
        TODO: 실제 로직 구현.
        """
        start_date_str = self.start_date.get()
        end_date_str = self.end_date.get()

        # 유효성 검사
        try:
            if start_date_str:
                datetime.strptime(start_date_str, "%Y-%m-%d")
            if end_date_str:
                datetime.strptime(end_date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("에러", "날짜 형식이 잘못되었습니다. (예: 2023-01-01)")
            return

        # TODO: 실제 필터 로직 구현(트리뷰에서 날짜 컬럼 참조 등)
        messagebox.showinfo("정보", f"날짜 필터를 적용했습니다.\n시작일: {start_date_str}, 종료일: {end_date_str}")

    def update_compare_mode(self):
        """
        라디오 버튼(비교 모드) 변경 시 호출됨.
        '조례비교' 또는 '세부조항' 모드에 따라 표시할 테이블 구조를 바꾸거나,
        세부 로직을 분기할 수 있음.
        """
        mode = self.compare_mode.get()
        messagebox.showinfo("비교 모드 변경", f"현재 비교 모드: {mode}")
        # TODO: 트리뷰 컬럼 구조를 바꾸거나 별도의 UI 업데이트가 필요하면 구현

    def export_to_excel(self):
        """
        '엑셀로 내보내기' 버튼 클릭 시.
        현재 트리뷰에 표시된 데이터를 Excel 파일로 저장.
        TODO: openpyxl 또는 xlsxwriter 등을 사용하여 구현 가능.
        """
        # 파일 저장 다이얼로그
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if not file_path:
            return  # 사용자가 취소

        # TODO: 실제 엑셀 저장 로직 구현
        # 예: openpyxl 사용하여 각 행/열에 트리뷰 데이터 삽입 후 저장

        messagebox.showinfo("엑셀 내보내기", f"엑셀 파일로 저장했습니다.\n경로: {file_path}")

    def on_exit(self):
        """
        '종료' 버튼 클릭 시 프로그램 종료.
        """
        self.destroy()

    def compare_clause_titles(self):

        # 기존 결과 리스트뷰 초기화
        self.result_view.delete(*self.result_view.get_children())

        # Treeview 컬럼 재정의
        columns = ("시군구", "조례제목", "상태")
        self.result_view["columns"] = columns

        # 각 컬럼별 설정 (헤더 및 정렬 방식 지정)
        column_settings = {
            "시군구": {"width": 100, "anchor": tk.CENTER},
            "조례제목": {"width": 300, "anchor": tk.CENTER},
            "상태": {"width": 100, "anchor": tk.CENTER},
        }

        for col, settings in column_settings.items():
            self.result_view.heading(col, text=col)
            self.result_view.column(col, **settings)

        admin_to_compare = self.admin_code_dict_to_compare

        admin_clause_titles = {}

        for admin, value in admin_to_compare.items():
            if value is not None:
                clause_title_to_url, article_number_to_url = get_ordinance_clause_titles(value['page_address'])
                admin_clause_titles[admin] = clause_title_to_url
                self.result_view.insert("", "end", value=[admin,
                                                          admin_to_compare[admin]['title'],
                                                          '조회 됨'])

            # url 정보가 없을경우 없음으로 표기
            else:
                admin_clause_titles[admin] = None
                self.result_view.insert("", "end", value=[admin, '조례없음'])

            # UI 업데이트 (즉시 반영)
            self.result_view.update()

        print(admin_clause_titles)

        # ---------- 조항 많은것 부터 내림차순으로 정렬 ----------
        # 인덱스 값(항목명)들의 등장 횟수를 저장할 Counter 객체 생성
        index_counts = Counter()

        # 데이터에서 각 지역별 항목명(키 값)을 수집하여 등장 횟수를 계산
        for region, sub_dict in admin_clause_titles.items():
            if sub_dict:  # None 값이 아닌 경우만 처리
                index_counts.update(sub_dict.keys())  # 항목명(인덱스 값)의 등장 횟수를 업데이트

        # 중복을 제거한 후 등장 횟수 기준으로 내림차순 정렬
        sorted_indices = sorted(index_counts.keys(), key=lambda x: index_counts[x], reverse=True)

        print(sorted_indices)

        self.xlwrite.create_compare_clause_titles_sheet(sorted_indices, admin_clause_titles)

        self.xlwrite.xl_workbook.close()


if __name__ == "__main__":
    app = OrdinanceCompareApp()
    app.mainloop()
