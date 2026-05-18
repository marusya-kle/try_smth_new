import requests
import time
import json
import re
from typing import List, Dict, Optional
import pandas as pd

def map_proteins_to_interpro_symbols(
        protein_names: List[str],
        organism_id: str = "9606",  # NCBI taxonomy ID for Homo sapiens
        delay_between_requests: float = 0.2
) -> pd.DataFrame:
    mapping_results = []
    total = len(protein_names)

    print(f"Маппинг:")

    for i, protein_name in enumerate(protein_names, 1):
        print(f"\n[{i}/{total}] Обработка: {protein_name}")

        result = {
            "input_name": protein_name,
            "mapped_gene_symbol": None,
            "uniprot_accession": None,
            "protein_name": None,
            "status": "Not found"
        }

        # Стратегия 1: Прямой поиск в UniProt
        result = try_uniprot_search(protein_name, organism_id, result)

        if result["mapped_gene_symbol"]:
            print(f"  Успешно: {protein_name} -> {result['mapped_gene_symbol']} ({result['uniprot_accession']})")
        else:
            print(f"  Не найден: {protein_name}")

        mapping_results.append(result)
        time.sleep(delay_between_requests)

    return pd.DataFrame(mapping_results)


def try_uniprot_search(query: str, organism_id: str, result: Dict) -> Dict:

    clean_query = query.strip()

    result = search_uniprot_by_field(clean_query, "gene_exact", organism_id, result)
    if result["mapped_gene_symbol"]:
        result["status"] = "Mapped (exact gene name)"
        return result

    result = search_uniprot_by_field(clean_query, "protein_name", organism_id, result)
    if result["mapped_gene_symbol"]:
        result["status"] = "Mapped (protein name)"
        return result

    result = search_uniprot_free_text(clean_query, organism_id, result)
    if result["mapped_gene_symbol"]:
        result["status"] = "Mapped (free text)"
        return result

    simplified_query = re.sub(r'[\d\s\-_]', '', clean_query)
    if simplified_query != clean_query:
        result = search_uniprot_by_field(simplified_query, "gene_exact", organism_id, result)
        if result["mapped_gene_symbol"]:
            result["status"] = "Mapped (simplified name)"
            return result

    return result


def search_uniprot_by_field(query: str, field: str, organism_id: str, result: Dict) -> Dict:

    if field == "gene_exact":
        query_param = f'gene:{query}'
    elif field == "protein_name":
        query_param = f'protein_name:{query}'
    else:
        query_param = query

    full_query = f'{query_param} AND organism_id:{organism_id}'

    url = "https://rest.uniprot.org/uniprotkb/search"
    params = {
        "query": full_query,
        "format": "json",
        "fields": "accession, gene_names, protein_name, organism_id",
        "size": 5
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("results"):
            first_result = data["results"][0]
            gene_names = first_result.get("genes", [])
            if gene_names:
                primary_gene = None
                for gene in gene_names:
                    if gene.get("geneName", {}).get("value"):
                        gene_value = gene["geneName"]["value"]
                        if gene.get("geneName", {}).get("type") == "primary":
                            primary_gene = gene_value
                            break
                        elif not primary_gene:
                            primary_gene = gene_value

                if primary_gene:
                    result["mapped_gene_symbol"] = primary_gene
                    result["uniprot_accession"] = first_result.get("primaryAccession")

                    protein_desc = first_result.get("proteinDescription", {})
                    if protein_desc.get("recommendedName", {}).get("fullName", {}).get("value"):
                        result["protein_name"] = protein_desc["recommendedName"]["fullName"]["value"]

                    return result

    except Exception as e:
        print(f"    Ошибка при поиске по полю {field}: {e}")

    return result


def search_uniprot_free_text(query: str, organism_id: str, result: Dict) -> Dict:
    url = "https://rest.uniprot.org/uniprotkb/search"
    params = {
        "query": f'({query}) AND organism_id:{organism_id}',
        "format": "json",
        "fields": "accession, gene_names, protein_name",
        "size": 5
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("results"):
            for uniprot_result in data["results"]:
                protein_desc = uniprot_result.get("proteinDescription", {})
                rec_name = protein_desc.get("recommendedName", {}).get("fullName", {}).get("value", "")
                gene_names = uniprot_result.get("genes", [])
                found = False
                for gene in gene_names:
                    gene_value = gene.get("geneName", {}).get("value", "")
                    if query.lower() in gene_value.lower() or gene_value.lower() in query.lower():
                        found = True
                        break
                if not found and query.lower() in rec_name.lower():
                    found = True

                if found:
                    if gene_names:
                        primary_gene = None
                        for gene in gene_names:
                            if gene.get("geneName", {}).get("value"):
                                gene_value = gene["geneName"]["value"]
                                if gene.get("geneName", {}).get("type") == "primary":
                                    primary_gene = gene_value
                                    break
                                elif not primary_gene:
                                    primary_gene = gene_value

                        if primary_gene:
                            result["mapped_gene_symbol"] = primary_gene
                            result["uniprot_accession"] = uniprot_result.get("primaryAccession")
                            result["protein_name"] = rec_name
                            return result

    except Exception as e:
        print(f"    Ошибка при свободном поиске: {e}")

    return result

class ProteinDomainAnalyzer:
    def __init__(self, delay_between_requests: float = 0.3):
        self.uniprot_url = "https://rest.uniprot.org/uniprotkb/search"
        self.uniprot_entry_url = "https://www.uniprot.org/uniprotkb"
        self.delay = delay_between_requests
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Python-Protein-Domain-Analyzer/1.0",
            "Accept": "application/json"
        })
        self.uniprot_cache = {}
        self.domains_cache = {}

    def get_uniprot_accession(self, gene_name: str) -> Optional[str]:
        if gene_name in self.uniprot_cache:
            return self.uniprot_cache[gene_name]

        params = {
            "query": f"gene:{gene_name} AND organism_id:9606",
            "format": "json",
            "fields": "accession",
            "size": 1
        }

        try:
            response = self.session.get(self.uniprot_url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("results"):
                accession = data["results"][0].get("primaryAccession")
                if accession:
                    print(f"    UniProt ID: {accession}")
                    self.uniprot_cache[gene_name] = accession
                    return accession

            self.uniprot_cache[gene_name] = None
            return None

        except Exception as e:
            print(f"    Ошибка поиска UniProt: {e}")
            self.uniprot_cache[gene_name] = None
            return None

    def get_protein_domains(self, protein_id: str) -> Dict:
        result = {
            "protein_id": protein_id,
            "interpro_domain_names": [],
            "status": "Not found"
        }
        uniprot_id = self.get_uniprot_accession(protein_id)
        if not uniprot_id:
            result["status"] = "Cannot find UniProt accession"
            return result
        if uniprot_id in self.domains_cache:
            result["interpro_domain_names"] = self.domains_cache[uniprot_id]
            result["status"] = "Success (from cache)"
            return result

        url = f"{self.uniprot_entry_url}/{uniprot_id}/entry"

        try:
            print(f"    Запрос к UniProt: {url}")
            response = self.session.get(url)

            if response.status_code == 200:
                domains = self._parse_uniprot_entry(response.text, uniprot_id)
                result["interpro_domain_names"] = domains
                result["status"] = "Success" if domains else "No domains"
                self.domains_cache[uniprot_id] = domains

            elif response.status_code == 404:
                result["status"] = "Protein not found"
            else:
                result["status"] = f"HTTP {response.status_code}"

        except Exception as e:
            result["status"] = f"Error: {e}"

        return result

    def _parse_uniprot_entry(self, html_content: str, uniprot_id: str) -> List[str]:

        json_url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}"

        try:
            response = self.session.get(json_url, params={"format": "json"})
            response.raise_for_status()
            data = response.json()

            domains = set()
            if "features" in data:
                for feature in data["features"]:
                    feature_type = feature.get("type", "")

                    if feature_type in ["Domain", "Region", "Repeat", "Zinc finger", "DNA binding"]:
                        description = feature.get("description", "")
                        if description:
                            domains.add(description)

                    if "interpro" in feature:
                        interpro_data = feature.get("interpro", {})
                        interpro_name = interpro_data.get("name")
                        if interpro_name:
                            domains.add(interpro_name)

                    interpro_id = feature.get("interpro_id")
                    if interpro_id and not description:
                        domains.add(interpro_id)

            if "comments" in data:
                for comment in data["comments"]:
                    comment_type = comment.get("type", "")
                    if comment_type == "DOMAIN":
                        text = comment.get("text", "")
                        if text:
                            domains.add(text)

            if not domains:
                domains = self._get_domains_via_interpro_api(uniprot_id)

            return sorted(list(domains))

        except Exception as e:
            print(f"    Ошибка парсинга JSON: {e}")
            return []

    def _get_domains_via_interpro_api(self, uniprot_id: str) -> List[str]:

        interpro_url = f"https://www.ebi.ac.uk/interpro/api/protein/UniProt/{uniprot_id}"

        try:
            response = self.session.get(interpro_url)

            if response.status_code == 200:
                data = response.json()
                domains = set()

                if "proteins" in data:
                    for protein in data["proteins"]:
                        if "entries" in protein:
                            for entry in protein["entries"]:
                                name = entry.get("name")
                                if name:
                                    domains.add(name)
                                elif entry.get("accession"):
                                    domains.add(entry["accession"])

                return sorted(list(domains))

        except Exception as e:
            print(f"    InterPro API также не работает: {e}")

        return []

    def analyze_multiple_proteins(self, protein_list: List[str]) -> Dict:
        results = {}
        total = len(protein_list)

        for i, protein in enumerate(protein_list, 1):
            print(f"\n[{i}/{total}] {protein}")

            domain_data = self.get_protein_domains(protein)
            results[protein] = domain_data["interpro_domain_names"]

            if domain_data["status"].startswith("Success"):
                if domain_data["interpro_domain_names"]:
                    print(f"  Найдено {len(domain_data['interpro_domain_names'])} доменов")
                    # Показываем первые 3 домена
                    for j, domain in enumerate(domain_data["interpro_domain_names"][:3], 1):
                        print(f"    {j}. {domain}")
                    if len(domain_data["interpro_domain_names"]) > 3:
                        print(f"    ... и {len(domain_data['interpro_domain_names']) - 3} других")
                else:
                    print(f"  Белок найден, но домены не обнаружены")
            else:
                print(f"  {domain_data['status']}")

            time.sleep(self.delay)

        return results


def get_encode_proteins() -> List[str]:

    url = "https://www.encodeproject.org/search/"
    params = {
        "type": "Experiment",
        "assay_title": "TF ChIP-seq",
        "biosample_ontology.term_name": "MCF-7",
        "status": "released",
        "field": "target.label",
        "format": "json",
        "limit": "all"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        proteins = []
        for exp in data.get("@graph", []):
            target = exp.get("target")
            if target and target.get("label"):
                proteins.append(target["label"])

        unique_proteins = sorted(list(set(proteins)))
        print(f"\nНайдено уникальных белков: {len(unique_proteins)}")
        return unique_proteins

    except Exception as e:
        print(f"Ошибка получения данных из ENCODE: {e}")
        return []


def main():

    tf_proteins = get_encode_proteins()
    mapping_df = map_proteins_to_interpro_symbols(tf_proteins)
    interpro_ready = mapping_df[mapping_df['mapped_gene_symbol'].notna()]['mapped_gene_symbol'].tolist()
    analyzer = ProteinDomainAnalyzer(delay_between_requests=0.3)
    domains_data = analyzer.analyze_multiple_proteins(interpro_ready)

    output_file = "domains.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(domains_data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
