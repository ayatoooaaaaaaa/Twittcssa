import streamlit as st
import tweepy

CLIENT_ID = st.secrets["X_CLIENT_ID"]
CLIENT_SECRET = st.secrets["X_CLIENT_SECRET"]

st.title("📱 Xログイン式・ツイート一括削除ツール")
st.write("「Xでログイン」ボタンを押して連携するだけで、あなたのツイートを安全に削除できます。")

# サイトのURLを自動で判別
if "localhost" in st.context.headers.get("host", ""):
    CALLBACK_URL = "http://127.0.0.1:8501/"
else:
    CALLBACK_URL = f"https://{st.context.headers.get('host')}/"

scopes = ["tweet.read", "tweet.write", "users.read"]

auth_handler = tweepy.OAuth2UserHandler(
    client_id=CLIENT_ID,
    redirect_uri=CALLBACK_URL,
    scope=scopes,
    client_secret=CLIENT_SECRET
)

# --- 認証フローの処理 ---
if "code" in st.query_params:
    st.success("Xとの連携を認証中...")
    
    try:
        # Xから戻ってきたときのアクセスURL（認証コードが含まれる全体）を生成
        # これをfetch_tokenに渡すことでエラーを回避します
        current_url = f"{CALLBACK_URL}?code={st.query_params['code']}"
        if "state" in st.query_params:
            current_url += f"&state={st.query_params['state']}"
            
        # 引数に authorization_response としてURL全体を正しく渡す
        token = auth_handler.fetch_token(authorization_response=current_url)
        
        # クライアントの作成
        client = tweepy.Client(access_token=token["access_token"])
        
        # ログインユーザーの情報を取得
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
        st.error(f"ログイン処理中にエラーが発生しました。アプリ設定を確認してください: {e}")
else:
    st.info("下のボタンからX（Twitter）アカウントと連携してください。APIキーの入力は不要です！")
    try:
        # 毎回クリーンな状態でURLを生成
        authorization_url = auth_handler.get_authorization_url()
        st.link_button("🔑 X（Twitter）でログイン", authorization_url)
    except Exception as e:
        st.error(f"ログインURLの生成に失敗しました。管理者側の設定を確認してください。 エラー: {e}")
