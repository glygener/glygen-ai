from abc import ABC, abstractmethod
import os
from dotenv import load_dotenv
import json
from typing import Dict, Optional, Tuple
from marshmallow import EXCLUDE
from marshmallow.exceptions import ValidationError

from .search_system_glycan_prompt import SEARCH_SYSTEM_PROMPT_GLYCAN
from .search_system_protein_prompt import SEARCH_SYSTEM_PROMPT_PROTEIN
from ..data_models import ProteinSearchFullSchema
from ..data_models import GlycanSearchFullSchema


class LLM(ABC):

    def __init__(self, api_key_name: str = "LLM_API_KEY", type: str = "glycan", max_tokens: int = 1_000, max_retries: int = 2):
        load_dotenv()
        self.api_key_name = api_key_name
        self.key_error_str = "key-error"
        self.relevancy_error_str = "relevancy-error"
        self._api_key = os.getenv(self.api_key_name)
        self._max_tokens = max_tokens
        self._max_retries = max_retries
        self._type = type
        if type == "protein":
            self._full_search_system_prompt = SEARCH_SYSTEM_PROMPT_PROTEIN
        else:
            self._full_search_system_prompt = SEARCH_SYSTEM_PROMPT_GLYCAN


    def _validate_api_key(self) -> bool:
        if self._api_key is None:
            return False
        return True

    @abstractmethod
    def advanced_search(self, query: str) -> Optional[Dict]:
        pass

    def handle_protein_data_special_cases(self, response):
        try:
            # special case to handle multiple uniprot_canonical_ac
            uniprot_canonical_ac = response.get("uniprot_canonical_ac")
            if uniprot_canonical_ac is not None and isinstance(uniprot_canonical_ac, list):
                response["uniprot_canonical_ac"] = ",".join(uniprot_canonical_ac)
            
            # special case to handle single amino acid before validating response
            glycosylated_aa = response.get("glycosylated_aa")
            if glycosylated_aa is not None and isinstance(glycosylated_aa, str):
                if "," in glycosylated_aa:
                    response["glycosylated_aa"] = [item.strip() for item in glycosylated_aa.split(',')]
                else:
                    my_list = []
                    my_list.append(glycosylated_aa)
                    response["glycosylated_aa"] = my_list

            # special case to handle organism name before validating response
            organism_name = response.get("organism_name")
            if organism_name is not None and isinstance(organism_name, str):
                if "," in organism_name:
                    my_list = [item.strip() for item in organism_name.split(',')]
                    if len(my_list) > 0:
                        response["organism_name"] = my_list[0]
            elif organism_name is not None and isinstance(organism_name, list):
                if len(my_list) > 0:
                    response["organism_name"] = organism_name[0]

        except Exception as e:
            pass

        return response
    
    def handle_glycan_data_special_cases(self, response):
        try:
            # special case to handle multiple glycan_id
            glycan_id = response.get("glycan_id")
            if glycan_id is not None and isinstance(glycan_id, list):
                response["glycan_id"] = ",".join(glycan_id)
            
            # special case to handle single organism name before validating response
            organism_name = response.get("organism_name")
            if organism_name is not None and isinstance(organism_name, str):
                if "," in organism_name:
                    response["organism_name"] = [item.strip() for item in organism_name.split(',')]
                else:
                    my_list = []
                    my_list.append(organism_name)
                    response["organism_name"] = my_list
        except Exception as e:
            pass

        return response

    def validate_advanced_search_response(
        self, llm_response: str
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        try:
            response = json.loads(llm_response)
            if self._type == "protein":
                response = self.handle_protein_data_special_cases(response)
                validated_response = ProteinSearchFullSchema().load(response, unknown=EXCLUDE)
            else:
                response = self.handle_glycan_data_special_cases(response)
                validated_response = GlycanSearchFullSchema().load(response, unknown=EXCLUDE)

            if not isinstance(validated_response, dict):
                return False, None, "Response is not valid Python dictionary"
            return True, validated_response, None
        except ValidationError as e:
            marshmallow_error = e.messages_dict
            return False, None, str(marshmallow_error)
        except Exception as e:
            return False, None, str(e)