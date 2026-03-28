#!/usr/bin/env python3

import argparse
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urlparse, urljoin
from collections import deque
import sys

def extract_wikipedia_links(url):
    """
    Извлекает все внутренние ссылки на Wikipedia из HTML страницы
    """
    try:
        # Добавляем User-Agent чтобы не быть заблокированным
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем все ссылки в основном содержимом статьи
        content_div = soup.find('div', {'id': 'mw-content-text'})
        
        if not content_div:
            return set()
        
        links = set()
        base_url = 'https://ru.wikipedia.org'
        
        # Находим все ссылки в содержимом
        for a_tag in content_div.find_all('a', href=True):
            href = a_tag['href']
            
            # Проверяем, что ссылка ведет на другую статью Wikipedia
            if href.startswith('/wiki/') and ':' not in href and '#' not in href:
                full_url = urljoin(base_url, href)
                links.add(full_url)
        
        return links
    
    except Exception as e:
        print(f"Ошибка при загрузке {url}: {e}", file=sys.stderr)
        return set()

def get_article_title(url):
    """
    Извлекает название статьи из URL
    """
    # Из URL вида https://ru.wikipedia.org/wiki/Название
    match = re.search(r'/wiki/(.+)$', url)
    if match:
        return match.group(1)
    return "unknown"

def crawl_wikipedia(start_url, max_depth):
    """
    Выполняет краулинг Wikipedia до заданной глубины
    """
    visited = set()
    graph = {}
    
    # Очередь для BFS: (url, depth)
    queue = deque([(start_url, 0)])
    visited.add(start_url)
    
    while queue:
        current_url, depth = queue.popleft()
        
        print(f"Обработка: {current_url} (глубина {depth})", file=sys.stderr)
        
        # Получаем ссылки с текущей страницы
        links = extract_wikipedia_links(current_url)
        graph[current_url] = list(links)
        
        # Если достигли максимальной глубины, не добавляем новые ссылки
        if depth < max_depth:
            for link in links:
                if link not in visited:
                    visited.add(link)
                    queue.append((link, depth + 1))
    
    return graph, visited

def main():
    parser = argparse.ArgumentParser(description='Wikipedia crawler')
    parser.add_argument('--url', required=True, help='Start Wikipedia URL')
    parser.add_argument('--depth', type=int, required=True, help='Crawling depth')
    
    args = parser.parse_args()
    
    # Проверяем, что URL ведет на Wikipedia
    if 'wikipedia.org' not in args.url:
        print("Ошибка: URL должен вести на Wikipedia", file=sys.stderr)
        sys.exit(1)
    
    print(f"Начинаем краулинг с {args.url}, глубина {args.depth}", file=sys.stderr)
    
    # Выполняем краулинг
    graph, visited = crawl_wikipedia(args.url, args.depth)
    
    # Получаем название стартовой статьи для имени файла
    start_title = get_article_title(args.url)
    output_filename = f"{start_title}.json"
    
    # Сохраняем граф в JSON
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    
    print(f"Сохранен граф в файл: {output_filename}", file=sys.stderr)
    print(f"Всего страниц обработано: {len(graph)}", file=sys.stderr)
    print(f"Всего уникальных ссылок: {len(visited)}", file=sys.stderr)

if __name__ == "__main__":
    main()
