"""
Copyright 2020, Institute for Systems Biology

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json
import os
import re
import uuid
import base64
from urllib.parse import unquote_plus
import tempfile
import synapseclient

from google.cloud import secretmanager
from google.cloud import storage
import googleapiclient.discovery

storage_client = storage.Client()


def obj_add(data, context):
    """
    Background Cloud Function to be triggered by Cloud Storage.
    Args:
        data (dict): The Cloud Functions event payload.
        context (google.cloud.functions.Context): Metadata of triggering event.
    """
    key = data['name']
    bucket = data['bucket']
    filename = os.path.basename(key)

    gc_project = os.environ.get('gcProjectName', 'gcProjectName environment variable is not set.')

    sync_to_synapse(data, bucket, filename, key, gc_project)
    print('File added: '+key)

def sync_to_synapse(data,bucket,filename,key,gc_project):
    syn = synapse_login(gc_project)

    if key[0].isdigit() == False:
        project_id = os.environ.get('synapseProjectId', 'synapseProjectId environment variable is not set.')
        parent = get_parent_folder(syn, project_id, key)
        if parent == project_id:
            return  # Do not sync files at the root level

        contentmd5 = get_md5(data)

        file_id = syn.findEntityId(filename, parent)
        storage_id = syn.restGET("/projectSettings/"+project_id+"/type/upload")['locations'][0]

        if file_id != None:
            targetmd5 = syn.get(file_id, downloadFile=False)['md5']

        if file_id == None or contentmd5 != targetmd5:
            size = data['size']
            contentType = data['contentType']

            fileHandle = {'concreteType': 'org.sagebionetworks.repo.model.file.GoogleCloudFileHandle',
                                'fileName'    : filename,
                                'contentSize' : size,
                                'contentType' : contentType,
                                'contentMd5'  : contentmd5,
                                'bucketName'  : bucket,
                                'key'         : key,
                                'storageLocationId': storage_id}
            fileHandle = syn.restPOST('/externalFileHandle/googleCloud', json.dumps(fileHandle), endpoint=syn.fileHandleEndpoint)
            f = synapseclient.File(parentId=parent, dataFileHandleId=fileHandle['id'], name=filename, synapseStore=False)
            f = syn.store(f)

def obj_delete(data, context):
    """Background Cloud Function to be triggered by Cloud Storage.
    Args:
        data (dict): The Cloud Functions event payload.
        context (google.cloud.functions.Context): Metadata of triggering event.
    """
    key = data['name']
    gc_project = os.environ.get('gcProjectName', 'gcProjectName environment variable is not set.')

    syn = synapse_login(gc_project)

    if key[0].isdigit() == False:
        filename = os.path.basename(key)
        project_id = os.environ.get('synapseProjectId', 'Specified environment variable is not set.')

        parent_id = get_parent_folder(syn, project_id, key, False)
        if parent_id == None:
            return

        if not filename:   # Object is a folder
            syn.delete(parent_id)
        else:
            file_id = syn.findEntityId(filename, parent_id)
            syn.delete(file_id)

def synapse_login(gc_project_name):
    syn_sa_pat = get_secret('synapse_service_pat', gc_project_name)
    syn = synapseclient.Synapse()
    syn.login(authToken = syn_sa_pat)

    return syn

def get_secret(secret_name, gc_project_name):
    client = secretmanager.SecretManagerServiceClient()
    resource_name = f"projects/{gc_project_name}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(name=resource_name)

    return response.payload.data.decode('UTF-8')

def get_md5(data):
    try:
        md5 = base64.b64decode(data['md5Hash']).hex()
    except:
        md5 = base64.b64decode(data['metadata']['content-md5']).hex()
        print('md5 not provided. Please include md5 as metadata and re-upload file')

    return md5

def get_parent_folder(syn, project_id, key, create_folder=True):
    parent_id = project_id
    folders = key.split('/')
    folders.pop(-1)

    if folders:
        for f in folders:
            folder_id = syn.findEntityId(f, parent_id)
            if folder_id == None:
                if not create_folder:
                    return None

                folder_id = syn.store(synapseclient.Folder(name=f, parent=parent_id), forceVersion=False)['id']
            parent_id = folder_id

    return parent_id
