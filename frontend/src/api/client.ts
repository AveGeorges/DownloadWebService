export type DownloadJob = {
  id: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  names_received: number;
  downloaded_count: number;
  total_known: number | null;
  error: string | null;
};

export type DownloadedFile = {
  id: string;
  filename: string;
  downloaded_at: string;
  size_bytes: number;
  job_id: string | null;
};

export type PaginatedFiles = {
  items: DownloadedFile[];
  total: number;
  limit: number;
  offset: number;
};

export type CalculationResult = {
  total: Record<string, number>;
  per_file: Array<{
    file_id: string;
    filename: string;
    counts: Record<string, number>;
  }>;
  errors: string[];
};

async function parseError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string };
    if (typeof body.detail === "string") {
      return body.detail;
    }
  } catch {
    // ignore
  }
  return `HTTP ${response.status}`;
}

export async function startDownloadJob(): Promise<DownloadJob> {
  const response = await fetch("/api/v1/download-jobs", { method: "POST" });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return (await response.json()) as DownloadJob;
}

export async function getDownloadJob(jobId: string): Promise<DownloadJob> {
  const response = await fetch(`/api/v1/download-jobs/${jobId}`);
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return (await response.json()) as DownloadJob;
}

export async function listFiles(limit: number, offset: number): Promise<PaginatedFiles> {
  const response = await fetch(`/api/v1/files?limit=${limit}&offset=${offset}`);
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return (await response.json()) as PaginatedFiles;
}

export async function selectAllFileIds(): Promise<string[]> {
  const response = await fetch("/api/v1/files/select-all-ids", { method: "POST" });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  const body = (await response.json()) as { ids: string[] };
  return body.ids;
}

export async function calculateStats(fileIds: string[]): Promise<CalculationResult> {
  const response = await fetch("/api/v1/calculations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_ids: fileIds }),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return (await response.json()) as CalculationResult;
}
