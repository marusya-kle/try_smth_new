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


**Результаты краулинга**

Глубина обхода: 5

Увы, графа связей не будет, так как перестало все работать при глубине 3. 

wikipedia_articles.py - это и есть веб-кроулер

draw_wiki.py - это скрипт для визуализации графа

**Задание 3: REST API в ENCODE**

```bash
nano get_domains.py
python3 hw2/get_domains.py
```
В задании было необходимо найти все DNase-seq и TF ChIP-seq эксперименты, поэтому мы их искали так: 
```bash
GET /search/?type=Experiment&assay_title=DNase-seq&status=released&limit=all&frame=object
GET /search/?type=Experiment&assay_title=TF+ChIP-seq&status=released&biosample_ontology.term_name=
{cell_line}&limit=all&frame=object
```
Использовали поля: @graph[].biosample_ontology.classification = "cell line", @graph[].biosample_ontology.term_name, @graph[].target.label.



Далее проходил маппинг, то есть сопоставление названий генов и UniProt ID. 

Создание задания на маппинг: ```bash POST /idmapping/run```

Проверка статуса: ```bash GET /idmapping/status/{jobId}```

Получение результатов: ```bash GET /idmapping/results/{jobId}```



После этого для списка UniProt ID получали все связанные с ними домены InterPro: 

```bash GET /protein/UniProt/{accession_ids}/entry/interpro/```

Данные брали из поля: results[].entry_interpro[].metadata.name.


Результат работы:
   - Лучшая клеточная линия: K562
   - Найдено TF белков: 23
   - Сопоставлено с UniProt: 23
   - Белков с доменами: 19
   - Всего найдено доменов Pfam: 31
