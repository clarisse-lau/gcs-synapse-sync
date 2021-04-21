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
import sys
import uuid
import base64
from urllib.parse import unquote_plus
import tempfile
import synapseclient

from google.cloud import secretmanager
from google.cloud import storage
import googleapiclient.discovery

storage_client = storage.Client()
compute = googleapiclient.discovery.build('compute', 'v1')


def obj_add(data, context):
    """
    Background Cloud Function to be triggered by Cloud Storage.
    Args:
        data (dict): The Cloud Functions event payload.
        context (google.cloud.functions.Context): Metadata of triggering event.
    """
    key = data['name']
    print('File added: '+key)
    bucket = data['bucket']

    bucket_client = storage_client.bucket(bucket)

    filename = os.path.basename(key)
    dirname = os.path.dirname(key)
    filepath = bucket+'/'+dirname
    prefix='minerva'

    gc_project = os.environ.get('gcProjectName', 'gcProjectName environment variable is not set.')

    if dirname == prefix and key.endswith('story.json'):
        input_tiff = tiff_in_file(bucket_client,key)
        if storage.Blob(bucket=bucket_client, name=dirname+'/'+input_tiff).exists(storage_client) == True:
            create_instance(gc_project, filename, input_tiff, filepath)
        else:
            print("{} image not found.".format(input_tiff))

    elif dirname == prefix and (key.endswith('ome.tif') or key.endswith('ome.tiff')):
        story_json = get_story_json(bucket_client,bucket,filename,prefix)
        for json in story_json:
            input_json = os.path.basename(json)
            create_instance(gc_project, input_json, filename, filepath)

    sync_to_synapse(data,bucket,filename,key,gc_project)

def tiff_in_file(bucket_client,key):
    blob = bucket_client.blob(key)
    json_content = json.loads(blob.download_as_string(client=None))
    in_file = os.path.basename(json_content['in_file'].replace('\\',os.sep))

    return in_file

def get_story_json(bucket_client,bucket,filename,prefix):
    story_json = []

    file_list = list(storage_client.list_blobs(bucket, prefix=prefix))
    for file in file_list:
        if file.name.endswith('story.json'):
            tiff_name = tiff_in_file(bucket_client,file.name)
            if tiff_name == filename:
                story_json.append(file.name)

    return story_json

def create_instance(gc_project, input_json, input_tiff, filepath):
    zone = os.environ.get('zone', 'zone environment variable is not set.')
    machine_type = os.environ.get('machineType', 'machineType environment variable is not set.')

    docker_image = os.environ.get('dockerImage', 'dockerImage environment variable is not set.')
    gce_container = "spec:\n  containers:\n    - name: minerva-test-1\n      image: '"+docker_image+"'\n      stdin: false\n      tty: false\n  restartPolicy: Always\n\n# This container declaration format is not public API and may change without notice. Please\n# use gcloud command-line tool or Google Cloud Console to run Containers on Google Compute Engine."

    vm_config = {
        "kind": "compute#instance",
        "name": "minerva-batch-"+re.sub('[^0-9a-zA-Z]+', '-', input_json),
        "zone": "projects/"+gc_project+"/zones/"+zone,
        "machineType": "projects/"+gc_project+"/zones/"+zone+"/machineTypes/"+machine_type,
        "displayDevice": {
            "enableDisplay": False
        },
        "metadata": {
            "kind": "compute#metadata",
            "items": [
                {
                    "key": "gce-container-declaration",
                    "value": gce_container
                },
                {
                    "key": "google-logging-enabled",
                    "value": True
                },
                {
                    "key": "INPUT_JSON",
                    "value": input_json
                },
                {
                    "key": "INPUT_TIFF",
                    "value": input_tiff
                },
                {
                    "key": "DIR_NAME",
                    "value": filepath
                }
            ]
        },
        "tags": {
            "items": []
        },
        "disks": [
            {
                "kind": "compute#attachedDisk",
                "type": "PERSISTENT",
                "boot": True,
                "mode": "READ_WRITE",
                "autoDelete": True,
                "deviceName": "minerva-instance-1",
                "initializeParams": {
                    "sourceImage": "projects/cos-cloud/global/images/cos-stable-89-16108-403-15",
                    "diskType": "projects/"+gc_project+"/zones/"+zone+"/diskTypes/pd-balanced",
                    "diskSizeGb": "150"
                },
                "diskEncryptionKey": {}
            }
        ],
        "canIpForward": False,
        "networkInterfaces": [
            {
                "kind": "compute#networkInterface",
                "subnetwork": "projects/"+gc_project+"/regions/"+zone+"/subnetworks/default",
                "accessConfigs": [
                    {
                        "kind": "compute#accessConfig",
                        "name": "External NAT",
                        "type": "ONE_TO_ONE_NAT",
                        "networkTier": "PREMIUM"
                    }
                ],
                "aliasIpRanges": []
            }
        ],
        "description": "",
        "labels": {
            "container-vm": "cos-stable-89-16108-403-15"
        },
        "scheduling": {
            "preemptible": False,
            "onHostMaintenance": "MIGRATE",
            "automaticRestart": True,
            "nodeAffinities": []
        },
        "deletionProtection": False,
        "reservationAffinity": {
            "consumeReservationType": "ANY_RESERVATION"
        },
        "serviceAccounts": [
            {
                "email": "compute-execute-batch-job@"+gc_project".iam.gserviceaccount.com",
                "scopes": [
                    "https://www.googleapis.com/auth/cloud-platform"
                ]
            }
        ],
        "shieldedInstanceConfig": {
            "enableSecureBoot": False,
            "enableVtpm": True,
            "enableIntegrityMonitoring": True
        },
        "confidentialInstanceConfig": {
            "enableConfidentialCompute": False
        }
    }

    compute.instances().insert(project=gc_project,zone=zone,body=vm_config).execute()


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
    username = get_secret('synapse_service_username', gc_project_name)
    apiKey = get_secret('synapse_service_apikey', gc_project_name)
    syn = synapseclient.Synapse()
    syn.login(email=username, apiKey=apiKey)

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
