#!/usr/bin/env python3

import json
import networkx as nx
import matplotlib.pyplot as plt
import argparse
import sys
from urllib.parse import unquote

def load_graph(json_file):
    """
    Загружает граф из JSON файла
    """
    with open(json_file, 'r', encoding='utf-8') as f:
        graph = json.load(f)
    return graph

def create_networkx_graph(graph):
    """
    Создает граф NetworkX из словаря ссылок
    """
    G = nx.DiGraph()
    
    for source, targets in graph.items():
        for target in targets:
            G.add_edge(source, target)
    
    return G

def get_short_name(url):
    """
    Извлекает короткое название статьи из URL
    """
    # Декодируем URL для читаемости
    name = url.split('/wiki/')[-1] if '/wiki/' in url else url
    name = unquote(name)
    
    # Ограничиваем длину
    if len(name) > 30:
        name = name[:27] + "..."
    
    return name

def draw_graph(G, start_article, output_image='graph.png'):
    """
    Рисует граф связей
    """
    plt.figure(figsize=(16, 12))
    
    # Используем spring layout для красивого расположения
    pos = nx.spring_layout(G, k=2, iterations=50)
    
    # Рисуем узлы
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                          node_size=2000, alpha=0.7)
    
    # Рисуем ребра
    nx.draw_networkx_edges(G, pos, edge_color='gray', 
                          arrows=True, arrowsize=20, alpha=0.5)
    
    # Рисуем метки (короткие имена)
    labels = {node: get_short_name(node) for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold')
    
    # Выделяем стартовую статью
    if start_article in G:
        nx.draw_networkx_nodes(G, pos, nodelist=[start_article], 
                              node_color='red', node_size=2500)
    
    plt.title(f"Граф связей Wikipedia\nНачальная статья: {get_short_name(start_article)}", 
              fontsize=14, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    
    # Сохраняем изображение
    plt.savefig(output_image, dpi=150, bbox_inches='tight')
    print(f"Граф сохранен в файл: {output_image}")
    
    # Показываем граф
    plt.show()

def main():
    parser = argparse.ArgumentParser(description='Draw Wikipedia graph from JSON')
    parser.add_argument('--json', required=True, help='JSON file with graph')
    parser.add_argument('--output', default='graph.png', help='Output image file')
    
    args = parser.parse_args()
    
    # Загружаем граф
    graph = load_graph(args.json)
    
    # Создаем NetworkX граф
    G = create_networkx_graph(graph)
    
    print(f"Загружен граф с {G.number_of_nodes()} узлами и {G.number_of_edges()} ребрами")
    
    # Получаем стартовую статью (первый ключ в JSON)
    start_article = list(graph.keys())[0] if graph else None
    
    # Рисуем граф
    draw_graph(G, start_article, args.output)
    
    # Выводим статистику
    print(f"\nСтатистика графа:")
    print(f"  Узлов: {G.number_of_nodes()}")
    print(f"  Ребер: {G.number_of_edges()}")
    print(f"  Средняя степень: {G.number_of_edges() / G.number_of_nodes():.2f}")

if __name__ == "__main__":
    main()
