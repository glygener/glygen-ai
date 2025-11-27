"""
Defines the main API endpoints for accessing and searching glygen_llm_api data.
"""

from flask import request
from flask_restx import Resource, Namespace, fields
import user_agents

# from .backend_utils import list_utils as list_utils
# from .backend_utils import search_utils as search_utils
from .backend_utils import ai_search
from .backend_utils import ai_glycan_search
from .backend_utils import ai_protein_search
from .token_validation import token_required


api = Namespace("search", description="GlyGen Search AI API namespace.")


# class FullSearch(Resource):

#     @api.doc("search")
#     @api.expect(full_search_model, validate=False)
#     def post(self):
#         return search_utils.full_search(request)

#     @api.doc(False)
#     def get(self):
#         return self.post()


# list_model = api.model(
#     "List Query",
#     {"id": fields.String(required=True, default="3def43533cf6434b633cd18d1a7da5b2")},
# )


# class List(Resource):

#     @api.doc("list")
#     @api.expect(list_model, validate=False)
#     def post(self):
#         return list_utils.list(request)

#     @api.doc(False)
#     def get(self):
#         return self.post()



ai_full_search_model = api.model(
    "AI Full Search Query",
    {
        "query": fields.String(
            required=True,
            default="Can you show me some n-linked glycans",
        )
    },
)

class AIFullSearch(Resource):

    @api.doc("ai_full_search")
    @api.expect(ai_full_search_model, validate=False)
    def post(self):
        return ai_search.ai_full_search(request)

ai_full_glycan_search_model = api.model(
    "AI Full Glycan Search Query",
    {
        "query": fields.String(
            required=True,
            default="Can you show me some n-linked glycans",
        )
    },
)

class AIFullGlycanSearch(Resource):

    @token_required
    @api.doc("ai_full_glycan_search")
    @api.expect(ai_full_glycan_search_model, validate=True)
    @api.response(200, 'Success')
    @api.response(400, 'Bad Request or Parsing Error')
    @api.response(401, 'Not Authorized')
    @api.response(429, 'Rate Limit Exceeded')
    @api.response(500, 'Internal Server Error') 
    def post(self):
        return ai_glycan_search.ai_full_search(request)

ai_full_protein_search_model = api.model(
    "AI Full Protein Search Query",
    {
        "query": fields.String(
            required=True,
            default="Can you show me some human proteins",
        )
    },
)

class AIFullProteinSearch(Resource):

    @token_required
    @api.doc("ai_full_protein_search")
    @api.response(200, 'Success')
    @api.response(400, 'Bad Request or Parsing Error')
    @api.response(401, 'Not Authorized')
    @api.response(429, 'Rate Limit Exceeded')
    @api.response(500, 'Internal Server Error') 
    @api.expect(ai_full_protein_search_model, validate=True)
    def post(self):
        return ai_protein_search.ai_full_search(request)


# api.add_resource(FullSearch, "/search")
# api.add_resource(List, "/list")
api.add_resource(AIFullGlycanSearch, "/glycan")
api.add_resource(AIFullProteinSearch, "/protein")
