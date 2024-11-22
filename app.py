import streamlit as st
from pydantic import BaseModel, Field
from pydantic.functional_validators import model_validator
from typing import List
from enum import StrEnum
from openai import AzureOpenAI
import os
from enum import Enum
from chord_theory import get_chord_theory_prompt

class NoteNames(StrEnum):
    """音名の列挙型"""
    C = "C"
    Cs = "C#"
    Db = "Db"
    D = "D"
    Ds = "D#"
    Eb = "Eb"
    E = "E"
    F = "F"
    Fs = "F#"
    Gb = "Gb"
    G = "G"
    Gs = "G#"
    Ab = "Ab"
    A = "A"
    As = "A#"
    Bb = "Bb"
    B = "B"

class ChordKey(BaseModel):
    """個々の鍵盤の情報"""
    x: int = Field(description="鍵の左端のx座標")
    is_black: bool = Field(description="黒鍵かどうか")
    finger: int = Field(description="運指番号")
    note: NoteNames = Field(description="音名")

class ChordQuiz(BaseModel):
    """コードクイズの形式"""
    chord_name: str = Field(description="コード名")
    keys: List[ChordKey] = Field(description="コードを構成する鍵盤情報のリスト")
    explanation: str = Field(description="運指の説明")

def create_svg(quiz_data: ChordQuiz) -> str:
    """ChordQuizデータからSVGを生成する"""
    # 白鍵の位置（2オクターブ分）
    white_keys = [
        10, 60, 110, 160, 210, 260, 310,  # 1オクターブ目
        360, 410, 460, 510, 560, 610, 660  # 2オクターブ目
    ]
    
    # 黒鍵の位置（2オクターブ分）
    black_keys = [
        45, 95, 195, 245, 295,  # 1オクターブ目
        395, 445, 545, 595, 645  # 2オクターブ目
    ]
    
    return f'''
    <div style="text-align: center;">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 200" style="max-width: 800px;">
            <!-- 白鍵の描画 -->
            {' '.join([f'<rect x="{x}" y="20" width="45" height="160" fill="white" stroke="black"/>' 
                      for x in white_keys])}
            
            <!-- 黒鍵の描画 -->
            {' '.join([f'<rect x="{x}" y="20" width="25" height="100" fill="black"/>' 
                      for x in black_keys])}
            
            {' '.join([f"""
                <!-- キーのハイライト -->
                <rect 
                    x="{key.x}" 
                    y="20" 
                    width="{25 if key.is_black else 45}" 
                    height="{100 if key.is_black else 160}" 
                    fill="#87CEEB" 
                    fill-opacity="0.5" 
                    stroke="black"
                />
                <!-- 運指番号の円と数字 -->
                <circle 
                    cx="{key.x + (12.5 if key.is_black else 22.5)}" 
                    cy="{150 if not key.is_black else 90}" 
                    r="15" 
                    fill="white" 
                    stroke="black"
                />
                <text 
                    x="{key.x + (12.5 if key.is_black else 22.5)}" 
                    y="{155 if not key.is_black else 95}" 
                    text-anchor="middle" 
                    font-size="16" 
                    fill="black"
                >{key.finger}</text>
                <!-- 音名 -->
                <text 
                    x="{key.x + (12.5 if key.is_black else 22.5)}" 
                    y="{50 if not key.is_black else 40}" 
                    text-anchor="middle" 
                    font-size="14" 
                    fill="black"
                >{key.note}</text>
            """ for key in quiz_data.keys])}
            
            <text x="350" y="15" text-anchor="middle" font-size="18" font-weight="bold" fill="black">{quiz_data.chord_name}</text>
        </svg>
    </div>
    '''

def get_new_chord() -> ChordQuiz:
    """OpenAI APIを使用して新しいコードクイズを取得"""
    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-10-01-preview"
    )
    
    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[{"role": "user", "content": get_chord_theory_prompt()}],
        response_format=ChordQuiz
    )
    
    return completion.choices[0].message.parsed

def main():
    st.set_page_config(page_title="ピアノコード運指クイズ", layout="wide")
    st.title("ピアノコード運指クイズ")
    
    if 'current_quiz' not in st.session_state:
        st.session_state.current_quiz = None
    if 'show_answer' not in st.session_state:
        st.session_state.show_answer = False
    
    show_debug = st.sidebar.checkbox("デバッグ情報を表示", False)
    
    if st.button("出題", use_container_width=True):
        with st.spinner("新しい問題を生成中..."):
            st.session_state.current_quiz = get_new_chord()
            st.session_state.show_answer = False
    
    if st.session_state.current_quiz:
        st.header(st.session_state.current_quiz.chord_name, divider="rainbow")
        
        if show_debug:
            with st.expander("デバッグ情報"):
                st.json(st.session_state.current_quiz.model_dump())
                st.markdown("### 座標値の確認")
                st.markdown("#### 白鍵の有効なx座標:")
                st.code("10, 60, 110, 160, 210, 260, 310, 360, 410, 460, 510, 560, 610, 660")
                st.markdown("#### 黒鍵の有効なx座標:")
                st.code("45, 95, 195, 245, 295, 395, 445, 545, 595, 645")
        
        if st.button("正解を見る", type="primary", use_container_width=True):
            st.session_state.show_answer = True
        
        if st.session_state.show_answer:
            st.info(st.session_state.current_quiz.explanation)
            st.components.v1.html(create_svg(st.session_state.current_quiz), height=250)

if __name__ == "__main__":
    main()