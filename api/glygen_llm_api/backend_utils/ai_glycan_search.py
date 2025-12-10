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
            llm_client = OpenAILLM(type="glycan")
        else:
            llm_client = OpenAILLM(type="glycan")

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
                    error_log=f"User made non-glycan query:\n{query}",
                    error_msg="non-glycan-related-query",
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


def _map_search_params_ai(query : dict) -> Tuple[Optional[Dict], int]:
    """Parse a natural language query into structured search parameters using OpenAI."""
    try:

        if query.get("error") is not None:
            return {}, 400

        search_params = query
        mass_type = None
        mapped_parameters = {
            "operation": "AND",
            "query_type": "search_glycan",
        }

        min_mass = search_params.get('mass_minimum')
        max_mass = search_params.get('mass_maximum')
        if  min_mass is not None or max_mass is not None:
            mass_type = search_params.get('mass_type', "Native")
            if mass_type == "Native":
                min = int(search_params.get('mass_minimum', 150))
                max = int(search_params.get('mass_maximum', 6751))
                if min > max:
                    temp = max
                    max = min
                    min = temp
                elif min == max:
                    if min >= (150 + 10):
                        min -= 10
                    if max <= (6751 - 10):
                        max += 10

                mapped_parameters["mass"] = {
                    "min": min,
                    "max": max
                }
                mapped_parameters["mass_type"] = "Native"
            else: 
                min = int(search_params.get('mass_minimum', 206))
                max = int(search_params.get('mass_maximum', 8307))
                if min > max:
                    temp = max
                    max = min
                    min = temp
                elif min == max:
                    if min >= (206 + 10):
                        min -= 10
                    if max <= (8307 - 10):
                        max += 10

                mapped_parameters["mass"] = {
                    "min": min,
                    "max": max
                }
                mapped_parameters["mass_type"] = "Permethylated"

        mon_min = search_params.get('monosaccharides_minimum')
        mon_max = search_params.get('monosaccharides_maximum')
        if  mon_min is not None or mon_max is not None:
            min = int(search_params.get('monosaccharides_minimum', 1))
            max = int(search_params.get('monosaccharides_maximum', 37))
            if min > max:
                temp = max
                max = min
                min = temp

            mapped_parameters["number_monosaccharides"] = {
                "min": min,
                "max": max
            }

        subsumption = "none"
        if  search_params.get('glycan_related') == "Subsumption":
            subsumption = "any"

        organism = search_params.get('organism_name')
        organism_condition = search_params.get('organism_condition', 'or')
        if organism is not None:
            organism_list = list(map(lambda org: {"glygen_name": org}, list(organism)))
            mapped_parameters["organism"] = {"organism_list":organism_list, "annotation_category":"", "operation": organism_condition}

        glycan_identifier = search_params.get('glycan_id')
        if  glycan_identifier is not None:
            mapped_parameters["glycan_identifier"] = {"glycan_id":glycan_identifier, "subsumption":subsumption}

        enzyme = search_params.get('biosynthetic_enzyme')
        if  enzyme is not None:
            mapped_parameters["enzyme"] = {"id":enzyme, "type":"gene"}

        id_namespace = search_params.get('glycan_id_namespace')
        if  id_namespace is not None:
            mapped_parameters["id_namespace"] = id_namespace

        glycan_type = search_params.get('glycan_type')
        if  glycan_type is not None:
            mapped_parameters["glycan_type"] = glycan_type

        glycan_subtype = search_params.get('glycan_subtype')
        if  glycan_subtype is not None:
            mapped_parameters["glycan_subtype"] = glycan_subtype

        glycan_name = search_params.get('glycan_name')
        if  glycan_name is not None:
            mapped_parameters["glycan_name"] = glycan_name

        protein_identifier = search_params.get('glycosylated_protein')
        if  protein_identifier is not None:
            mapped_parameters["protein_identifier"] = protein_identifier

        glycan_motif = search_params.get('glycan_motif')
        if  glycan_motif is not None:
            mapped_parameters["glycan_motif"] = glycan_motif

        pmid = search_params.get('publication_id')
        if  pmid is not None:
            mapped_parameters["pmid"] = pmid

        binding_protein_id = search_params.get('binding_protein')
        if  binding_protein_id is not None:
            mapped_parameters["binding_protein_id"] = binding_protein_id

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