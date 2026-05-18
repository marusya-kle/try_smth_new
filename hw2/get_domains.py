#!/usr/bin/env python3

import requests
import json
from collections import Counter
import time
import sys

def fetch_encode_data(url):
    try:
        headers = {'accept': 'application/json'}  # Добавляем заголовок, чтобы API вернул нам JSON
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Вызовет исключение для плохих статус-кодов (4xx, 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к ENCODE: {e}", file=sys.stderr)
        return None

def find_best_cell_line_for_dnase():
    print("1. Поиск клеточной линии с максимальным числом DNase-seq...")
    # limit=all - получить все результаты, frame=object - получить полные объекты
    url = "https://www.encodeproject.org/search/?type=Experiment&assay_title=DNase-seq&status=released&limit=all&frame=object"
    
    data = fetch_encode_data(url)
    if not data:
        print("Не удалось получить данные о DNase-seq экспериментах.", file=sys.stderr)
        return None

    # Считаем, сколько экспериментов приходится на каждую клеточную линию
    cell_line_counter = Counter()
    for experiment in data.get('@graph', []):
        biosample = experiment.get('biosample_ontology', {})
        if biosample.get('classification') == 'cell line':
            term_name = biosample.get('term_name')
            if term_name:
                cell_line_counter[term_name] += 1

    if not cell_line_counter:
        print("Не найдено подходящих клеточных линий с DNase-seq.", file=sys.stderr)
        return None

    best_cell_line = cell_line_counter.most_common(1)[0][0]
    print(f"   Найдена лучшая линия: '{best_cell_line}' ({cell_line_counter[best_cell_line]} экспериментов DNase-seq)")
    return best_cell_line

def get_tf_proteins_for_cell_line(cell_line):
    print(f"\n2. Поиск белков (TF ChIP-seq) для линии '{cell_line}'...")
    # Формируем запрос для TF ChIP-seq экспериментов по нашей клеточной линии
    # Используем biosample_ontology.term_name для фильтрации
    url = f"https://www.encodeproject.org/search/?type=Experiment&assay_title=TF+ChIP-seq&status=released&biosample_ontology.term_name={cell_line}&limit=all&frame=object"
    
    data = fetch_encode_data(url)
    if not data:
        print(f"Не удалось получить данные о TF ChIP-seq для {cell_line}.", file=sys.stderr)
        return []

    protein_genes = set()
    for experiment in data.get('@graph', []):
        target = experiment.get('target', {})
        gene_name = target.get('label')
        if gene_name:
            protein_genes.add(gene_name)

    print(f"   Найдено уникальных белков: {len(protein_genes)}")
    return list(protein_genes)

def get_uniprot_ids_from_genes(gene_symbols):
    print("\n3. Маппинг Gene Symbols на UniProt ID...")
    uniprot_ids = []
    url = "https://rest.uniprot.org/idmapping/run"  
    params = {
        'from': 'Gene_Name',
        'to': 'UniProtKB',
        'ids': ' '.join(gene_symbols)
    }
    
    try:
        print("   Отправка запроса на маппинг...")
        response = requests.post(url, data=params)
        response.raise_for_status()
        # Получаем ID нашего задания (jobId)
        job_id = response.json().get('jobId')
        if not job_id:
            print("   Ошибка: Не удалось получить jobId от UniProt.", file=sys.stderr)
            return []

        print(f"   Job ID: {job_id}. Ожидание результатов...")

        status_url = f"https://rest.uniprot.org/idmapping/status/{job_id}"
        while True:
            status_response = requests.get(status_url)
            status_response.raise_for_status()
            status_data = status_response.json()
            if status_data.get('results') is not None:

                break
            
            time.sleep(1)
        

        results_url = f"https://rest.uniprot.org/idmapping/results/{job_id}"
        results_response = requests.get(results_url)
        results_response.raise_for_status()
        results_data = results_response.json()

        for result in results_data.get('results', []):
            # to это и есть UniProtKB ID
            uniprot_id = result.get('to', {}).get('primaryAccession')
            if uniprot_id:
                uniprot_ids.append(uniprot_id)
                
        uniprot_ids = list(set(uniprot_ids))
        print(f"   Успешно сопоставлено: {len(uniprot_ids)} белков.")
        return uniprot_ids
        
    except requests.exceptions.RequestException as e:
        print(f"   Ошибка при маппинге через UniProt: {e}", file=sys.stderr)
        return []

def get_interpro_domains_for_proteins(uniprot_ids):

    print(f"\n4. Получение доменов InterPro для {len(uniprot_ids)} белков...")
    all_domains = set()
    batch_size = 100
    for i in range(0, len(uniprot_ids), batch_size):
        batch = uniprot_ids[i:i+batch_size]
        ids_param = ','.join(batch)
        url = f"https://www.ebi.ac.uk/interpro/api/protein/UniProt/{ids_param}/entry/interpro"
        
        try:
            print(f"   Обработка пакета {i//batch_size + 1}...")
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            for protein_results in data.get('results', []):
                for interpro_entry in protein_results.get('entry_interpro', []):
                    # Информация о самом домене InterPro
                    entry_metadata = interpro_entry.get('metadata', {})
                    domain_name = entry_metadata.get('name')
                    if domain_name:
                        all_domains.add(domain_name)
            # Небольшая пауза, чтобы не перегружать сервер
            time.sleep(0.5)
        except requests.exceptions.RequestException as e:
            print(f"   Ошибка при запросе к InterPro API: {e}", file=sys.stderr)
            # Продолжаем со следующим пакетом, даже если этот упал
    
    print(f"   Найдено уникальных доменов: {len(all_domains)}")
    return sorted(list(all_domains)) # Возвращаем отсортированный список

def main():    
    best_line = find_best_cell_line_for_dnase()
    if not best_line:
        sys.exit(1)
  
    protein_genes = get_tf_proteins_for_cell_line(best_line)
    if not protein_genes:
        print("Не удалось найти белки для TF ChIP-seq. Завершение.", file=sys.stderr)
        sys.exit(1)
    
    uniprot_ids = get_uniprot_ids_from_genes(protein_genes)
    if not uniprot_ids:
        print("Не удалось сопоставить белки с UniProt ID. Завершение.", file=sys.stderr)
        sys.exit(1)
        
    final_domains = get_interpro_domains_for_proteins(uniprot_ids)
    if not final_domains:
        print("Не удалось получить домены InterPro. Завершение.", file=sys.stderr)
        sys.exit(1)

    output_data = {
        "best_cell_line": best_line,
        "domains": final_domains
    }
    
    with open('domains.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*50)
    print(f"Файл 'domains.json' создан.")
    print(f"Лучшая клеточная линия: {best_line}")
    print(f"Найдено доменов: {len(final_domains)}")
    print("Примеры доменов:", final_domains[:5])

if __name__ == "__main__":
    main()

