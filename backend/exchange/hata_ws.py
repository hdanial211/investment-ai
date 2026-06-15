import asyncio
import websockets
import json
import logging

logger = logging.getLogger(__name__)

class HataWebSocket:
    def __init__(self, on_message_callback=None):
        # Base url for Malaysia Hata WS
        self.url = "wss://websocket-my.hata.io/ws" 
        self.on_message_callback = on_message_callback
        self.is_running = False

    async def connect(self):
        self.is_running = True
        while self.is_running:
            try:
                logger.info(f"Connecting to Hata WS: {self.url}")
                async with websockets.connect(self.url) as websocket:
                    logger.info("Connected!")
                    
                    # Example subscribe to a public channel like trade or kline.
                    # This format might need to be adjusted based on actual Hata API docs.
                    subscribe_msg = {
                        "method": "subscribe",
                        "params": ["trade.BTC_MYR", "kline.1m.BTC_MYR"]
                    }
                    await websocket.send(json.dumps(subscribe_msg))
                    
                    while self.is_running:
                        message = await websocket.recv()
                        data = json.loads(message)
                        if self.on_message_callback:
                            self.on_message_callback(data)
                        else:
                            print(data)
                            
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WS Connection closed. Reconnecting in 5s...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"WS Error: {e}")
                await asyncio.sleep(5)

    def stop(self):
        self.is_running = False

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ws = HataWebSocket()
    try:
        asyncio.run(ws.connect())
    except KeyboardInterrupt:
        ws.stop()
