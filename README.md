💬 Gemini Q&A 챗봇 (PyQt6 + TTS 기능)

이 프로젝트는 Python의 PyQt6 프레임워크를 사용하여 구축된 간단한 데스크톱 챗봇 애플리케이션입니다. Google Gemini API를 백엔드로 사용하여 실시간으로 질문에 답변하며, gTTS 및 playsound 라이브러리를 이용한 텍스트 음성 변환(TTS) 기능을 제공하여 Gemini의 응답을 음성으로 들을 수 있습니다.

✨ 주요 특징 (Features)

지속적인 대화 기록: QTextEdit 위젯에 사용자 질문과 Gemini 응답이 누적되어 대화의 흐름을 한눈에 파악할 수 있습니다.

비동기 TTS 재생: playsound의 블로킹(Blocking) 문제를 해결하기 위해 **TTSThread**라는 별도의 PyQt6 스레드를 사용하여 음성 재생 중에도 UI가 멈추지 않고 반응하도록 설계되었습니다.

간편한 API 연동: google-genai 라이브러리를 사용하여 Gemini 2.5 Flash 모델과 손쉽게 통신합니다.

API 키 관리: 코드가 사용자 제공 API 키를 환경 변수(GEMINI_API_KEY)에서 로드하는 것을 기본으로 하며, 임시 키를 코드 내에 포함하여 즉시 테스트가 가능하도록 설정되어 있습니다.

직관적인 UI: 질문 입력창, 전송 버튼, 답변 읽기 버튼 등으로 구성되어 있어 사용이 간편합니다.

🛠️ 설치 및 요구 사항 (Prerequisites)

이 애플리케이션을 실행하려면 Python 3.x 환경이 필요하며, 다음 라이브러리들을 설치해야 합니다.

터미널이나 명령 프롬프트에서 아래 명령어를 실행하여 필요한 모든 패키지를 설치합니다.

pip install PyQt6 google-genai gtts playsound==1.2.2


주의: playsound 라이브러리는 최신 버전에서 때때로 문제를 일으킬 수 있어, 안정적인 버전 1.2.2를 명시적으로 설치하는 것을 권장합니다.

🚀 실행 방법 (How to Run)

1. API 키 설정 (권장)

보안을 위해 API 키는 환경 변수로 설정하는 것이 좋습니다.

# Linux/macOS
export GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY_HERE"

# Windows (Command Prompt)
set GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY_HERE"


🔑 참고: 현재 코드는 사용자님께서 제공하신 키(AIzaSyDFYx3mr8dY8HwRMaPD2egzjVso7mkgops)를 코드 상단 os.environ 부분에 임시로 설정해 두었기 때문에, 별도의 환경 변수 설정 없이 바로 테스트할 수 있습니다. 하지만 실제 배포 시에는 환경 변수 사용을 권장합니다.

2. 애플리케이션 실행

파이썬 스크립트를 저장한 후 다음 명령어로 실행합니다.

python gemini_chat_app.py


💻 코드 구조 분석

TTSThread 클래스의 역할

가장 중요한 수정 사항이자 이 앱의 핵심 기능은 TTSThread에 있습니다.

playsound 함수는 음성 재생이 완료될 때까지 메인 스레드를 완전히 멈추게(Blocking) 합니다. 데스크톱 애플리케이션(PyQt6)의 메인 스레드는 UI 이벤트 처리(버튼 클릭, 창 움직임 등)를 담당하는데, 이 스레드가 멈추면 **애플리케이션 전체가 멈추는 현상(Not Responding)**이 발생합니다.

TTSThread는 다음과 같이 동작합니다.

스레드 분리: QThread를 상속받아 TTS 작업을 메인 UI 스레드로부터 분리합니다.

gTTS 파일 생성: run() 메서드 내에서 텍스트를 temp_response.mp3 파일로 저장합니다.

playsound 실행: 블로킹 함수인 playsound()를 이 별도 스레드에서 실행합니다.

시그널링: 재생이 완료되거나 오류가 발생하면 self.finished.emit() 시그널을 통해 메인 UI에 알려줍니다.

UI 복구: 메인 스레드의 on_tts_finished 슬롯이 시그널을 받아 "답변 읽기" 버튼을 다시 활성화하고 텍스트를 원래대로 되돌립니다.

이 구조 덕분에 사용자는 TTS 음성을 들으면서도 동시에 새로운 질문을 입력하거나 창을 이동하는 등 UI와 상호작용할 수 있습니다.
