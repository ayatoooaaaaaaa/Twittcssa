import streamlit as st
import tweepy

# ⚠️ OAuth 2.0用の新しい鍵をSecretsから読み込みます
CLIENT_ID = st.secrets["X_CLIENT_ID"]
CLIENT_SECRET = st.secrets["X_CLIENT_SECRET"]

st.title("📱 Xログイン式・ツイート一括削除ツール")
st.write("「Xでログイン」ボタンを押して連携するだけで、あなたのツイートを安全に削除できます。")

# サイトのURLを自動で判別してCallback URLに設定
if "localhost" in st.context.headers.get("host", ""):
    CALLBACK_URL = "http://127.0.0.1:8501/"
else:
    CALLBACK_URL = f"https://{st.context.headers.get('host')}/"

# ツイートの読み込み・削除に必要な権限（スコープ）を指定
scopes = ["tweet.read", "tweet.write", "users.read"]

# OAuth 2.0 認証ハンドラーを準備
auth_handler = tweepy.OAuth2UserHandler(
    client_id=CLIENT_ID,
    redirect_uri=CALLBACK_URL,
    scope=scopes,
    client_secret=CLIENT_SECRET
)

# --- 認証フローの処理 ---
if "code" in st.query_params:
    st.success("Xとの連携を認証中...")
    
    # セッションから認証URL生成時の状態を復元
    if "auth_url" in st.session_state:
        try:
            # 認可コードからアクセストークンを取得
            token = auth_handler.fetch_token(st.experimental_get_query_params()["code"][0] if hasattr(st, "experimental_get_query_params") else st.query_params["code"])
            
            # OAuth 2.0用のクライアントを作成
            client = tweepy.Client(
                access_token=token["access_token"]
            )
            
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
            st.error(f"ログイン処理中にエラーが発生しました: {e}")
else:
    # まだログインしていない一般のユーザーに見せる画面
    st.info("下のボタンからX（Twitter）アカウントと連携してください。APIキーの入力は不要です！")
    try:
        authorization_url = auth_handler.get_authorization_url()
        st.session_state.auth_url = authorization_url
        st.link_button("🔑 X（Twitter）でログイン", authorization_url)
    except Exception as e:
        st.error(f"ログインURLの生成に失敗しました。管理者側の設定を確認してください。 エラー: {e}")
