"""
LLM-based deal extraction and validation service.
Uses OpenAI-compatible API to parse forum posts and extract structured deal information.

Supports BATCH mode: send all titles at once, get back which are valid + structured data.
"""
import json
from typing import Optional, Dict, Any, List
import requests
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class LLMDealExtractor:
    """Extract and validate deals using LLM."""
    
    def __init__(self):
        self.api_url = getattr(settings, 'llm_api_url', 'http://localhost:5005/2121212121/v1/chat/completions')
        self.api_key = getattr(settings, 'llm_api_key', '')
        self.model = getattr(settings, 'llm_model', 'gpt-5.1')
        self.timeout = 120  # Longer timeout for batch requests

    def batch_validate_and_extract(
        self,
        threads: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Validate and extract deal info for multiple threads in ONE LLM call.
        
        Args:
            threads: List of dicts with keys: id, title, summary (optional), content (optional)
        
        Returns:
            Dict mapping thread id -> extracted deal data (only for valid deals)
        """
        if not threads:
            return {}

        prompt = self._build_batch_prompt(threads)
        
        try:
            response = self._call_llm(prompt)
            if not response:
                logger.error("batch_llm_returned_empty")
                return {}
            
            # Parse JSON response
            result = json.loads(response)
            
            # Result should be {"deals": [{"id": "...", "is_valid": true/false, ...}, ...]}
            deals_list = result.get('deals', [])
            
            valid_deals = {}
            for deal in deals_list:
                thread_id = deal.get('id')
                if thread_id and deal.get('is_valid', False):
                    valid_deals[thread_id] = deal
                    logger.info("batch_deal_valid", id=thread_id, provider=deal.get('provider_name'))
                elif thread_id:
                    logger.debug("batch_deal_rejected", id=thread_id, reason=deal.get('rejection_reason'))
            
            logger.info(
                "batch_validation_complete",
                total=len(threads),
                valid=len(valid_deals),
                rejected=len(threads) - len(valid_deals)
            )
            
            return valid_deals
            
        except json.JSONDecodeError as e:
            logger.error("batch_llm_parse_failed", error=str(e), response=response[:500] if response else None)
            return {}
        except Exception as e:
            logger.error("batch_llm_failed", error=str(e))
            return {}

    def _build_batch_prompt(self, threads: List[Dict[str, Any]]) -> str:
        """Build prompt for batch validation."""
        # Build thread list
        thread_entries = []
        for t in threads:
            entry = f"[ID: {t['id']}]\nTitle: {t['title']}"
            if t.get('summary'):
                entry += f"\nSummary: {t['summary'][:500]}"
            if t.get('content'):
                entry += f"\nContent Preview: {t['content'][:800]}"
            thread_entries.append(entry)
        
        threads_text = "\n\n---\n\n".join(thread_entries)
        
        return f"""You are an expert at identifying real hosting deals from forum posts.

I have {len(threads)} forum post titles/summaries. For EACH one, determine:
1. Is it a REAL hosting deal (VPS, dedicated, shared, cloud, reseller)?
2. If valid, extract the structured deal information.

**THREAD LIST:**

{threads_text}

**VALIDATION RULES:**
Mark is_valid=FALSE if the post is:
- A discussion, news, blog, or opinion post
- A question asking for recommendations
- About non-hosting topics (AI, software, drama, stats)
- An expired or out-of-stock deal
- Missing pricing or hosting specs

Mark is_valid=TRUE ONLY if:
- It offers hosting services (VPS, dedicated, shared, cloud, reseller)
- Has specific pricing mentioned
- From a hosting provider offering services

**OUTPUT FORMAT (JSON only, no markdown):**
{{
  "deals": [
    {{
      "id": "thread_id_here",
      "is_valid": false,
      "rejection_reason": "Discussion post, not a deal"
    }},
    {{
      "id": "another_thread_id",
      "is_valid": true,
      "provider_name": "Company Name",
      "provider_domain": "company.com",
      "deal_type": "VPS",
      "configurations": [
        {{
          "name": "Plan Name",
          "cpu_brand": "AMD|Intel|ARM" or null,
          "cpu_model": "EPYC 7xx3" or null,
          "cpu_cores": 1,
          "ram_mb": 1024,
          "storage_gb": 20,
          "bandwidth_gb": 1000,
          "ipv4": 1,
          "ipv6": true,
          "price_amount": 5.00,
          "price_currency": "USD",
          "billing_period": "month",
          "location": "US-East"
        }}
      ],
      "locations": ["US-East"],
      "highlights": ["NVMe", "DDoS Protection"],
      "promo_code": "BLACKFRIDAY" or null,
      "promo_url": "https://special-offer-link" or null,
      "order_url": "https://..." or null
    }}
  ]
}}

**IMPORTANT:**
- Return an entry for EVERY thread ID provided
- Extract ALL configurations/plans as separate items
- Provider domain = actual company website, NOT forum URL
- Be strict: only mark valid if clearly an active deal with specs+pricing
"""

    def extract_deal_info(self, post_title: str, post_content: str, post_url: str) -> Optional[Dict[str, Any]]:
        """
        Extract structured deal information from a forum post using LLM.
        
        Returns dict with:
        - provider_name: Actual hosting company name
        - provider_domain: Official website domain (not forum)
        - is_valid: Whether this is a legitimate, current deal
        - deal_type: Type of service (VPS, Dedicated, Shared Hosting, etc.)
        - configurations: Extracted plans/tiers (each one becomes a separate card)
        - locations: Available data center locations
        - highlights: Key selling points
        - expires_at: Deal expiration if mentioned
        """
        
        prompt = self._build_extraction_prompt(post_title, post_content)
        
        try:
            response = self._call_llm(prompt)
            if not response:
                return None
                
            # Parse JSON response from LLM
            extracted = json.loads(response)
            
            # Validate required fields
            if not extracted.get('is_valid', False):
                logger.info(
                    "deal_rejected_by_llm",
                    reason=extracted.get('rejection_reason'),
                    url=post_url
                )
                return None
            
            logger.info(
                "deal_extracted_successfully",
                provider=extracted.get('provider_name'),
                url=post_url
            )
            
            return extracted
            
        except json.JSONDecodeError as e:
            logger.error(
                "llm_response_parse_failed",
                error=str(e),
                response=response[:200] if response else None
            )
            return None
        except Exception as e:
            logger.error(
                "llm_extraction_failed",
                error=str(e),
                url=post_url
            )
            return None
    
    def _build_extraction_prompt(self, title: str, content: str) -> str:
        """Build the extraction prompt for the LLM."""
        return f"""You are an expert at analyzing hosting deal forum posts. Extract structured information from the following post.

**Post Title:** {title}

**Post Content:**
{content[:3000]}  

**CRITICAL: First determine if this is a REAL HOSTING DEAL**
Set is_valid=false if the post is:
- A discussion, news article, or blog post (NOT a deal)
- A question asking for recommendations
- About non-hosting topics (AI, software reviews, charity drama, etc.)
- An expired or out-of-stock deal
- Missing actual pricing and hosting specs

Set is_valid=true ONLY if:
- It offers VPS, dedicated servers, shared hosting, or cloud services
- Has specific pricing (like $5/mo, €10/yr, etc.)
- Mentions actual specs (RAM, CPU, storage, bandwidth)
- Is from a hosting provider offering services

**For VALID deals, extract each pricing tier/configuration separately.**
Each configuration MUST include pricing and at least RAM + storage + bandwidth (or clearly stated equivalents).

**Output Format (JSON only, no markdown):**
{{
  "is_valid": true/false,
  "rejection_reason": "Not a hosting deal - discussion/news post" or null,
  "provider_name": "Official Company Name",
  "provider_domain": "company-website.com",
    "deal_type": "VPS|Dedicated|Shared|Cloud|Reseller|Other",
  "configurations": [
    {{
      "name": "Plan 1 / Small VPS",
            "cpu_brand": "AMD|Intel|ARM" or null,
            "cpu_model": "EPYC 7xx3" or null,
      "ram_mb": 1024,
      "cpu_cores": 1,
      "storage_gb": 20,
      "bandwidth_gb": 1000,
            "ipv4": 1,
            "ipv6": true,
            "storage_type": "NVMe" or null,
      "price_amount": 2.50,
      "price_currency": "USD",
      "billing_period": "month",
      "location": "Tokyo, Japan"
    }},
    {{
      "name": "Plan 2 / Medium VPS",
            "cpu_brand": "AMD|Intel|ARM" or null,
            "cpu_model": "EPYC 7xx3" or null,
      "ram_mb": 2048,
      "cpu_cores": 2,
      "storage_gb": 40,
      "bandwidth_gb": 2000,
            "ipv4": 1,
            "ipv6": true,
            "storage_type": "NVMe" or null,
      "price_amount": 5.00,
      "price_currency": "USD",
      "billing_period": "month",
      "location": "Tokyo, Japan"
    }}
  ],
  "locations": ["Tokyo, Japan", "US-East"],
  "highlights": ["NVMe Storage", "DDoS Protection"],
  "expires_at": "2025-12-31" or null,
  "order_url": "https://provider.com/order" or null
}}

**EXAMPLES of INVALID posts (set is_valid=false):**
- "Is FOSSBilling a WHMCS-Killer?" - software discussion
- "How Can There Possibly Be More Charity Host Drama?" - drama/news
- "When It Comes to AI, Are You a Maximalist?" - AI discussion
- "Whatever Happened About that Provider?" - discussion question
- "Nerding Out on LowEndTalk Stats" - statistics post

**Important:**
- Extract ALL configurations/plans mentioned as separate items
- Each configuration should have its own specs and price
- Include IPv4/IPv6 if mentioned (IPv4 as integer count; IPv6 as true/false)
- Include CPU brand/model/cores when available
- Provider domain must be the actual hosting company website, NOT forums
- Be strict about validation - only mark as valid if it's clearly an active deal
"""
    
    def _call_llm(self, prompt: str) -> Optional[str]:
        """Call the LLM API and return the response."""
        headers = {
            'Content-Type': 'application/json',
        }
        
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        payload = {
            'model': self.model,
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are a precise data extraction assistant. Always respond with valid JSON only, no markdown formatting.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.1,  # Low temperature for consistent extraction
            'stream': False
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 404:
                logger.error(
                    "llm_api_404",
                    url=self.api_url,
                    message="LLM endpoint returned 404. Check LLM_API_URL in .env"
                )
                return None
            
            response.raise_for_status()
            
            data = response.json()
            
            # Extract message content
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0]['message']['content']
                
                # Strip markdown code blocks if present
                content = content.strip()
                if content.startswith('```json'):
                    content = content[7:]
                if content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                
                return content.strip()
            
            return None
            
        except requests.RequestException as e:
            logger.error(
                "llm_api_request_failed",
                error=str(e),
                url=self.api_url
            )
            return None


# Singleton instance
_extractor_instance: Optional[LLMDealExtractor] = None


def get_llm_extractor() -> LLMDealExtractor:
    """Get or create the LLM extractor singleton."""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = LLMDealExtractor()
    return _extractor_instance
