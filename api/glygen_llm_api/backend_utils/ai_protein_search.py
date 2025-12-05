from flask import Request, current_app
from typing import Tuple, Dict, Optional
from pprint import pformat
import json
import math
from . import LLM_PROVIDER
from . import db as db_utils
from . import utils as utils
from .search_utils import _search_query_builder
from .llm import LLM
from .llm.openai_api import OpenAILLM
from .llm.rate_limiter import ai_search_rate_limiter


def ai_full_search(api_request: Request) -> Tuple[Dict, int]:
    """Entry point for the AI-assisted search endpoint."""

    is_bot = utils.get_is_bot(api_request)
    if is_bot == True:
        error_obj = db_utils.log_error(
            error_log="No bots allowed",
            error_msg="no-bots-allowed",
            origin="ai_full_search"
        )
        return error_obj, 401

    request_arguments, request_http_code = utils.get_request_object(
        api_request, "ai_search"
    )
    
    if request_http_code != 200:
        return request_arguments, request_http_code

    user_query = request_arguments["query"]

    # Check rate limit before proceeding
    if not ai_search_rate_limiter.can_make_request():
        rate_status = ai_search_rate_limiter.get_status()
        error_obj = db_utils.log_error(
            error_log="Rate limit exceeded for AI search",
            error_msg="rate-limit-exceeded",
            origin="ai_full_search",
            rate_limit_status=rate_status,
        )
        return error_obj, 429

    # Generate structured search parameters using OpenAI
    search_params, search_params_http_code = _parse_full_search_query_ai(user_query)
    if search_params_http_code != 200:
        return search_params, search_params_http_code
    
    mapped_parameters, error_code = _map_search_params_ai(search_params)
    if error_code != 200:
        return mapped_parameters, search_params_http_code

    ai_search_metadata = {
        "original_query": user_query,
        "parsed_parameters": search_params,
        "mapped_parameters": mapped_parameters
    }

    return ai_search_metadata, search_params_http_code


def _parse_full_search_query_ai(query: str) -> Tuple[Dict, int]:
    """Parse a natural language query into structured search parameters using OpenAI."""

    try:
        llm_client: LLM
        if LLM_PROVIDER == "openai":
            llm_client = OpenAILLM(type="protein")
        else:
            llm_client = OpenAILLM(type="protein")

        search_params = llm_client.advanced_search(query)

        if search_params is None:
            error_obj = db_utils.log_error(
                error_log=f"Unable to parse query using LLM provider: `{LLM_PROVIDER}`\nquery: {query}",
                error_msg="unable-to-parse-query-using-llm",
                origin="_parse_full_search_query_ai",
            )
            return error_obj, 400

        if "error" in search_params:
            if search_params["error"] == llm_client.key_error_str:
                error_obj = db_utils.log_error(
                    error_log="Unable to find LLM API key",
                    error_msg="llm-key-error",
                    origin="_parse_full_search_query_ai",
                )
                return error_obj, 401
            elif search_params["error"] == llm_client.relevancy_error_str:
                error_obj = db_utils.log_error(
                    error_log=f"User made non-protein query:\n{query}",
                    error_msg="non-protein-related-query",
                    origin="_parse_full_search_query_ai",
                )
                return error_obj, 400

        return search_params, 200

    except Exception as e:
        error_obj = db_utils.log_error(
            error_log=f"Unable to parse query using LLM provider: `{LLM_PROVIDER}`\nquery: {query}\nerror: {e}",
            error_msg="unable-to-parse-query-using-llm",
            origin="_parse_full_search_query_ai",
        )
        return error_obj, 400

def _map_amino_acids(aa_list_input : tuple) -> str:
    aa_list_dict = { 
                        "serine": "S", "ser": "S", "threonine": "T", "thr": "T", "asparagine": "N", "asn": "N",
                        "tyrosine": "Y", "tyr": "Y", "lysine": "K", "lys": "K", "tryptophan": "W", "trp": "W",
                        "aspartic acid": "D", "aspartic": "D", "asp": "D", "cysteine": "C", "cys": "C", 
                        "glutamic acid": "E",  "glutamic": "E", "glu": "E", "arginine": "R", "arg": "R"
                    }
    
    aa_list= list(set(map(lambda aa: aa_list_dict.get(aa.lower()), list(aa_list_input))))
    return aa_list

def _map_glycosylation_evidence_type(glyco_evidence_input : str) -> str:
    glyco_evidence_dict = { 
                        "all sites": "all_sites", "all reported sites": "all_reported_sites_with_without_glycans", 
                        "all reported sites with or without glycans": "all_reported_sites_with_without_glycans", 
                        "all reported sites (with or without glycans)": "all_reported_sites_with_without_glycans", 
                        "sites reported with glycans": "sites_reported_with_glycans", "sites reported without glycans": "sites_reported_without_glycans",
                        "predicted sites": "predicted_sites", "sites detected by literature mining": "sites_detected_by_literature_mining"
                    }
        
    glyco_evidence_type= glyco_evidence_dict.get(glyco_evidence_input.lower())
    return glyco_evidence_type

def _map_search_params_ai(query : dict) -> Tuple[Optional[Dict], int]:
    """Parse a natural language query into structured search parameters using OpenAI."""
    try:

        if query.get("error") is not None:
            return {}, 400

        search_params = query
        mapped_parameters = {
            "operation": "AND",
            "query_type": "search_protein",
        }

        min_mass = search_params.get('mass_minimum')
        max_mass = search_params.get('mass_maximum')
        if  min_mass is not None or max_mass is not None:
            min = int(search_params.get('mass_minimum', 260))
            max = int(search_params.get('mass_maximum', 4007076))
            if min > max:
                temp = max
                max = min
                min = temp 
            mapped_parameters["mass"] = {
                "min": min,
                "max": max
            }

        organism = search_params.get('organism_name')
        if organism is not None:
            mapped_parameters["organism"] = {"name":organism}

        uniprot_canonical_ac = search_params.get('uniprot_canonical_ac')
        if  uniprot_canonical_ac is not None:
            mapped_parameters["uniprot_canonical_ac"] = uniprot_canonical_ac

        refseq_ac = search_params.get('refseq_ac')
        if  refseq_ac is not None:
            mapped_parameters["refseq_ac"] = refseq_ac

        protein_name = search_params.get('protein_name')
        if  protein_name is not None:
            mapped_parameters["protein_name"] = protein_name

        gene_name = search_params.get('gene_name')
        if  gene_name is not None:
            mapped_parameters["gene_name"] = gene_name

        go_term = search_params.get('go_term')
        if  go_term is not None:
            mapped_parameters["go_term"] = go_term

        go_id = search_params.get('go_id')
        if  go_id is not None:
            mapped_parameters["go_id"] = go_id

        pathway_id = search_params.get('pathway_id')
        if  pathway_id is not None:
            mapped_parameters["pathway_id"] = pathway_id

        glycosylation_type = search_params.get('glycosylation_type')
        if  glycosylation_type is not None:
            mapped_parameters["glycosylation_type"] = glycosylation_type

        glycosylation_subtype = search_params.get('glycosylation_subtype')
        if  glycosylation_subtype is not None:
            mapped_parameters["glycosylation_subtype"] = glycosylation_subtype

        glycosylated_aa = search_params.get('glycosylated_aa')
        glycosylated_aa_condition = search_params.get('glycosylated_aa_condition', 'or')
        if glycosylated_aa is not None:
            aa_list = _map_amino_acids(glycosylated_aa)
            mapped_parameters["glycosylated_aa"] = {"aa_list":aa_list, "operation": glycosylated_aa_condition}

        glycosylation_evidence_type = search_params.get('glycosylation_evidence_type')
        if glycosylation_evidence_type is not None:
            glycosylation_evidence = _map_glycosylation_evidence_type(glycosylation_evidence_type)
            mapped_parameters["glycosylation_evidence"] = glycosylation_evidence

        disease_name = search_params.get('disease_name')
        if  disease_name is not None:
            mapped_parameters["disease_name"] = disease_name

        disease_id = search_params.get('disease_id')
        if  disease_id is not None:
            mapped_parameters["disease_id"] = disease_id

        binding_glycan_id = search_params.get('binding_glycan_id')
        if  binding_glycan_id is not None:
            mapped_parameters["binding_glycan_id"] = binding_glycan_id

        attached_glycan_id = search_params.get('attached_glycan_id')
        if  attached_glycan_id is not None:
            mapped_parameters["attached_glycan_id"] = attached_glycan_id

        pmid = search_params.get('publication_id')
        if  pmid is not None:
            mapped_parameters["pmid"] = pmid

        biomarker_disease = search_params.get('biomarker_disease')
        biomarker_type = search_params.get('biomarker_type')

        if  biomarker_disease is not None or biomarker_type is not None:
           mapped_parameters["biomarker"] = {}

        if  biomarker_disease is not None:
           mapped_parameters["biomarker"]["disease_name"] = biomarker_disease

        if  biomarker_type is not None:
            mapped_parameters["biomarker"]["type"] = biomarker_type

        return mapped_parameters, 200

    except Exception as e:
        error_obj = db_utils.log_error(
            error_log=f"Unable to parse query using LLM provider: `{LLM_PROVIDER}`\nquery: {query}\nerror: {e}",
            error_msg="unable-to-map-query-using-llm",
            origin="_map_search_params_ai",
        )
        return error_obj, 400
    

if __name__ == "__main__":
    _map_search_params_ai()