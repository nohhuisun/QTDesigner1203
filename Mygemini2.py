import sys
import os
from PyQt6.QtWidgets import (
    QApplication, 
    QWidget, 
    QLineEdit, 
    QTextEdit, 
    QPushButton,
    QVBoxLayout, 
    QHBoxLayout, 
    QMessageBox, 
    QLabel
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import time # QThread 예제를 위해 임포트

# TTS 관련 라이브러리 임포트
try:
    from gtts import gTTS
    # playsound는 블로킹(Blocking) 함수이므로, 
    # UI 정지 현상을 막기 위해 별도의 스레드에서 실행해야 합니다.
    from playsound import playsound
except ImportError:
    print("🚨 오류: TTS 라이브러리 ('gtts', 'playsound')를 찾을 수 없습니다.")
    print("설치하려면 터미널에서 'pip install gtts playsound' 명령을 실행하세요.")
    # 특정 버전 설치를 권장합니다: 'pip install gtts playsound==1.2.2'
    sys.exit(1)


# Google GenAI 라이브러리 임포트
try:
    from google import genai
except ImportError:
    print("🚨 오류: 'google-genai' 라이브러리를 찾을 수 없습니다.")
    print("설치하려면 터미널에서 'pip install google-genai' 명령을 실행하세요.")
    sys.exit(1)

# --- ⚠️ 중요: Gemini API 키 설정 ⚠️ ---
# 실제 사용자의 API 키로 대체해야 합니다.
os.environ["GEMINI_API_KEY"] = "AIzaSyDFYx3mr8dY8HwRMaPD2egzjVso7mkgops"
# ------------------------------------


# --- TTS 재생을 위한 별도 스레드 클래스 ---
class TTSThread(QThread):
    """UI를 멈추지 않도록 playsound를 별도의 스레드에서 실행합니다."""
    # 재생이 완료되면 UI에게 알리는 시그널
    finished = pyqtSignal()
    
    def __init__(self, text_to_speak, parent=None):
        super().__init__(parent)
        self.text = text_to_speak
        self.tts_file = "temp_response.mp3"
        
    def run(self):
        try:
            # 1. 텍스트를 음성 파일로 변환
            # playsound는 파일 경로에 한글이 있으면 오류가 발생할 수 있어 임시 파일 이름을 ASCII로 지정합니다.
            tts = gTTS(text=self.text, lang='ko', slow=False)
            tts.save(self.tts_file)
            
            # 2. 음성 파일 재생 (블로킹 동작)
            playsound(self.tts_file)

        except Exception as e:
            # 재생 중 오류가 발생해도 UI를 멈추지 않고 스레드 종료
            print(f"TTS 재생 스레드 오류 발생: {e}")
        
        finally:
            # 3. 재생 후 임시 파일 삭제
            if os.path.exists(self.tts_file):
                os.remove(self.tts_file)
            
            # 4. 완료 시그널 전송
            self.finished.emit()


class GeminiApp(QWidget):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gemini Q&A 챗봇 (TTS 및 대화 기록 누적)")
        self.setGeometry(100, 100, 800, 600) 
        
        # 1. Gemini 클라이언트 초기화 및 API 키 확인
        self.client = None
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key or api_key == "YOUR_ACTUAL_GEMINI_API_KEY_HERE":
            QMessageBox.critical(
                self, 
                "API 키 오류", 
                "⚠️ API 키가 설정되지 않았거나 유효하지 않은 더미 값입니다.\n"
                "코드 상단 os.environ[\"GEMINI_API_KEY\"] = \"...\" 부분에 실제 키를 입력해야 합니다."
            )
            
        else:
            try:
                self.client = genai.Client()
            except Exception as e:
                error_msg = f"Gemini API 클라이언트 초기화 오류: {e}"
                QMessageBox.critical(self, "API 오류", "Gemini API 클라이언트 초기화에 실패했습니다.\n\n" + error_msg)
                print(error_msg)
                self.client = None
                
        # 2. UI 위젯 생성 및 레이아웃 설정
        self.answerDisplay = QTextEdit() 
        self.answerDisplay.setReadOnly(True) 
        self.answerDisplay.setFontPointSize(10)
        self.answerDisplay.append("📢 질문을 입력하고 '전송' 버튼을 누르세요. (Gemini 2.5 Flash 사용)")
        self.answerDisplay.append("<hr>") # 구분선 추가
        
        self.lineEditMyQuestion = QLineEdit() 
        self.lineEditMyQuestion.setPlaceholderText("여기에 질문을 입력하세요...")
        
        self.btnSent = QPushButton("전송 (Sent) 💬") 
        self.btnSent.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")

        # TTS 재생 버튼 추가
        self.btnTTS = QPushButton("답변 읽기 🔊")
        self.btnTTS.setStyleSheet("background-color: #008CBA; color: white; padding: 10px;")
        self.btnTTS.setEnabled(False) # 처음에는 비활성화
        
        # UI 레이아웃
        main_layout = QVBoxLayout()
        main_layout.addWidget(QLabel("✅ 대화 기록:"))
        main_layout.addWidget(self.answerDisplay)
        main_layout.addWidget(QLabel("❓ 나의 질문:"))
        
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.lineEditMyQuestion)
        input_layout.addWidget(self.btnSent)
        
        main_layout.addLayout(input_layout)
        main_layout.addWidget(self.btnTTS) 
        
        self.setLayout(main_layout)

        # 3. 시그널 연결
        self.btnSent.clicked.connect(self.ask_gemini) 
        self.lineEditMyQuestion.returnPressed.connect(self.ask_gemini)
        self.btnTTS.clicked.connect(self.read_tts) 

        # 마지막으로 받은 Gemini 응답 텍스트를 저장할 변수
        self.last_gemini_response = ""
        # TTS 스레드 변수
        self.tts_thread = None

    def read_tts(self):
        """TTS 스레드를 시작하여 마지막 응답을 읽어주는 함수"""
        if not self.last_gemini_response:
            QMessageBox.warning(self, "TTS 오류", "읽을 내용이 없습니다. 먼저 질문하여 응답을 받아주세요.")
            return
        
        # TTS 스레드가 이미 실행 중이면 중지
        if self.tts_thread and self.tts_thread.isRunning():
            QMessageBox.information(self, "TTS 정보", "현재 음성 재생 중입니다.")
            return

        # 버튼 비활성화 및 텍스트 변경 (사용자에게 재생 중임을 알림)
        self.btnTTS.setEnabled(False)
        original_text = self.btnTTS.text()
        self.btnTTS.setText("음성 재생 중... 🎧")

        # TTS 스레드 생성 및 시작
        self.tts_thread = TTSThread(self.last_gemini_response)
        # 스레드 종료 시 호출될 슬롯 연결
        self.tts_thread.finished.connect(lambda: self.on_tts_finished(original_text))
        self.tts_thread.start()

    def on_tts_finished(self, original_text):
        """TTS 스레드 종료 시 호출되어 UI를 복구하는 함수"""
        self.btnTTS.setEnabled(True)
        self.btnTTS.setText(original_text)
        self.tts_thread = None # 스레드 객체 해제

    def ask_gemini(self): 
        # API 클라이언트 초기화 실패 시 처리
        if not self.client:
            QMessageBox.critical(self, "API 오류", "Gemini API 클라이언트가 초기화되지 않았습니다. API 키를 확인하세요.")
            return

        question = self.lineEditMyQuestion.text().strip()

        if not question:
            QMessageBox.warning(self, "입력 오류", "질문을 입력해주세요.")
            return
        
        # 질문 입력창 비우기
        self.lineEditMyQuestion.clear()
        
        # 1. 질문을 대화 기록에 추가 (HTML로 스타일 적용)
        self.answerDisplay.append(f"<p style='color:#3333FF;'><b>👤 나의 질문:</b> {question}</p>")
        
        # 응답 대기 메시지 추가
        self.answerDisplay.append("<p style='color:orange;'>⏳ Gemini가 응답을 생성하는 중입니다...</p>")
        
        # UI 갱신을 강제
        QApplication.processEvents() 

        try:
            # API 호출
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=question
            )
            
            gemini_text = response.text
            self.last_gemini_response = gemini_text.strip()
            
            # 마지막 줄 (대기 메시지)을 제거하고 응답을 추가 (QTextEdit의 append 사용)
            self.answerDisplay.setText(self.answerDisplay.toPlainText().replace("⏳ Gemini가 응답을 생성하는 중입니다...", ""))
            self.answerDisplay.append(f"<p style='color:#007700;'><b>🤖 Gemini 응답:</b></p><pre>{self.last_gemini_response}</pre>")
            self.answerDisplay.append("<hr>") # 구분선 추가
            
            # TTS 버튼 활성화
            self.btnTTS.setEnabled(True)
            
        except Exception as e:
            # API 호출 중 예외 처리
            error_message = f"API 호출 중 오류 발생: {e}"
            print(error_message)
            
            self.answerDisplay.setText(self.answerDisplay.toPlainText().replace("⏳ Gemini가 응답을 생성하는 중입니다...", ""))
            self.answerDisplay.append(f"<p style='color:red;'>🚨 <b>오류 발생:</b> {error_message}</p>")
            self.answerDisplay.append("<hr>")
            
            self.last_gemini_response = "" # 오류 시 TTS 방지
            self.btnTTS.setEnabled(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GeminiApp()
    window.show()
    sys.exit(app.exec())