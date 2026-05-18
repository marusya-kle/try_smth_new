**Задание 2: Веб-кроулер Wikipedia**

**Название статьи:** Дорогомилово

**Ссылка:** https://ru.wikipedia.org/wiki/Дорогомилово

**Команды для выполнения**

```bash
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
screen -S dorogomilovo  # cоздала новую screen-сессию
python3 wikipedia_articles.py --url "https://ru.wikipedia.org/wiki/Дорогомилово" --depth 5 # написала это в новом окне, тем самым запустив краулер
# Ctrl+A, затем D # нажала, чтобы выйти из сессии
screen -r dorogomilovo # вернулась к сессии
python draw_wiki.py --json Дорогомилово.json --output graph.png # визуализация графа
```


## Результаты краулинга

Глубина обхода: 5

Увы, графа связей не будет, так как перестало все работать при глубине 3. 

### wikipedia_articles.py
- это и есть веб-кроулер

### draw_wiki.py
- это скрипт для визуализации графа

## Установка зависимостей

```bash
pip install requests beautifulsoup4 networkx matplotlib
