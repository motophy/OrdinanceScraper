import requests
from bs4 import BeautifulSoup

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