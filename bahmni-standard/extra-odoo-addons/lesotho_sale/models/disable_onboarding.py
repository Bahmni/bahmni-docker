# from odoo import SUPERUSER_ID, api


# def pre_init_hook(cr):
#     """Pre-init: Set states to closed before module installs"""
#     cr.execute("""
#         UPDATE res_company
#         SET sale_onboarding_order_confirmation_state = 'closed',
#             sale_onboarding_sample_quotation_state = 'closed'
#     """)


# def post_init_hook(cr, registry):
#     """Post-init: Disable all onboarding actions"""
#     env = api.Environment(cr, SUPERUSER_ID, {})

#     # Find and disable all onboarding-related client actions
#     client_actions = env["ir.actions.client"].search([("name", "ilike", "onboarding")])
#     client_actions.write({"active": False})

#     # Disable window actions too
#     window_actions = env["ir.actions.act_window"].search(
#         [("name", "ilike", "onboarding")]
#     )
#     window_actions.write({"active": False})

#     print("✓ Disabled all onboarding actions")
from odoo import SUPERUSER_ID, api


def pre_init_hook(cr):
    """Set all onboarding states to closed BEFORE module installation"""
    cr.execute("""
        UPDATE res_company
        SET sale_onboarding_order_confirmation_state = 'closed',
            sale_onboarding_sample_quotation_state = 'closed',
            account_onboarding_invoice_layout_state = 'closed'
        WHERE id IN (SELECT id FROM res_company)
    """)

    print("✓ Pre-hook: Set all onboarding states to 'closed'")


def post_init_hook(cr, registry):
    """Disable all onboarding actions AFTER module installation"""
    env = api.Environment(cr, SUPERUSER_ID, {})

    # DISABLE THE SPECIFIC ACTION YOU MENTIONED
    try:
        quotations_action = env.ref("sale.action_quotations_with_onboarding")
        if quotations_action:
            quotations_action.write({"active": False})
            print(f"✓ Disabled action: sale.action_quotations_with_onboarding")
    except:
        print("⚠ Could not find sale.action_quotations_with_onboarding")

    # DISABLE ALL OTHER ONBOARDING ACTIONS
    # Client actions (QWeb/JS actions)
    client_actions = env["ir.actions.client"].search(
        [
            "|",
            "|",
            ("name", "ilike", "onboarding"),
            ("name", "ilike", "Onboarding"),
            ("xml_id", "ilike", "onboarding"),
        ]
    )
    if client_actions:
        client_actions.write({"active": False})
        print(f"✓ Disabled {len(client_actions)} client actions")

    # Window actions (like the one you mentioned)
    window_actions = env["ir.actions.act_window"].search(
        [
            "|",
            "|",
            ("name", "ilike", "onboarding"),
            ("name", "ilike", "Onboarding"),
            ("xml_id", "ilike", "onboarding"),
        ]
    )
    if window_actions:
        window_actions.write({"active": False})
        print(f"✓ Disabled {len(window_actions)} window actions")

    # Also check for server actions
    server_actions = env["ir.actions.server"].search([("name", "ilike", "onboarding")])
    if server_actions:
        server_actions.write({"active": False})
        print(f"✓ Disabled {len(server_actions)} server actions")

    # Disable all onboarding panel views
    views = env["ir.ui.view"].search(
        [("name", "ilike", "onboarding"), ("type", "=", "qweb")]
    )
    if views:
        views.write({"active": False})
        print(f"✓ Disabled {len(views)} onboarding views")

    print("✓ Post-hook: All onboarding actions disabled")
