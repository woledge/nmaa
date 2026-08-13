# -*- coding: utf-8 -*-
{
    'name': 'CRM Salesperson Data Isolation',
    'version': '18.0.1.0.2',
    'category': 'Sales/CRM',
    'summary': 'Restrict salespersons to see only their own contacts and CRM leads',
    'description': """
        CRM Salesperson Data Isolation
        ==============================
        This module ensures that each CRM salesperson can ONLY see their own customers
        and leads — preventing unauthorized access to other salespersons' data.

        A salesperson can see a contact/lead ONLY if:
        - They are assigned as the Salesperson (user_id field) on the record, OR
        - They are the one who created the record (create_uid)

        This restriction applies to:
        - CRM Leads (crm.lead) — via Record Rules (ir.rule)
        - Contacts (res.partner) — via Search Override

        Sales Managers and Administrators retain full access to all records.

        Auto-Sync Feature:
        When a salesperson is assigned to a CRM lead, the linked contact's
        Salesperson field is automatically updated to maintain consistency.
        Also syncs when the lead's partner is changed.
    """,
    'author': 'Custom Development',
    'depends': ['crm', 'sales_team', 'contacts'],
    'data': [
        'security/security.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    'auto_install': False,
}
