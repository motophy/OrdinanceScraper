# config/logging_config.py
import logging
import logging.handlers
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    # 헤더와 메시지를 다른 색으로 표시
    # 색상 코드
    GRAY = '\033[90m'  # 회색 (헤더용)
    WHITE = '\033[97m'  # 흰색 (메시지용)
    CYAN = '\033[36m'  # 하늘색
    GREEN = '\033[32m'  # 초록
    YELLOW = '\033[33m'  # 노랑
    RED = '\033[31m'  # 빨강
    MAGENTA = '\033[35m'  # 자주
    RESET = '\033[0m'  # 리셋

    def format(self, record):
        # 원본 포맷 실행
        formatted = super().format(record)

        # 헤더 부분 (첫 줄)과 메시지 부분 (둘째 줄) 분리
        lines = formatted.split('\n')

        if len(lines) >= 2:
            # 첫 줄 (헤더) - 회색
            header = f"{self.GRAY}{lines[0]}{self.RESET}"

            # 둘째 줄 (메시지) - 흰색
            message = f"{self.WHITE}{lines[1]}{self.RESET}"

            # 나머지 줄 있으면 추가
            rest = '\n'.join(lines[2:]) if len(lines) > 2 else ''

            return f"{header}\n{message}" + (f"\n{rest}" if rest else '')

        return formatted


def setup_logging(log_filename):
    """로깅 시스템 초기화 - 에러만 파일에 저장"""

    # logs 폴더 생성 (없으면 만들기)
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 루트 로거 가져오기 (모든 로거의 최상위 부모)
    root_logger = logging.getLogger()

    # 로그 레벨 설정 (DEBUG = 모든 로그 허용)
    root_logger.setLevel(logging.DEBUG)
    # root_logger.setLevel(logging.CRITICAL + 1)

    # 기존 핸들러 제거 (중복 방지 - 여러 번 호출될 경우 대비)
    root_logger.handlers.clear()

    # === 콘솔 출력 설정 (화면에 색상으로 표시) ===

    # 콘솔 핸들러 생성 (stdout으로 출력)
    console_handler = logging.StreamHandler()

    # 콘솔은 모든 레벨 출력 (DEBUG부터)
    console_handler.setLevel(logging.DEBUG)

    # 색상 포맷터 생성 및 적용
    colored_formatter = ColoredFormatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s\n'  # 첫 줄: 시간, 레벨, 모듈명, 함수명
        '%(message)s\n',  # 둘째 줄: 메시지
        datefmt='%Y-%m-%d %H:%M:%S'  # 시간 형식
    )
    console_handler.setFormatter(colored_formatter)

    # 루트 로거에 콘솔 핸들러 추가
    root_logger.addHandler(console_handler)

    # === 에러 파일 저장 설정 (에러만 파일에 기록) ===

    # 파일 핸들러 생성 (자동 로테이션)
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / log_filename,  # 파일 경로: logs/error.log
        maxBytes=10 * 1024 * 1024,  # 파일 크기 10MB 넘으면 백업
        backupCount=5,  # 최대 5개 백업 파일 유지 (error.log.1 ~ error.log.5)
        encoding='utf-8'  # 한글 깨짐 방지
    )

    # 파일은 ERROR 레벨 이상만 저장
    error_handler.setLevel(logging.INFO)

    # 일반 포맷터 생성 (파일은 색상 코드 제외)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s\n | %(funcName)s'
        '%(message)s\n',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    error_handler.setFormatter(file_formatter)

    # 루트 로거에 에러 파일 핸들러 추가
    root_logger.addHandler(error_handler)

    # # 초기화 완료 메시지 (필요시 주석 해제)
    # logging.info("로깅 시스템 초기화 완료")