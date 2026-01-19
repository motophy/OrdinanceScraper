from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import urllib.parse
import time

# ------ 함수 목록 ------
def encode_url(text: str) -> str:
    """
    텍스트를 퍼센트인코딩하는 함수
    :param text: 변환할 단어
    :return: 퍼센트 URL 인코딩
    """
    return urllib.parse.quote_plus(text)

def get_ordinance_info(ordinance_element, search_keyword):
    """
    조례 정보 조회
    :param ordinance_element: 검색된 조례 요소
    :param search_keyword: 검색어
    :return: 조례정보 리스트 리턴, 조례제목과 불일치시 None 리턴
    """
    # 조레 제목
    ordinance_title = ordinance_element.find_element(by='tag name', value='strong').text

    # 키워드 중에 조례에 하나라도 포함 되지 않으면 None 리턴
    keyword_list = search_keyword.split(' ')
    if any(word not in ordinance_title for word in keyword_list):
        return None


    # 조례관련정보 작성
    ordinance_info = ordinance_element.find_element(by='tag name', value='span').text
    ordinance_admin = ' '.join(ordinance_info.split(' ')[:2])
    ordinance_update_date = ordinance_info.split(' ')[2]
    ordinance_department = ' '.join(ordinance_info.split(' ')[3:])
    # 페이지 주소 찾기
    ordinance_page_parameters = ordinance_element.get_attribute('onclick')
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

def get_ordinanace_clause_titles(web_driver, url):
    web_driver.get(url)
    ordinance_title = []
    clause_elements = web_driver.find_elements(by='xpath', value='//*[@id="cms-lnb"]/ul/li/ul/li[1]/ul/li/a')
    for clause_element in clause_elements:
        ordinance_title.append(clause_element.text[clause_element.text.find('(')+1:-1])

    ordinance_title = [el.text[el.text.find('(') + 1:-1] for el in clause_elements]


# ------ 클래스 선언 ------
class OpenWebdriver:
    def __init__(self, search_keyword):

        # ----- 인스턴스 변수선언 ----
        self.admin_ordinance_dict = None        # 조례 딕셔너리 None값 선언
        self.keyword = search_keyword           # 검색 키워드 선언

        # ----- 크롬드라이버 설정 -----
        # 크롬 옵션 설정 (필요할 경우)
        chrome_options: Options = webdriver.ChromeOptions()
        # chrome_options.add_argument("--headless")  # GUI 없이 실행 (선택)

        # Selenium Manager가 자동으로 최신 ChromeDriver 사용
        self.driver = webdriver.Chrome(options=chrome_options)

    def get_numbers_page_to_find(self):
        url = 'https://www.elis.go.kr/main/totSrchList?ctpvCd=&sggCd=&curPage=1&srchKwd='

        # 검색페이지로 이동
        self.driver.get(
            url + encode_url(self.keyword)
        )

        # 총 검색된 요소
        sum_element_results_to_search = int(self.driver.find_element(by='xpath', value='//*[@id="container"]/div/div/div[3]/div[1]/p/span').text)

        numbers_page_to_find = sum_element_results_to_search // 10

        if sum_element_results_to_search % 10 != 0:
            numbers_page_to_find += 1

        # print(numbers_page_to_find)

        return numbers_page_to_find

    def get_admin_ordinance_dict(self):
        # 조례 딕셔너리 선언
        self.admin_ordinance_dict = {}

        # 조회할 페이지수 구하기
        numbers_page = self.get_numbers_page_to_find()

        for page_number in range(numbers_page):
            url = 'https://www.elis.go.kr/main/totSrchList?ctpvCd=&sggCd=&curPage=1&srchKwd='

            # 검색페이지로 이동
            self.driver.get(f'https://www.elis.go.kr/main/totSrchList?ctpvCd=&sggCd=&curPage='
                            f'{page_number + 1}'
                            f'&srchKwd={encode_url(self.keyword)}')

            # 페이지 내에서 조례요소 리스트로 만들기
            ordinance_elements_list = self.driver.find_elements(by='xpath',
                                                                value='//*[@id="container"]/div/div/div[4]/div/a')

            # 조례리스트 순차적으로 조회
            for ordinance_element in ordinance_elements_list:
                # 조례 정보 검색
                ordinance_info = get_ordinance_info(ordinance_element, self.keyword)

                # 제목과 키워들 불일치 None 값이므로 넘김
                if ordinance_info is None:
                    continue

                # 딕녀너리 작성
                self.admin_ordinance_dict[ordinance_info[0]] = {
                    'title': ordinance_info[1],
                    'update_date': ordinance_info[2],
                    'department': ordinance_info[3],
                    'page': ordinance_info[4]
                }

    def get_ordinance_text(self):
        # 순차적으로 딕셔너리에서 조회
        for ordinanace_admin, ordinanace_info in self.admin_ordinance_dict.items():
            # 페이지 이동
            self.driver.get(ordinanace_info['page'])

            self.driver.find_element(by='xpath', value='//*[@id="btnSave"]').click()
            time.sleep(1)
            self.driver.switch_to.window(self.driver.window_handles[1])
            time.sleep(1)
            self.driver.find_element(by='xpath', value='/html/body/div/div/div/div[1]/a[1]').click()
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])





    def run_process(self):

        # 조례 검색
        self.get_admin_ordinance_dict()
        self.get_ordinance_text()




if __name__ == '__main__':
    keyword = '청소년 바우처'

    # driver class 실행
    driver = OpenWebdriver(keyword)

    driver.run_process()

