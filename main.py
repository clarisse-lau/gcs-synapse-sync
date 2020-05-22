import json
import os
import sys
import uuid
import base64
from urllib.parse import unquote_plus

import tempfile
import synapseclient

syn = synapseclient.Synapse()
syn.login(email=os.environ.get('username', 'username environment variable is not set.'),
    apiKey=os.environ.get('apiKey', 'apiKey environment variable is not set.'), silent=True)

def syn_create(data, context):
    """
    Background Cloud Function to be triggered by Cloud Storage.
    Args:
        data (dict): The Cloud Functions event payload.
        context (google.cloud.functions.Context): Metadata of triggering event.
    """
    key = data['name']
    print(key)
    inclFolders = os.environ.get('foldersToSync', 'foldersToSync environment variable is not set.')

    if key.split('/')[0] in inclFolders.split(','): 
        filename = os.path.basename(key)
        bucket = data['bucket']
        project_id = os.environ.get('synapseProjectId', 'synapseProjectId environment variable is not set.')
        storage_id = syn.restGET("/projectSettings/"+project_id+"/type/upload")['locations'][0]
        
        parent = get_parent_folder(project_id, key)
        contentmd5 = base64.b64decode(data['md5Hash']).hex()
        file_id = syn.findEntityId(filename, parent)

        if file_id != None:
            targetmd5 = syn.get(file_id,downloadFile=False)['md5'];

        # create filehandle if it does not exist in Synapse or if existing file was modified (check md5):
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
    inclFolders = os.environ.get('foldersToSync', 'foldersToSync environment variable is not set.') 
    
    if key.split('/')[0] in inclFolders.split(','):
        filename = os.path.basename(key)
        print("filename: " + filename)
        project_id = os.environ.get('synapseProjectId', 'Specified environment variable is not set.')
        parent_id = get_parent_folder(project_id, key)
        file_id = syn.findEntityId(filename, parent_id)
        syn.delete(file_id)

def get_parent_folder(project_id, key):
    parent_id = project_id
    folders = key.split('/')
    folders=folders[:-1]

    for f in folders:
        folder_id = syn.findEntityId(f, parent_id)
        if folder_id == None:
            # create folder
            folder_id = syn.store(synapseclient.Folder(name=f, parent=parent_id), forceVersion=False)['id']
        parent_id = folder_id

    return parent_id


