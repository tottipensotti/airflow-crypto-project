import requests
import time
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta

default_args = {
    "owner": "Totti",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
}

coins = [
    {"id":"bitcoin", "symbol":"BTC", "name": "Bitcoin"},
    {"id":"ethereum", "symbol":"ETH", "name": "Ethereum"},
    {"id":"solana", "symbol":"SOL", "name": "Solana"},
    {"id":"dogecoin", "symbol":"DOGE", "name": "Dogecoin"},
    {"id":"cardano", "symbol":"ADA", "name": "Cardano"},
    {"id":"uniswap", "symbol":"UNI", "name": "Uniswap"},
    {"id":"shiba-inu", "symbol":"SHIB", "name": "Shiba Inu"},
    {"id":"polkadot", "symbol":"DOT", "name": "Polkadot"},
    {"id":"avalanche-2", "symbol":"AVAX", "name": "Avalanche"},
    {"id":"chainlink", "symbol":"LINK", "name": "Chainlink"},
    {"id":"binancecoin", "symbol":"BNB", "name": "Binance Coin"},
    {"id":"ripple", "symbol":"XRP", "name": "Ripple"},
]

id_to_symbol={coin["id"]: coin["symbol"].upper() for coin in coins}
id_to_name={coin["id"]: coin["name"] for coin in coins}

crypto_list = [
    "bitcoin", "ethereum", "solana", "dogecoin", "cardano","uniswap",
    "shiba-inu", "polkadot", "avalanche-2", "chainlink","binancecoin","ripple"
]

def fetch_data(crypto_id, **kwargs):
    url = "https://api.coingecko.com/api/v3/simple/price"
    print(f"[INFO] Fetching price for {crypto_id}...")
    try:
        response = requests.get(url, params = {"ids": crypto_id, "vs_currencies": "usd"})
        response.raise_for_status()
        data = response.json()
        price = data[crypto_id]["usd"]
        print(f"[INFO] Current {crypto_id} price is ${price}")
        print(f"[INFO] All cryptocurrencies fetched.")
        return {
            "name": id_to_name.get(crypto_id),
            "ticker": id_to_symbol.get(crypto_id),
            "price": price,
            "timestamp": datetime.now().isoformat()
        }
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] {e}")
        raise

def insert_data(**context):
    time.sleep(2)
    crypto_data = context["ti"].xcom_pull(task_ids="get_crypto_price")
    if not crypto_data:
        raise ValueError("No data pulled from XCom; fetch_data may have failed.")
    hook = PostgresHook(postgres_conn_id="postgres_default")

    hook.run(
        "INSERT INTO crypto.prices (name, ticker, price, updated_at) VALUES (%s, %s, %s, %s)",
        parameters=(
            crypto_data["name"],
            crypto_data["ticker"],
            crypto_data["price"],
            crypto_data["timestamp"]
        )
    )

def create_dag(dag_id, schedule, default_args, crypto_id):
    dag = DAG(
        dag_id,
        default_args=default_args,
        schedule=schedule,
        start_date=datetime.now(),
        catchup=False,
        tags=["crypto"]
    )

    with dag:
        t1 = PythonOperator(
            task_id="get_crypto_price",
            python_callable=fetch_data,
            op_args=[crypto_id]
        )

        t2 = PythonOperator(
            task_id="insert_crypto_price",
            python_callable=insert_data,
            provide_context=True
        )

for coin in crypto_list:
    dag_id = f"{coin}_price"
    default_args = default_args
    schedule = "*/15 * * * *"

    globals()[dag_id] = create_dag(dag_id, schedule, default_args, coin)