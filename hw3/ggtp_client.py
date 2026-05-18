#!/usr/bin/env python3
"""
GGTP (Guessing Game Transfer Protocol) - Клиент
Реализация игры в угадывание числа поверх UDP.
"""

import socket
import sys
import time
import re


class GGTPClient:
    """UDP клиент для протокола GGTP."""
    
    def __init__(self, server_host='127.0.0.1', server_port=8888, timeout=5.0):
        self.server_addr = (server_host, server_port)
        self.timeout = timeout
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(timeout)
        self.lower_bound = 1
        self.upper_bound = 100
        self.attempts = 0
        self.max_attempts = 0
    
    def send_message(self, message: str) -> str:
        """Отправляет сообщение и возвращает ответ."""
        print(f"C: {message}")
        self.sock.sendto(message.encode(), self.server_addr)
        
        try:
            data, _ = self.sock.recvfrom(1024)
            response = data.decode().strip()
            print(f"S: {response}")
            return response
        except socket.timeout:
            print(f" Тайм-аут! Сервер не ответил на '{message}'")
            return "TIMEOUT"
        except Exception as e:
            print(f" Ошибка: {e}")
            return "ERROR"
    
    def play(self):
        """Запускает игру."""
        print(" GGTP Клиент запущен")
        print(f" Сервер: {self.server_addr[0]}:{self.server_addr[1]}")
        print("=" * 50)
        
        # HELO с тайм-аутом
        helo_msg = f"HELO {self.timeout}"
        response = self.send_message(helo_msg)
        
        if response.startswith("TIMEOUT") or response.startswith("ERROR"):
            print(" Не удалось подключиться к серверу")
            return
        
        # Парсим WLCM сообщение
        if not response.startswith("WLCM"):
            print(f" Неожиданный ответ: {response}")
            return
        
        parts = response.split()
        if len(parts) != 3:
            print(f" Неверный формат WLCM: {response}")
            return
        
        try:
            self.lower_bound = int(parts[1])
            self.upper_bound = int(parts[2])
            range_size = self.upper_bound - self.lower_bound + 1
            self.max_attempts = range_size.bit_length()
            print(f" Диапазон: {self.lower_bound}..{self.upper_bound}")
            print(f" Максимум попыток: {self.max_attempts}")
            print("=" * 50)
        except ValueError:
            print(f" Ошибка парсинга чисел: {response}")
            return
        
        # Основной игровой цикл
        while self.attempts < self.max_attempts:
            try:
                guess = input(f" Введите число ({self.lower_bound}-{self.upper_bound}): ")
                
                # Проверка ввода
                if not guess.isdigit():
                    print(" Введите число!")
                    continue
                
                guess_num = int(guess)
                if guess_num < self.lower_bound or guess_num > self.upper_bound:
                    print(f" Число вне диапазона! ({self.lower_bound}-{self.upper_bound})")
                    continue
                
                self.attempts += 1
                response = self.send_message(f"GUES {guess_num}")
                
                if response.startswith("BING"):
                    win_key = response.split()[1] if len(response.split()) > 1 else ""
                    print(f"\n ПОБЕДА! Вы угадали число за {self.attempts} попыток!")
                    print(f" Победный ключ: {win_key}")
                    return
                
                elif response == "MORE":
                    self.lower_bound = guess_num + 1
                    print(f"️ Больше! Диапазон: {self.lower_bound}..{self.upper_bound}")
                
                elif response == "LESS":
                    self.upper_bound = guess_num - 1
                    print(f" Меньше! Диапазон: {self.lower_bound}..{self.upper_bound}")
                
                elif response == "FAIL":
                    print(f"\n Игра проиграна! Закончились попытки ({self.max_attempts})")
                    return
                
                elif response == "TIMEOUT":
                    print(" Тайм-аут сервера!")
                    return
                
                else:
                    print(f"️ Неизвестный ответ: {response}")
                    
            except KeyboardInterrupt:
                print("\n Игра прервана пользователем")
                return
            except Exception as e:
                print(f" Ошибка: {e}")
                return
        
        print(f"\n Игра проиграна! Закончились попытки ({self.max_attempts})")


def main():
    """Основная функция клиента."""
    import argparse
    
    parser = argparse.ArgumentParser(description='GGTP Клиент')
    parser.add_argument('--host', default='127.0.0.1', help='Хост сервера')
    parser.add_argument('--port', type=int, default=8888, help='Порт сервера')
    parser.add_argument('--timeout', type=float, default=5.0, help='Тайм-аут (секунды)')
    
    args = parser.parse_args()
    
    client = GGTPClient(server_host=args.host, server_port=args.port, timeout=args.timeout)
    client.play()


if __name__ == "__main__":
    main()
