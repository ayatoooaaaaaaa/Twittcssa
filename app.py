import streamlit as st
import tweepy
import requests
import base64

CLIENT_ID = st.secrets["X_CLIENT_ID"]
CLIENT_SECRET = st.secrets["X_CLIENT_SECRET"]

st.title("📱 Xログイン式・ツイート一括削除ツール")
st.write("安全にツイートを一括削除するためのツールです。")

# サイトのURL
if "localhost" in st.context.headers.get("host", ""):
    CALLBACK_URL = "http://127.0.0.1:8501/"
else:
    CALLBACK_URL = f"https://{st.context.headers.get('host')}/"

# 1. ユーザーに連携用リンクを踏んでもらう
st.header("ステップ 1: Xアカウントと連携する")

# ライブラリのバグを回避するため、固定のStateで認証URLを作成
scopes = "tweet.read tweet.write users.read"
authorization_url = (
    f"https://twitter.com/i/oauth2/authorize"
    f"?response_type=code"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri={CALLBACK_URL}"
    f"&scope=tweet.read%20tweet.write%20users.read"
    f"&state=mystate123"
    f"&code_challenge=challenge"
    f"&code_challenge_method=plain"
)

st.markdown(f"**[👉 ここをクリックしてXでアプリを連携する]({authorization_url})**")
st.caption("※クリックすると新しいタブでXの許可画面が開きます。すでに許可済みの場合はそのままURLが変わります。")

# 2. 連携後にURLに表示される「code=xxxx」の「xxxx」の部分を自分で貼ってもらう
st.header("ステップ 2: 認証コードを入力する")
st.write("Xの画面で『アプリにアクセスを許可』を押した後、ブラウザのURL欄を確認してください。")
st.write("URLの中にある `code=xxxxxxxxx` の部分をコピーして下に貼り付けてください。")

user_code = st.text_input("ここにコピーしたコードを入力")

if user_code:
    if st.button("🔑 このコードでログインして削除画面を開く", type="primary"):
        try:
            with st.spinner("ログイン処理中..."):
                # ライブラリの相性問題を完全スルーして、直接APIを叩いてトークンをもぎ取る最強の処理
                token_url = "https://api.twitter.com/2/oauth2/token"
                auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
                b64_auth_str = base64.b64encode(auth_str.encode()).decode()
                
                headers = {
                    "Authorization": f"Basic {b64_auth_str}",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
                data = {
                    "code": user_code.strip(),
                    "grant_type": "authorization_code",
                    "redirect_uri": CALLBACK_URL,
                    "code_verifier": "challenge"
                }
                
                response = requests.post(token_url, headers=headers, data=data)
                res_data = response.json()
                
                if "access_token" not in res_data:
                    st.error(f"Xからエラーが返されました: {res_data}")
                else:
                    access_token = res_data["access_token"]
                    client = tweepy.Client(access_token=access_token)
                    me = client.get_me()
                    
                    st.success(f"🎉 ログイン成功: @{me.data.username} として接続しました！")
                    st.session_state["x_client"] = client
                    st.session_state["x_user_id"] = me.data.id

        except Exception as e:
            st.error(f"ログイン処理中に予期せぬエラーが発生しました: {e}")

# --- ログイン成功後の削除画面の表示 ---
if "x_client" in st.session_state:
    st.hr()
    st.header("⚙️ ツイートの削除設定")
    max_results = st.slider("削除する最大件数", min_value=1, max_value=100, value=10)
    
    if st.button("🚀 ツイートを取得して削除を開始する", type="primary"):
        client = st.session_state["x_client"]
        user_id = st.session_state["x_user_id"]
        
        with st.spinner("削除中..."):
            tweets = client.get_users_tweets(id=user_id, max_results=max_results)
            if not tweets.data:
                st.info("削除できるツイートが見つかりませんでした。")
            else:
                progress_bar = st.progress(0)
                success_count = 0
                for i, tweet in enumerate(tweets.data):
                    try:
                        client.delete_tweet(id=tweet.id)
                        success_count += 1
                    except Exception:
                        pass
                    progress_bar.progress((i + 1) / len(tweets.data))
                st.success(f"✨ 完了しました！ 削除件数: {success_count} / {len(tweets.data)}")
