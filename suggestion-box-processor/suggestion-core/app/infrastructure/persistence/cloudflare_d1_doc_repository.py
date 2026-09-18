import httpx
from app.domain.suggestion import Suggestion
from app.domain.repositories.suggestion_repository import SuggestionRepository
from app.infrastructure.persistence.document import SuggestionDocument


class CloudflareD1DocRepository(SuggestionRepository):
    def __init__(self, d1_client):
        self.d1_client = d1_client
        self.url = "https://your-cloudflare-d1-endpoint"  # Replace with your actual Cloudflare D1 endpoint
        self.headers = {
            "Authorization": "Bearer YOUR_API_TOKEN",  # Replace with your actual API token
            "Content-Type": "application/json"
        }

    async def save(self, suggestion: Suggestion) -> Suggestion:
        document = SuggestionDocument.model_validate(suggestion, from_attributes=True)
        query = "INSERT OR REPLACE INTO suggestions (id, document, status) VALUES (?, ?, ?);"
        
        body = {
            "sql": query,
            "params": [str(document.id), document.model_dump_json(), document.status.status]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.url, headers=self.headers, json=body)
            if response.status_code != 200 or not response.json().get("success"):
                raise RuntimeError(f"Cloudflare D1 Save Failure: {response.text}")
        return suggestion
