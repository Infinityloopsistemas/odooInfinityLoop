# -*- coding: utf-8 -*-
{
    'name': "LINK SIVA",

    'summary': """
       Enlace de SIVA para partners """,

    'description': """
      Se correlacionan los partners de GIVA con la urls de los SIVA , se trata de tener los partners correlacionados con las companys de SIVA
    """,

    'author': "Infinityloop Sistemas",
    'website': "http://www.infinityloop.es",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Utilities',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','project'],

    # always loaded
    'data': [
         'security/ir.model.access.csv',
         'views/project_view.xml',
         'views/partner_view.xml',
    ],
    # only loaded in demonstration mode

    'installable': True,
    'auto_install': False,
}