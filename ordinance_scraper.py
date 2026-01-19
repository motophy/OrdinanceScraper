# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# noinspection SpellCheckingInspection
import logging
# noinspection SpellCheckingInspection
import urllib.parse
import requests
from bs4 import BeautifulSoup
from collections import Counter  # 요소의 개수를 쉽게 계산할 수 있는 Counter 모듈 불러오기
import xlwrite
from logging_config import setup_logging
from ordinance_scraper_constant import Constant


# ------ 함수 목록 ------
def encode_url(text: str) -> str:
    """
    텍스트를 퍼센트인코딩하는 함수
    :param text: 변환할 단어
    :return: 퍼센트 URL 인코딩
    """
    return urllib.parse.quote_plus(text)

def get_numbers_page_to_find(self):
    # URL 구성 및 요청
    base_url = 'https://www.elis.go.kr/main/totSrchList?ctpvCd=&sggCd=&curPage=1&srchKwd='
    full_url = base_url + encode_url(self.keyword)
    response = requests.get(full_url, headers=self.headers)

    # HTML 파싱
    soup = BeautifulSoup(response.text, "html.parser")

    # 총 검색 결과 수 추출
    result_count_selector = '#container > div > div > div.list-top > div.left > p > span'
    result_count_element = soup.select_one(result_count_selector)
    print(result_count_element)

    total_results = int(result_count_element.get_text().replace(',', ''))

    # 총 페이지 수 계산 (한 페이지당 10개 기준)
    ITEMS_PER_PAGE = 10
    total_pages = (total_results + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE  # 올림 계산

    print(total_pages)
    return total_pages

def get_ordinance_info(ordinance_element, search_keyword):
    """
    조례 정보 조회
    :param ordinance_element: 검색된 조례 요소
    :param search_keyword: 검색어
    :return: 조례정보 리스트 리턴, 조례제목과 불일치시 None 리턴
    """
    # 조례 제목
    ordinance_title = ordinance_element.select_one('a > strong').get_text()[367:-12]

    # 키워드 중에 조례에 하나라도 포함 되지 않으면 None 리턴
    keyword_list = search_keyword.split(' ')
    if any(word not in ordinance_title for word in keyword_list):
        return None

    # 조례제목에 키워드 내용이 없으면 None 리턴
    # if search_keyword not in ordinance_title and search_keyword.replace(' ', '') not in ordinance_title:
    #     return None

    # 조례관련정보 작성
    ordinance_info = ordinance_element.select_one('a > span').get_text()
    ordinance_admin = ' '.join(ordinance_info.split(' ')[:2])
    ordinance_update_date = ordinance_info.split(' ')[2]
    ordinance_department = ' '.join(ordinance_info.split(' ')[3:])
    # 페이지 주소 찾기
    ordinance_page_parameters = ordinance_element.select_one('a').get('onclick')
    ordinance_page_parameters = (
        ordinance_page_parameters[ordinance_page_parameters.find("s('") + 3:
                                  ordinance_page_parameters.find("', ")],
        ordinance_page_parameters[ordinance_page_parameters.find("', '") + 4:
                                  ordinance_page_parameters.find("');")])
    ordinance_page = (f"https://www.elis.go.kr/allalr/"
                      f"selectAlrBdtOne?alrNo={ordinance_page_parameters[0]}"
                      f"&histNo={ordinance_page_parameters[1]}&menuNm=main")

    return [ordinance_admin, ordinance_title,
            ordinance_update_date, ordinance_department, ordinance_page]


def get_ordinance_clause(soup):
    """
    HTML에서 조례 조항을 추출하여 딕셔너리로 반환하는 함수.

    :param soup: BeautifulSoup 객체 (조례 페이지의 HTML을 파싱한 객체)
    :return: 조례 조항을 포함하는 딕셔너리
             예: { "제1조": ["내용1", "내용2"], "제2조": ["내용3", "내용4"] }
    """

    ordinance_clause_dict = {}

    # 조항 요소 리스트 가져오기
    clause_elements = soup.select('#cms-lnb > ul > li > ul > li.curr > ul > li')

    for clause_element in clause_elements:
        # 조항 제목 추출
        clause_title = clause_element.get_text()

        # 조항제목이 없을경우 넘기기
        if '(' not in clause_title:
            continue

        # ------ 엑셀 시트제목 작성시 오류 방지 ------
        # 조항 제목이 30자 이상이면 30자로 맞추기
        if len(clause_title) > 30:
            clause_title = clause_title[:30]
        # 조항 제목에 개정등의 불필요문자 있으면 끊기
        if '<' in clause_title:
            clause_title = clause_title[clause_title.find('(') + 1:clause_title.find('<')]
        else:
            clause_title = clause_title[clause_title.find('(') + 1:clause_title.find(')')]

        # 조항 ID 추출
        clause_id = clause_element.select_one('a').get('href')[1:]

        # 해당 조항의 내용을 가져오기
        clause_container = soup.find(id=clause_id)
        if not clause_container:
            continue

        clauses = clause_container.select('p')
        clause_texts = []

        for clause in clauses:
            clause_html = str(clause)
            try:
                # 특정 HTML 구조(중첩된 <p> 태그)에서 첫 번째 조항을 올바르게 추출
                if '<p class="p-02">' in clause_html and '<p class="p-01">' in clause_html:
                    first_clause_html = clause_html.split('<p class="p-02">')[0] + '</p>'
                    first_clause_soup = BeautifulSoup(first_clause_html, "html.parser")
                    extracted_text = first_clause_soup.get_text().replace('\xa0', ' ')
                    clause_texts.append(extracted_text[extracted_text.find(') ') + 2:])
                else:
                    extracted_text = clause.get_text().replace('\xa0', ' ')
                    if '제' == extracted_text[0] and ') ' in extracted_text:
                        clause_texts.append(extracted_text[extracted_text.find(') ') + 2:])
                    else:
                        clause_texts.append(extracted_text)
            except:
                pass


        # 조항 데이터를 딕셔너리에 저장
        ordinance_clause_dict[clause_title] = clause_texts

    return ordinance_clause_dict


def get_sorted_indices_by_count(admin_clause_titles):
    # ---------- 조항 많은것 부터 내림차순으로 정렬 ----------
    # 인덱스 값(항목명)들의 등장 횟수를 저장할 Counter 객체 생성
    index_counts = Counter()

    # 데이터에서 각 지역별 항목명(키 값)을 수집하여 등장 횟수를 계산
    for region, sub_dict in admin_clause_titles.items():
        if sub_dict:  # None 값이 아닌 경우만 처리
            index_counts.update(sub_dict.keys())  # 항목명(인덱스 값)의 등장 횟수를 업데이트

    # 중복을 제거한 후 등장 횟수 기준으로 내림차순 정렬
    sorted_indices = sorted(index_counts.keys(), key=lambda x: index_counts[x], reverse=True)

    return sorted_indices


def get_sorted_indices_by_name(admin_clause_titles):
    # 인덱스 값(항목명)들을 저장할 집합 생성 (중복 제거)
    index_names = set()

    # 데이터에서 각 지역별 항목명(키 값)을 수집
    for region, sub_dict in admin_clause_titles.items():
        if sub_dict:  # None 값이 아닌 경우만 처리
            index_names.update(sub_dict.keys())  # 항목명 추가

    # 이름(알파벳/한글순) 기준으로 정렬
    sorted_indices = sorted(index_names)

    return sorted_indices


# ------ 클래스 선언 ------
class OrdinanceScraper:
    def __init__(self, search_keyword):
        logging.info('OrdinanceScraper 클래스 실행')

        # ----- 상수 선언 ----
        self.selector = Constant.SELECTOR
        self.header = Constant.HEADER

        # ----- 인스턴스 변수선언 ----

        # 요청 헤더 설정
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/"
                          "120.0.0.0 Safari/537.36"
        }


    def get_numbers_page_to_find(self):
        url = 'https://www.elis.go.kr/main/totSrchList?ctpvCd=&sggCd=&curPage=1&srchKwd='

        # 웹페이지 요청
        req = requests.get(url + encode_url(self.keyword), headers=self.headers)
        # BeautifulSoup로 파싱
        soup = BeautifulSoup(req.text, "html.parser")

        # 총 검색된 요소
        # sum_element_results_to_search = int(self.driver.find_element(by='xpath', value='//*[@id="container"]/div/div/div[3]/div[1]/p/span').text)
        element = soup.select_one('#container > div > div > div.list-top > div.left > p > span')
        print(element)
        sum_element_results_to_search = int(element.get_text().replace(',',''))

        numbers_page_to_find = sum_element_results_to_search // 10

        if sum_element_results_to_search % 10 != 0:
            numbers_page_to_find += 1
        print(numbers_page_to_find)
        return numbers_page_to_find

    def get_admin_ordinance_dict_in_search_page(self):
        # 조례 딕셔너리 선언
        admin_ordinance_dict = {}

        # 조회할 페이지수 구하기
        numbers_page = self.get_numbers_page_to_find()

        for page_number in range(numbers_page):

            # 검색웹페이지 요청
            req = requests.get(f'https://www.elis.go.kr/main/totSrchList?ctpvCd=&sggCd=&'
                               f'curPage={page_number + 1}'
                               f'&srchKwd={encode_url(self.keyword)}', headers=self.headers)
            # BeautifulSoup로 파싱
            soup = BeautifulSoup(req.text, "html.parser")

            # 페이지 내에서 조례요소 리스트로 만들기
            ordinance_elements_list = soup.select('#container > div.inner > div > div.search-result-list > div')

            # 조례리스트 순차적으로 조회
            for ordinance_element in ordinance_elements_list:
                # 조례 정보 검색
                try:
                    ordinance_info = get_ordinance_info(ordinance_element, self.keyword)
                except:
                    ordinance_info = None

                # 제목과 키워들 불일치 None 값이므로 넘김
                if ordinance_info is None:
                    continue

                # 딕녀너리 작성
                admin_ordinance_dict[ordinance_info[0]] = {
                    'title': ordinance_info[1],
                    'update_date': ordinance_info[2],
                    'department': ordinance_info[3],
                    'page_address': ordinance_info[4]
                }
        self.admin_ordinance_dict = dict(sorted(admin_ordinance_dict.items()))

    def get_ordinance_clause_dict(self):
        # 시군구 조례조항딕셔너리 선언
        self.admin_ordinance_clause_dict = {}

        # 순차적으로 딕셔너리에서 조회
        for ordinanace_admin, ordinanace_info in self.admin_ordinance_dict.items():
            print(f'{ordinanace_admin} 조회 중')
            # 조례 페이지 요청
            req = requests.get(ordinanace_info['page_address'], headers=self.headers)
            # BeautifulSoup로 파싱
            soup = BeautifulSoup(req.text, "html.parser")

            self.admin_ordinance_clause_dict[ordinanace_admin] = get_ordinance_clause(soup)
        self.sorted_indices_by_count = get_sorted_indices_by_count(self.admin_ordinance_clause_dict)
        self.sorted_indices_by_name = get_sorted_indices_by_name(self.admin_ordinance_clause_dict)

    def run_process(self):

        # 조례 검색
        self.get_admin_ordinance_dict_in_search_page()
        # 엑셀 작성
        self.xlwrite = xlwrite.XlWrite(self.keyword)
        self.xlwrite.create_admin_search_resurlt(self.admin_ordinance_dict)
        self.get_ordinance_clause_dict()
        self.xlwrite.create_compare_clause_titles_sheet(self.sorted_indices_by_name, self.admin_ordinance_clause_dict)
        self.xlwrite.create_compare_clause_sheet(self.sorted_indices_by_name, self.admin_ordinance_clause_dict)
        self.xlwrite.xl_workbook.close()


if __name__ == '__main__':
    setup_logging(log_filename=f'logs.log')
    keyword = '농어촌민박 지원'


    crawler = OrdinanceScraper(keyword)
    crawler.get_numbers_page_to_find()
    # crawler.run_process()
