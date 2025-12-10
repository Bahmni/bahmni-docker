"""
Database migration script to add the new fields
This runs automatically when module is installed
"""


def migrate(cr, installed_version):
    """
    Add new columns to existing tables
    This is safe - if columns already exist, they won't be re-added
    """

    # ============ SALE ORDER TABLE ADDITIONS ============
    sale_order_columns = [
        # Clinical encounter fields
        ("encounter_uuid", "VARCHAR"),
        ("visit_uuid", "VARCHAR"),
        ("location_name", "VARCHAR"),
        ("encounter_type", "VARCHAR"),
        # Provider fields
        ("provider_name", "VARCHAR"),
        ("provider_uuid", "VARCHAR"),
        # Clinical data fields
        ("diagnosis", "TEXT"),
        ("clinical_notes", "TEXT"),
        ("disposition", "VARCHAR"),
        # Timestamp fields
        ("encounter_datetime", "TIMESTAMP"),
        # Computed fields (will be stored)
        ("has_clinical_data", "BOOLEAN"),
        ("clinical_data_summary", "VARCHAR"),
    ]

    for column_name, column_type in sale_order_columns:
        try:
            cr.execute(f"""
                ALTER TABLE sale_order
                ADD COLUMN IF NOT EXISTS {column_name} {column_type}
            """)
            print(f"✓ Added column {column_name} to sale_order")
        except Exception as e:
            print(f"✗ Failed to add {column_name} to sale_order: {e}")

    # Add indexes for frequently searched fields
    indexes = [
        ("sale_order_encounter_uuid_idx", "sale_order", "encounter_uuid"),
        ("sale_order_visit_uuid_idx", "sale_order", "visit_uuid"),
        ("sale_order_location_name_idx", "sale_order", "location_name"),
        ("sale_order_provider_name_idx", "sale_order", "provider_name"),
        ("sale_order_has_clinical_data_idx", "sale_order", "has_clinical_data"),
    ]

    for index_name, table_name, column_name in indexes:
        try:
            cr.execute(f"""
                CREATE INDEX IF NOT EXISTS {index_name}
                ON {table_name} ({column_name})
                WHERE {column_name} IS NOT NULL
            """)
            print(f"✓ Created index {index_name}")
        except Exception as e:
            print(f"✗ Failed to create index {index_name}: {e}")

    # ============ SALE ORDER LINE TABLE ADDITIONS ============
    sale_order_line_columns = [
        # Prescription dosing fields
        ("frequency", "VARCHAR"),
        ("route", "VARCHAR"),
        ("dose", "DECIMAL(12,4)"),
        ("dose_units", "VARCHAR"),
        # Duration fields
        ("duration", "INTEGER"),
        ("duration_units", "VARCHAR"),
        # Special instructions
        ("as_needed", "BOOLEAN"),
        ("administration_instructions", "TEXT"),
        # Date fields
        ("start_date", "TIMESTAMP"),
        ("stop_date", "TIMESTAMP"),
        ("expire_date", "TIMESTAMP"),
        # Drug details
        ("drug_form", "VARCHAR"),
        ("drug_strength", "VARCHAR"),
        ("drug_uuid", "VARCHAR"),
        # Order references
        ("external_order_uuid", "VARCHAR"),
        ("order_number", "VARCHAR"),
        # Computed fields
        ("has_prescription_data", "BOOLEAN"),
        ("full_prescription_text", "VARCHAR"),
        ("prescription_summary", "VARCHAR"),
    ]

    for column_name, column_type in sale_order_line_columns:
        try:
            cr.execute(f"""
                ALTER TABLE sale_order_line
                ADD COLUMN IF NOT EXISTS {column_name} {column_type}
            """)
            print(f"✓ Added column {column_name} to sale_order_line")
        except Exception as e:
            print(f"✗ Failed to add {column_name} to sale_order_line: {e}")

    # Add indexes for order line fields
    line_indexes = [
        ("sale_order_line_frequency_idx", "sale_order_line", "frequency"),
        ("sale_order_line_route_idx", "sale_order_line", "route"),
        (
            "sale_order_line_external_order_uuid_idx",
            "sale_order_line",
            "external_order_uuid",
        ),
        ("sale_order_line_order_number_idx", "sale_order_line", "order_number"),
        ("sale_order_line_drug_uuid_idx", "sale_order_line", "drug_uuid"),
        (
            "sale_order_line_has_prescription_data_idx",
            "sale_order_line",
            "has_prescription_data",
        ),
    ]

    for index_name, table_name, column_name in line_indexes:
        try:
            cr.execute(f"""
                CREATE INDEX IF NOT EXISTS {index_name}
                ON {table_name} ({column_name})
                WHERE {column_name} IS NOT NULL
            """)
            print(f"✓ Created index {index_name}")
        except Exception as e:
            print(f"✗ Failed to create index {index_name}: {e}")

    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)
    print("\nNew fields have been added to:")
    print("1. sale_order table - for clinical encounter data")
    print("2. sale_order_line table - for prescription details")
    print("\nNext prescription sync will populate these fields automatically.")
