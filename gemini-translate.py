import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai


def get_article_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    content_div = soup.find('div', class_='entry-content')
    if not content_div:
        raise ValueError("지정된 클래스를 가진 div를 찾을 수 없습니다.")

    content = []
    paragraph_count = 0
    for element in content_div.children:
        if element.name == 'p' and 'wp-block-paragraph' in element.get('class', []):
            content.append(('text', element.text.strip()))
            paragraph_count += 1
        elif element.name == 'figure' and 'wp-block-image' in element.get('class', []):
            img = element.find('img')
            if img and img.get('src'):
                content.append(('image', img['src'], paragraph_count))

    return content


def translate_text(text, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

    translate_prompt = f"""다음 텍스트를 한국어로 번역해주세요. 원문의 문단 구조를 유지해주세요. 각 문단은 새로운 줄로 구분해주세요:

{text}

번역:"""
    translate_response = model.generate_content(translate_prompt)
    return translate_response.text


def summarize_text(text, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    summarize_prompt = f"""다음 텍스트에 대해 다음 작업을 수행해주세요:
    1. 핵심 키워드 5개를 추출하세요.
    2. 200자 이내로 요약하세요.
    
    텍스트: {text}
    
    형식:
    핵심 키워드: 키워드1, 키워드2, 키워드3, 키워드4, 키워드5
    요약: (200자 이내의 요약)"""

    summarize_response = model.generate_content(summarize_prompt)
    return summarize_response.text


def main():
    st.title("URL 내용 추출, 번역 및 요약 애플리케이션")

    api_key = st.text_input("Google Gemini API 키를 입력하세요", type="password")
    url = st.text_input("번역할 기사의 URL을 입력하세요")

    if st.button("번역 및 요약 시작"):
        if not api_key or not url:
            st.error("API 키와 URL을 모두 입력해주세요.")
            return

        try:
            with st.spinner("내용을 추출하고 번역 및 요약 중입니다..."):
                content = get_article_content(url)

                # 전체 텍스트 추출
                full_text = "\n\n".join(
                    [item[1] for item in content if item[0] == 'text'])

                # 전체 텍스트 번역
                translated_text = translate_text(full_text, api_key)
                translated_paragraphs = translated_text.split('\n')

                st.subheader("번역된 내용")
                paragraph_count = 0
                for item in content:
                    if item[0] == 'text':
                        st.write(translated_paragraphs[paragraph_count])
                        st.write("")  # 빈 줄 추가로 문단 구분
                        paragraph_count += 1
                    elif item[0] == 'image':
                        st.image(item[1], use_column_width=True)

                st.subheader("요약 및 키워드")
                summary = summarize_text(translated_text, api_key)
                st.write(summary)

        except Exception as e:
            st.error(f"오류 발생: {str(e)}")


if __name__ == "__main__":
    main()
