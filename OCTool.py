import requests
from bs4 import BeautifulSoup
import urllib.parse
import json


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
        'page_parameters': ordinance_page_parameters
    }
    # print(ordinance_title, ordinance_update_date, ordinance_department, ordinance_page_parameters)
    return result_dict


class Elis:
    def __init__(self):
        # json파일에서 시군구 코드 딕셔너리 불러오기
        with open('administrative_before.json', 'r', encoding='utf-8') as file:
            self.administrative_code_dict = json.load(file)

        # 비교할 시군구 초기 변수선언
        self.admin_code_dict_to_compeare = None

        # 요청 헤더 설정
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def verify_and_fetch(self, dict_to_search, search_keyword):
        """
        시군구별 조례를 조회 하여 각 정보를 딕셔너리형태로 리턴
        해당없는 조례는 None retrun
        :param dict_to_search: 조회할 딕셔너리값 ex) {"경북 봉화군": "47":"920"}
        :param search_keyword: 조회할 키워드 ex) {실종자 수색}
        :return: 조회된 값
                ex) {"경북 봉화군" : {"title": "실종자 수색 지원 조례",  조례제목
                                    "update_date": "2024.12.01"     제개정일
                                    "department": "안전건설과"        담당부서
                                    "page_parameters": "[]"         조례페이지 파라미터값
        """
        # 비교할 시군구 초기 변수선언
        self.admin_code_dict_to_compeare = {}

        for admin, code in dict_to_search.items():
            # 시군구별 순차적으로 조회하여 추가
            info = get_ordinance_link(code, search_keyword)
            self.admin_code_dict_to_compeare[admin] = info
            if info is not None:
                print(admin, info['title'])
            else:
                print(admin, '조례없음')
        print(self.admin_code_dict_to_compeare)


if __name__ == '__main__':
    get_ordinance_link([47, 900], '실종자')

    ordin = Elis()

    filtered_dict = {key: value for key, value in ordin.administrative_code_dict.items() if '경북' in key}
    print(filtered_dict)

    ordin.verify_and_fetch(filtered_dict, '실종자')

    # ordin
