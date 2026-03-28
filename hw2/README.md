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
