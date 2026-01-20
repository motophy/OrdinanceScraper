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


# ------ 클래스 선언 ------
class OrdinanceScraper:
    def __init__(self):
        logging.info('OrdinanceScraper 클래스 실행')

        # ----- 상수 선언 ----
        self.selector = Constant.SELECTOR
        self.headers = Constant.HEADERS

        # ----- 인스턴스 변수선언 ----





    def get_admin_ordinance_dict_in_search_page(self, search_keyword):
        logging.info('조례리스트 검색시작')

        # 조회할 페이지수 구하기
        numbers_page = self._get_numbers_page_to_find(search_keyword)
        if not numbers_page:
            logging.critical('조회할 페이지 수 실패로 프로그램 종료')
            exit()

        # 조례 딕셔너리 선언
        admin_ordinance_dict = dict()

        for page_number in range(numbers_page):

            # 검색웹페이지 요청
            req = requests.get(f'https://www.elis.go.kr/main/totSrchList?ctpvCd=&sggCd=&'
                               f'curPage={page_number + 1}'
                               f'&srchKwd={urllib.parse.quote_plus(search_keyword)}', headers=self.headers)
            # BeautifulSoup로 파싱
            soup = BeautifulSoup(req.text, "html.parser")

            logging.info(f'{page_number + 1} 페이지 조회중')


            # 페이지 내에서 조례요소 리스트로 만들기
            ordinance_elements_list = soup.select(self.selector['ordinance_elements_list'])
        #
        #     # 조례리스트 순차적으로 조회
        #     for ordinance_element in ordinance_elements_list:
        #         # 조례 정보 검색
        #         try:
        #             ordinance_info = get_ordinance_info(ordinance_element, self.keyword)
        #         except:
        #             ordinance_info = None
        #
        #         # 제목과 키워들 불일치 None 값이므로 넘김
        #         if ordinance_info is None:
        #             continue
        #
        #         # 딕녀너리 작성
        #         admin_ordinance_dict[ordinance_info[0]] = {
        #             'title': ordinance_info[1],
        #             'update_date': ordinance_info[2],
        #             'department': ordinance_info[3],
        #             'page_address': ordinance_info[4]
        #         }
        # self.admin_ordinance_dict = dict(sorted(admin_ordinance_dict.items()))


    def run_process(self, search_keyword):

        # 조례 검색
        self.get_admin_ordinance_dict_in_search_page(search_keyword)
        # 엑셀 작성
        # self.xlwrite = xlwrite.XlWrite(self.keyword)
        # self.xlwrite.create_admin_search_resurlt(self.admin_ordinance_dict)
        # self.get_ordinance_clause_dict()
        # self.xlwrite.create_compare_clause_titles_sheet(self.sorted_indices_by_name, self.admin_ordinance_clause_dict)
        # self.xlwrite.create_compare_clause_sheet(self.sorted_indices_by_name, self.admin_ordinance_clause_dict)
        # self.xlwrite.xl_workbook.close()

    # ------ 내부함수 목록 ------
    def _get_numbers_page_to_find(self, search_keyword):
        url = 'https://www.elis.go.kr/main/totSrchList?ctpvCd=&sggCd=&curPage=1&srchKwd='

        # 웹페이지 요청
        req = requests.get(url + urllib.parse.quote_plus(search_keyword), headers=self.headers)
        # BeautifulSoup로 파싱
        soup = BeautifulSoup(req.text, "html.parser")

        # 총 검색된 조례 갯수 구하기
        # element = soup.select_one('#container > div > div > div.list-top > div.left > p > span')
        element = soup.select_one(self.selector['searched_ordinance_count'])
        if not element:
            logging.error('총 조례 건수 조회 실패')
            return False
        sum_element_results_to_search = int(element.get_text().replace(',',''))
        logging.debug(f'조회된 조례 갯수 :\n{sum_element_results_to_search}')

        numbers_page_to_find = sum_element_results_to_search // 10

        # 조례 갯수로 페이지 수 구하기
        if sum_element_results_to_search % 10 != 0:
            numbers_page_to_find += 1

        logging.info(f'조회된 페이지 갯수 :\n{numbers_page_to_find}')
        return numbers_page_to_find

if __name__ == '__main__':
    setup_logging(log_filename=f'logs.log')
    keyword = '농어촌민박 지원'


    crawler = OrdinanceScraper()
    # crawler.get_numbers_page_to_find()
    crawler.run_process(keyword)
