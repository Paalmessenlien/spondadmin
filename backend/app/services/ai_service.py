"""
AI Service - reusable abstraction for calling AI providers.

Usage:
    from app.services.ai_service import AIService

    result = await AIService.chat(
        db,
        messages=[{"role": "user", "content": "Hello"}],
        provider="openai",  # or None for auto-select
    )
    print(result["content"])
"""
import time
import logging
from datetime import datetime
from typing import Optional, List, Dict

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_provider_config_service import AIProviderConfigService

logger = logging.getLogger(__name__)

# Default base URLs
OPENAI_BASE_URL = "https://api.openai.com/v1"
ANTHROPIC_BASE_URL = "https://api.anthropic.com"


class AIService:
    @staticmethod
    async def chat(
        db: AsyncSession,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> dict:
        """
        Send a chat request to an AI provider.

        Args:
            db: Database session
            messages: List of message dicts with 'role' and 'content'
            provider: Provider name or None for auto-select
            model: Model override or None to use provider default
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            dict with keys: provider, model, content, usage
        """
        if provider:
            config = await AIProviderConfigService.get_by_provider(db, provider)
            if not config:
                raise ValueError(f"Unknown provider: {provider}")
        else:
            config = await AIProviderConfigService.get_first_enabled(db)
            if not config:
                raise ValueError("No AI provider is enabled. Configure one in Settings > AI Providers.")

        if not config.api_key_encrypted:
            raise ValueError(f"No API key configured for {config.display_name}")
        if not config.is_enabled:
            raise ValueError(f"{config.display_name} is not enabled")

        api_key = AIProviderConfigService.get_decrypted_key(config)
        use_model = model or config.default_model

        if config.provider == "anthropic":
            return await AIService._call_anthropic(api_key, messages, use_model, max_tokens, temperature)
        else:
            base_url = config.base_url or OPENAI_BASE_URL
            return await AIService._call_openai_compatible(
                api_key, messages, use_model, max_tokens, temperature, base_url, config.provider
            )

    @staticmethod
    async def _call_openai_compatible(
        api_key: str,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
        base_url: str,
        provider_name: str,
    ) -> dict:
        """Call OpenAI or OpenAI-compatible API (DeepSeek) via httpx."""
        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=headers)

        if resp.status_code != 200:
            error_body = resp.text
            try:
                error_data = resp.json()
                error_msg = error_data.get("error", {}).get("message", error_body)
            except Exception:
                error_msg = error_body
            raise ValueError(f"API error ({resp.status_code}): {error_msg}")

        data = resp.json()
        choice = data["choices"][0]
        usage = None
        if "usage" in data:
            usage = {
                "prompt_tokens": data["usage"].get("prompt_tokens"),
                "completion_tokens": data["usage"].get("completion_tokens"),
                "total_tokens": data["usage"].get("total_tokens"),
            }

        message = choice.get("message", {})
        content = message.get("content", "")

        # DeepSeek-R1 models use reasoning_content for chain-of-thought
        # and may leave content empty. Fall back to reasoning_content.
        if not content and message.get("reasoning_content"):
            content = message["reasoning_content"]

        return {
            "provider": provider_name,
            "model": data.get("model", model),
            "content": content,
            "usage": usage,
        }

    @staticmethod
    async def _call_anthropic(
        api_key: str,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> dict:
        """Call Anthropic Claude API via httpx."""
        url = f"{ANTHROPIC_BASE_URL}/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        # Extract system message if present
        system_text = None
        chat_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system_text = msg["content"]
            else:
                chat_messages.append(msg)

        payload = {
            "model": model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_text:
            payload["system"] = system_text

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=headers)

        if resp.status_code != 200:
            error_body = resp.text
            try:
                error_data = resp.json()
                error_msg = error_data.get("error", {}).get("message", error_body)
            except Exception:
                error_msg = error_body
            raise ValueError(f"API error ({resp.status_code}): {error_msg}")

        data = resp.json()
        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")

        usage = None
        if "usage" in data:
            usage = {
                "prompt_tokens": data["usage"].get("input_tokens"),
                "completion_tokens": data["usage"].get("output_tokens"),
                "total_tokens": (data["usage"].get("input_tokens", 0) +
                                 data["usage"].get("output_tokens", 0)),
            }

        return {
            "provider": "anthropic",
            "model": data.get("model", model),
            "content": content,
            "usage": usage,
        }

    # ---- Receipt OCR (vision) -------------------------------------------

    # Vision-capable providers, in preference order. DeepSeek is text-only and
    # is deliberately excluded — receipt OCR needs to actually see the image.
    VISION_PROVIDERS = ("anthropic", "openai")

    # Controlled expense categories the model may choose. Mirrors
    # app.models.expense.EXPENSE_CATEGORIES.
    RECEIPT_CATEGORIES = (
        "utstyr", "reise", "bevertning", "kontor", "premier", "bane_anlegg", "kurs", "annet",
    )

    @staticmethod
    def _preprocess_receipt(image_bytes: bytes, mime_type: str) -> tuple[bytes, str]:
        """Normalise a receipt photo: HEIC→JPEG, downscale, strip EXIF.

        Caps the longest edge at 1600px to keep vision token cost sane. Falls
        back to the original bytes if Pillow (or HEIF support) isn't available.
        """
        try:
            import io
            from PIL import Image, ImageOps
            try:
                import pillow_heif  # noqa: F401
                pillow_heif.register_heif_opener()
            except Exception:
                pass

            img = Image.open(io.BytesIO(image_bytes))
            # Honour EXIF orientation before we re-encode (which drops EXIF),
            # so rotated phone photos reach the vision model upright.
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")
            max_edge = 1600
            if max(img.size) > max_edge:
                ratio = max_edge / max(img.size)
                img = img.resize((int(img.width * ratio), int(img.height * ratio)))
            out = io.BytesIO()
            img.save(out, format="JPEG", quality=85)
            return out.getvalue(), "image/jpeg"
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Receipt preprocessing failed, using original bytes: {e}")
            return image_bytes, mime_type

    @staticmethod
    async def extract_receipt(
        db: AsyncSession,
        image_bytes: bytes,
        mime_type: str,
        provider: Optional[str] = None,
    ) -> Optional[dict]:
        """OCR a receipt image via a vision-capable provider; return suggested
        fields, or ``None`` if no vision provider is enabled.

        Returns dict: {amount, currency, date(YYYY-MM-DD), payee, category,
        description, _provider, _model}. All values may be null if unreadable.
        """
        import base64
        import json
        import re

        candidates = [provider] if provider else list(AIService.VISION_PROVIDERS)
        config = None
        api_key = None
        for name in candidates:
            c = await AIProviderConfigService.get_by_provider(db, name)
            if not (c and c.is_enabled and c.api_key_encrypted):
                continue
            try:
                api_key = AIProviderConfigService.get_decrypted_key(c)
            except Exception as e:  # noqa: BLE001 - bad/rotated key, try next provider
                logger.warning(f"Vision provider {name} key undecryptable, skipping: {e}")
                continue
            config = c
            break
        if not config or not api_key:
            logger.info("Receipt OCR skipped: no usable vision provider enabled")
            return None

        model = config.default_model
        norm_bytes, norm_mime = AIService._preprocess_receipt(image_bytes, mime_type)
        b64 = base64.b64encode(norm_bytes).decode()

        cats = ", ".join(AIService.RECEIPT_CATEGORIES)
        system = (
            "Du leser kvitteringer for et norsk idrettslag. Returner KUN gyldig JSON "
            "med feltene: amount (tall, totalbeløp), currency (ISO, f.eks. NOK), "
            "date (YYYY-MM-DD, kjøpsdato), payee (butikk/leverandør), "
            f"category (én av: {cats}), description (kort norsk beskrivelse av kjøpet). "
            "Bruk null for felter du ikke finner. Ingen tekst utenom JSON-objektet."
        )

        if config.provider == "anthropic":
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": [
                    {"type": "image", "source": {
                        "type": "base64", "media_type": norm_mime, "data": b64,
                    }},
                    {"type": "text", "text": "Les kvitteringen og returner JSON."},
                ]},
            ]
            result = await AIService._call_anthropic(api_key, messages, model, 1024, 0.1)
        else:
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": [
                    {"type": "text", "text": "Les kvitteringen og returner JSON."},
                    {"type": "image_url", "image_url": {
                        "url": f"data:{norm_mime};base64,{b64}",
                    }},
                ]},
            ]
            base_url = config.base_url or OPENAI_BASE_URL
            result = await AIService._call_openai_compatible(
                api_key, messages, model, 1024, 0.1, base_url, config.provider
            )

        content = (result.get("content") or "").strip()
        parsed = None
        try:
            parsed = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            if "```" in content:
                m = re.search(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)
                if m:
                    try:
                        parsed = json.loads(m.group(1).strip())
                    except (json.JSONDecodeError, ValueError):
                        pass
            if parsed is None:
                m = re.search(r"\{.*\}", content, re.DOTALL)
                if m:
                    try:
                        parsed = json.loads(m.group(0))
                    except (json.JSONDecodeError, ValueError):
                        pass
        if not isinstance(parsed, dict):
            logger.warning(f"Receipt OCR returned unparseable content: {content[:200]!r}")
            return None

        category = parsed.get("category")
        if category not in AIService.RECEIPT_CATEGORIES:
            category = None
        return {
            "amount": parsed.get("amount"),
            "currency": parsed.get("currency") or "NOK",
            "date": parsed.get("date"),
            "payee": parsed.get("payee"),
            "category": category,
            "description": parsed.get("description"),
            "_provider": config.provider,
            "_model": result.get("model", model),
        }

    @staticmethod
    async def test_credentials(db: AsyncSession, provider: str) -> dict:
        """
        Test provider credentials with a simple request.

        Returns dict with: provider, status, message, model_used, response_time_ms
        """
        config = await AIProviderConfigService.get_by_provider(db, provider)
        if not config:
            return {"provider": provider, "status": "failed", "message": "Unknown provider"}

        if not config.api_key_encrypted:
            return {"provider": provider, "status": "failed", "message": "No API key configured"}

        start_time = time.time()
        try:
            result = await AIService.chat(
                db,
                messages=[{"role": "user", "content": "Say 'ok' and nothing else."}],
                provider=provider,
                max_tokens=10,
                temperature=0,
            )
            elapsed_ms = int((time.time() - start_time) * 1000)

            # Update test status
            config.last_tested_at = datetime.utcnow()
            config.test_status = "success"
            config.test_error = None
            await db.flush()

            return {
                "provider": provider,
                "status": "success",
                "message": f"Successfully connected to {config.display_name}",
                "model_used": result.get("model"),
                "response_time_ms": elapsed_ms,
            }
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)

            # Update test status
            config.last_tested_at = datetime.utcnow()
            config.test_status = "failed"
            config.test_error = error_msg
            await db.flush()

            return {
                "provider": provider,
                "status": "failed",
                "message": error_msg,
                "response_time_ms": elapsed_ms,
            }
