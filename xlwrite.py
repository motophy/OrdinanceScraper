import xlsxwriter
import json


class XlWrite:
    def __init__(self, xlsx_file):
        self.xl_workbook = xlsxwriter.Workbook(f'{xlsx_file}.xlsx')

        # 서식지정
        # 서식 지정
        self.header_format = self.xl_workbook.add_format({"bold": True, "align": "center", "border": 1, "bg_color": "#DDDDDD"})
        self.cell_format = self.xl_workbook.add_format({"align": "center", "border": 1})
        self.clause_format = self.xl_workbook.add_format({"align": "left", "border": 1})

    def create_admin_search_resurlt(self, admin_code_dict_to_compare):
        data = admin_code_dict_to_compare

        sheet = self.xl_workbook.add_worksheet('시군구 조례검색결과')

        # 헤더 작성
        headers = ["지역", "조례명", "개정일", "담당 부서", "페이지 주소"]
        for col, header in enumerate(headers):
            sheet.write(0, col, header, self.header_format)

        # 데이터 삽입
        row = 1
        column_widths = [len(header) for header in headers]  # 열 너비 저장

        for region, info in data.items():

            if info:  # None 값 건너뜀
                values = [region, info["title"], info["update_date"], info["department"], info["page_address"]]
            else:
                values = [region, '조례없음']

            for col, value in enumerate(values):
                sheet.write(row, col, value, self.cell_format)
                column_widths[col] = max(column_widths[col], len(str(value)))  # 최대 길이 업데이트
            row += 1

        # 열 너비 자동 조정
        for col, width in enumerate(column_widths):
            width = round(width * 1.2)
            sheet.set_column(col, col, width + 10)

    def create_compare_clause_titles_sheet(self, sorted_indices, admin_clause_titles):

        sheet = self.xl_workbook.add_worksheet('시군구 조항제목비교')

        # 헤더 작성
        headers = ['시군구'] + sorted_indices
        for col, header in enumerate(headers):
            sheet.write(0, col, header, self.header_format)

        # 데이터 삽입
        row = 1
        column_widths = [len(header) for header in headers]  # 열 너비 저장

        for region, info in admin_clause_titles.items():
            for col in range(len(headers)):
                sheet.write(row, col, '', self.cell_format)

            sheet.write(row, 0, region, self.cell_format)

            if info:
                for title, code in info.items():
                    col = headers.index(title)
                    sheet.write(row, col, 'O', self.cell_format)

            row += 1

        # 열 너비 자동 조정
        for col, width in enumerate(column_widths):
            width = round(width * 1.2)
            sheet.set_column(col, col, width + 10)


    def create_compare_clause_sheet(self, sorted_indices, admin_clause_dict):
        for clause_title in sorted_indices:
            sheet_title = clause_title

            # for char in ['[',']',':','*','?','/','\\']:
            #     sheet_title = sheet_title.replace(char, '')
            # if len(clause_title) > 30:
            #     sheet = self.xl_workbook.add_worksheet(sheet_title[:30])
            # else:
            #     sheet = self.xl_workbook.add_worksheet(sheet_title)

            sheet = self.xl_workbook.add_worksheet(sheet_title)

            column_widths = []
            row = 1
            for clause_admin, clause_dict in admin_clause_dict.items():
                if clause_title not in clause_dict:
                    continue
                write_value = [clause_admin] + clause_dict[clause_title]
                for col, value in enumerate(write_value):
                    sheet.write(row, col, value, self.clause_format)
                    # 리스트 크기를 확장한 후 값 할당
                    if col >= len(column_widths):
                        column_widths.append(len(str(value)))
                    else:
                        column_widths[col] = max(column_widths[col], len(str(value)))
                row += 1
            # 열 너비 자동 조정
            for col, width in enumerate(column_widths):
                width = round(width * 1.5)
                sheet.set_column(col, col, width + 10)

            sheet.write(0, 0, '시군구', self.header_format)
            for col in range(1, len(column_widths)):
                sheet.write(0, col, f'세부항목 {col}', self.header_format)

