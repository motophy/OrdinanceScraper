import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 크롬 옵션 설정 (필요 시 headless 모드 사용 가능)
chrome_options = Options()
# chrome_options.add_argument("--headless")  # GUI 없이 실행 (선택 사항)
driver = webdriver.Chrome(options=chrome_options)

# 웹페이지 열기
driver.get("https://www.elis.go.kr/")

# 광역자치단체 버튼 클릭
driver.find_element(by='xpath', value='//*[@id="btnCtpv"]').click()

# 광역자치단체 목록 가져오기
region_elements = driver.find_elements(by='xpath',
                                       value='/html/body/div[2]/div[2]/form[1]/div[1]/div/div[1]/div[1]/div[1]/div[1]/div[2]/div/a')

administrative_data = {}

for region in region_elements:
    # '전체' 옵션은 스킵
    if region.text == '전체':
        continue

    # 지역명 및 코드 추출
    region_name = region.text
    region_code = region.get_attribute("onclick")[11:13]
    print(region_name, region_code)

    # 해당 지역 클릭
    time.sleep(1)
    region.click()
    time.sleep(1)  # 페이지 로딩 대기

    # 시군 조회 버튼 클릭
    driver.find_element(by='xpath', value='//*[@id="btnSgg"]').click()

    # 시군 목록 가져오기
    district_elements = driver.find_elements(by='xpath',
                                             value='/html/body/div[2]/div[2]/form[1]/div[1]/div/div[1]/div[1]/div[1]/div[2]/div[2]/div/a')

    district_dict = {}

    for district in district_elements:
        # '전체' 옵션은 스킵
        if district.text == '전체':
            continue

        # 시군명 및 코드 추출
        district_name = district.text
        # district_code = int(district.get_attribute("id").split('_')[1])
        district_code = district.get_attribute("id").split('_')[1]
        print(district_name, region_code, district_code)

        # 데이터 저장
        district_dict[f"{region_name} {district_name}"] = (region_code, district_code)

    # 시군 조회 닫기
    district_elements[-1].click()
    driver.find_element(by='xpath', value='//*[@id="btnCtpv"]').click()

    # 광역자치단체 데이터 저장
    administrative_data[region_name] = district_dict

# JSON 파일로 저장
with open('administrative_code.json', 'w', encoding='utf-8') as file:
    json.dump(administrative_data, file, ensure_ascii=False, indent=4)
