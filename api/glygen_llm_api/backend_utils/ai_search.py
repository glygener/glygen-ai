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

    is_bot = api_request.headers.get('User-Agent')
    if is_bot:
        error_obj = db_utils.log_error(
            error_log="No bots allowed",
            error_msg="no-bots-allowed",
            origin="ai_full_search",
            rate_limit_status=rate_status,
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
    mapped_parameters, error_code = _map_search_params_ai(search_params)


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
            llm_client = OpenAILLM()
        else:
            llm_client = OpenAILLM()

        search_params = llm_client.advanced_search(query)

        if search_params is None:
            error_obj = db_utils.log_error(
                error_log=f"Unable to parse query using LLM provider: `{LLM_PROVIDER}`\nquery: {query}",
                error_msg="internal-server-error",
                origin="_parse_full_search_query_ai",
            )
            return error_obj, 500

        if "error" in search_params:
            if search_params["error"] == llm_client.key_error_str:
                error_obj = db_utils.log_error(
                    error_log="Unable to find LLM API key",
                    error_msg="internal-server-error",
                    origin="_parse_full_search_query_ai",
                )
                return error_obj, 500
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
            error_msg="internal-server-error",
            origin="_parse_full_search_query_ai",
        )
        return error_obj, 500


def _map_search_params_ai(query : dict) -> Tuple[Optional[Dict], int]:
    """Parse a natural language query into structured search parameters using OpenAI."""
    try:
        search_params = query
        input_mass = None
        mass_type = None
        mapped_parameters = {
            "operation": "AND",
            "query_type": "search_glycan",
        }

        print(json.dumps(query))

        if  search_params.get('mass_minimum') or search_params.get('mass_maximum'):
            mapped_parameters["mass"] = {
                min: int(search_params.get('mass_minimum', 0)),
                max: int(search_params.get('mass_maximum')),
            }
            mapped_parameters["mass_type"] = search_params['mass_type']

        input_monosaccharides = None
        if  search_params.get('monosaccharides_minimum') or search_params.get('monosaccharides_minimum'):
            mapped_parameters["number_monosaccharides"] = {
                min: int(search_params.get('monosaccharides_minimum', 0)),
                max: int(search_params.get('monosaccharides_maximum')),
            }

        subsumption = "none"
        if  search_params.get('glycan_related') == "Subsumption":
            subsumption = "any"

        organism = search_params.get('organism_name')
        if organism is not None:
            mapped_parameters["organism"] = {"organism_list":[{"glygen_name":organism}],"annotation_category":"","operation":"or"}

        glycan_identifier = search_params.get('glycan_id')
        if  glycan_identifier is not None:
            mapped_parameters["glycan_identifier"] = {"glycan_id":glycan_identifier, "subsumption":subsumption}

        enzyme = search_params.get('biosynthetic_enzyme')
        if  enzyme is not None:
            mapped_parameters["enzyme"] = {"id":enzyme,"type":"gene"}

        glycan_type = search_params.get('glycan_type'),
        if  glycan_type is not None:
            mapped_parameters["glycan_type"] = glycan_type[0]

        glycan_subtype = search_params.get('glycan_subtype')
        if  glycan_subtype is not None:
            mapped_parameters["glycan_subtype"] = glycan_subtype[0]

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
        if  biomarker_disease is not None:
           mapped_parameters["biomarker"] = {}
           mapped_parameters.biomarker["disease_name"] = biomarker_disease

        biomarker_type = search_params.get('biomarker_type')
        if  biomarker_type is not None:
            mapped_parameters["biomarker"] = {}
            mapped_parameters.biomarker["type"] = biomarker_type

        return mapped_parameters, 200

    except Exception as e:
        error_obj = db_utils.log_error(
            error_log=f"Unable to parse query using LLM provider: `{LLM_PROVIDER}`\nquery: {query}\nerror: {e}",
            error_msg="internal-server-error",
            origin="_map_search_params_ai",
        )
        return error_obj, 500