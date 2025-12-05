"""
Defines Marshmallow schemas for validating API request and response data structures.
"""

from marshmallow import Schema, fields, EXCLUDE, validate

# --- Base Schemas ---

class GlycanSearchFullSchema(Schema):

    class Meta(Schema.Meta):
        unknown = EXCLUDE

    glycan_id = fields.Str(required=False)
    glycan_related = fields.Str(
        required=False,
        validate=validate.OneOf(
            {
                "Exact", "Subsumption"
            }
        ),
    )
    glycan_id_namespace = fields.Str(
        required=False,
        validate=validate.OneOf(
            {
                "PubChem Substance", "GlyTouCan", "GlyCosmos", "PubChem Compound", "KEGG Glycan", "CFG", "ChEBI", "GlyConnect", "SandBox", "Glycan Array Data Repository", "Glycosciences.de", "UniCarbDB", "CarbBank", "BCSDB", "UniCarbKB", "GlycoEpitope", "Glycan Structure Dictionary", "BiomarkerKB", "PDB", "GPTwiki", "Reactome", "Rhea", "MatrixDB", "Metabolomics Workbench"
            }
        ),
    )
    mass_minimum = fields.Number(required=False)
    mass_maximum = fields.Number(required=False)
    monosaccharides_minimum = fields.Number(required=False)
    monosaccharides_maximum = fields.Number(required=False)
    mass_type = fields.Str(
        required=False,
        validate=validate.OneOf(
            {
                "Native", "Permethylated"
            }
        ),
    )
    organism_name = fields.List(
        fields.Str(
            required=False,
            validate=validate.OneOf(
                {
                    "Pig", "Rattus", "Bovine", "Human", "Mouse", "Rat", "Zebrafish", "Chicken", "Hamster", "SARS-CoV-2", "Yeast", "Fruit fly", "Arabidopsis", "Cellular slime mold", "HCV", "HCoV-SARS", "HCV-H77"
                }
            ),
        )
    )
    organism_condition = fields.Str(
        required=False,
        validate=validate.OneOf(["and", "AND", "or", "OR"]),
    )
    glycan_type = fields.Str(
        required=False,
        validate=validate.OneOf(
            {
                "N-linked", "Other", "O-linked", "Glycosphingolipid", "GAG", "Human Milk Oligosaccharide", "GPI anchor"
            }
        ),
    )
    glycan_subtype = fields.Str(
        required=False,
        validate=validate.OneOf(
            {
                "Alditol-reduced", "Complex", "Core-fucosylated", "Triantennary", "Biantennary", "Bisected", "Arm-fucosylated", "Monoantennary", "Truncated", 
                "Tetraantennary", "other", "Hybrid", "High mannose", "Paucimannose", "Core 2", "Core 3", "Core 5", "Core 6", "Core 7", "O-mannose", "Core 1", "Core 8", "Core 4", "O-mannose core", "O-fucose core", "Core 9", "O-GlcNAc",
                "Ganglio series", "Isoglobo series", "Lacto series", "Neo-lacto series", "Globo series", "Gala series", "Muco series", "Mollu series", "Arthro series", "Keratan sulfate"
            }
        ),
    )
    glycan_name = fields.Str(required=False)
    glycosylated_protein = fields.Str(required=False)
    binding_protein = fields.Str(required=False)
    glycan_motif = fields.Str(required=False)
    biosynthetic_enzyme = fields.Str(required=False)
    publication_id = fields.Str(required=False)
    biomarker_disease = fields.Str(required=False)
    biomarker_type = fields.Str(
        required=False,
        validate=validate.OneOf(
            {
                "diagnostic", "prognostic", "monitoring", "predictive"
            }
        ),
    )
    operation = fields.Str(
        required=False,
        missing="AND",
        validate=validate.OneOf(["and", "AND", "or", "OR"]),
    )


class ProteinSearchFullSchema(Schema):

    class Meta(Schema.Meta):
        unknown = EXCLUDE

    uniprot_canonical_ac = fields.Str(required=False)
    refseq_ac = fields.Str(required=False)
    mass_minimum = fields.Number(required=False)
    mass_maximum = fields.Number(required=False)
    organism_name = fields.Str(
        required=False,
        validate=validate.OneOf(
            {
                "Pig", "Bovine", "Human", "Mouse", "Rat", "Zebrafish", "Chicken", "Hamster", "SARS-CoV-2", "Yeast", "Fruit fly", "Arabidopsis", "Cellular slime mold", "HCV-Japanese", "HCoV-SARS", "HCV-H77"
            }
        ),
    )
    protein_name = fields.Str(required=False)
    gene_name = fields.Str(required=False)
    go_term = fields.Str(required=False)
    go_id = fields.Str(required=False)
    binding_glycan_id = fields.Str(required=False)
    attached_glycan_id = fields.Str(required=False)
    glycosylation_type = fields.Str(
        required=False,
        validate=validate.OneOf(
            {
                "C-linked", "N-linked", "O-linked", "S-linked"
            }
        ),
    )
    glycosylation_subtype = fields.Str(
        required=False,
        validate=validate.OneOf(
            {
                "Complex", "High mannose", "Hybrid", "C-Mannosylation", "O-Fucosylation", "O-GalNAcylation", "O-Galactosylation", "O-GlcNAcylation", "O-Glucosylation", "O-Mannosylation", "other"
            }
        ),
    )
    glycosylated_aa = fields.List(
        fields.Str(
            required=False,
            validate=validate.OneOf(
                {
                    "Serine", "Ser", "Threonine", "Thr", "Asparagine", "Asn", "Tyrosine", "Tyr", "Lysine", "Lys", "Tryptophan", "Trp", "Aspartic acid", "Asp", "Cysteine", "Cys", "Glutamic acid", "Glu", "Arginine", "Arg"
                }
            ),
        )
    )
    glycosylated_aa_condition = fields.Str(
        required=False,
        validate=validate.OneOf(["and", "AND", "or", "OR"]),
    )
    glycosylation_evidence_type = fields.Str(
        required=False,
        validate=validate.OneOf(
            {
                "All sites", "All reported sites", "All reported sites with or without Glycans", "All reported sites (with or without Glycans)", "Sites reported with Glycans", "Sites reported without Glycans", "Predicted sites", "Sites detected by literature mining"
            }
        )
    )
    pathway_id = fields.Str(required=False)
    disease_name = fields.Str(required=False)
    disease_id = fields.Str(required=False)
    publication_id = fields.Str(required=False)
    biomarker_disease = fields.Str(required=False)
    biomarker_type = fields.Str(
        required=False,
        validate=validate.OneOf(
            {
                "diagnostic", "prognostic", "monitoring", "predictive", "response", "risk"
            }
        ),
    )
    operation = fields.Str(
        required=False,
        missing="AND",
        validate=validate.OneOf(["and", "AND", "or", "OR"]),
    )

class AISearchSchema(Schema):

    class Meta(Schema.Meta):
        unknown = EXCLUDE

    query = fields.Str(required=True)


# --- Logging Schemas ---


class FrontendLogger(Schema):

    class Meta(Schema.Meta):
        unknown = EXCLUDE

    type = fields.Str(required=True)
    page = fields.Str(required=True)
    user = fields.Str(required=True)
    id = fields.Str(required=True)
    message = fields.Str(required=True)


# --- Clear Cache Schema ---


class ClearCacheSchema(Schema):

    class Meta(Schema.Meta):
        unknown = EXCLUDE

    api_key = fields.Str(required=True)



# --- Schema Mapping ---

SCHEMA_MAP = {
    "glycan_search_full": GlycanSearchFullSchema,
    "protein_search_full": ProteinSearchFullSchema,
    "frontend_logging": FrontendLogger,
    "clear_cache": ClearCacheSchema,
    "ai_search": AISearchSchema,
}
