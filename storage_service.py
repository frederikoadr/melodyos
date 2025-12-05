import os
from uuid import uuid4
from appwrite.client import Client
from appwrite.services.storage import Storage
from appwrite.input_file import InputFile

class StorageService:
    def __init__(self):
        self.endpoint = os.getenv("APPWRITE_ENDPOINT")
        self.project_id = os.getenv("APPWRITE_PROJECT_ID")
        self.api_key = os.getenv("APPWRITE_API_KEY")
        self.bucket_id = os.getenv("APPWRITE_BUCKET_ID") or ""

        client = Client()
        client.set_endpoint(self.endpoint)
        client.set_project(self.project_id)
        client.set_key(self.api_key)

        self.storage = Storage(client)

    def upload_file(self, local_path: str) -> str:
        file_id = str(uuid4())

        self.storage.create_file(
            bucket_id=self.bucket_id,
            file_id=file_id,
            file=InputFile.from_path(local_path)
        )
        
        download_url = (
            f"{self.endpoint}/storage/buckets/{self.bucket_id}/files/{file_id}/view"
            f"?project={self.project_id}"
        )
        return download_url
