import falcon
import json
import mysql.connector
import config
import uuid
from datetime import datetime, timezone, timedelta
import os
import base64
import sys
from core.userlogger import user_logger


class KnowledgeFileCollection:
    @staticmethod
    def __init__():
        """"Initializes KnowledgeFileCollection"""
        pass

    @staticmethod
    def on_options(req, resp):
        resp.status = falcon.HTTP_200

    @staticmethod
    def on_get(req, resp):
        cnx = mysql.connector.connect(**config.myems_user_db)
        cursor = cnx.cursor(dictionary=True)

        query = (" SELECT uuid, display_name "
                 " FROM tbl_users ")
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        cnx.disconnect()

        user_dict = dict()
        if rows is not None and len(rows) > 0:
            for row in rows:
                user_dict[row['uuid']] = row['display_name']

        cnx = mysql.connector.connect(**config.myems_system_db)
        cursor = cnx.cursor(dictionary=True)

        query = (" SELECT id, file_name, uuid, upload_datetime_utc, upload_user_uuid, file_object"
                 " FROM tbl_knowledge_files "
                 " ORDER BY upload_datetime_utc desc ")
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        cnx.disconnect()

        result = list()
        if rows is not None and len(rows) > 0:
            timezone_offset = int(config.utc_offset[1:3]) * 60 + int(config.utc_offset[4:6])
            if config.utc_offset[0] == '-':
                timezone_offset = -timezone_offset
            for row in rows:
                # Base64 encode the bytes
                base64_encoded_data = base64.b64encode(row['file_object'])
                # get the Base64 encoded data using human-readable characters.
                base64_message = base64_encoded_data.decode('utf-8')
                upload_datetime_local = row['upload_datetime_utc'].replace(tzinfo=None) + \
                    timedelta(minutes=timezone_offset)
                meta_result = {"id": row['id'],
                               "file_name": row['file_name'],
                               "uuid": row['uuid'],
                               "upload_datetime": upload_datetime_local.strftime('%Y-%m-%dT%H:%M:%S'),
                               "user_display_name": user_dict.get(row['upload_user_uuid'], None),
                               "file_size_bytes": sys.getsizeof(row['file_object']),
                               "file_bytes_base64": base64_message
                               }
                result.append(meta_result)

        resp.body = json.dumps(result)

    @staticmethod
    @user_logger
    def on_post(req, resp):
        """Handles POST requests"""

        try:
            upload = req.get_param('file')
            # Read upload file as binary
            raw_blob = upload.file.read()
            # Retrieve filename
            filename = upload.filename
            file_uuid = str(uuid.uuid4())

            # Define file_path
            file_path = os.path.join(config.upload_path, file_uuid)

            # Write to a temporary file to prevent incomplete files from
            # being used.
            temp_file_path = file_path + '~'

            open(temp_file_path, 'wb').write(raw_blob)

            # Now that we know the file has been fully saved to disk
            # move it into place.
            os.rename(temp_file_path, file_path)
        except Exception as ex:
            raise falcon.HTTPError(falcon.HTTP_400, title='API.ERROR',
                                   description='API.FAILED_TO_UPLOAD_KNOWLEDGE_FILE')

        # Verify User Session
        token = req.headers.get('TOKEN')
        user_uuid = req.headers.get('USER-UUID')
        if token is None:
            raise falcon.HTTPError(falcon.HTTP_400, title='API.BAD_REQUEST',
                                   description='API.TOKEN_NOT_FOUND_IN_HEADERS_PLEASE_LOGIN')
        if user_uuid is None:
            raise falcon.HTTPError(falcon.HTTP_400, title='API.BAD_REQUEST',
                                   description='API.USER_UUID_NOT_FOUND_IN_HEADERS_PLEASE_LOGIN')

        cnx = mysql.connector.connect(**config.myems_user_db)
        cursor = cnx.cursor()

        query = (" SELECT utc_expires "
                 " FROM tbl_sessions "
                 " WHERE user_uuid = %s AND token = %s")
        cursor.execute(query, (user_uuid, token,))
        row = cursor.fetchone()

        if row is None:
            if cursor:
                cursor.close()
            if cnx:
                cnx.disconnect()
            raise falcon.HTTPError(falcon.HTTP_400, title='API.BAD_REQUEST',
                                   description='API.INVALID_SESSION_PLEASE_RE_LOGIN')
        else:
            utc_expires = row[0]
            if datetime.utcnow() > utc_expires:
                if cursor:
                    cursor.close()
                if cnx:
                    cnx.disconnect()
                raise falcon.HTTPError(falcon.HTTP_400, title='API.BAD_REQUEST',
                                       description='API.USER_SESSION_TIMEOUT')

        cursor.execute(" SELECT id "
                       " FROM tbl_users "
                       " WHERE uuid = %s ",
                       (user_uuid,))
        row = cursor.fetchone()
        if row is None:
            if cursor:
                cursor.close()
            if cnx:
                cnx.disconnect()
            raise falcon.HTTPError(falcon.HTTP_400, title='API.BAD_REQUEST',
                                   description='API.INVALID_USER_PLEASE_RE_LOGIN')
        else:
            user_id = row[0]

        cnx = mysql.connector.connect(**config.myems_system_db)
        cursor = cnx.cursor()

        add_values = (" INSERT INTO tbl_knowledge_files "
                      " (file_name, uuid, upload_datetime_utc, upload_user_uuid, file_object ) "
                      " VALUES (%s, %s, %s, %s, %s) ")
        cursor.execute(add_values, (filename,
                                    file_uuid,
                                    datetime.utcnow(),
                                    user_uuid,
                                    raw_blob))
        new_id = cursor.lastrowid
        cnx.commit()
        cursor.close()
        cnx.disconnect()

        resp.status = falcon.HTTP_201
        resp.location = '/knowledgefiles/' + str(new_id)


class KnowledgeFileItem:
    @staticmethod
    def __init__():
        """"Initializes KnowledgeFileItem"""
        pass

    @staticmethod
    def on_options(req, resp, id_):
        resp.status = falcon.HTTP_200

    @staticmethod
    def on_get(req, resp, id_):
        if not id_.isdigit() or int(id_) <= 0:
            raise falcon.HTTPError(falcon.HTTP_400, title='API.BAD_REQUEST',
                                   description='API.INVALID_KNOWLEDGE_FILE_ID')

        cnx = mysql.connector.connect(**config.myems_user_db)
        cursor = cnx.cursor()

        query = (" SELECT uuid, display_name "
                 " FROM tbl_users ")
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        cnx.disconnect()

        user_dict = dict()
        if rows is not None and len(rows) > 0:
            for row in rows:
                user_dict[row[0]] = row[1]

        cnx = mysql.connector.connect(**config.myems_system_db)
        cursor = cnx.cursor()

        query = (" SELECT id, file_name, uuid, upload_datetime_utc, upload_user_uuid "
                 " FROM tbl_knowledge_files "
                 " WHERE id = %s ")
        cursor.execute(query, (id_,))
        row = cursor.fetchone()
        cursor.close()
        cnx.disconnect()

        if row is None:
            raise falcon.HTTPError(falcon.HTTP_404, title='API.NOT_FOUND',
                                   description='API.KNOWLEDGE_FILE_NOT_FOUND')

        timezone_offset = int(config.utc_offset[1:3]) * 60 + int(config.utc_offset[4:6])
        if config.utc_offset[0] == '-':
            timezone_offset = -timezone_offset

        upload_datetime_local = row[3].replace(tzinfo=timezone.utc) + timedelta(minutes=timezone_offset)

        result = {"id": row[0],
                  "file_name": row[1],
                  "uuid": row[2],
                  "upload_datetime": upload_datetime_local.strftime('%Y-%m-%dT%H:%M:%S'),
                  "user_display_name": user_dict.get(row[4], None)}
        resp.body = json.dumps(result)

    @staticmethod
    @user_logger
    def on_delete(req, resp, id_):
        if not id_.isdigit() or int(id_) <= 0:
            raise falcon.HTTPError(falcon.HTTP_400,
                                   title='API.BAD_REQUEST',
                                   description='API.INVALID_KNOWLEDGE_FILE_ID')

        cnx = mysql.connector.connect(**config.myems_system_db)
        cursor = cnx.cursor()

        cursor.execute(" SELECT uuid "
                       " FROM tbl_knowledge_files "
                       " WHERE id = %s ", (id_,))
        row = cursor.fetchone()
        if row is None:
            cursor.close()
            cnx.disconnect()
            raise falcon.HTTPError(falcon.HTTP_404,
                                   title='API.NOT_FOUND',
                                   description='API.KNOWLEDGE_FILE_NOT_FOUND')

        try:
            file_uuid = row[0]
            # Define file_path
            file_path = os.path.join(config.upload_path, file_uuid)
            # remove the file from disk
            os.remove(file_path)
        except Exception as ex:
            raise falcon.HTTPError(falcon.HTTP_400, title='API.ERROR',
                                   description='API.KNOWLEDGE_FILE_CANNOT_BE_REMOVED_FROM_DISK')

        cursor.execute(" DELETE FROM tbl_knowledge_files WHERE id = %s ", (id_,))
        cnx.commit()

        cursor.close()
        cnx.disconnect()

        resp.status = falcon.HTTP_204


class KnowledgeFileRestore:
    @staticmethod
    def __init__():
        """"Initializes KnowledgeFileRestore"""
        pass

    @staticmethod
    def on_options(req, resp, id_):
        resp.status = falcon.HTTP_200

    @staticmethod
    def on_get(req, resp, id_):
        if not id_.isdigit() or int(id_) <= 0:
            raise falcon.HTTPError(falcon.HTTP_400, title='API.BAD_REQUEST',
                                   description='API.INVALID_KNOWLEDGE_FILE_ID')

        cnx = mysql.connector.connect(**config.myems_system_db)
        cursor = cnx.cursor()

        query = (" SELECT uuid, file_object "
                 " FROM tbl_knowledge_files "
                 " WHERE id = %s ")
        cursor.execute(query, (id_,))
        row = cursor.fetchone()
        cursor.close()
        cnx.disconnect()

        if row is None:
            raise falcon.HTTPError(falcon.HTTP_404, title='API.NOT_FOUND',
                                   description='API.KNOWLEDGE_FILE_NOT_FOUND')

        result = {"uuid": row[0],
                  "file_object": row[1]}
        try:
            raw_blob = result["file_object"]
            file_uuid = result["uuid"]

            # Define file_path
            file_path = os.path.join(config.upload_path, file_uuid)

            # Write to a temporary file to prevent incomplete files from
            # being used.
            temp_file_path = file_path + '~'

            open(temp_file_path, 'wb').write(raw_blob)

            # Now that we know the file has been fully saved to disk
            # move it into place.
            os.replace(temp_file_path, file_path)
        except Exception as ex:
            raise falcon.HTTPError(falcon.HTTP_400, title='API.ERROR',
                                   description='API.FAILED_TO_RESTORE_KNOWLEDGE_FILE')
        resp.body = json.dumps('success')

