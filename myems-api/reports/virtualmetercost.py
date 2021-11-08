import falcon
import simplejson as json
import mysql.connector
import config
from datetime import datetime, timedelta, timezone
from core import utilities
from decimal import Decimal
import excelexporters.virtualmetercost


class Reporting:
    @staticmethod
    def __init__():
        """"Initializes Reporting"""
        pass

    @staticmethod
    def on_options(req, resp):
        resp.status = falcon.HTTP_200

    ####################################################################################################################
    # PROCEDURES
    # Step 1: valid parameters
    # Step 2: query the virtual meter and energy category
    # Step 3: query base period energy consumption
    # Step 4: query base period energy cost
    # Step 5: query reporting period energy consumption
    # Step 6: query reporting period energy cost
    # Step 7: query tariff data
    # Step 8: construct the report
    ####################################################################################################################
    @staticmethod
    def on_get(req, resp):
        print(req.params)
        virtual_meter_id = req.params.get('virtualmeterid')
        period_type = req.params.get('periodtype')
        base_period_start_datetime_local = req.params.get('baseperiodstartdatetime')
        base_period_end_datetime_local = req.params.get('baseperiodenddatetime')
        reporting_period_start_datetime_local = req.params.get('reportingperiodstartdatetime')
        reporting_period_end_datetime_local = req.params.get('reportingperiodenddatetime')

        ################################################################################################################
        # Step 1: valid parameters
        ################################################################################################################
        if virtual_meter_id is None:
            raise falcon.HTTPError(falcon.HTTP_400,
                                   title='API.BAD_REQUEST',
                                   description='API.INVALID_VIRTUAL_METER_ID')
        else:
            virtual_meter_id = str.strip(virtual_meter_id)
            if not virtual_meter_id.isdigit() or int(virtual_meter_id) <= 0:
                raise falcon.HTTPError(falcon.HTTP_400,
                                       title='API.BAD_REQUEST',
                                       description='API.INVALID_VIRTUAL_METER_ID')

        if period_type is None:
            raise falcon.HTTPError(falcon.HTTP_400, title='API.BAD_REQUEST', description='API.INVALID_PERIOD_TYPE')
        else:
            period_type = str.strip(period_type)
            if period_type not in ['hourly', 'daily', 'weekly', 'monthly', 'yearly']:
                raise falcon.HTTPError(falcon.HTTP_400, title='API.BAD_REQUEST', description='API.INVALID_PERIOD_TYPE')

        timezone_offset = int(config.utc_offset[1:3]) * 60 + int(config.utc_offset[4:6])
        if config.utc_offset[0] == '-':
            timezone_offset = -timezone_offset

        base_start_datetime_utc = None
        if base_period_start_datetime_local is not None and len(str.strip(base_period_start_datetime_local)) > 0:
            base_period_start_datetime_local = str.strip(base_period_start_datetime_local)
            try:
                base_start_datetime_utc = datetime.strptime(base_period_start_datetime_local, '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                raise falcon.HTTPError(falcon.HTTP_400, title='API.BAD_REQUEST',
                                       description="API.INVALID_BASE_PERIOD_START_DATETIME")
            base_start_datetime_utc = base_start_datetime_utc.replace(tzinfo=timezone.utc) - \
                timedelta(minutes=timezone_offset)

        base_end_datetime_utc = None
        if base_period_end_datetime_local is not None and len(str.strip(base_period_end_datetime_local)) > 0:
            base_period_end_datetime_local = str.strip(base_period_end_datetime_local)
            try:
                base_end_datetime_utc = datetime.strptime(base_period_end_datetime_local, '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                raise falcon.HTTPError(falcon.HTTP_400, title='API.BAD_REQUEST',
                                       description="API.INVALID_BASE_PERIOD_END_DATETIME")
            base_end_datetime_utc = base_end_datetime_utc.replace(tzinfo=timezone.utc) - \
                timedelta(minutes=timezone_offset)

        if base_start_datetime_utc is not None and base_end_datetime_utc is not None and \
                base_start_datetime_utc >= base_end_datetime_utc:
            raise falcon.HTTPError(falcon.HTTP_400, title='API.BAD_REQUEST',
                                   description='API.INVALID_BASE_PERIOD_END_DATETIME')

        if reporting_period_start_datetime_local is None:
            raise falcon.HTTPError(falcon.HTTP_400, title='API.BAD_REQUEST',
                                   description="API.INVALID_REPORTING_PERIOD_START_DATETIME")
        else:
            reporting_period_start_datetime_local = str.strip(reporting_period_start_datetime_local)
            try:
                reporting_start_datetime_utc = datetime.strptime(reporting_period_start_datetime_local,
                                                                 '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                raise falcon.HTTPError(falcon.HTTP_400, title='API.BAD_REQUEST',
                                       description="API.INVALID_REPORTING_PERIOD_START_DATETIME")
            reporting_start_datetime_utc = reporting_start_datetime_utc.replace(tzinfo=timezone.utc) - \
                timedelta(minutes=timezone_offset)

        if reporting_period_end_datetime_local is None:
            raise falcon.HTTPError(falcon.HTTP_400, title='API.BAD_REQUEST',
                                   description="API.INVALID_REPORTING_PERIOD_END_DATETIME")
        else:
            reporting_period_end_datetime_local = str.strip(reporting_period_end_datetime_local)
            try:
                reporting_end_datetime_utc = datetime.strptime(reporting_period_end_datetime_local,
                                                               '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                raise falcon.HTTPError(falcon.HTTP_400, title='API.BAD_REQUEST',
                                       description="API.INVALID_REPORTING_PERIOD_END_DATETIME")
            reporting_end_datetime_utc = reporting_end_datetime_utc.replace(tzinfo=timezone.utc) - \
                timedelta(minutes=timezone_offset)

        if reporting_start_datetime_utc >= reporting_end_datetime_utc:
            raise falcon.HTTPError(falcon.HTTP_400, title='API.BAD_REQUEST',
                                   description='API.INVALID_REPORTING_PERIOD_END_DATETIME')

        ################################################################################################################
        # Step 2: query the virtual meter and energy category
        ################################################################################################################
        cnx_system = mysql.connector.connect(**config.myems_system_db)
        cursor_system = cnx_system.cursor()

        cnx_energy = mysql.connector.connect(**config.myems_energy_db)
        cursor_energy = cnx_energy.cursor()

        cnx_billing = mysql.connector.connect(**config.myems_billing_db)
        cursor_billing = cnx_billing.cursor()

        cursor_system.execute(" SELECT m.id, m.name, m.cost_center_id, m.energy_category_id, "
                              "        ec.name, ec.unit_of_measure, ec.kgce, ec.kgco2e "
                              " FROM tbl_virtual_meters m, tbl_energy_categories ec "
                              " WHERE m.id = %s AND m.energy_category_id = ec.id ", (virtual_meter_id,))
        row_virtual_meter = cursor_system.fetchone()
        if row_virtual_meter is None:
            if cursor_system:
                cursor_system.close()
            if cnx_system:
                cnx_system.disconnect()

            if cursor_energy:
                cursor_energy.close()
            if cnx_energy:
                cnx_energy.disconnect()

            if cursor_billing:
                cursor_billing.close()
            if cnx_billing:
                cnx_billing.disconnect()
            raise falcon.HTTPError(falcon.HTTP_404, title='API.NOT_FOUND', description='API.VIRTUAL_METER_NOT_FOUND')

        virtual_meter = dict()
        virtual_meter['id'] = row_virtual_meter[0]
        virtual_meter['name'] = row_virtual_meter[1]
        virtual_meter['cost_center_id'] = row_virtual_meter[2]
        virtual_meter['energy_category_id'] = row_virtual_meter[3]
        virtual_meter['energy_category_name'] = row_virtual_meter[4]
        virtual_meter['unit_of_measure'] = config.currency_unit
        virtual_meter['kgce'] = row_virtual_meter[6]
        virtual_meter['kgco2e'] = row_virtual_meter[7]

        ################################################################################################################
        # Step 3: query base period energy consumption
        ################################################################################################################
        query = (" SELECT start_datetime_utc, actual_value "
                 " FROM tbl_virtual_meter_hourly "
                 " WHERE virtual_meter_id = %s "
                 " AND start_datetime_utc >= %s "
                 " AND start_datetime_utc < %s "
                 " ORDER BY start_datetime_utc ")
        cursor_energy.execute(query, (virtual_meter['id'], base_start_datetime_utc, base_end_datetime_utc))
        rows_virtual_meter_hourly = cursor_energy.fetchall()

        rows_virtual_meter_periodically = utilities.aggregate_hourly_data_by_period(rows_virtual_meter_hourly,
                                                                                    base_start_datetime_utc,
                                                                                    base_end_datetime_utc,
                                                                                    period_type)
        base = dict()
        base['timestamps'] = list()
        base['values'] = list()
        base['total_in_category'] = Decimal(0.0)
        base['total_in_kgce'] = Decimal(0.0)
        base['total_in_kgco2e'] = Decimal(0.0)

        for row_virtual_meter_periodically in rows_virtual_meter_periodically:
            current_datetime_local = row_virtual_meter_periodically[0].replace(tzinfo=timezone.utc) + \
                                     timedelta(minutes=timezone_offset)
            if period_type == 'hourly':
                current_datetime = current_datetime_local.strftime('%Y-%m-%dT%H:%M:%S')
            elif period_type == 'daily':
                current_datetime = current_datetime_local.strftime('%Y-%m-%d')
            elif period_type == 'weekly':
                current_datetime = current_datetime_local.strftime('%Y-%m-%d')
            elif period_type == 'monthly':
                current_datetime = current_datetime_local.strftime('%Y-%m')
            elif period_type == 'yearly':
                current_datetime = current_datetime_local.strftime('%Y')

            actual_value = Decimal(0.0) if row_virtual_meter_periodically[1] is None \
                else row_virtual_meter_periodically[1]
            base['timestamps'].append(current_datetime)
            base['total_in_kgce'] += actual_value * virtual_meter['kgce']
            base['total_in_kgco2e'] += actual_value * virtual_meter['kgco2e']

        ################################################################################################################
        # Step 4: query base period energy cost
        ################################################################################################################
        query = (" SELECT start_datetime_utc, actual_value "
                 " FROM tbl_virtual_meter_hourly "
                 " WHERE virtual_meter_id = %s "
                 " AND start_datetime_utc >= %s "
                 " AND start_datetime_utc < %s "
                 " ORDER BY start_datetime_utc ")
        cursor_billing.execute(query, (virtual_meter['id'], base_start_datetime_utc, base_end_datetime_utc))
        rows_virtual_meter_hourly = cursor_billing.fetchall()

        rows_virtual_meter_periodically = utilities.aggregate_hourly_data_by_period(rows_virtual_meter_hourly,
                                                                                    base_start_datetime_utc,
                                                                                    base_end_datetime_utc,
                                                                                    period_type)

        base['values'] = list()
        base['total_in_category'] = Decimal(0.0)

        for row_virtual_meter_periodically in rows_virtual_meter_periodically:
            actual_value = Decimal(0.0) if row_virtual_meter_periodically[1] is None \
                else row_virtual_meter_periodically[1]
            base['values'].append(actual_value)
            base['total_in_category'] += actual_value

        ################################################################################################################
        # Step 5: query reporting period energy consumption
        ################################################################################################################
        query = (" SELECT start_datetime_utc, actual_value "
                 " FROM tbl_virtual_meter_hourly "
                 " WHERE virtual_meter_id = %s "
                 " AND start_datetime_utc >= %s "
                 " AND start_datetime_utc < %s "
                 " ORDER BY start_datetime_utc ")
        cursor_billing.execute(query, (virtual_meter['id'], reporting_start_datetime_utc, reporting_end_datetime_utc))
        rows_virtual_meter_hourly = cursor_billing.fetchall()

        rows_virtual_meter_periodically = utilities.aggregate_hourly_data_by_period(rows_virtual_meter_hourly,
                                                                                    reporting_start_datetime_utc,
                                                                                    reporting_end_datetime_utc,
                                                                                    period_type)
        reporting = dict()
        reporting['timestamps'] = list()
        reporting['values'] = list()
        reporting['total_in_category'] = Decimal(0.0)
        reporting['total_in_kgce'] = Decimal(0.0)
        reporting['total_in_kgco2e'] = Decimal(0.0)

        for row_virtual_meter_periodically in rows_virtual_meter_periodically:
            current_datetime_local = row_virtual_meter_periodically[0].replace(tzinfo=timezone.utc) + \
                                     timedelta(minutes=timezone_offset)
            if period_type == 'hourly':
                current_datetime = current_datetime_local.strftime('%Y-%m-%dT%H:%M:%S')
            elif period_type == 'daily':
                current_datetime = current_datetime_local.strftime('%Y-%m-%d')
            elif period_type == 'weekly':
                current_datetime = current_datetime_local.strftime('%Y-%m-%d')
            elif period_type == 'monthly':
                current_datetime = current_datetime_local.strftime('%Y-%m')
            elif period_type == 'yearly':
                current_datetime = current_datetime_local.strftime('%Y')

            actual_value = Decimal(0.0) if row_virtual_meter_periodically[1] is None \
                else row_virtual_meter_periodically[1]

            reporting['timestamps'].append(current_datetime)
            reporting['total_in_kgce'] += actual_value * virtual_meter['kgce']
            reporting['total_in_kgco2e'] += actual_value * virtual_meter['kgco2e']

        ################################################################################################################
        # Step 6: query reporting period energy cost
        ################################################################################################################
        query = (" SELECT start_datetime_utc, actual_value "
                 " FROM tbl_virtual_meter_hourly "
                 " WHERE virtual_meter_id = %s "
                 " AND start_datetime_utc >= %s "
                 " AND start_datetime_utc < %s "
                 " ORDER BY start_datetime_utc ")
        cursor_billing.execute(query, (virtual_meter['id'], reporting_start_datetime_utc, reporting_end_datetime_utc))
        rows_virtual_meter_hourly = cursor_billing.fetchall()

        rows_virtual_meter_periodically = utilities.aggregate_hourly_data_by_period(rows_virtual_meter_hourly,
                                                                                    reporting_start_datetime_utc,
                                                                                    reporting_end_datetime_utc,
                                                                                    period_type)

        for row_virtual_meter_periodically in rows_virtual_meter_periodically:
            actual_value = Decimal(0.0) if row_virtual_meter_periodically[1] is None \
                else row_virtual_meter_periodically[1]

            reporting['values'].append(actual_value)
            reporting['total_in_category'] += actual_value

        ################################################################################################################
        # Step 7: query tariff data
        ################################################################################################################
        parameters_data = dict()
        parameters_data['names'] = list()
        parameters_data['timestamps'] = list()
        parameters_data['values'] = list()

        tariff_dict = utilities.get_energy_category_tariffs(virtual_meter['cost_center_id'],
                                                            virtual_meter['energy_category_id'],
                                                            reporting_start_datetime_utc,
                                                            reporting_end_datetime_utc)
        tariff_timestamp_list = list()
        tariff_value_list = list()
        for k, v in tariff_dict.items():
            # convert k from utc to local
            k = k + timedelta(minutes=timezone_offset)
            tariff_timestamp_list.append(k.isoformat()[0:19])
            tariff_value_list.append(v)

        parameters_data['names'].append('TARIFF-' + virtual_meter['energy_category_name'])
        parameters_data['timestamps'].append(tariff_timestamp_list)
        parameters_data['values'].append(tariff_value_list)

        ################################################################################################################
        # Step 8: construct the report
        ################################################################################################################
        if cursor_system:
            cursor_system.close()
        if cnx_system:
            cnx_system.disconnect()

        if cursor_energy:
            cursor_energy.close()
        if cnx_energy:
            cnx_energy.disconnect()

        if cursor_billing:
            cursor_billing.close()
        if cnx_billing:
            cnx_billing.disconnect()

        result = {
            "virtual_meter": {
                "cost_center_id": virtual_meter['cost_center_id'],
                "energy_category_id": virtual_meter['energy_category_id'],
                "energy_category_name": virtual_meter['energy_category_name'],
                "unit_of_measure": config.currency_unit,
                "kgce": virtual_meter['kgce'],
                "kgco2e": virtual_meter['kgco2e'],
            },
            "base_period": {
                "total_in_category": base['total_in_category'],
                "total_in_kgce": base['total_in_kgce'],
                "total_in_kgco2e": base['total_in_kgco2e'],
                "timestamps": base['timestamps'],
                "values": base['values'],
            },
            "reporting_period": {
                "increment_rate":
                    (reporting['total_in_category'] - base['total_in_category']) / base['total_in_category']
                    if base['total_in_category'] > 0 else None,
                "total_in_category": reporting['total_in_category'],
                "total_in_kgce": reporting['total_in_kgce'],
                "total_in_kgco2e": reporting['total_in_kgco2e'],
                "timestamps": reporting['timestamps'],
                "values": reporting['values'],
            },
            "parameters": {
                "names": parameters_data['names'],
                "timestamps": parameters_data['timestamps'],
                "values": parameters_data['values']
            },
        }

        # export result to Excel file and then encode the file to base64 string
        result['excel_bytes_base64'] = \
            excelexporters.virtualmetercost.export(result,
                                                   virtual_meter['name'],
                                                   reporting_period_start_datetime_local,
                                                   reporting_period_end_datetime_local,
                                                   period_type)

        resp.text = json.dumps(result)
