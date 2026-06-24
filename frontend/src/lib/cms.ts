/** Types mirroring the Django CMS serializer output for service pages. */

export interface CmsStep {
  number: string;
  title: string;
  description: string;
  order: number;
}

export interface CmsFeatureItem {
  text: string;
  order: number;
}

export interface CmsFeatureGroup {
  title: string;
  items: CmsFeatureItem[];
  order: number;
}

export interface CmsFAQ {
  question: string;
  answer: string;
  order: number;
}

export interface CmsImage {
  url: string;
  alt: string;
  caption: string;
  order: number;
}

export interface CmsServicePage {
  slug: string;
  hero_image_url: string | null;
  hero_image_alt: string;
  tagline: string;
  description: string;
  meta_title: string;
  meta_description: string;
  papermoon_does: string[];
  client_does: string[];
  steps: CmsStep[];
  feature_groups: CmsFeatureGroup[];
  faqs: CmsFAQ[];
  images: CmsImage[];
  updated_at: string;
}

// Call Django directly (avoids self-referential HTTP in the container — localhost
// resolves to IPv6 ::1 in Docker but Next.js only binds IPv4 0.0.0.0:3000).
const DJANGO_URL =
  process.env.DJANGO_INTERNAL_URL ?? "http://localhost:8000/api/v1";

/** Fetch CMS data for a service page slug. Returns null if not found. */
export async function fetchCmsServicePage(
  slug: string
): Promise<CmsServicePage | null> {
  try {
    const res = await fetch(`${DJANGO_URL}/cms/services/${slug}/`, {
      next: { revalidate: 60, tags: [`service-page-${slug}`] },
    });
    if (!res.ok) return null;
    const json = await res.json();
    // Unwrap Django unified response envelope { success, data, error }
    return (json?.data ?? json) as CmsServicePage | null;
  } catch {
    return null;
  }
}
