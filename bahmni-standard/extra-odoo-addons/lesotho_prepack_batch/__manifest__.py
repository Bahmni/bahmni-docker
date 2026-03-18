{
    "name": "Lesotho Prepack Batch",
    "summary": "Batch-oriented prepacking workflow for Bahmni dispensing.",
    "version": "16.0.1.0.0",
    "category": "Manufacturing",
    "author": "MOH Lesotho",
    "license": "LGPL-3",
    "depends": [
        "mrp",
        "stock",
        "lesotho_manufacturing",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "views/prepack_batch_views.xml",
        "views/mrp_production_views.xml",
    ],
    "installable": True,
    "application": False,
}
