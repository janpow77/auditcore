"""Bilder dekodieren, Metadaten entfernen und als begrenztes PNG neu schreiben."""

from dataclasses import dataclass
from datetime import timedelta
from io import BytesIO
from uuid import uuid4

from .errors import AccountError, require
from .models import Actor, Asset
from .permissions import authenticated, authorize
from .runtime import Runtime


@dataclass(frozen=True)
class ImagePolicy:
    max_bytes: int
    max_pixels: int
    output_size: int
    preview_size: int
    draft_lifetime: timedelta


@dataclass(frozen=True)
class Crop:
    x: float
    y: float
    size: float


def sanitize_image(data: bytes, policy: ImagePolicy, crop: Crop | None) -> tuple[bytes, bytes]:
    from PIL import Image, ImageOps, UnidentifiedImageError

    require(0 < len(data) <= policy.max_bytes, "invalid_image", "Bilddatei zu groß oder leer.")
    try:
        with Image.open(BytesIO(data)) as source:
            require(
                source.format in {"JPEG", "PNG", "WEBP"},
                "invalid_image",
                "JPEG, PNG oder WebP erforderlich.",
            )
            require(
                source.width * source.height <= policy.max_pixels,
                "invalid_image",
                "Bildauflösung zu groß.",
            )
            require(
                getattr(source, "n_frames", 1) == 1,
                "invalid_image",
                "Animierte Bilder nicht unterstützt.",
            )
            image = ImageOps.exif_transpose(source).convert("RGBA")
            if crop:
                require(
                    0 < crop.size <= 1
                    and 0 <= crop.x <= 1 - crop.size
                    and 0 <= crop.y <= 1 - crop.size,
                    "invalid_crop",
                    "Ungültiger Bildausschnitt.",
                )
                edge = min(image.size) * crop.size
                left, top = crop.x * image.width, crop.y * image.height
                image = image.crop((round(left), round(top), round(left + edge), round(top + edge)))
            outputs: list[bytes] = []
            for size in (policy.output_size, policy.preview_size):
                result = image.copy()
                result.thumbnail((size, size))
                result.info.clear()
                stream = BytesIO()
                result.save(stream, format="PNG")
                outputs.append(stream.getvalue())
            return outputs[0], outputs[1]
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as error:
        raise AccountError("invalid_image", "Bild konnte nicht verarbeitet werden.") from error


class AssetService:
    def __init__(self, runtime: Runtime, policy: ImagePolicy) -> None:
        require(
            min(policy.max_bytes, policy.max_pixels, policy.output_size, policy.preview_size) > 0
            and policy.draft_lifetime.total_seconds() > 0,
            "invalid",
            "Bildgrenzen müssen positiv sein.",
        )
        self.runtime, self.policy = runtime, policy

    def upload(
        self, actor: Actor, data: bytes, *, tenant_id: str = "", crop: Crop | None = None
    ) -> str:
        with self.runtime.repository.transaction() as state:
            authenticated(state, actor)
            if tenant_id:
                authorize(state, actor, tenant_id, "branding.update")
            content, preview = sanitize_image(data, self.policy, crop)
            asset = Asset(
                uuid4().hex,
                actor.account_id,
                tenant_id,
                content,
                preview,
                "image/png",
                self.runtime.now() + self.policy.draft_lifetime,
            )
            state.assets[asset.id] = asset
            return asset.id

    def read(self, actor: Actor, asset_id: str, *, preview: bool = False) -> bytes:
        with self.runtime.repository.transaction() as state:
            account = authenticated(state, actor)
            asset = state.assets.get(asset_id)
            require(asset is not None, "not_found", "Bild nicht verfügbar.")
            assert asset is not None
            if asset.attached and asset.tenant_id:
                authorize(state, actor, asset.tenant_id, "tenant.read")
            else:
                require(
                    asset.owner_id == account.id
                    or account.platform_admin
                    or account.image_id == asset.id,
                    "forbidden",
                    "Bild nicht zugänglich.",
                )
            require(
                asset.attached or asset.expires_at > self.runtime.now(),
                "expired",
                "Bildentwurf abgelaufen.",
            )
            return asset.preview if preview else asset.content

    def purge_drafts(self) -> int:
        """Host-Aufräumjob; nur nicht zugeordnete, abgelaufene Entwürfe."""
        with self.runtime.repository.transaction() as state:
            expired = [
                key
                for key, asset in state.assets.items()
                if not asset.attached and asset.expires_at <= self.runtime.now()
            ]
            for key in expired:
                del state.assets[key]
            return len(expired)
