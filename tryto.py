import re
import streamlit as st
from openai import OpenAI
from pytube import YouTube
from urllib.request import urlopen
from bs4 import BeautifulSoup

def init_page():
    st.set_page_config(page_title="YouTube Summarizer", page_icon="📝")
    st.header("ゆっくり台本メーカー")
    st.sidebar.title("オプション")

def select_characters():
    characters = st.sidebar.radio("キャラクターを選択:", ("ずんだもんとナレーター", "霊夢と魔理沙"))
    return characters

def select_input_method():
    input_method = st.sidebar.radio("情報の取得方法を選択:", ("動画", "記事URL"))
    return input_method

def get_video_urls():
    video_url1 = st.text_input("動画1のURL:", key="url1")
    video_url2 = st.text_input("動画2のURL:", key="url2")
    theme = st.text_input("テーマを入力してください。(1単語)")
    return video_url1, video_url2, theme

def get_text_urls():
    url1 = st.text_input("記事URL1:", key="url_input1")
    url2 = st.text_input("記事URL2:", key="url_input2")
    theme = st.text_input("テーマを入力してください。(1単語)")
    return url1, url2, theme

def fetch_text_from_url(url):
    try:
        html = urlopen(url).read()
        soup = BeautifulSoup(html, 'html.parser')

        # 特定のタグ（例えば、articleやdivタグで特定のクラスを持つもの）をターゲットにする
        article_tags = soup.find_all(['article', 'div'], class_=lambda x: x and 'main' in x.lower())
        paragraphs = [p.get_text(separator=' ', strip=True) for p in article_tags]

        # 見つからない場合は通常の段落タグを利用
        if not paragraphs:
            paragraphs = [p.get_text(separator=' ', strip=True) for p in soup.find_all('p')]

        # 長さでフィルタリング
        body_text = ' '.join([p for p in paragraphs if len(p) > 50])

        return body_text
    except Exception as e:
        st.error(f"Error fetching data from {url}: {e}")
        return ""


def download_transcribe_and_extract(video_url, model_name, theme, client):
    youtube_video = YouTube(video_url)
    audio_stream = youtube_video.streams.filter(only_audio=True).first()
    audio_file_path = audio_stream.download()

    with open(audio_file_path, "rb") as audio_file:
        transcript_response = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            language="ja",
            response_format='text',
        )

    transcript_text = transcript_response

    return extract_elements(transcript_text, model_name, theme, client)

def extract_elements(text_data, model_name, theme, client):
    prompt = (
        f"###テキストデータから、提供するテキストから情報を余すことなく抽出するために、下記をstep-by-stepで実行してください。\n"
        f"\n"
        f"Step1:提供するテキストから情報を余すことなく抽出し、詳述する。\n"
        f"注意：取得した情報に時間や世代数、年代などの数字がある場合は必ず記載してください。\n"
        f"また、抽出する情報は以下の要素を含めるようにして、充分な説明ができるようにしてください。\n"
        f"情報の深さ：\n"
        f"- 各トピックについて詳細に説明し、関連する背景情報や補足情報も含めてください。\n"
        f"- 可能な限り因果関係や関連性を明示し、理解を深めるための具体例を提供してください。\n"
        f"情報の広さ：\n"
        f"- テキスト全体を通じて幅広いトピックをカバーし、主要なポイントだけでなく、細部についても言及してください。\n"
        f"- 各トピックがどのように関連しているかを説明し、全体の理解を助けるようにしてください。\n"
        f"情報の構造：\n"
        f"- 論理的な順序で情報を整理し、自然な流れで説明してください。\n"
        f"- 各段落やセクションが明確に関連し合うようにし、読者が情報をスムーズに追えるようにしてください。\n"
        f"文脈と背景情報：\n"
        f"- 各情報の背景や歴史的文脈を詳しく説明し、その重要性や関連性を明確にしてください。\n"
        f"- テキスト内で言及されている人物、場所、出来事について詳しい説明を加え、読者が理解しやすいようにしてください。\n"
        f"\n"
        f"\n"
        f"Step2:抽出した情報を文脈や背景情報を含めて詳述する自然な文章形式でまとめてください。\n"
        f"\n"
        f"注意：箇条書きではなく、自然な文章形式でまとめてください。\n"
        f"詳細な説明が可能：文脈提供や因果関係の説明を通じて、読者がより深く理解できるようにしてください。\n"
        f"自然な流れ：読みやすく、ストーリーテリングを取り入れることで、読者の興味を引き続けてください。\n"
        f"複雑な情報の伝達：多層的な情報提供や関係性の詳細な説明を行い、全体像の理解を深めてください。\n"
        f"表現の豊かさ：感情やニュアンスを豊かに伝えるために、比喩や修辞技法を駆使してください。\n"
        f"読者の引き込み：感情移入しやすい物語やエピソードを含め、共感を呼び起こすようにしてください。\n"
        f"論理の明示：複雑な論理や推論を順序立てて説明し、主張を裏付けるための詳細な証拠やデータを含めてください。\n"
        f"読者教育：新しい知識や視点を提供し、読者の理解を深める手助けをしてください。\n"
        f"記憶の強化：ストーリーテリングや詳細な説明を通じて、読者の記憶に残りやすくしてください。\n"
        f"感情的なつながり：感動や共感を引き起こすような内容を含め、読者との個人的なつながりを築いてください。\n"
        f"\n"
        f"参考フォーマットを参考に出力してください。\n"
        f"参考フォーマット=\n"
        f"'''"
        f"Step1:提供するテキストから情報を余すことなく抽出し、詳述する。\n"
        f"〜Step1の内容をここに入力〜\n"
        f"\n"
        f"Step2:抽出した情報を文脈や背景情報を含めて詳述する自然な文章形式でまとめてください。\n"
        f"〜Step2の内容をここに入力〜\n"
        f"'''\n"
        f"\n"
        f"\n"
        f"###テキストデータ\n"
        f"{text_data}\n"
    )
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}]
    )
    content = response.choices[0].message.content

    # Step2の文言を除外し、その後の文章を抽出
    step2_content = re.search(r"Step2:抽出した情報を文脈や背景情報を含めて詳述する自然な文章形式でまとめてください。\n(.*)", content, re.DOTALL)
    elements = step2_content.group(1).strip() if step2_content else ""
    
    return elements

def combine_elements(element1, element2, model_name, client):
    prompt = (
        f"以下の2つの情報を基に、ステップバイステップで3つのカテゴリに分けて情報を整理してください:\n"
        f"Step1.情報1と2から被っている情報を詳述\n"
        f"Step2.情報1と2のどちらかのみで出てきた情報を詳述\n"
        f"Step3.Step1, 2の全ての情報から推論できること\n"
        f"\n"
        f"出力は必ず、以下の参考フォーマットに従って出力してください。\n"
        f"参考フォーマット=\n"
        f"'''"
        f"Step1.情報1と2から被っている情報を詳述\n"
        f"〜Step1の内容をここに入力〜\n"
        f"\n"
        f"Step2.情報1と2のどちらかのみで出てきた情報を詳述\n"
        f"〜Step2の内容をここに入力〜\n"
        f"\n"
        f"Step3.Step1, 2の全ての情報から推論できること\n"
        f"〜Step3の内容をここに入力〜\n"
        f"'''\n"
        f"\n"
        f"###情報1:\n"
        f"{element1}\n"
        f"\n"
        f"###情報2:\n"
        f"{element2}\n"
        f"\n"
        f"補足：\n"
        f"各ステップには必ず最低1つは情報を入れてください。\n"
        f"指示の復唱はしないでください。\n"
        f"自己評価はしないでください。\n"
    )
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}]
    )
    content = response.choices[0].message.content

    # 各カテゴリに分けて情報を抽出
    part1 = re.search(r"Step1.情報1と2から被っている情報を詳述\n(.*?)\nStep2.情報1と2のどちらかのみで出てきた情報を詳述", content, re.DOTALL)
    part2 = re.search(r"Step2.情報1と2のどちらかのみで出てきた情報を詳述\n(.*?)\nStep3.Step1, 2の全ての情報から推論できること", content, re.DOTALL)
    part3 = re.search(r"Step3.Step1, 2の全ての情報から推論できること\n(.*)", content, re.DOTALL)

    info1 = part1.group(1).strip() if part1 else ""
    info2 = part2.group(1).strip() if part2 else ""
    info3 = part3.group(1).strip() if part3 else ""
    
    return info1, info2, info3

def generate_final_script1(info1, model_name, theme, characters, client):
    if characters == "ずんだもんとナレーター":
        system_prompt = (
            f"### Context ###\n"
            f"ユーザーが入力したスクリプトから、{theme}に関するYouTube動画を作成する原稿の一部を作成してください。\n"
            f"\n"
            f"### Objective ###\n"
            f"スクリプトの内容をもとに解説を行う動画の台本を作成してください。\n"
            f"動画のキャラクターは、解説係のナレーターと勉強係のずんだもんの2人です。\n"
            f"\n"
            f"### Style ###\n"
            f"- 以下の登場人物2名の会話形式で進行してください。\n"
            f"\n"
            f"###ナレーター\n"
            f"- 必要に応じて敬語を使用し、丁寧な解説係として振る舞ってください。\n"
            f"- 性格: 真面目な解説役。\n"
            f"- 一人称：「私」\n"
            f"\n"
            f"###ずんだもん\n"
            f"- 学習係として、明るく元気な性格。\n"
            f"- 一人称：「僕」「ずんだもん」\n"
            f"- 語尾: 〜のだ、〜なのだ\n"
            f"- 例:\n"
            f"  - 「僕の名前はずんだもんなのだ」\n"
            f"  - 「朝なのだ、早く起きるのだ」\n"
            f"\n"
            f"###2人の会話例\n"
            f"ずんだもん：こんにちは！僕の名前はずんだもんなのだ！\n"
            f"ナレーター：こんにちは、今日は{theme}についてお話ししようと思います。\n"
            f"ずんだもん：{theme}? 聞いたことあるのだ\n"
            f"〜会話続く〜\n"
            f"\n"
        )

        user_prompt = (
            f"以下の内容を元に、ナレーターとずんだもんの会話形式で{theme}に関する動画原稿の一部を作成してください。\n"
            f"スクリプト内の情報を、ナレーターが全て解説してください。\n"
            f"ずんだもんは解説を受けて、リアクションや疑問点をナレーターに返してください。動画の原稿としてスムーズに話が繋がるようにしてください。\n"
            f"\n"
            f"###スクリプト\n"
            f"{info1}\n"
            f"\n"
            f"\n"
            f"補足：\n"
            f"映像の説明は除外してください。\n"
            f"出力してもらう内容は原稿の一部です。最終的には他の原稿と結合するため、動画の終わりの挨拶は必要ないです。\n"
            f"指示の復唱はしないでください。\n"
            f"自己評価はしないでください。\n"
            f"結論やまとめは書かないでください。\n"
        )
    else:
        system_prompt = (
            f"### Context ###\n"
            f"ユーザーが入力したスクリプトから、{theme}に関するYouTube動画を作成する原稿の一部を作成してください。\n"
            f"\n"
            f"### Objective ###\n"
            f"スクリプトの内容をもとに解説を行う動画の台本を作成してください。\n"
            f"動画のキャラクターは、解説係の魔理沙と勉強係の霊夢の2人です。\n"
            f"\n"
            f"### Style ###\n"
            f"- 以下の登場人物2名の会話形式で進行してください。\n"
            f"\n"
            f"###魔理沙\n"
            f"- やや強気で物知りな女性。\n"
            f"- 突っ込み役として、霊夢の発言に対して訂正や補足をする。\n"
            f"-霊夢のことは呼び捨てにし、語尾に「だぜ！」をつけてしゃべる。\n"
            f"\n"
            f"###霊夢\n"
            f"- 少し抜けているところがあり、魔理沙に比べて知識量が少ない。\n"
            f"- 魔理沙に対してわからないことを質問する役割を持つ。\n"
            f"魔理沙のことは呼び捨てにする。\n"
            f"ボケ役としての役割があり、時々的外れなことを言い、それに対して魔理沙に修正される。\n"
            f"\n"
            f"###2人の会話例\n"
            f"霊夢：みなさん、こんにちは\n"
            f"魔理沙：こんにちは、今日は{theme}についてお話ししようと思います。\n"
            f"霊夢：{theme}? 聞いたことはあるわね。\n"
            f"〜会話続く〜\n"
            f"\n"
        )

        user_prompt = (
            f"以下の内容を元に、魔理沙と霊夢の会話形式で{theme}に関する動画原稿の一部を作成してください。\n"
            f"スクリプト内の情報を、魔理沙が全て解説してください。\n"
            f"霊夢は解説を受けて、リアクションや疑問点を魔理沙に返してください。動画の原稿としてスムーズに話が繋がるようにしてください。\n"
            f"\n"
            f"###スクリプト\n"
            f"{info1}\n"
            f"\n"
            f"\n"
            f"補足：\n"
            f"映像の説明は除外してください。\n"
            f"出力してもらう内容は原稿の一部です。最終的には他の原稿と結合するため、動画の終わりの挨拶は必要ないです。\n"
            f"指示の復唱はしないでください。\n"
            f"自己評価はしないでください。\n"
            f"結論やまとめは書かないでください。\n"
        )

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    final_script1 = response.choices[0].message.content
    return final_script1

def generate_final_script2(info2, model_name, theme, final_script1, characters, client):
    if characters == "ずんだもんとナレーター":
        system_prompt = (
            f"### Context ###\n"
            f"ユーザーが入力したスクリプトから、{theme}に関するYouTube動画を作成する原稿の一部を作成してください。\n"
            f"\n"
            f"### Objective ###\n"
            f"スクリプトの内容をもとに解説を行う動画の台本を作成してください。\n"
            f"動画のキャラクターは、解説係のナレーターと勉強係のずんだもんの2人です。\n"
            f"\n"
            f"### Style ###\n"
            f"- 以下の登場人物2名の会話形式で進行してください。\n"
            f"\n"
            f"###ナレーター\n"
            f"- 必要に応じて敬語を使用し、丁寧な解説係として振る舞ってください。\n"
            f"- 性格: 真面目な解説役。\n"
            f"- 一人称：「私」\n"
            f"\n"
            f"###ずんだもん\n"
            f"- 学習係として、明るく元気な性格。\n"
            f"- 一人称：「僕」「ずんだもん」\n"
            f"- 語尾: 〜のだ、〜なのだ\n"
            f"- 例:\n"
            f"  - 「僕の名前はずんだもんなのだ」\n"
            f"  - 「朝なのだ、早く起きるのだ」\n"
            f"\n"
            f"###2人の会話例\n"
            f"ずんだもん：こんにちは！僕の名前はずんだもんなのだ！\n"
            f"ナレーター：こんにちは、今日は{theme}についてお話ししようと思います。\n"
            f"ずんだもん：{theme}? 聞いたことあるのだ\n"
            f"〜会話続く〜\n"
            f"\n"
        )

        user_prompt = (
            f"以下の内容を元に、ナレーターとずんだもんの会話形式で{theme}に関する動画原稿の一部を作成してください。\n"
            f"###スクリプト内の情報を、ナレーターが全て詳細に解説してください。\n"
            f"ナレーターは、「こんな話もあります。」から会話を始めてください。\n"
            f"ずんだもんは解説を受けて、リアクションや疑問点をナレーターに返してください。動画の原稿としてスムーズに話が繋がるようにしてください。\n"
            f"今回作成してもらう原稿は、###前部分の原稿の続きとなります。最終的には他の原稿と結合するため、動画の冒頭や、終わりに挨拶は必要ないです。\n"
            f"\n"
            f"###スクリプト\n"
            f"{info2}\n"
            f"\n"
            f"\n"
            f"###前部分の原稿\n"
            f"{final_script1}\n"
            f"補足：\n"
            f"映像の説明は除外してください。\n"
            f"出力してもらう内容は原稿の一部です。最終的には他の原稿と結合するため、動画の冒頭や、終わりに挨拶は必要ないです。\n"
            f"指示の復唱はしないでください。\n"
            f"自己評価はしないでください。\n"
            f"結論やまとめは書かないでください。\n"
        )
    else:
        system_prompt = (
            f"### Context ###\n"
            f"ユーザーが入力したスクリプトから、{theme}に関するYouTube動画を作成する原稿の一部を作成してください。\n"
            f"\n"
            f"### Objective ###\n"
            f"スクリプトの内容をもとに解説を行う動画の台本を作成してください。\n"
            f"動画のキャラクターは、解説係の魔理沙と勉強係の霊夢の2人です。\n"
            f"\n"
            f"### Style ###\n"
            f"- 以下の登場人物2名の会話形式で進行してください。\n"
            f"\n"
            f"###魔理沙\n"
            f"- やや強気で物知りな女性。\n"
            f"- 突っ込み役として、霊夢の発言に対して訂正や補足をする。\n"
            f"-霊夢のことは呼び捨てにし、語尾に「だぜ！」をつけてしゃべる。\n"
            f"\n"
            f"###霊夢\n"
            f"- 少し抜けているところがあり、魔理沙に比べて知識量が少ない。\n"
            f"- 魔理沙に対してわからないことを質問する役割を持つ。\n"
            f"魔理沙のことは呼び捨てにする。\n"
            f"ボケ役としての役割があり、時々的外れなことを言い、それに対して魔理沙に修正される。\n"
            f"\n"
            f"###2人の会話例\n"
            f"霊夢：みなさん、こんにちは\n"
            f"魔理沙：こんにちは、今日は{theme}についてお話ししようと思います。\n"
            f"霊夢：{theme}? 聞いたことはあるわね。\n"
            f"〜会話続く〜\n"
            f"\n"
        )

        user_prompt = (
            f"以下の内容を元に、魔理沙と霊夢の会話形式で{theme}に関する動画原稿の一部を作成してください。\n"
            f"###スクリプト内の情報を、魔理沙が全て詳細に解説してください。\n"
            f"魔理沙は、「こんな話もあります。」から会話を始めてください。\n"
            f"霊夢は解説を受けて、リアクションや疑問点を魔理沙に返してください。動画の原稿としてスムーズに話が繋がるようにしてください。\n"
            f"今回作成してもらう原稿は、###前部分の原稿の続きとなります。最終的には他の原稿と結合するため、動画の冒頭や、終わりに挨拶は必要ないです。\n"
            f"\n"
            f"###スクリプト\n"
            f"{info2}\n"
            f"\n"
            f"\n"
            f"###前部分の原稿\n"
            f"{final_script1}\n"
            f"補足：\n"
            f"映像の説明は除外してください。\n"
            f"出力してもらう内容は原稿の一部です。最終的には他の原稿と結合するため、動画の冒頭や、終わりに挨拶は必要ないです。\n"
            f"指示の復唱はしないでください。\n"
            f"自己評価はしないでください。\n"
            f"結論やまとめは書かないでください。\n"
        )

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    final_script2 = response.choices[0].message.content
    return final_script2

def generate_final_script3(info3, model_name, theme, final_script1, final_script2, characters, client):
    if characters == "ずんだもんとナレーター":
        system_prompt = (
            f"### Context ###\n"
            f"ユーザーが入力したスクリプトから、{theme}に関するYouTube動画を作成する原稿の一部を作成してください。\n"
            f"\n"
            f"### Objective ###\n"
            f"スクリプトの内容をもとに解説を行う動画の台本を作成してください。\n"
            f"動画のキャラクターは、解説係のナレーターと勉強係のずんだもんの2人です。\n"
            f"\n"
            f"### Style ###\n"
            f"- 以下の登場人物2名の会話形式で進行してください。\n"
            f"\n"
            f"###ナレーター\n"
            f"- 必要に応じて敬語を使用し、丁寧な解説係として振る舞ってください。\n"
            f"- 性格: 真面目な解説役。\n"
            f"- 一人称：「私」\n"
            f"\n"
            f"###ずんだもん\n"
            f"- 学習係として、明るく元気な性格。\n"
            f"- 一人称：「僕」「ずんだもん」\n"
            f"- 語尾: 〜のだ、〜なのだ\n"
            f"- 例:\n"
            f"  - 「僕の名前はずんだもんなのだ」\n"
            f"  - 「朝なのだ、早く起きるのだ」\n"
            f"\n"
            f"###2人の会話例\n"
            f"ずんだもん：こんにちは！僕の名前はずんだもんなのだ！\n"
            f"ナレーター：こんにちは、今日は{theme}についてお話ししようと思います。\n"
            f"ずんだもん：{theme}? 聞いたことあるのだ\n"
            f"〜会話続く〜\n"
            f"\n"
        )

        user_prompt = (
            f"以下の内容を元に、ステップバイステップで、ナレーターとずんだもんの会話形式で{theme}に関する動画の原稿の一部を作成してください。\n"
            f"まず、今回作成してもらう原稿は、###前部分の原稿の続きとなります。最終的には他の原稿と結合するため、動画の冒頭に挨拶は必要ないです。\n"
            f"###スクリプト内の情報を、ナレーターが全て詳細に解説してください。\n"
            f"ずんだもんは解説を受けて、リアクションをしてください。二人のやりとりは動画の原稿としてスムーズに話が繋がるようにしてください。\n"
            f"\n"
            f"また、この動画は{theme}に関する視聴者の学習のメインとなる教材です。\n"
            f"視聴者の学習の手助けとなるよう、貴方の後期のコーパスの学習データで{theme}に関する知識で、###スクリプトや###前部分の原稿にまだ載せていない情報がもしあれば併せてナレーターが解説してください。\n"
            f"\n"
            f"###スクリプトの解説後、ナレーターは、動画のまとめとして###スクリプトやこれまでの###前部分の原稿をもとに動画の最後を簡単にまとめてください。\n"
            f"動画の最後には挨拶と共にチャンネル登録や高評価もお願いしてください。\n"
            f"\n"
            f"###スクリプト\n"
            f"{info3}\n"
            f"\n"
            f"\n"
            f"###前部分の原稿\n"
            f"{final_script1}\n"
            f"{final_script2}\n"
            f"補足：\n"
            f"映像の説明は除外してください。\n"
            f"出力してもらう内容は原稿の一部です。前部分の原稿と結合するため、動画の冒頭に挨拶は必要ないです。\n"
            f"指示の復唱はしないでください。\n"
            f"自己評価はしないでください。\n"
            f"結論やまとめは書かないください。\n"
        )
    else:
        system_prompt = (
            f"### Context ###\n"
            f"ユーザーが入力したスクリプトから、{theme}に関するYouTube動画を作成する原稿の一部を作成してください。\n"
            f"\n"
            f"### Objective ###\n"
            f"スクリプトの内容をもとに解説を行う動画の台本を作成してください。\n"
            f"動画のキャラクターは、解説係の魔理沙と勉強係の霊夢の2人です。\n"
            f"\n"
            f"### Style ###\n"
            f"- 以下の登場人物2名の会話形式で進行してください。\n"
            f"\n"
            f"###魔理沙\n"
            f"- やや強気で物知りな女性。\n"
            f"- 突っ込み役として、霊夢の発言に対して訂正や補足をする。\n"
            f"-霊夢のことは呼び捨てにし、語尾に「だぜ！」をつけてしゃべる。\n"
            f"\n"
            f"###霊夢\n"
            f"- 少し抜けているところがあり、魔理沙に比べて知識量が少ない。\n"
            f"- 魔理沙に対してわからないことを質問する役割を持つ。\n"
            f"魔理沙のことは呼び捨てにする。\n"
            f"ボケ役としての役割があり、時々的外れなことを言い、それに対して魔理沙に修正される。\n"
            f"\n"
            f"###2人の会話例\n"
            f"霊夢：みなさん、こんにちは\n"
            f"魔理沙：こんにちは、今日は{theme}についてお話ししようと思います。\n"
            f"霊夢：{theme}? 聞いたことはあるわね。\n"
            f"〜会話続く〜\n"
            f"\n"
        )

        user_prompt = (
            f"以下の内容を元に、ステップバイステップで、魔理沙と霊夢の会話形式で{theme}に関する動画の原稿の一部を作成してください。\n"
            f"まず、今回作成してもらう原稿は、###前部分の原稿の続きとなります。最終的には他の原稿と結合するため、動画の冒頭に挨拶は必要ないです。\n"
            f"###スクリプト内の情報を、魔理沙が全て詳細に解説してください。\n"
            f"霊夢は解説を受けて、リアクションをしてください。二人のやりとりは動画の原稿としてスムーズに話が繋がるようにしてください。\n"
            f"\n"
            f"また、この動画は{theme}に関する視聴者の学習のメインとなる教材です。\n"
            f"視聴者の学習の手助けとなるよう、貴方の後期のコーパスの学習データで{theme}に関する知識で、###スクリプトや###前部分の原稿にまだ載せていない情報がもしあれば併せて魔理沙が解説してください。\n"
            f"\n"
            f"###スクリプトの解説後、魔理沙は、動画のまとめとして###スクリプトやこれまでの###前部分の原稿をもとに動画の最後を簡単にまとめてください。\n"
            f"動画の最後には挨拶と共にチャンネル登録や高評価もお願いしてください。\n"
            f"\n"
            f"###スクリプト\n"
            f"{info3}\n"
            f"\n"
            f"\n"
            f"###前部分の原稿\n"
            f"{final_script1}\n"
            f"{final_script2}\n"
            f"補足：\n"
            f"映像の説明は除外してください。\n"
            f"出力してもらう内容は原稿の一部です。前部分の原稿と結合するため、動画の冒頭に挨拶は必要ないです。\n"
            f"指示の復唱はしないでください。\n"
            f"自己評価はしないでください。\n"
            f"結論やまとめは書かないでください。\n"
        )

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    final_script3 = response.choices[0].message.content
    return final_script3

def main():
    init_page()
    characters = select_characters()
    input_method = select_input_method()
    api_key = st.text_input("OpenAI APIキー:", type="password")
    model_name = "gpt-4o"

    if input_method == "動画":
        video_url1, video_url2, theme = get_video_urls()
    else:
        url1, url2, theme = get_text_urls()

    if st.button("台本生成") and api_key:
        client = OpenAI(api_key=api_key)

        if input_method == "動画":
            st.subheader("台本を作成中...")
            info1 = download_transcribe_and_extract(video_url1, model_name, theme, client)
            info2 = download_transcribe_and_extract(video_url2, model_name, theme, client)
        else:
            st.subheader("台本を作成中...")
            text1 = fetch_text_from_url(url1)
            text2 = fetch_text_from_url(url2)
            info1 = extract_elements(text1, model_name, theme, client)
            info2 = extract_elements(text2, model_name, theme, client)

        combined_elements = combine_elements(info1, info2, model_name, client)

        if 'final_script1' not in st.session_state:
            st.session_state['final_script1'] = generate_final_script1(combined_elements[0], model_name, theme, characters, client)
            st.session_state['final_script2'] = generate_final_script2(combined_elements[1], model_name, theme, st.session_state['final_script1'], characters, client)
            st.session_state['final_script3'] = generate_final_script3(combined_elements[2], model_name, theme, st.session_state['final_script1'], st.session_state['final_script2'], characters, client)

            st.session_state['combined_script'] = st.session_state['final_script1'] + "\n\n" + st.session_state['final_script2'] + "\n\n" + st.session_state['final_script3']

        st.subheader("台本が完成しました！")
        st.text_area("台本:", value=st.session_state['combined_script'], height=400)

        st.download_button(
            label="台本をダウンロード",
            data=st.session_state['combined_script'],
            file_name="combined_script.txt",
            mime="text/plain"
        )

if __name__ == "__main__":
    main()
