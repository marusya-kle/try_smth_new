Команды для выполнения hw1:
wsl
ssh -T git@github.com
git status
cd try_smth_new/hw1
nano README.md
nano complement.py
git add
git commit -m "Мои изменения"
git push

Задание 2. 
Файл complement.py является исполняемым, так как в начале стоит #!/usr/bin/env python3. Также потому что chmod +x complement.py. После этого запускаем  ./complement.py --seq ATGCCGATGG 
И получаем:
CCATCGGCAT
0.6

Задание 3. 
