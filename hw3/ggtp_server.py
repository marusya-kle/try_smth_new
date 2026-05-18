#!/usr/bin/env python3
"""
GGTP (Guessing Game Transfer Protocol) - Синхронный сервер
Реализация игры в угадывание числа поверх UDP с использованием socket.
"""

import socket
import hashlib
import random
import struct
import time
from threading import Thread
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class GameSession:
    """Игровая сессия для клиента."""
    secret_number: int
    lower_bound: int
    upper_bound: int
    max_attempts: int
    attempts_left: int
    last_activity: float


class GGTPServer:
    """Синхронный UDP сервер для протокола GGTP."""
    
    def __init__(self, host='127.0.0.1', port=8888):
        self.host = host
        self.port = port
        self.sessions: Dict[Tuple[str, int], GameSession] = {}
        self.running = False
        self.sock = None
        
    def _compute_crc32_seed(self, client_addr: Tuple[str, int]) -> int:
        """Вычисляет seed на основе CRC32 от IP-адреса."""
        ip = client_addr[0]
        crc = struct.unpack('I', hashlib.md5(ip.encode()).digest()[:4])[0]
        return crc
    
    def _generate_secret(self, seed: int) -> Tuple[int, int, int]:
        """Генерирует загаданное число и границы."""
        random.seed(seed)
        upper_bound = random.randint(100, 1000)
        lower_bound = 1
        secret = random.randint(lower_bound, upper_bound)
        return lower_bound, upper_bound, secret
    
    def _compute_win_key(self, client_addr: Tuple[str, int], secret: int) -> str:
        """Вычисляет победный ключ."""
        ip = client_addr[0]
        data = f"{ip}:{secret}".encode()
        return hashlib.sha256(data).hexdigest()[:64]
    
    def _parse_message(self, data: bytes) -> Tuple[str, list]:
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
    
    def _cleanup_timeout_sessions(self):
        """Удаляет сессии с истекшим тайм-аутом."""
        now = time.time()
        timeout = 30
        to_remove = [addr for addr, session in self.sessions.items() 
                     if now - session.last_activity > timeout]
        
        for addr in to_remove:
            print(f"️ Удалена сессия {addr}")
            del self.sessions[addr]
    
    def handle_client(self, data: bytes, addr: Tuple[str, int]) -> bytes:
        """Обрабатывает запрос клиента и возвращает ответ."""
        command, args = self._parse_message(data)
        
        if command == 'HELO':
            return self._handle_helo(addr, args)
        elif command == 'GUES':
            return self._handle_gues(addr, args)
        else:
            return b"FAIL Unknown command"
    
    def _handle_helo(self, addr: Tuple[str, int], args: list) -> bytes:
        """Обрабатывает HELO."""
        if addr in self.sessions:
            session = self.sessions[addr]
            session.last_activity = time.time()
            return f"WLCM {session.lower_bound} {session.upper_bound}".encode()
        
        seed = self._compute_crc32_seed(addr)
        lower_bound, upper_bound, secret = self._generate_secret(seed)
        max_attempts = int((upper_bound - lower_bound + 1).bit_length())
        
        session = GameSession(
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
        
        return f"WLCM {lower_bound} {upper_bound}".encode()
    
    def _handle_gues(self, addr: Tuple[str, int], args: list) -> bytes:
        """Обрабатывает GUES."""
        if addr not in self.sessions:
            return b"FAIL No active game"
        
        session = self.sessions[addr]
        session.last_activity = time.time()
        
        if not args or not args[0].isdigit():
            return b"FAIL Invalid number"
        
        guess = int(args[0])
        session.attempts_left -= 1
        
        if guess == session.secret_number:
            win_key = self._compute_win_key(addr, session.secret_number)
            print(f" Игрок {addr[0]}:{addr[1]} угадал!")
            del self.sessions[addr]
            return f"BING {win_key}".encode()
        elif session.attempts_left <= 0:
            print(f" Игрок {addr[0]}:{addr[1]} не угадал")
            del self.sessions[addr]
            return b"FAIL"
        elif guess < session.secret_number:
            return b"MORE"
        else:
            return b"LESS"
    
    def start(self):
        """Запускает сервер."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(1.0)  # Тайм-аут для возможности остановки
        
        print(f" GGTP сервер запущен на {self.host}:{self.port}")
        self.running = True
        
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                response = self.handle_client(data, addr)
                if response:
                    self.sock.sendto(response, addr)
                
                # Периодическая очистка
                self._cleanup_timeout_sessions()
                
            except socket.timeout:
                continue
            except Exception as e:
                print(f"️ Ошибка: {e}")
        
        self.sock.close()
    
    def stop(self):
        """Останавливает сервер."""
        self.running = False


if __name__ == "__main__":
    server = GGTPServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n Сервер остановлен")
        server.stop()
