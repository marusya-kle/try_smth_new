#!/usr/bin/env python3
"""
GGTP (Guessing Game Transfer Protocol) - Асинхронный сервер
Реализация игры в угадывание числа поверх UDP с использованием asyncio.
"""

import asyncio
import hashlib
import random
import socket
import struct
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class GameSession:
    """Игровая сессия для клиента."""
    client_addr: Tuple[str, int]
    secret_number: int
    lower_bound: int
    upper_bound: int
    max_attempts: int
    attempts_left: int
    last_activity: float


class GGTPAsyncServer:
    """Асинхронный UDP сервер для протокола GGTP."""
    
    def __init__(self, host='127.0.0.1', port=8888):
        self.host = host
        self.port = port
        self.sessions: Dict[Tuple[str, int], GameSession] = {}
        self.loop = asyncio.get_running_loop()
        self.transport: Optional[asyncio.DatagramTransport] = None
        
    def _compute_crc32_seed(self, client_addr: Tuple[str, int]) -> int:
        """Вычисляет seed на основе CRC32 от IP-адреса."""
        ip = client_addr[0]
        crc = struct.unpack('I', hashlib.md5(ip.encode()).digest()[:4])[0]
        return crc
    
    def _generate_secret(self, seed: int) -> Tuple[int, int, int]:
        """
        Генерирует загаданное число и границы.
        Возвращает: (lower_bound, upper_bound, secret_number)
        """
        random.seed(seed)
        # Верхняя граница от 100 до 1000
        upper_bound = random.randint(100, 1000)
        # Нижняя граница всегда 1
        lower_bound = 1
        # Загаданное число
        secret = random.randint(lower_bound, upper_bound)
        return lower_bound, upper_bound, secret
    
    def _compute_win_key(self, client_addr: Tuple[str, int], secret: int) -> str:
        """Вычисляет победный ключ (хэш от IP и загаданного числа)."""
        ip = client_addr[0]
        data = f"{ip}:{secret}".encode()
        return hashlib.sha256(data).hexdigest()[:64]  # 64-значная hex-строка
    
    def _parse_message(self, data: bytes, addr: Tuple[str, int]) -> Tuple[str, list]:
        """Парсит входящее сообщение."""
        try:
            decoded = data.decode('utf-8').strip()
            parts = decoded.split()
            if not parts:
                return 'UNKNOWN', []
            
            command = parts[0].upper()
            args = parts[1:] if len(parts) > 1 else []
            return command, args
        except Exception:
            return 'UNKNOWN', []
    
    def _send_message(self, message: str, addr: Tuple[str, int]):
        """Отправляет сообщение клиенту."""
        if self.transport:
            self.transport.sendto(message.encode(), addr)
    
    async def _cleanup_timeout_sessions(self):
        """Удаляет сессии, у которых истекло время ожидания."""
        now = time.time()
        timeout = 30  # 30 секунд бездействия
        to_remove = []
        for addr, session in self.sessions.items():
            if now - session.last_activity > timeout:
                to_remove.append(addr)
        
        for addr in to_remove:
            print(f"️  Удалена сессия {addr} по тайм-ауту")
            del self.sessions[addr]
    
    async def _handle_helo(self, addr: Tuple[str, int], args: list):
        """Обрабатывает HELO сообщение."""
        # Проверяем, есть ли уже игра для этого IP
        if addr in self.sessions:
            # Игра уже существует
            session = self.sessions[addr]
            self._send_message(f"WLCM {session.lower_bound} {session.upper_bound}", addr)
            session.last_activity = time.time()
            return
        
        # Извлекаем тайм-аут, если указан
        client_timeout = float(args[0]) if args else 30.0
        
        # Инициализируем новую игру
        seed = self._compute_crc32_seed(addr)
        lower_bound, upper_bound, secret = self._generate_secret(seed)
        max_attempts = int((upper_bound - lower_bound + 1).bit_length())  # log2(range)
        
        # Создаем сессию
        session = GameSession(
            client_addr=addr,
            secret_number=secret,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            max_attempts=max_attempts,
            attempts_left=max_attempts,
            last_activity=time.time()
        )
        self.sessions[addr] = session
        
        print(f" Новая игра: {addr[0]}:{addr[1]}")
        print(f" Диапазон: {lower_bound}..{upper_bound} (попыток: {max_attempts})")
        print(f" Загадано: {secret}")
        
        # Отправляем приветствие
        self._send_message(f"WLCM {lower_bound} {upper_bound}", addr)
    
    async def _handle_gues(self, addr: Tuple[str, int], args: list):
        """Обрабатывает GUES сообщение."""
        # Проверяем существование сессии
        if addr not in self.sessions:
            self._send_message("FAIL No active game", addr)
            return
        
        session = self.sessions[addr]
        session.last_activity = time.time()
        
        # Проверяем формат
        if not args or not args[0].isdigit():
            self._send_message("FAIL Invalid number", addr)
            return
        
        guess = int(args[0])
        session.attempts_left -= 1
        
        # Проверяем попытку
        if guess == session.secret_number:
            # Угадано!
            win_key = self._compute_win_key(addr, session.secret_number)
            self._send_message(f"BING {win_key}", addr)
            print(f" Игрок {addr[0]}:{addr[1]} угадал число {session.secret_number}!")
            print(f" Победный ключ: {win_key[:16]}...")
            del self.sessions[addr]
            
        elif session.attempts_left <= 0:
            # Закончились попытки
            self._send_message("FAIL", addr)
            print(f" Игрок {addr[0]}:{addr[1]} не угадал. Загадано: {session.secret_number}")
            del self.sessions[addr]
            
        elif guess < session.secret_number:
            self._send_message("MORE", addr)
            print(f"   {addr[0]}:{addr[1]} → {guess} (нужно больше)")
            
        else:
            self._send_message("LESS", addr)
            print(f" {addr[0]}:{addr[1]} → {guess} (нужно меньше)")
    
    async def handle_datagram(self, data: bytes, addr: Tuple[str, int]):
        """Обрабатывает входящую датаграмму."""
        command, args = self._parse_message(data, addr)
        
        if command == 'HELO':
            await self._handle_helo(addr, args)
        elif command == 'GUES':
            await self._handle_gues(addr, args)
        else:
            self._send_message("FAIL Unknown command", addr)
    
    async def start(self):
        """Запускает сервер."""
        print(f" Запуск GGTP сервера на {self.host}:{self.port}")
        
        # Создаем UDP сокет
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        
        # Регистрируем транспорт
        self.transport, _ = await self.loop.create_datagram_endpoint(
            lambda: GGTPAsyncServerProtocol(self),
            sock=sock
        )
        
        # Запускаем периодическую очистку
        while True:
            await asyncio.sleep(10)
            await self._cleanup_timeout_sessions()
    
    def stop(self):
        """Останавливает сервер."""
        if self.transport:
            self.transport.close()


class GGTPAsyncServerProtocol(asyncio.DatagramProtocol):
    """Протокол для обработки UDP датаграмм."""
    
    def __init__(self, server: GGTPAsyncServer):
        self.server = server
    
    def datagram_received(self, data: bytes, addr: Tuple[str, int]):
        """Вызывается при получении датаграммы."""
        asyncio.create_task(self.server.handle_datagram(data, addr))
    
    def error_received(self, exc):
        """Вызывается при ошибке."""
        print(f"️ Ошибка: {exc}")


async def main():
    server = GGTPAsyncServer(host='127.0.0.1', port=8888)
    try:
        await server.start()
    except KeyboardInterrupt:
        print("\n Сервер остановлен")
        server.stop()


if __name__ == "__main__":
    asyncio.run(main())
