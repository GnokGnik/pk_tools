'''
This python file generates an excel file that shows comparison based on 2 versions.

------
For improve: Use configparse and/or argparse instead of hard-coding credentials
'''

import erppeek
import xlsxwriter
ODOOV9_URL = 'http://spg9.cier.tech'
ODOOV9_DB = 's-pg'
ODOOV9_USR = 'paolo'
ODOOV9_PWD = 'paolo321!'

ODOOV13_URL = 'http://52.56.174.80/'
ODOOV13_DB = 'spg13'
ODOOV13_USR = 'paolo'
ODOOV13_PWD = 'SPOdoo20Pg!'


class Reports(object):

    def compare_fields(self, amodels, bmodels):
        # Requires return of extract_model_fields from Helpers
        '''
        Sample Structure = {'res.users': 'id': {'type': int, 'relation': None}}
        '''
        reports = {}
        for model in amodels:
            if not bmodels.get(model):
                # Hardcoded Odoo 13, assumption is always Odoo 9 vs Odoo 13
                reports.update({model: 'This model doesn\'t exist in Odoo 13'})
            else:
                afields = amodels.get(model)
                bfields = bmodels.get(model)
                reports.update({model: {}})
                for field in afields:
                    # check if field exist in a and b
                    if field in bfields.get(field):
                        if afields.get(field).get('type') == bfields.get(field).get('type'):
                            type_compare = True
                        else:
                            type_compare = False

                        field_type = (afields.get(field).get('type'), bfields.get(field).get('type'))
                        reports[model].update({field: {'status': 'Exist',
                                                       'type_compare': type_compare,
                                                       'type': field_type}})
                    else:
                        reports[model].update({field: {'status': 'Doesn\'t Exist',
                                                       'type_compare': False,
                                                       'type': ()}})
        return reports


class Helpers(object):
    def extract_installed_modules(self, client):
        module_ids = client.model('ir.module.module').search([('state', '=', 'installed')])
        module_rec = client.model('ir.module.module').read(module_ids, ['name', 'state'])
        return [{'module_name': module['name'], 'state': module['state']} for module in module_rec]

    def extract_model_with_data(self, client):
        ignore_models = ['wizard.ir.model.menu.create', 'ir.model.fields', 'ir.model.access', 'ir.model.constraint',
                         'ir.model.data', 'ir.model', 'ir.model.relation']
        model_ids = client.model('ir.model').search([('model', 'not in', ignore_models)])
        model_rec = client.model('ir.model').read(model_ids, ['model'])
        model_details = []

        counter = 1
        for model in model_rec:
            print(counter,'/',len(model_rec))
            model_name = model['model']
            model_detail = {'model_name': model_name, 'total_records': 0}
            try:
                model_data = client.model(model_name).search_count([])
            except:
                model_data = 'No Access'
            model_detail.update({'total_records': model_data})

            model_details.append(model_detail)
            counter += 1
            if counter == 5:
                break

        return model_details

    def extract_model_fields(self, client, model_details, use_all_model=False):
        # Expecting the return of extract_model_with_data as parameter
        if not use_all_model:
            models = [rec.get('model_name') for rec in model_details]
        else:
            ignore_models = ['wizard.ir.model.menu.create', 'ir.model.fields', 'ir.model.access', 'ir.model.constraint',
                             'ir.model.data', 'ir.model', 'ir.model.relation']
            model_ids = client.model('ir.model').search([('model', 'not in', ignore_models)])
            model_rec = client.model('ir.model').read(model_ids, ['model'])
            models = [rec['model'] for rec in model_rec]
        model_details = {}
        counter = 1
        for model in models:
            print(counter, '/', len(models))
            fields = client.model(model).fields_get()
            model_details.update({model: {}})
            for field in fields:
                model_details[model].update({field: {'type': fields.get(field).get('type'),
                                                     'relation': fields.get(field).get('relation')}})
            counter += 1

            if counter == 5:
                break
        return model_details


class Server(object):
    def __init__(self, odoo, options):
        self.helpers = Helpers()

        self.extract_model_with_data = {}
        if options.get('extract_installed'):
            self.installed_modules = self.helpers.extract_installed_modules(odoo)

        if options.get('extract_model_with_data'):
            self.extract_model_with_data = self.helpers.extract_model_with_data(odoo)

        if options.get('extract_model_fields'):
            self.extract_model_fields = self.helpers.extract_model_fields(odoo,
                                                                          self.extract_model_with_data,
                                                                          use_all_model=options.get('use_all_model'))


if __name__ == "__main__":
    odoo9 = erppeek.Client('http://spg9.cier.tech', 's-pg', 'paolo', 'paolo321!')
    odoo9 = Server(odoo9, options={'extract_installed': True, 'extract_model_with_data': True,
                                   'extract_model_fields': True, 'use_all_model': False})

    odoo13 = erppeek.Client('http://52.56.174.80/', 'spg13', 'paolo', 'SPOdoo20Pg!')
    odoo13 = Server(odoo13, options={'extract_installed': False, 'extract_model_with_data': False,
                                   'extract_model_fields': True, 'use_all_model': True})

    field_comparison_report = reports.compare_fields(odoo9.extract_model_fields, odoo13.extract_model_fields)