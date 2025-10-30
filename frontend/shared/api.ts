/**
 * Shared code between client and server
 * Useful to share types between client and server
 * and/or small pure JS functions that can be used on both client and server
 */

// API Types for Closing Disclosure Analyzer

export interface LoanTerms {
  loan_amount?: number;
  interest_rate_pct?: number;
  apr?: number;
  monthly_principal_interest?: number;
  prepayment_penalty?: boolean | { has?: boolean };
  balloon_payment?: boolean | { has?: boolean };
}

export interface LoanInformation {
  loan_term_years?: number;
  product?: string;
  loan_type?: string;
}

export interface LoanCalculations {
  apr_pct?: number;
}

export interface BorrowersTransaction {
  cash_to_close_amount?: number;
  cash_to_close_direction?: string;
}

export interface SummariesOfTransactions {
  borrowers_transaction?: BorrowersTransaction;
}

export interface ExtractedData {
  loan_terms?: LoanTerms;
  loan_information?: LoanInformation;
  loan_calculations?: LoanCalculations;
  summaries_of_transactions?: SummariesOfTransactions;
  confidence_notes?: string[];
}

export interface ReportItem {
  section: string;
  label: string;
  observed?: string | number;
  expected?: string;
  status: "PASS" | "WARN" | "FAIL";
  note?: string;
  rule?: string;
  computed?: {
    loan_amount?: number;
  };
}

export interface Report {
  verdict: "PASS" | "WARN" | "FAIL";
  items: ReportItem[];
}

export interface AnalysisResponse {
  ok: boolean;
  error?: string;
  extracted?: ExtractedData;
  report?: Report;
}

export interface SummaryResponse {
  summary: string;
}

export interface FileInfo {
  file_name: string;
  name: string;
  title?: string;
  path: string;
  size?: number;
  summary?: string[];
  fullSummary?: string[];
}


// export interface FileInfo {
//   name: string;
//   title?: string;
//   path: string;
//   size: number;
//   summary?: string[];
//   fullSummary?: string[];
//   previewSummary?: string[];
// }

export interface UploadResponse {
  success: boolean;
  message?: string;
  files?: FileInfo[];
  error?: string;
}

// API Functions
function getApiBase(): string {
  // Client-side only: access Vite env vars
  if (typeof window !== 'undefined') {
    return (import.meta as any).env?.VITE_API_BASE || "http://127.0.0.1:8000";
  }
  return "http://127.0.0.1:8000";
}

function getFlaskApiBase(): string {
  // Flask backend API base URL
  if (typeof window !== 'undefined') {
    return (import.meta as any).env?.VITE_BACKEND_URL || "http://127.0.0.1:5000";
  }
  return "http://127.0.0.1:5000";
}

export async function analyzeClosingDisclosure(
  file: File,
  fastMode: boolean = true
): Promise<AnalysisResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${getApiBase()}/api/analyze?fast=${fastMode}`, {
    method: "POST",
    body: formData,
  });

  const json = await response.json();

  if (!json.ok) {
    throw new Error(json.error || "Analysis failed");
  }

  return json;
}

export async function generateSummary(items: ReportItem[]): Promise<string> {
  const response = await fetch(`${getApiBase()}/api/summary`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(items),
  });

  const json: SummaryResponse = await response.json();
  return json.summary || "";
}


export async function uploadFileToFlask(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(`${getFlaskApiBase()}/api/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `Upload failed with status: ${response.status}`);
    }

    const data: UploadResponse = await response.json();

    // Ensure we have the correct structure
    if (!data.success) {
      throw new Error(data.error || "Upload failed");
    }

    return data;
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Upload failed",
    };
  }
}
