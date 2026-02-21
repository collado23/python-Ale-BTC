import os
import time
import threading
from datetime import datetime
import pytz

from http.server import BaseHTTPRequestHandler, HTTPServer
from binance.client import Client
from binance.enums import *

# ===== CONFIG =====
SYMBOLS = ["SOLUSDC", "XRPUSDC", "BNBUSDC"]
LEVERAGE_NORMAL = 5
LEVERAGE_USA = 7
LEVERAGE_BOOST = 15

BOOST_TRIGGER = 2.9
STOP_LOSS = -1.6
TRAILING_GAP = 0.5
FEE = 0.08

# ===== SERVER SALUD (Railway) =====
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"BOT ONLINE")

def run_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

# ===== SESIÓN USA =====
def is_usa_session():
    utc_now = datetime.utcnow()
    ny = pytz.timezone("America/New_York")
    ny_time = utc_now.replace(tzinfo=pytz.utc).astimezone(ny)
    return 9 <= ny_time.hour < 16

# ===== BALANCE USDC =====
def get_usdc_balance(client):
    balances = client.futures_account_balance()
    for b in balances:
        if b['asset'] == 'USDC':
            return float(b['balance'])
    return 0.0

# ===== CALCULAR CANTIDAD =====
def calculate_qty(client, symbol, price, leverage):
    balance = get_usdc_balance(client)
    capital = balance * 0.90
    qty = (capital * leverage) / price

    if "XRP" in symbol:
        return round(qty, 0)
    else:
        return round(qty, 2)

# ===== RECONEXIÓN =====
def reconnect_position(client):
    positions = client.futures_position_information()
    for p in positions:
        amt = float(p['positionAmt'])
        if amt != 0:
            return {
                "symbol": p['symbol'],
                "side": "LONG" if amt > 0 else "SHORT",
                "entry": float(p['entryPrice']),
                "qty": abs(amt),
                "leverage": int(p['leverage']),
                "max_roi": 0
            }
    return None

# ===== BOT =====
def bot():
    threading.Thread(target=run_server, daemon=True).start()

    client = Client(
        os.getenv("BINANCE_API_KEY"),
        os.getenv("BINANCE_API_SECRET")
    )

    operation = reconnect_position(client)
    last_loss_symbol = None
    pause_until = 0
    symbol_index = 0

    print("🚀 BOT V143 INICIADO")

    while True:
        try:
            now = time.time()

            if now < pause_until:
                print("⏸ Descansando 1 minuto...", end="\r")
                time.sleep(5)
                continue

            # ===== MODO SEGÚN SESIÓN =====
            if is_usa_session():
                leverage_entry = LEVERAGE_USA
                boost_trigger = 2.5
                session_label = "🇺🇸 USA"
            else:
                leverage_entry = LEVERAGE_NORMAL
                boost_trigger = BOOST_TRIGGER
                session_label = "🌍 GLOBAL"

            # ===== GESTIÓN =====
            if operation:
                price = float(client.futures_symbol_ticker(
                    symbol=operation["symbol"]
                )["price"])

                diff = (
                    (price - operation["entry"]) / operation["entry"]
                    if operation["side"] == "LONG"
                    else (operation["entry"] - price) / operation["entry"]
                )

                roi = (diff * 100 * operation["leverage"]) - FEE

                # Stop Loss
                if roi <= STOP_LOSS:
                    side_close = SIDE_SELL if operation["side"] == "LONG" else SIDE_BUY

                    client.futures_create_order(
                        symbol=operation["symbol"],
                        side=side_close,
                        type=ORDER_TYPE_MARKET,
                        quantity=operation["qty"]
                    )

                    print(f"\n🛑 STOP LOSS {operation['symbol']} {roi:.2f}%")

                    last_loss_symbol = operation["symbol"]
                    pause_until = time.time() + 60
                    symbol_index = (SYMBOLS.index(operation["symbol"]) + 1) % len(SYMBOLS)
                    operation = None
                    continue

                # Salto a 15x
                if roi >= boost_trigger and operation["leverage"] < 15:
                    client.futures_change_leverage(
                        symbol=operation["symbol"],
                        leverage=LEVERAGE_BOOST
                    )
                    operation["leverage"] = LEVERAGE_BOOST
                    print(f"\n🔥 SALTO A 15X {operation['symbol']}")

                # Trailing dinámico
                if operation["leverage"] == 15:
                    if roi > operation["max_roi"]:
                        operation["max_roi"] = roi

                    if roi <= operation["max_roi"] - TRAILING_GAP:
                        side_close = SIDE_SELL if operation["side"] == "LONG" else SIDE_BUY

                        client.futures_create_order(
                            symbol=operation["symbol"],
                            side=side_close,
                            type=ORDER_TYPE_MARKET,
                            quantity=operation["qty"]
                        )

                        print(f"\n✅ TRAILING EXIT {operation['symbol']} {roi:.2f}%")
                        operation = None
                        continue

                print(f"{session_label} | {operation['symbol']} | ROI: {roi:.2f}%   ", end="\r")

            # ===== ENTRADA =====
            if not operation:
                for i in range(len(SYMBOLS)):
                    symbol = SYMBOLS[(symbol_index + i) % len(SYMBOLS)]

                    if symbol == last_loss_symbol:
                        continue

                    klines = client.futures_klines(symbol=symbol, interval='1m', limit=30)
                    closes = [float(k[4]) for k in klines]
                    opens = [float(k[1]) for k in klines]

                    e9 = sum(closes[-9:]) / 9
                    e27 = sum(closes[-27:]) / 27

                    last_close = closes[-2]
                    last_open = opens[-2]

                    if (last_close > last_open and e9 > e27) or \
                       (last_close < last_open and e9 < e27):

                        price = float(client.futures_symbol_ticker(symbol=symbol)["price"])
                        qty = calculate_qty(client, symbol, price, leverage_entry)

                        if qty <= 0:
                            continue

                        side = SIDE_BUY if last_close > last_open else SIDE_SELL

                        client.futures_change_leverage(
                            symbol=symbol,
                            leverage=leverage_entry
                        )

                        client.futures_create_order(
                            symbol=symbol,
                            side=side,
                            type=ORDER_TYPE_MARKET,
                            quantity=qty
                        )

                        operation = {
                            "symbol": symbol,
                            "side": "LONG" if side == SIDE_BUY else "SHORT",
                            "entry": price,
                            "qty": qty,
                            "leverage": leverage_entry,
                            "max_roi": 0
                        }

                        symbol_index = SYMBOLS.index(symbol)
                        print(f"\n🎯 ENTRADA {symbol}")
                        break

            time.sleep(5)

        except Exception as e:
            print(f"\n⚠ ERROR: {e}")
            time.sleep(10)

if __name__ == "__main__":
    bot()
