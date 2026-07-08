import streamlit as st
import tweepy
import requests
import base64

CLIENT_ID = st.secrets["X_CLIENT_ID"]
CLIENT_SECRET = st.secrets["X_CLIENT_SECRET"]

st.title("📱 Xログイン式・ツイート直接削除ツール")
st.write("無料プランの制限を回避し、指定したツイートを安全に削除します。")

CALLBACK_URL = "https://twittcssa-nfkrngpahr8urhhomfjzg.streamlit.app/"

st.header("ステップ 1: Xアカウントと連携する")

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

st.header("ステップ 2: 認証コードを入力する")
user_code = st.text_input("ここにコピーしたコードを入力")

if user_code:
    if st.button("🔑 ログインして削除画面を開く", type="primary"):
        try:
            with st.spinner("トークンを回収中..."):
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
                    st.error(f"X側でエラーが発生しました: {res_data}")
                else:
                    st.success("🎉 ログインに成功しました！下のフォームから削除できます。")
                    st.session_state["access_token"] = res_data["access_token"]

        except Exception as e:
            st.error(f"システムエラー: {e}")

# --- ログイン成功後に表示する「直接削除画面」 ---
if "access_token" in st.session_state:
    st.markdown("---")
    st.header("🗑️ ツイートの直接削除")
    st.write("消したいツイートのURL、またはツイートIDを入力してください。")
    st.caption("例: `https://x.com/username/status/1234567890` または `1234567890`")
    
    tweet_input = st.text_input("ツイートのURL または ID")
    
    if st.button("🚨 このツイートを完全に削除する", type="primary"):
        if tweet_input:
            # URLからID（数字の部分）だけを抜き出す処理
            tweet_id = tweet_input.split("/status/")[-1].split("?")[0].strip()
            
            if tweet_id.isdigit():
                try:
                    with st.spinner("削除を実行中..."):
                        client = tweepy.Client(access_token=st.session_state["access_token"])
                        client.delete_tweet(id=int(tweet_id))
                    st.success(f"✨ ツイート（ID: {tweet_id}）の削除に成功しました！")
                except Exception as e:
                    st.error(f"削除に失敗しました。すでに消えているか、権限がない可能性があります: {e}")
            else:
                st.error("有効なツイートIDまたはURLを入力してください。")
