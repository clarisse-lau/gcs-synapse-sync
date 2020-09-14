import json
import os
import sys
import uuid
import base64
from google.cloud import secretmanager
from urllib.parse import unquote_plus
import tempfile
import synapseclient

def syn_create(data, context):
    """
    Background Cloud Function to be triggered by Cloud Storage.
    Args:
        data (dict): The Cloud Functions event payload.
        context (google.cloud.functions.Context): Metadata of triggering event.
    """
    key = data['name']

    gc_project = os.environ.get('gcProjectName', 'gcProjectName environment variable is not set.')
    username = get_secret('synapse_service_username', gc_project)
    apiKey = get_secret('synapse_service_apikey', gc_project)

    syn = synapseclient.Synapse()
    syn.login(email=username, apiKey=apiKey)

    if key[0].isdigit() == False: 
        project_id = os.environ.get('synapseProjectId', 'synapseProjectId environment variable is not set.')
        parent = get_parent_folder(syn, project_id, key)
        if parent == None:
            return  # Do not sync files at the root level
        
        contentmd5 = base64.b64decode(data['md5Hash']).hex()
        filename = os.path.basename(key)
        bucket = data['bucket']
        file_id = syn.findEntityId(filename, parent)
        storage_id = syn.restGET("/projectSettings/"+project_id+"/type/upload")['locations'][0]

        if file_id != None:
            targetmd5 = syn.get(file_id, downloadFile=False)['md5'];

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

def syn_delete(data, context):
    """Background Cloud Function to be triggered by Cloud Storage.
    Args:
        data (dict): The Cloud Functions event payload.
        context (google.cloud.functions.Context): Metadata of triggering event.
    """
    key = data['name']
    gc_project = os.environ.get('gcProjectName', 'gcProjectName environment variable is not set.')
    username = get_secret('synapse_service_username', gc_project)
    apiKey = get_secret('synapse_service_apikey', gc_project)

    syn = synapseclient.Synapse()
    syn.login(email=username, apiKey=apiKey)
    
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

def get_secret(secret_name, gc_project_name):
    client = secretmanager.SecretManagerServiceClient()
    resource_name = f"projects/{gc_project_name}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(resource_name)
    return response.payload.data.decode('UTF-8')

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
