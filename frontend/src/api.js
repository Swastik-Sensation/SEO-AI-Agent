const API_BASE = 'http://localhost:8000';

export async function apiHealth() {
  const r = await fetch(`${API_BASE}/api/health`);
  return r.json();
}

export async function apiDetectNiche(url, maxPages = 5) {
  const r = await fetch(`${API_BASE}/api/detect-niche`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, max_pages: maxPages }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function apiStartAudit({ url, niche, maxPages = 25, useAi = true }) {
  const r = await fetch(`${API_BASE}/api/audit/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, niche, max_pages: maxPages, use_ai: useAi }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function apiGetStatus(jobId) {
  const r = await fetch(`${API_BASE}/api/audit/${jobId}/status`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function apiGetResult(jobId) {
  const r = await fetch(`${API_BASE}/api/audit/${jobId}/result`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function apiStartOpportunitySearch({
  url, projectName, niche, location, targetAudience, linksPerCategory = 50,
  checkPresence = true, brandHandles = [], teamSheetId = null, backlinkExportId = null,
  linkSuffix = '', linkSuffixes = [],
}) {
  const r = await fetch(`${API_BASE}/api/opportunities/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url,
      project_name: projectName,
      niche,
      location,
      target_audience: targetAudience,
      links_per_category: linksPerCategory,
      check_presence: checkPresence,
      brand_handles: brandHandles,
      team_sheet_id: teamSheetId,
      backlink_export_id: backlinkExportId,
      link_suffix: linkSuffix,
      link_suffixes: linkSuffixes,
    }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function apiGetOpportunityStatus(jobId) {
  const r = await fetch(`${API_BASE}/api/opportunities/${jobId}/status`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function apiGetOpportunityResult(jobId) {
  const r = await fetch(`${API_BASE}/api/opportunities/${jobId}/result`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export function getDownloadUrl(jobId, type) {
  return `${API_BASE}/api/audit/${jobId}/download/${type}`;
}

export function getOpportunityDownloadUrl(jobId) {
  return `${API_BASE}/api/opportunities/${jobId}/download/csv`;
}

export function getOpportunityXlsxDownloadUrl(jobId) {
  return `${API_BASE}/api/opportunities/${jobId}/download/xlsx`;
}

export async function apiListJobs() {
  const r = await fetch(`${API_BASE}/api/jobs`);
  return r.json();
}

export async function apiStartBlogCheck({ projectUrl, blogUrl, niche, focusKeyword, checkLinks }) {
  const r = await fetch(`${API_BASE}/api/blog-checker/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      project_url: projectUrl,
      blog_url: blogUrl,
      niche: niche || undefined,
      focus_keyword: focusKeyword || undefined,
      check_links: Boolean(checkLinks),
    }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function apiGetBlogStatus(jobId) {
  const r = await fetch(`${API_BASE}/api/blog-checker/${jobId}/status`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function apiGetBlogResult(jobId) {
  const r = await fetch(`${API_BASE}/api/blog-checker/${jobId}/result`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export function getBlogDownloadUrl(jobId) {
  return `${API_BASE}/api/blog-checker/${jobId}/download/csv`;
}

export async function apiStartProfileCheck({ projectUrl, profileUrl, businessName, niche, maxPosts = 5 }) {
  const r = await fetch(`${API_BASE}/api/profile-checker/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      project_url: projectUrl,
      profile_url: profileUrl,
      business_name: businessName || undefined,
      niche: niche || undefined,
      max_posts: Number(maxPosts) || 5,
    }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function apiGetProfileStatus(jobId) {
  const r = await fetch(`${API_BASE}/api/profile-checker/${jobId}/status`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function apiGetProfileResult(jobId) {
  const r = await fetch(`${API_BASE}/api/profile-checker/${jobId}/result`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export function getProfileDownloadUrl(jobId) {
  return `${API_BASE}/api/profile-checker/${jobId}/download/csv`;
}

export async function apiStartPublisherSearch({ niche, location, keywords, maxPublishers = 20 }) {
  const r = await fetch(`${API_BASE}/api/publishers/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      niche,
      location: location || undefined,
      keywords: keywords || undefined,
      max_publishers: Number(maxPublishers) || 20,
    }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function apiGetPublisherStatus(jobId) {
  const r = await fetch(`${API_BASE}/api/publishers/${jobId}/status`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function apiGetPublisherResult(jobId) {
  const r = await fetch(`${API_BASE}/api/publishers/${jobId}/result`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export function getPublisherXlsxDownloadUrl(jobId) {
  return `${API_BASE}/api/publishers/${jobId}/download/xlsx`;
}

export function getPublisherCsvDownloadUrl(jobId) {
  return `${API_BASE}/api/publishers/${jobId}/download/csv`;
}


