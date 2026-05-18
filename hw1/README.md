Команды для выполнения hw1:
wsl
ssh -T git@github.com
git status
cd try_smth_new/hw1
nano README.md
git add
git commit -m "Мои изменения"
git push

Задание 2. 
nano complement.py
Файл complement.py является исполняемым, так как в начале стоит #!/usr/bin/env python3. Также потому что chmod +x complement.py. После этого запускаем  ./complement.py --seq ATGCCGATGG 
И получаем:
CCATCGGCAT
0.6

Задание 3. 
nano count_kmers.py
nano test.fna
chmod +x count_kmers.py
./count_kmers.py --fa test.fna
cat cnts.json

Вывод таков: {
  "seq1": {
    "ATGC": 1,
    "TGCG": 1,
    "GCGT": 1,
    "CGTA": 2,
    "GTAC": 1,
    "TACG": 1,
    "ACGT": 1,
    "GTAG": 1,
    "TAGC": 2,
    "AGCT": 2,
    "GCTA": 2,
    "CTAG": 2
  },
  "seq2": {
    "GCTA": 3,
    "CTAG": 3,
    "TAGC": 3,
    "AGCT": 2,
    "AGCU": 1,
    "GCUU": 1,
    "CUUA": 1,
    "UUAG": 1,
    "UAGC": 1
}
Получилась некая проблема: я сразу сделала правильно и ввела git pull, чего делать не следовало. Поэтому пришлось еще раз заменить k=3 (в гитхабе) и добавить print в конце (с ПК). В итоге git push выдал ошибку как и должен был. Я сделала git pull, затем в репозитории я сделала (соединение) git pull --no-rebase, и прошел он так "Merge made by the 'ort' strategy.". После чего git status сообщил, что есть два коммита, которые после git push соединились в один файл, где и k=3, и print в конце. 

Ура!

