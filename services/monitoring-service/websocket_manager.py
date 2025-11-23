from fastapi import WebSocket
from typing import List
import json

class ConnectionManager:
    """WebSocket connection manager for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        client_info = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            print(f"[WebSocketManager] Conexão aceita - client={client_info}, total={len(self.active_connections)}")
        except Exception as e:
            print(f"[WebSocketManager] ERRO ao aceitar conexão - client={client_info}, error={str(e)}", exc_info=True)
            raise
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        client_info = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"[WebSocketManager] Conexão removida - client={client_info}, total={len(self.active_connections)}")
        else:
            print(f"[WebSocketManager] AVISO: Tentativa de remover conexão inexistente - client={client_info}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific WebSocket"""
        client_info = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"
        try:
            await websocket.send_text(message)
            print(f"[WebSocketManager] Mensagem pessoal enviada - client={client_info}, size={len(message)}")
        except Exception as e:
            print(f"[WebSocketManager] ERRO ao enviar mensagem pessoal - client={client_info}, error={str(e)}", exc_info=True)
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected WebSockets"""
        disconnected = []
        total = len(self.active_connections)
        print(f"[WebSocketManager] Iniciando broadcast - total_connections={total}, message_size={len(message)}")
        
        for i, connection in enumerate(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception as e:
                client_info = f"{connection.client.host}:{connection.client.port}" if connection.client else "unknown"
                print(f"[WebSocketManager] ERRO ao fazer broadcast - connection={i+1}/{total}, client={client_info}, error={str(e)}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        if disconnected:
            print(f"[WebSocketManager] Removendo {len(disconnected)} conexões desconectadas")
            for connection in disconnected:
                self.disconnect(connection)
        
        successful = total - len(disconnected)
        print(f"[WebSocketManager] Broadcast concluído - enviado={successful}/{total}")
    
    async def broadcast_to_role(self, message: str, target_role: str):
        """Broadcast message to specific user role (would need user context)"""
        # This would require storing user information with connections
        # For now, broadcast to all
        await self.broadcast(message)


