import streamlit as st
import tweepy

# ⚠️ ソースコードには本物のキーは絶対に書かないでください！
# 後ほどStreamlitの設定画面（Secrets）に保存します
API_KEY = st.secrets["X_API_KEY"]
API_KEY_SECRET = st.secrets["X_API_KEY_SECRET"]

# ページのタイトルや説明（Streamlitが自動で綺麗なHTML画面にしてくれます）
st.title("📱 Xログイン式・ツイート一括削除ツール")
st.write("「Xでログイン」ボタンを押して連携するだけで、あなたのツイートを安全に削除できます。")

# サイトのURLを自動で判別してCallback URL（Xから戻ってくる先のURL）に設定
if "localhost" in st.context.headers.get("host", ""):
    CALLBACK_URL = "http://127.0.0.1:8501/"
else:
    CALLBACK_URL = f"https://{st.context.headers.get('host')}/"

# Xの認証ハンドラーを準備
auth = tweepy.OAuth1UserHandler(API_KEY, API_KEY_SECRET, callback=CALLBACK_URL)

# --- 認証フローの処理 ---
if "oauth_verifier" in st.query_params:
    st.success("Xとの連携を認証中...")
    auth.request_token = st.session_state.request_token
    verifier = st.query_params["oauth_verifier"]
    
    try:
        # アクセストークンを自動取得
        access_token, access_token_secret = auth.get_access_token(verifier)
        client = tweepy.Client(
            consumer_key=API_KEY,
            consumer_secret=API_KEY_SECRET,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        
        # ログインしたユーザーの情報を取得
        me = client.get_me()
        st.success(f"🎉 ログイン成功: @{me.data.username} として接続中")
        
        # --- 削除機能の表示 ---
        st.header("⚙️ ツイートの削除設定")
        max_results = st.slider("削除する最大件数を選んでください", min_value=1, max_value=100, value=10)
        
        if st.button("ツイートを取得して削除を開始する", type="primary"):
            with st.spinner("ツイートを取得中..."):
                tweets = client.get_users_tweets(id=me.data.id, max_results=max_results)
            
            if not tweets.data:
                st.info("削除できるツイートが見つかりませんでした。")
            else:
                st.subheader(f"{len(tweets.data)} 件を削除します:")
                progress_bar = st.progress(0)
                
                success_count = 0
                for i, tweet in enumerate(tweets.data):
                    try:
                        client.delete_tweet(id=tweet.id)
                        success_count += 1
                    except Exception as e:
                        st.error(f"削除失敗: {tweet.id} (エラー: {e})")
                    progress_bar.progress((i + 1) / len(tweets.data))
                
                st.success(f"✨ 完了しました！ 削除件数: {success_count} / {len(tweets.data)}")
                
    except Exception as e:
        st.error(f"ログイン処理中にエラーが発生しました: {e}")

else:
    # まだログインしていない一般のユーザーに見せる画面
    st.info("下のボタンからX（Twitter）アカウントと連携してください。APIキーの入力は不要です！")
    try:
        redirect_url = auth.get_authorization_url()
        st.session_state.request_token = auth.request_token
        st.link_button("🔑 X（Twitter）でログイン", redirect_url)
    except Exception as e:
        st.error(f"ログインURLの生成に失敗しました。管理者側の設定を確認してください。 エラー: {e}")