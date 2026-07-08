import streamlit as st
import tweepy

CLIENT_ID = st.secrets["X_CLIENT_ID"]
CLIENT_SECRET = st.secrets["X_CLIENT_SECRET"]

st.title("📱 Xログイン式・ツイート一括削除ツール")
st.write("安全にツイートを一括削除するためのツールです。")

# サイトのURL
if "localhost" in st.context.headers.get("host", ""):
    CALLBACK_URL = "http://127.0.0.1:8501/"
else:
    CALLBACK_URL = f"https://{st.context.headers.get('host')}/"

scopes = ["tweet.read", "tweet.write", "users.read"]

# 毎回完全に独立した状態で認証を動かす
auth_handler = tweepy.OAuth2UserHandler(
    client_id=CLIENT_ID,
    redirect_uri=CALLBACK_URL,
    scope=scopes,
    client_secret=CLIENT_SECRET
)

# 1. まずはユーザーに連携用リンクを踏んでもらう
st.header("ステップ 1: Xアカウントと連携する")
try:
    # 毎回エラーの起きないクリーンなURLを生成
    authorization_url = auth_handler.get_authorization_url()
    st.markdown(f"**[👉 ここをクリックしてXでアプリを連携する]({authorization_url})**")
    st.caption("※クリックすると新しいタブでXの許可画面が開きます。")
except Exception as e:
    st.error(f"URL生成エラー: {e}")

# 2. 連携後にURLに表示される「code=xxxx」の「xxxx」の部分を自分で貼ってもらう形にする
st.header("ステップ 2: 認証コードを入力する")
st.write("Xの画面で『アプリにアクセスを許可』を押した後、ブラウザのURL欄を確認してください。")
st.write("URLの中にある `code=xxxxxxxxx` の、**`code=` から後ろの英数字の文字列**をコピーして下に貼り付けてください。")

user_code = st.text_input("ここにコピーしたコードを入力（例: dndVc3dEcU...）")

if user_code:
    if st.button("🔑 このコードでログインして削除画面を開く", type="primary"):
        try:
            with st.spinner("ログイン処理中..."):
                # ユーザーがコピペしてくれたコードを使って直接トークンを奪取
                token = auth_handler.fetch_token(code=user_code.strip())
                client = tweepy.Client(access_token=token["access_token"])
                me = client.get_me()
                
            st.success(f"🎉 ログイン成功: @{me.data.username} として接続しました！")
            
            # --- 削除機能 ---
            st.header("⚙️ ツイートの削除設定")
            max_results = st.slider("削除する最大件数", min_value=1, max_value=100, value=10)
            
            if st.button("🚀 ツイートを取得して削除を開始する"):
                with st.spinner("削除中..."):
                    tweets = client.get_users_tweets(id=me.data.id, max_results=max_results)
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
                        
        except Exception as e:
            st.error(f"ログインに失敗しました。コードが古いか、入力が間違っている可能性があります: {e}")
