Какие команды я использовала для того, чтобы сделать 2 домашнее задание:

wsl
cd /mnt/c/Users/klesh/try_smth_new/hw2$
nano wikipedia_articles.py
nano draw_wiki.py
nano README.md
sudo apt install python3-bs4
sudo apt install python3-networkx
sudo apt install python3-matplotlib
sudo apt install python3-requests
sudo apt install screen
pip3 list | grep -E "bs4|networkx|matplotlib|requests|screen"
screen -S dorogomilovo # cоздала новую screen-сессию
python3 wikipedia_articles.py --url "https://ru.wikipedia.org/wiki/Дорогомилово" --depth 5 # написала это в новом окне, тем самым запустив краулер
Ctrl+A, затем D # нажала, чтобы выйти из сессии
screen -r dorogomilovo # вернулась к сессии

python draw_wiki.py --json Программирование.json --output graph.png # визуализация графа

# Домашнее задание 2: Веб-кроулер Wikipedia

## Начальная статья

**Название статьи:** Парк Победы (станция метро,Москва)

**Ссылка:** https://ru.wikipedia.org/wiki/Парк_Победы_(станция_метро,_Москва)

## Результаты краулинга

Глубина обхода: 5

### Граф связей

![Граф связей Wikipedia](graph.png)

## Описание работы

### wikipedia_articles.py

Веб-кроулер, который:
- Принимает URL стартовой статьи и глубину обхода
- Рекурсивно собирает все внутренние ссылки на другие статьи Wikipedia
- Избегает повторного посещения страниц
- Сохраняет граф связей в JSON файл (название_статьи.json)

### draw_wiki.py

Скрипт для визуализации графа:
- Загружает JSON с графом
- Создает визуализацию с помощью NetworkX и Matplotlib
- Выделяет красным цветом стартовую статью
- Сохраняет изображение в формате PNG

## Установка зависимостей

```bash
pip install requests beautifulsoup4 networkx matplotlib
