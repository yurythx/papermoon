import type { CmsServicePage } from "@/lib/cms";
import type { ServiceContent } from "@/lib/services-content";

export interface GalleryImage {
  url: string;
  alt: string;
  caption: string;
}

/** ServiceContent enriched with CMS-sourced gallery images. */
export interface MergedService extends ServiceContent {
  galleryImages: GalleryImage[];
}

/**
 * Merge CMS data onto the static service definition.
 * CMS fields take priority when non-empty; static fields are the fallback.
 * Only overrides fields the CMS actually has content for — a blank CMS tagline
 * does not erase a filled static tagline.
 */
export function mergeService(
  base: ServiceContent,
  cms: CmsServicePage | null
): MergedService {
  const fallbackGalleryImages = base.screenshots.map((image) => ({
    url: image.src,
    alt: image.alt,
    caption: image.caption,
  }));

  if (!cms) return { ...base, galleryImages: fallbackGalleryImages };

  const cmsGalleryImages = cms.images
    .filter((img) => !!img.url)
    .map((img) => ({ url: img.url, alt: img.alt, caption: img.caption }));

  return {
    ...base,
    tagline: cms.tagline || base.tagline,
    description: cms.description || base.description,
    heroImage: cms.hero_image_url || base.heroImage,
    heroImageAlt: cms.hero_image_alt || base.heroImageAlt,
    metaTitle: cms.meta_title || base.metaTitle,
    metaDescription: cms.meta_description || base.metaDescription,
    papermoonDoes:
      cms.papermoon_does.length > 0 ? cms.papermoon_does : base.papermoonDoes,
    clientDoes:
      cms.client_does.length > 0 ? cms.client_does : base.clientDoes,
    steps:
      cms.steps.length > 0
        ? cms.steps.map((s) => ({
            num: String(s.number),
            title: s.title,
            description: s.description,
          }))
        : base.steps,
    featureGroups:
      cms.feature_groups.length > 0
        ? cms.feature_groups.map((g) => ({
            title: g.title,
            items: g.items.map((i) => i.text),
          }))
        : base.featureGroups,
    faqs:
      cms.faqs.length > 0
        ? cms.faqs.map((f) => ({ q: f.question, a: f.answer }))
        : base.faqs,
    galleryImages: cmsGalleryImages.length > 0 ? cmsGalleryImages : fallbackGalleryImages,
  };
}
