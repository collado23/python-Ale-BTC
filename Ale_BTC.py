import os
import sys
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from binance.client import Client
from binance.enums import *

# ===== CONFIG =====
SYMBOLS = ["SOLUSDC", "XRPUSDC", "BNBUSDC"]
LEVERAGE_INITIAL = 5
LEVERAGE_BOOST = 15
BOOST_TRIGGER = 2.9
STOP_LOSS = -1.6
FEE = 0.08
CAPITAL_PERCENT = 0.90

# ===== LOG FORZADO (Railway fix) =====
def log(msg):
    print(msg)
    sys.stdout.flush()

# ===== HEALTH SERVER =====
class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"BOT ONLINE")

def run_server():
    port = int(os.getenv("PORT", 8080))
    HTTPServer(("0.0.0.0", port), Health).serve_forever()

# ===== BALANCE USDC =====
def get_usdc_balance(client):
    balances = client.futures_account_balance()
    for b in balances:
        if b['asset'] == 'USDC':
            return float(b['balance'])
    return 0.0

# ===== CALCULAR QTY AUTOMÁTICO =====
def calculate_qty(client, symbol, price, leverage):
    balance = get_usdc_balance(client)
    capital = balance * CAPITAL_PERCENT
    raw_qty = (capital * leverage) / price

    if "XRP" in symbol:
        return round(raw_qty, 0)
    elif "BNB" in symbol:
        return round(raw_qty, 2)
    else:
        return round(raw_qty, 2)

# ===== TRAILING DINÁMICO =====
def get_dynamic_gap(max_roi):
    if max_roi >= 10:
        return 0.25
    elif max_roi >= 8:
        return 0.30
    elif max_roi >= 6:
        return 0.40
    else:
        return 0.50

# ===== BOT =====
def bot():
    threading.Thread(target=run_server, daemon=True).start()

    client = Client(
        os.getenv("BINANCE_API_KEY"),
        os.getenv("BINANCE_API_SECRET")
    )

    operation = None
    log("🚀 BOT V143 COMPLETO INICIADO")

    while True:
        try:
            # =============================
            # GESTIÓN DE OPERACIÓN ACTIVA
            # =============================
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

                # Guardar historial ROI
                operation["roi_history"].append(roi)
                if len(operation["roi_history"]) > 3:
                    operation["roi_history"].pop(0)

                # 🔥 SALTO A 15X CON IMPULSO
                if (
                    roi >= BOOST_TRIGGER
                    and operation["leverage"] == LEVERAGE_INITIAL
                    and len(operation["roi_history"]) == 3
                    and operation["roi_history"][2] > operation["roi_history"][1] > operation["roi_history"][0]
                ):
                    client.futures_change_leverage(
                        symbol=operation["symbol"],
                        leverage=LEVERAGE_BOOST
                    )
                    operation["leverage"] = LEVERAGE_BOOST
                    operation["max_roi"] = roi
                    log(f"🔥 SALTO CONFIRMADO A 15X EN {operation['symbol']}")

                # 📈 TRAILING DINÁMICO
                if operation["leverage"] == LEVERAGE_BOOST:
                    if roi > operation["max_roi"]:
                        operation["max_roi"] = roi

                    gap = get_dynamic_gap(operation["max_roi"])
                    trailing_stop = operation["max_roi"] - gap

                    if roi <= trailing_stop:
                        side_close = SIDE_SELL if operation["side"] == "LONG" else SIDE_BUY
                        client.futures_create_order(
                            symbol=operation["symbol"],
                            side=side_close,
                            type=ORDER_TYPE_MARKET,
                            quantity=operation["qty"]
                        )
                        log(f"🏁 TRAILING STOP | ROI: {roi:.2f}%")
                        operation = None
                        continue

                # 🛑 STOP FIJO
                if roi <= STOP_LOSS:
                    side_close = SIDE_SELL if operation["side"] == "LONG" else SIDE_BUY
                    client.futures_create_order(
                        symbol=operation["symbol"],
                        side=side_close,
                        type=ORDER_TYPE_MARKET,
                        quantity=operation["qty"]
                    )
                    log(f"🛑 STOP LOSS | ROI: {roi:.2f}%")
                    operation = None
                    continue

                log(f"{operation['symbol']} | ROI: {roi:.2f}%")

            # =============================
            # BUSCAR NUEVA ENTRADA
            # =============================
            if not operation:
                for symbol in SYMBOLS:

                    klines = client.futures_klines(
                        symbol=symbol,
                        interval='1m',
                        limit=30
                    )

                    closes = [float(k[4]) for k in klines]
                    opens = [float(k[1]) for k in klines]

                    e9 = sum(closes[-9:]) / 9
                    e27 = sum(closes[-27:]) / 27

                    last_close = closes[-2]
                    last_open = opens[-2]

                    # LONG
                    if last_close > last_open and e9 > e27:
                        price = float(client.futures_symbol_ticker(symbol=symbol)["price"])
                        qty = calculate_qty(client, symbol, price, LEVERAGE_INITIAL)

                        if qty <= 0:
                            continue

                        client.futures_change_leverage(symbol=symbol, leverage=LEVERAGE_INITIAL)

                        client.futures_create_order(
                            symbol=symbol,
                            side=SIDE_BUY,
                            type=ORDER_TYPE_MARKET,
                            quantity=qty
                        )

                        operation = {
                            "symbol": symbol,
                            "side": "LONG",
                            "entry": price,
                            "leverage": LEVERAGE_INITIAL,
                            "qty": qty,
                            "max_roi": 0,
                            "roi_history": []
                        }

                        log(f"🎯 LONG 5X EN {symbol} | QTY: {qty}")
                        break

                    # SHORT
                    if last_close < last_open and e9 < e27:
                        price = float(client.futures_symbol_ticker(symbol=symbol)["price"])
                        qty = calculate_qty(client, symbol, price, LEVERAGE_INITIAL)

                        if qty <= 0:
                            continue

                        client.futures_change_leverage(symbol=symbol, leverage=LEVERAGE_INITIAL)

                        client.futures_create_order(
                            symbol=symbol,
                            side=SIDE_SELL,
                            type=ORDER_TYPE_MARKET,
                            quantity=qty
                        )

                        operation = {
                            "symbol": symbol,
                            "side": "SHORT",
                            "entry": price,
                            "leverage": LEVERAGE_INITIAL,
                            "qty": qty,
                            "max_roi": 0,
                            "roi_history": []
                        }

                        log(f"🎯 SHORT 5X EN {symbol} | QTY: {qty}")
                        break

            time.sleep(5)

        except Exception as e:
            log(f"⚠ ERROR: {e}")
            time.sleep(10)

if __name__ == "__main__":
    bot()
