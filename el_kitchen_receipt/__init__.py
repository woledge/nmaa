# -*- coding: utf-8 -*-
from . import models


def _pre_init_hook(env):
    """
    يحفظ البيانات القديمة من حقل x_driver_name (Char) قبل ما الموديل يترقى
    ويتحول الحقل لـ Many2one. بيتخزن في جدول مؤقت.
    """
    cr = env.cr
    cr.execute("""
        CREATE TABLE IF NOT EXISTS _pilot_migration_tmp (
            model TEXT NOT NULL,
            record_id INTEGER NOT NULL,
            driver_name TEXT
        );
    """)

    tables = [
        ('sale_order', 'sale_order'),
        ('res_partner', 'res_partner'),
        ('stock_picking', 'stock_picking'),
        ('account_move', 'account_move'),
    ]
    for model, table in tables:
        # نتأكد إن العمود موجود (ممكن يكون الترقية الأولى ومفيش بيانات قديمة)
        cr.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = %s AND column_name = 'x_driver_name'
        """, (table,))
        if cr.fetchone():
            cr.execute("""
                INSERT INTO _pilot_migration_tmp (model, record_id, driver_name)
                SELECT %s, id, x_driver_name FROM """ + table + """
                WHERE x_driver_name IS NOT NULL AND x_driver_name != ''
            """, (model,))
            # نفضي العمود عشان تحويل النوع varchar -> integer ميكسرش
            cr.execute(
                'UPDATE "' + table + '" SET x_driver_name = NULL '
                'WHERE x_driver_name IS NOT NULL'
            )


def _post_init_hook(env):
    """
    بعد الترقية: الحقل بقي Many2one (x_driver_name_id).
    نقرأ البيانات المحفوظة، ننشئ سجلات x.pilot، ونحدث الإيدجاز.
    """
    cr = env.cr

    # نجمع كل الأسماء الفريدة
    cr.execute("SELECT DISTINCT driver_name FROM _pilot_migration_tmp WHERE driver_name IS NOT NULL")
    all_names = [row[0] for row in cr.fetchall()]

    # ننشئ سجل x.pilot لكل اسم فريد
    name_to_id = {}
    for name in all_names:
        pilot = env['x.pilot'].create({'name': name})
        name_to_id[name] = pilot.id

    # نحدث كل الجداول بالـ ID الجديد
    table_map = {
        'sale_order': 'sale_order',
        'res_partner': 'res_partner',
        'stock_picking': 'stock_picking',
        'account_move': 'account_move',
    }
    cr.execute("SELECT model, record_id, driver_name FROM _pilot_migration_tmp")
    for model, record_id, driver_name in cr.fetchall():
        pilot_id = name_to_id.get(driver_name)
        if pilot_id:
            table = table_map.get(model)
            if table:
                cr.execute(
                    'UPDATE "' + table + '" SET x_driver_name = %s WHERE id = %s',
                    (pilot_id, record_id)
                )

    # نمسح الجدول المؤقت
    cr.execute('DROP TABLE IF EXISTS _pilot_migration_tmp')
    env['ir.model.data'].clear_caches()
